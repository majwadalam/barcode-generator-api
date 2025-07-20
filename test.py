# test_barcode_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
import base64
import json

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "supported_formats" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_supported_formats():
    """Test getting supported formats"""
    response = client.get("/formats")
    assert response.status_code == 200
    data = response.json()
    assert "supported_formats" in data
    assert "code128" in data["supported_formats"]

def test_generate_barcode_code128():
    """Test generating Code 128 barcode"""
    payload = {
        "data": "TEST123",
        "format": "code128"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["format"] == "code128"
    assert data["data"] == "TEST123"
    assert "image_base64" in data
    
    # Verify base64 image is valid
    image_data = base64.b64decode(data["image_base64"])
    assert len(image_data) > 0

def test_generate_barcode_ean13():
    """Test generating EAN-13 barcode"""
    payload = {
        "data": "123456789012",
        "format": "ean13"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200

def test_generate_barcode_upc():
    """Test generating UPC barcode"""
    payload = {
        "data": "12345678901",
        "format": "upc"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200

def test_generate_barcode_image_endpoint():
    """Test generating barcode as image file"""
    payload = {
        "data": "TEST123",
        "format": "code128"
    }
    response = client.post("/generate/image", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_quick_generate():
    """Test quick generate with query parameters"""
    response = client.get("/generate/quick?data=TEST123&format=code128")
    assert response.status_code == 200

def test_quick_generate_image():
    """Test quick generate returning image"""
    response = client.get("/generate/quick?data=TEST123&format=code128&return_image=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_invalid_format():
    """Test invalid barcode format"""
    payload = {
        "data": "TEST123",
        "format": "invalid_format"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422  # Validation error

def test_empty_data():
    """Test empty data"""
    payload = {
        "data": "",
        "format": "code128"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422  # Validation error

def test_invalid_ean13_length():
    """Test invalid EAN-13 data length"""
    payload = {
        "data": "12345",  # Too short for EAN-13
        "format": "ean13"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 400

def test_custom_styling():
    """Test custom barcode styling"""
    payload = {
        "data": "STYLED123",
        "format": "code128",
        "width": 3.0,
        "height": 20.0,
        "background": "white",
        "foreground": "black",
        "font_size": 12
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] == True

# example_usage.py
"""
Example usage of the Barcode Generator API
"""
import requests
import base64
from io import BytesIO
from PIL import Image

# API base URL
BASE_URL = "http://localhost:8000"

def example_generate_barcode():
    """Example: Generate a Code 128 barcode"""
    url = f"{BASE_URL}/generate"
    payload = {
        "data": "EXAMPLE123",
        "format": "code128",
        "width": 2.5,
        "height": 15.0,
        "font_size": 12
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Barcode generated successfully!")
        print(f"Format: {data['format']}")
        print(f"Data: {data['data']}")
        
        # Save image from base64
        image_data = base64.b64decode(data['image_base64'])
        with open("barcode_example.png", "wb") as f:
            f.write(image_data)
        print("Barcode saved as 'barcode_example.png'")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def example_generate_upc():
    """Example: Generate a UPC barcode"""
    url = f"{BASE_URL}/generate"
    payload = {
        "data": "12345678901",  # 11 digits for UPC
        "format": "upc"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("UPC barcode generated successfully!")
    else:
        print(f"Error: {response.text}")

def example_generate_ean13():
    """Example: Generate an EAN-13 barcode"""
    url = f"{BASE_URL}/generate"
    payload = {
        "data": "123456789012",  # 12 digits for EAN-13
        "format": "ean13"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("EAN-13 barcode generated successfully!")
    else:
        print(f"Error: {response.text}")

def example_download_image():
    """Example: Download barcode as image file"""
    url = f"{BASE_URL}/generate/image"
    payload = {
        "data": "DOWNLOAD123",
        "format": "code128"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        with open("downloaded_barcode.png", "wb") as f:
            f.write(response.content)
        print("Barcode downloaded as 'downloaded_barcode.png'")
    else:
        print(f"Error: {response.text}")

def example_quick_generate():
    """Example: Quick generate with query parameters"""
    url = f"{BASE_URL}/generate/quick"
    params = {
        "data": "QUICK123",
        "format": "code128",
        "return_image": False
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("Quick barcode generated successfully!")
        print(response.json())
    else:
        print(f"Error: {response.text}")

def example_get_formats():
    """Example: Get supported formats"""
    url = f"{BASE_URL}/formats"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        formats = response.json()
        print("Supported formats:")
        for format_name in formats["supported_formats"]:
            print(f"- {format_name}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Barcode Generator API Examples")
    print("=" * 40)
    
    # Get supported formats
    example_get_formats()
    print()
    
    # Generate different types of barcodes
    example_generate_barcode()
    example_generate_upc()
    example_generate_ean13()
    example_download_image()
    example_quick_generate()

