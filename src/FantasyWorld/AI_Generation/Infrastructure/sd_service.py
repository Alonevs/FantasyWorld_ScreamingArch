import requests
import base64
import os
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator

class StableDiffusionService(ImageGenerator):
    def __init__(self):
        # Tu puerto actual (7861)
        self.api_url = "http://127.0.0.1:7861/sdapi/v1/txt2img"

    def generate_concept_art(self, prompt: str) -> str:
        # Añadimos palabras clave para forzar estilo 2D simple y rápido
        estilo_miniatura = "game icon, 2d vector art, flat style, simple, rpg item style"
        full_prompt = f"{estilo_miniatura}, {prompt}"
        
        print(f" ⚡ [SD RÁPIDO] Generando miniatura: {prompt[:30]}...")
        
        payload = {
            "prompt": full_prompt,
            "negative_prompt": "photorealistic, 3d, detailed background, noise, messy, text, watermark",
            
            # --- CONFIGURACIÓN DE VELOCIDAD ---
            "steps": 15,              # Bajamos a 15 (muy rápido)
            "width": 384,             # Tu tamaño de tarjeta
            "height": 512,
            "cfg_scale": 6,           # Un poco más bajo para que sea más creativo/libre
            "sampler_name": "Euler a",# El sampler más rápido del oeste
            "seed": -1
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30) # Timeout corto
            if response.status_code == 200:
                return response.json()['images'][0]
            else:
                print(f"❌ Error SD: {response.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ Error conexión SD: {e}")
            return None