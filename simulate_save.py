import requests
import json
import base64
import io
from PIL import Image
import random

JID = "JhZCO1vxI7"
URL = f"http://127.0.0.1:8000/api/save_foto/{JID}/"

# Generate 512x512 image
print("Generating 512x512 image...")
img = Image.new('RGB', (512, 512), color = 'red')
buffer = io.BytesIO()
img.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
BASE64_IMG = f"data:image/png;base64,{img_str}"

payload = {
    "image": BASE64_IMG,
    "title": "Large Debug Image"
}

print(f"Sending request to {URL} with payload size {len(BASE64_IMG)} bytes...")
try:
    response = requests.post(URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
