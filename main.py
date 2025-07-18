from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import barcode
from barcode.writer import ImageWriter
import io
import base64
from PIL import Image
import uvicorn
import traceback

# Initialize FastAPI app
app = FastAPI(
    title="Barcode Generator API",
    description="Generate barcode images in various formats (UPC, EAN, Code 128, etc.)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Supported barcode formats
SUPPORTED_FORMATS = {
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

# Pydantic models
class BarcodeRequest(BaseModel):
    data: str
    format: Literal[
        "code128", "code39", "ean8", "ean13", "ean14", 
        "jan", "upc", "isbn10", "isbn13", "issn", "itf", "pzn"
    ]
    width: Optional[float] = 2.0
    height: Optional[float] = 15.0
    quiet_zone: Optional[float] = 6.5
    font_size: Optional[int] = 10
    text_distance: Optional[float] = 5.0
    background: Optional[str] = "white"
    foreground: Optional[str] = "black"

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Data cannot be empty')
        return v.strip()

    @field_validator('width', 'height', 'quiet_zone', 'text_distance')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Value must be positive')
        return v

    @field_validator('font_size')
    @classmethod
    def validate_font_size(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('Font size must be between 1 and 100')
        return v

class BarcodeResponse(BaseModel):
    success: bool
    format: str
    data: str
    image_base64: Optional[str] = None
    message: Optional[str] = None

# Helper functions
def validate_barcode_data(data: str, format_name: str) -> bool:
    """Validate if data is appropriate for the given barcode format"""
    try:
        # For most formats, we'll let the barcode library handle validation
        # Only strict validation for formats that require specific lengths
        if format_name == "ean8":
            return len(data) == 7 and data.isdigit()
        elif format_name == "ean13":
            return len(data) == 12 and data.isdigit()
        elif format_name == "upc":
            return len(data) == 11 and data.isdigit()
        elif format_name == "isbn10":
            return len(data) == 9 and data.isdigit()
        elif format_name == "isbn13":
            return len(data) == 12 and data.isdigit()
        # For other formats, allow the library to validate
        return True
    except:
        return False

def generate_barcode_image(request: BarcodeRequest) -> io.BytesIO:
    """Generate barcode image and return as BytesIO"""
    try:
        # Get barcode class
        barcode_class = SUPPORTED_FORMATS[request.format]
        
        # Create writer with custom options
        writer = ImageWriter()
        writer.format = 'PNG'
        
        # Set writer options
        options = {
            'module_width': request.width,
            'module_height': request.height,
            'quiet_zone': request.quiet_zone,
            'font_size': request.font_size,
            'text_distance': request.text_distance,
            'background': request.background,
            'foreground': request.foreground,
        }
        
        # Generate barcode - let the library handle most validation
        try:
            code = barcode_class(request.data, writer=writer)
        except Exception as e:
            # If the barcode library fails, provide a helpful error message
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid data '{request.data}' for format '{request.format}': {str(e)}"
            )
        
        # Save to BytesIO
        buffer = io.BytesIO()
        code.write(buffer, options=options)
        buffer.seek(0)
        
        return buffer
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full traceback for debugging
        print(f"Unexpected error in generate_barcode_image: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating barcode: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Barcode Generator API",
        "version": "1.0.0",
        "supported_formats": list(SUPPORTED_FORMATS.keys()),
        "endpoints": {
            "generate": "/generate",
            "generate_image": "/generate/image",
            "formats": "/formats",
            "docs": "/docs"
        }
    }

@app.get("/formats")
async def get_supported_formats():
    """Get list of supported barcode formats"""
    return {
        "supported_formats": list(SUPPORTED_FORMATS.keys()),
        "format_details": {
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
            "pzn": "PZN - Pharmazentralnummer"
        }
    }

@app.post("/generate", response_model=BarcodeResponse)
async def generate_barcode(request: BarcodeRequest):
    """Generate barcode and return as base64 encoded image"""
    try:
        # For most formats, let the barcode library handle validation
        # Only do strict pre-validation for formats that definitely need it
        if request.format in ["ean8", "ean13", "upc", "isbn10", "isbn13"]:
            if not validate_barcode_data(request.data, request.format):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid data length or format for {request.format}. Expected numeric data with specific length."
                )
        
        # Generate barcode image
        image_buffer = generate_barcode_image(request)
        
        # Convert to base64
        image_base64 = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
        
        return BarcodeResponse(
            success=True,
            format=request.format,
            data=request.data,
            image_base64=image_base64,
            message="Barcode generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in generate_barcode: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/generate/image")
async def generate_barcode_image_endpoint(request: BarcodeRequest):
    """Generate barcode and return as image file"""
    try:
        # For most formats, let the barcode library handle validation
        if request.format in ["ean8", "ean13", "upc", "isbn10", "isbn13"]:
            if not validate_barcode_data(request.data, request.format):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid data length or format for {request.format}. Expected numeric data with specific length."
                )
        
        # Generate barcode image
        image_buffer = generate_barcode_image(request)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(image_buffer.getvalue()),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=barcode_{request.format}_{request.data}.png"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in generate_barcode_image_endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/generate/quick")
async def quick_generate(
    data: str = Query(..., description="Data to encode in barcode"),
    format: str = Query("code128", description="Barcode format"),
    return_image: bool = Query(False, description="Return image file instead of base64")
):
    """Quick barcode generation with query parameters"""
    try:
        # Validate format
        if format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported format. Supported formats: {list(SUPPORTED_FORMATS.keys())}"
            )
        
        # Create request object with defaults
        request = BarcodeRequest(data=data, format=format)
        
        if return_image:
            return await generate_barcode_image_endpoint(request)
        else:
            return await generate_barcode(request)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "barcode-generator"}

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

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )