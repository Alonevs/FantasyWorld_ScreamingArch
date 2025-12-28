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
        # ✅ PUERTO CONFIRMADO POR TU TEST (7860 para SD WebUI)
        self.api_url = getattr(settings, 'SD_API_URL', "http://127.0.0.1:7860")
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
            # 1. Llamada directa (Sin cambios de modelo, usamos el que ya tienes cargado)
            response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload, timeout=120)
            
            if response.status_code == 200:
                r = response.json()
                # Devolvemos el string base64 directamente
                return r['images'][0]
            else:
                print(f"❌ Error SD ({response.status_code}): {response.text[:100]}")
                return None

        except requests.exceptions.ConnectionError:
            print(f"💀 NO CONECTA a la IA de imagen. ¿Seguro que la ventana negra sigue abierta?")
            return None
        except Exception as e:
            print(f"⚠️ Error inesperado en SD: {e}")
            return None
            
    # Alias para compatibilidad
    def generate_image(self, prompt, filename):
        return self.generate_concept_art(prompt)