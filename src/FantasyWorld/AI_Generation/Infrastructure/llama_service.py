import requests
import json
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class Llama3Service(LoreGenerator):
    def __init__(self):
        # URL Oobabooga
        self.api_url = "http://127.0.0.1:5000/v1/completions"
        self.headers = {"Content-Type": "application/json"}

    def generate_description(self, prompt: str) -> str:
        print(f" 🧠 [IA] Procesando solicitud: {prompt[:50]}...")
        
        # --- LIMPIEZA DE PROMPT ---
        # Antes decíamos: "Genera una historia oscura sobre {prompt}"
        # AHORA: Le pasamos tu instrucción directa, pero con formato de Chat para que Llama entienda.
        
        # Formato Alpaca/Chat estándar que funciona bien con Llama 3
        full_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n"

        payload = {
            "prompt": full_prompt,
            "max_tokens": 300,       # Un poco más de espacio
            "temperature": 0.7,      # Creatividad equilibrada
            "top_p": 0.9,
            "seed": -1,
            "stream": False,
            "stop": ["###"]          # Que pare si intenta hablar por el usuario
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                texto = data['choices'][0]['text']
                return texto.strip()
            else:
                print(f"❌ Error API: {response.text}")
                return "Error: La IA no respondió correctamente."

        except Exception as e:
            print(f" ⚠️ Error conexión IA: {e}")
            return "Error: No se pudo conectar con Oobabooga."