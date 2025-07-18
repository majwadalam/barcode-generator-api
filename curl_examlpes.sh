# curl_examples.sh
#!/bin/bash
# cURL examples for the Barcode Generator API

echo "Barcode Generator API - cURL Examples"
echo "====================================="

# 1. Get API info
echo "1. Get API info:"
curl -X GET "http://localhost:8000/" | jq .
echo

# 2. Get supported formats
echo "2. Get supported formats:"
curl -X GET "http://localhost:8000/formats" | jq .
echo

# 3. Generate Code 128 barcode
echo "3. Generate Code 128 barcode:"
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"data": "HELLO123", "format": "code128"}' | jq .
echo

# 4. Generate EAN-13 barcode
echo "4. Generate EAN-13 barcode:"
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"data": "123456789012", "format": "ean13"}' | jq .
echo

# 5. Generate UPC barcode
echo "5. Generate UPC barcode:"
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"data": "12345678901", "format": "upc"}' | jq .
echo

# 6. Download barcode as image
echo "6. Download barcode as image:"
curl -X POST "http://localhost:8000/generate/image" \
     -H "Content-Type: application/json" \
     -d '{"data": "DOWNLOAD123", "format": "code128"}' \
     --output barcode.png
echo "Barcode saved as barcode.png"
echo

# 7. Quick generate with query parameters
echo "7. Quick generate:"
curl -X GET "http://localhost:8000/generate/quick?data=QUICK123&format=code128" | jq .
echo

# 8. Health check
echo "8. Health check:"
curl -X GET "http://localhost:8000/health" | jq .
echo