import requests
import json
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class Llama3Service(LoreGenerator):
    def __init__(self):
        # ⚠️ CONFIGURACIÓN OOBABOOGA ⚠️
        # Si usas start_api.bat, normalmente abre el puerto 5000.
        # Endpoint 'v1/completions' es el estándar compatible con OpenAI.
        self.api_url = "http://127.0.0.1:5000/v1/completions" 
        
        # Parámetros para controlar la creatividad de Llama 3
        self.headers = {"Content-Type": "application/json"}

    def generate_description(self, prompt: str) -> str:
        print(f" 🧠 [OOBABOOGA] Enviando prompt: {prompt}...")
        
        # Preparamos el prompt estilo 'chat' o 'instrucción'
        full_prompt = f"### Instruction:\nGenera una descripción breve (max 3 líneas) y oscura para un mundo de fantasía llamado: {prompt}\n\n### Response:\n"

        payload = {
            "prompt": full_prompt,
            "max_tokens": 200,       # Longitud de la respuesta
            "temperature": 0.7,      # Creatividad (0.1 aburrido, 1.0 loco)
            "top_p": 0.9,
            "seed": -1,
            "stream": False
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Oobabooga devuelve: {'choices': [{'text': '...'}]}
                texto_generado = data['choices'][0]['text']
                return texto_generado.strip()
            else:
                print(f"❌ Error API: {response.text}")
                return f"[Error] Oobabooga respondió: {response.status_code}"

        except requests.exceptions.ConnectionError:
            print(" ⚠️ No pude conectar a http://127.0.0.1:5000")
            print("    ¿Ejecutaste 'start_api.bat' y esperaste a que cargara el modelo?")
            return "[Error de Conexión] Enciende Oobabooga primero."