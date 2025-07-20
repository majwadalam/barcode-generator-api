from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Union
import barcode
from barcode.writer import ImageWriter
import qrcode
from qrcode.image.pil import PilImage
import io
import base64
from PIL import Image
import cv2
import numpy as np
from pyzbar import pyzbar
import uvicorn
import traceback

# Initialize FastAPI app with comprehensive OpenAPI metadata
app = FastAPI(
    title="Barcode & QR Code Generator API",
    description="""
    A comprehensive API for generating barcodes, QR codes, and scanning them from images.
    
    **Features:**
    - Generate various barcode formats (UPC, EAN, Code 128, etc.)
    - Generate QR codes with customizable options
    - Scan and decode barcodes/QR codes from uploaded images
    - Return results as base64 or image files
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Barcode Generator API",
        "url": "https://github.com/your-repo/barcode-generator-api",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Supported barcode formats
BARCODE_FORMATS = {
    "code128": barcode.Code128,
    "code39": barcode.Code39,
    "ean8": barcode.EAN8,
    "ean13": barcode.EAN13,
    "ean14": barcode.EAN14,
    "jan": barcode.JAN,
    "upc": barcode.UPCA,
    "isbn10": barcode.ISBN10,
    "isbn13": barcode.ISBN13,
    "issn": barcode.ISSN,
    "itf": barcode.ITF,
    "pzn": barcode.PZN,
}

# Pydantic Schemas

class BarcodeGenerationRequest(BaseModel):
    """Request schema for barcode generation"""
    data: str = Field(..., description="Data to encode in the barcode", min_length=1)
    format: Literal[
        "code128", "code39", "ean8", "ean13", "ean14", 
        "jan", "upc", "isbn10", "isbn13", "issn", "itf", "pzn"
    ] = Field(..., description="Barcode format to generate")
    return_format: Literal["base64", "image"] = Field(
        default="base64", 
        description="Return format: base64 string or downloadable image file"
    )
    
    # Styling options
    width: Optional[float] = Field(default=2.0, gt=0, description="Module width")
    height: Optional[float] = Field(default=15.0, gt=0, description="Module height") 
    quiet_zone: Optional[float] = Field(default=6.5, ge=0, description="Quiet zone width")
    font_size: Optional[int] = Field(default=10, ge=1, le=100, description="Font size for text")
    text_distance: Optional[float] = Field(default=5.0, ge=0, description="Distance between barcode and text")
    background_color: Optional[str] = Field(default="white", description="Background color")
    foreground_color: Optional[str] = Field(default="black", description="Foreground color")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        return v.strip()

class QRCodeGenerationRequest(BaseModel):
    """Request schema for QR code generation"""
    data: str = Field(..., description="Data to encode in the QR code", min_length=1)
    return_format: Literal["base64", "image"] = Field(
        default="base64",
        description="Return format: base64 string or downloadable image file"
    )
    
    # QR Code specific options
    version: Optional[int] = Field(default=1, ge=1, le=40, description="QR code version (1-40)")
    error_correction: Literal["L", "M", "Q", "H"] = Field(
        default="M", 
        description="Error correction level: L(~7%), M(~15%), Q(~25%), H(~30%)"
    )
    box_size: Optional[int] = Field(default=10, ge=1, description="Size of each box in pixels")
    border: Optional[int] = Field(default=4, ge=0, description="Border size in boxes")
    fill_color: Optional[str] = Field(default="black", description="Fill color")
    back_color: Optional[str] = Field(default="white", description="Background color")

class GenerationResponse(BaseModel):
    """Response schema for generation operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    format: str = Field(..., description="Format of the generated code")
    data: str = Field(..., description="Original data that was encoded")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image (only if return_format=base64)")
    message: str = Field(..., description="Status message")

class ScanResult(BaseModel):
    """Schema for individual scan result"""
    data: str = Field(..., description="Decoded data from the code")
    type: str = Field(..., description="Type of code detected (QRCODE, CODE128, etc.)")
    quality: Optional[int] = Field(None, description="Quality score of the detection")
    polygon: List[List[int]] = Field(..., description="Polygon coordinates of the detected code")

class ScanResponse(BaseModel):
    """Response schema for scanning operations"""
    success: bool = Field(..., description="Whether the scan was successful")
    codes_found: int = Field(..., description="Number of codes detected")
    results: List[ScanResult] = Field(..., description="List of detected codes")
    message: str = Field(..., description="Status message")

class SupportedFormatsResponse(BaseModel):
    """Response schema for supported formats"""
    barcode_formats: List[str] = Field(..., description="Supported barcode formats")
    qr_code_supported: bool = Field(..., description="Whether QR codes are supported")
    format_details: dict = Field(..., description="Detailed information about each format")

class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")

# Helper Functions

def create_barcode_image(request: BarcodeGenerationRequest) -> io.BytesIO:
    """Generate barcode image and return as BytesIO"""
    try:
        barcode_class = BARCODE_FORMATS[request.format]
        
        writer = ImageWriter()
        writer.format = 'PNG'
        
        options = {
            'module_width': request.width,
            'module_height': request.height,
            'quiet_zone': request.quiet_zone,
            'font_size': request.font_size,
            'text_distance': request.text_distance,
            'background': request.background_color,
            'foreground': request.foreground_color,
        }
        
        code = barcode_class(request.data, writer=writer)
        
        buffer = io.BytesIO()
        code.write(buffer, options=options)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to generate barcode: {str(e)}"
        )

def create_qr_code_image(request: QRCodeGenerationRequest) -> io.BytesIO:
    """Generate QR code image and return as BytesIO"""
    try:
        # Map error correction levels
        error_correction_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }
        
        qr = qrcode.QRCode(
            version=request.version,
            error_correction=error_correction_map[request.error_correction],
            box_size=request.box_size,
            border=request.border,
        )
        
        qr.add_data(request.data)
        qr.make(fit=True)
        
        img = qr.make_image(
            fill_color=request.fill_color,
            back_color=request.back_color,
            image_factory=PilImage
        )
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate QR code: {str(e)}"
        )

def scan_codes_from_image(image_data: bytes) -> List[ScanResult]:
    """Scan and decode barcodes/QR codes from image data"""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image format")
        
        # Convert to grayscale for better detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Decode barcodes and QR codes
        decoded_objects = pyzbar.decode(gray)
        
        results = []
        for obj in decoded_objects:
            # Convert polygon points to list format
            polygon = [[point.x, point.y] for point in obj.polygon]
            
            result = ScanResult(
                data=obj.data.decode('utf-8'),
                type=obj.type,
                quality=getattr(obj, 'quality', None),
                polygon=polygon
            )
            results.append(result)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scan image: {str(e)}"
        )

# API Endpoints

@app.get("/", 
         summary="API Information",
         description="Get basic information about the API and available endpoints")
async def get_api_info():
    """Root endpoint with API information"""
    return {
        "name": "Barcode & QR Code Generator API",
        "version": "2.0.0",
        "description": "Generate and scan barcodes and QR codes",
        "endpoints": {
            "create_barcode": "/create-barcode",
            "create_qr_code": "/create-qr-code", 
            "scan_image": "/scan-image",
            "supported_formats": "/supported-formats",
            "health": "/health",
            "documentation": "/docs"
        }
    }

@app.post("/create-barcode",
          response_model=GenerationResponse,
          summary="Generate Barcode",
          description="Generate a barcode in various formats with customizable styling options")
async def create_barcode(request: BarcodeGenerationRequest):
    """Generate a barcode with the specified format and options"""
    try:
        image_buffer = create_barcode_image(request)
        
        if request.return_format == "image":
            return StreamingResponse(
                io.BytesIO(image_buffer.getvalue()),
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=barcode_{request.format}_{request.data}.png"
                }
            )
        else:
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
            return GenerationResponse(
                success=True,
                format=request.format,
                data=request.data,
                image_base64=image_base64,
                message="Barcode generated successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/create-qr-code",
          response_model=GenerationResponse, 
          summary="Generate QR Code",
          description="Generate a QR code with customizable error correction and styling options")
async def create_qr_code(request: QRCodeGenerationRequest):
    """Generate a QR code with the specified options"""
    try:
        image_buffer = create_qr_code_image(request)
        
        if request.return_format == "image":
            return StreamingResponse(
                io.BytesIO(image_buffer.getvalue()),
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=qrcode_{hash(request.data)}.png"
                }
            )
        else:
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
            return GenerationResponse(
                success=True,
                format="qrcode",
                data=request.data,
                image_base64=image_base64,
                message="QR code generated successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/scan-image",
          response_model=ScanResponse,
          summary="Scan Barcodes and QR Codes", 
          description="Upload an image to scan and decode any barcodes or QR codes found")
async def scan_image(image: UploadFile = File(..., description="Image file containing barcodes or QR codes")):
    """Scan and decode barcodes/QR codes from an uploaded image"""
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read image data
        image_data = await image.read()
        
        # Scan for codes
        results = scan_codes_from_image(image_data)
        
        return ScanResponse(
            success=True,
            codes_found=len(results),
            results=results,
            message=f"Scan completed. Found {len(results)} code(s)."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/supported-formats",
         response_model=SupportedFormatsResponse,
         summary="Get Supported Formats",
         description="Get a list of all supported barcode formats and QR code capabilities")
async def get_supported_formats():
    """Get information about supported barcode formats and capabilities"""
    format_details = {
        "code128": "Code 128 - Variable length, alphanumeric",
        "code39": "Code 39 - Variable length, alphanumeric", 
        "ean8": "EAN-8 - 8 digits",
        "ean13": "EAN-13 - 13 digits",
        "ean14": "EAN-14 - 14 digits",
        "jan": "JAN - Japanese Article Number",
        "upc": "UPC-A - 12 digits",
        "isbn10": "ISBN-10 - 10 digits",
        "isbn13": "ISBN-13 - 13 digits", 
        "issn": "ISSN - International Standard Serial Number",
        "itf": "ITF - Interleaved 2 of 5",
        "pzn": "PZN - Pharmazentralnummer",
        "qrcode": "QR Code - Variable length, high capacity 2D code"
    }
    
    return SupportedFormatsResponse(
        barcode_formats=list(BARCODE_FORMATS.keys()),
        qr_code_supported=True,
        format_details=format_details
    )

@app.get("/health",
         response_model=HealthResponse,
         summary="Health Check",
         description="Check the health status of the API service")
async def health_check():
    """Health check endpoint for monitoring and load balancing"""
    return HealthResponse(
        status="healthy",
        service="barcode-qr-generator",
        version="2.0.0"
    )

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "detail": str(exc)}
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": "Endpoint not found"}
    )