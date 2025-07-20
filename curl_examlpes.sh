#!/bin/bash
# cURL examples for the Barcode & QR Code Generator API v2.0

echo "Barcode & QR Code Generator API - cURL Examples"
echo "=============================================="

# 1. Get API info
echo "1. Get API info:"
curl -X GET "http://localhost:8000/" | jq .
echo

# 2. Get supported formats
echo "2. Get supported formats:"
curl -X GET "http://localhost:8000/supported-formats" | jq .
echo

# 3. Generate Code 128 barcode (base64)
echo "3. Generate Code 128 barcode (base64):"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "HELLO123", 
       "format": "code128",
       "return_format": "base64"
     }' | jq .
echo

# 4. Generate EAN-13 barcode with custom styling
echo "4. Generate EAN-13 barcode with custom styling:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "123456789012", 
       "format": "ean13",
       "return_format": "base64",
       "width": 3.0,
       "height": 20.0,
       "background_color": "white",
       "foreground_color": "black"
     }' | jq .
echo

# 5. Download UPC barcode as image file
echo "5. Download UPC barcode as image file:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "12345678901", 
       "format": "upc",
       "return_format": "image"
     }' \
     --output upc_barcode.png
echo "UPC barcode saved as upc_barcode.png"
echo

# 6. Generate QR code (base64)
echo "6. Generate QR code (base64):"
curl -X POST "http://localhost:8000/create-qr-code" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "https://example.com",
       "return_format": "base64",
       "error_correction": "M"
     }' | jq .
echo

# 7. Generate QR code with high error correction
echo "7. Generate QR code with high error correction:"
curl -X POST "http://localhost:8000/create-qr-code" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "This is a test QR code with lots of data!",
       "return_format": "base64",
       "error_correction": "H",
       "box_size": 15,
       "border": 2,
       "fill_color": "blue",
       "back_color": "yellow"
     }' | jq .
echo

# 8. Download QR code as image file
echo "8. Download QR code as image file:"
curl -X POST "http://localhost:8000/create-qr-code" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "Download this QR code!",
       "return_format": "image",
       "box_size": 12
     }' \
     --output qr_code.png
echo "QR code saved as qr_code.png"
echo

# 9. Scan an image for barcodes/QR codes (requires an image file)
echo "9. Scan image for codes (example - requires test image):"
echo "# First create a test QR code"
curl -X POST "http://localhost:8000/create-qr-code" \
     -H "Content-Type: application/json" \
     -d '{
       "data": "Test scan data",
       "return_format": "image"
     }' \
     --output test_qr.png

echo "# Now scan the image"
curl -X POST "http://localhost:8000/scan-image" \
     -F "image=@test_qr.png" | jq .
echo

# 10. Health check
echo "10. Health check:"
curl -X GET "http://localhost:8000/health" | jq .
echo

# 11. Generate different barcode types
echo "11. Generate different barcode types:"
echo "Code 39:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{"data": "CODE39", "format": "code39", "return_format": "base64"}' | jq .message
echo

echo "ITF:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{"data": "1234567890", "format": "itf", "return_format": "base64"}' | jq .message
echo

# 12. Error handling examples
echo "12. Error handling examples:"
echo "Invalid barcode format:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{"data": "test", "format": "invalid_format"}' | jq .
echo

echo "Empty data:"
curl -X POST "http://localhost:8000/create-barcode" \
     -H "Content-Type: application/json" \
     -d '{"data": "", "format": "code128"}' | jq .
echo

echo "Examples completed!"
echo "Note: Some examples create image files (*.png) in the current directory"