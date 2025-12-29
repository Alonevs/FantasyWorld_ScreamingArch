import requests
import json

print("🧪 Probando conexión con Stable Diffusion...")
print("=" * 60)

url = "http://127.0.0.1:7861/sdapi/v1/txt2img"
payload = {
    "prompt": "test image, simple landscape, best quality",
    "negative_prompt": "bad quality, low quality",
    "steps": 10,
    "width": 512,
    "height": 512,
    "cfg_scale": 7,
    "sampler_name": "Euler a",
    "seed": -1
}

print(f"📍 URL: {url}")
print(f"📦 Payload: {json.dumps(payload, indent=2)}")
print("\n🔄 Enviando request...")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'images' in data and len(data['images']) > 0:
            img_b64 = data['images'][0]
            print(f"🎨 Imagen recibida: {len(img_b64)} caracteres base64")
            print("✅ STABLE DIFFUSION FUNCIONA CORRECTAMENTE")
        else:
            print(f"❌ Respuesta sin imágenes: {data}")
    else:
        print(f"❌ Error: {response.text[:500]}")
        
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ NO SE PUDO CONECTAR")
    print(f"   Error: {e}")
    print(f"   💡 Verifica que Stable Diffusion esté corriendo con --api en puerto 7861")
    
except requests.exceptions.Timeout:
    print(f"\n⏳ TIMEOUT: El servidor tardó más de 60s")
    
except Exception as e:
    print(f"\n⚠️ Error inesperado: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
