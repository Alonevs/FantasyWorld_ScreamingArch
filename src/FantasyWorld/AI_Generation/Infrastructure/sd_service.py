import requests
import io
import base64
import time
from PIL import Image
from django.conf import settings
import os
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator

class StableDiffusionService(ImageGenerator):
    def __init__(self):
        # ✅ PUERTO 7861 (Stable Diffusion con --api)
        self.api_url = getattr(settings, 'SD_API_URL', "http://127.0.0.1:7861")
        self.headers = {"Content-Type": "application/json"}

    def generate_concept_art(self, prompt: str, category: str = "defecto") -> str:
        # Limpiamos el prompt por si acaso
        print(f" 🎨 [SD] Conectando a {self.api_url}...")
        print(f"    Prompt: {prompt[:60]}...")

        # Payload optimizado para revAnimated (Estilo 2.5D / Ilustración)
        payload = {
            "prompt": f"(best quality, masterpiece, highres), {prompt}, (vibrant colors, soft lighting)",
            "negative_prompt": "bad anatomy, low quality, text, watermark, glitch, deformed, mutated, ugly, blur, pixelated",
            "steps": 25,            # Un poco más de calidad
            "width": 512,
            "height": 768,          # Formato Retrato
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras", # El mejor para revAnimated
            "seed": -1
        }

        try:
            start_time = time.time()
            response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload, timeout=120)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ [SD] 200 OK. Imagen generada en {elapsed:.1f}s.")
                r = response.json()
                return r['images'][0]
            else:
                print(f"❌ Error SD ({response.status_code}) tras {elapsed:.1f}s: {response.text[:100]}")
                return None

        except requests.exceptions.ConnectionError:
            print(f"❌ NO SE PUDO CONECTAR al servidor de GENERACIÓN DE IMÁGENES (Stable Diffusion)")
            print(f"   URL esperada: {self.api_url}")
            print(f"   💡 Asegúrate de que Stable Diffusion WebUI esté corriendo con --api en puerto 7861")
            return None
        except requests.exceptions.Timeout:
            print(f"⏳ TIMEOUT: El servidor de imágenes tardó demasiado en responder")
            return None
        except Exception as e:
            print(f"⚠️ Error inesperado en SD: {e}")
            return None
            
    # Alias para compatibilidad
    def generate_image(self, prompt, filename):
        return self.generate_concept_art(prompt)