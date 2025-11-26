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
        self.api_url = "http://127.0.0.1:7861"
        
        # --- ⚙️ CONFIGURACIÓN DE MODELOS (None = Usar el que esté cargado en la Web) ---
        self.models_config = {
            "mapa": None,
            "criatura": None,
            "defecto": None
        }
        
        # --- RECETAS DE PROMPT ---
        self.styles = {
            "mapa": "isometric view, fantasy map, geographical details, atlas style, terrain features, top down view",
            "criatura": "character design, full body, creature concept art, highly detailed biology, monster manual style",
            "defecto": "fantasy concept art, masterpiece, best quality"
        }

        self.negative_prompt = "ugly, blurry, text, watermark, bad anatomy, disfigured, lowres, UI elements"

    def _get_current_model(self):
        try:
            r = requests.get(f"{self.api_url}/sdapi/v1/options")
            return r.json().get("sd_model_checkpoint")
        except: return None

    def _swap_model(self, target_model):
        # Si no hay modelo objetivo (None), NO hacemos nada y respetamos el actual
        if not target_model: return 
        
        current = self._get_current_model()
        if current == target_model: return
            
        print(f" 🔄 CAMBIANDO MODELO: De '{current}' a '{target_model}'...")
        payload = {"sd_model_checkpoint": target_model}
        requests.post(f"{self.api_url}/sdapi/v1/options", json=payload)
        time.sleep(1) 
        print(" ✅ Modelo cargado.")

    def generate_concept_art(self, prompt_base: str, category: str = "defecto") -> str:
        # 1. Cambiar modelo (Solo si está configurado en self.models_config)
        target_model = self.models_config.get(category)
        self._swap_model(target_model)
        
        # 2. Preparar prompt
        style = self.styles.get(category, self.styles["defecto"])
        full_prompt = f"{style}, {prompt_base}"
        
        print(f" 🎨 [SD] Generando ({category}): '{prompt_base}'...")

        payload = {
            "prompt": full_prompt,
            "negative_prompt": self.negative_prompt,
            "steps": 20,
            "width": 512,
            "height": 768,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras"
        }

        try:
            response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload, timeout=120)
            if response.status_code == 200:
                return response.json()['images'][0]
            else:
                print(f"❌ Error API SD: {response.status_code}")
                return None
        except Exception as e:
            print(f" ⚠️ Error conexión SD: {e}")
            return None
            
    def generate_image(self, prompt, filename):
        return self.generate_concept_art(prompt)