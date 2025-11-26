import requests
import json
import re
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class Llama3Service(LoreGenerator):
    def __init__(self):
        self.api_url_completion = "http://127.0.0.1:5000/v1/completions"
        self.api_url_chat = "http://127.0.0.1:5000/v1/chat/completions"
        self.headers = {"Content-Type": "application/json"}

    def _call_api(self, prompt, max_tokens=300, stop=None, temperature=0.7):
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "seed": -1,
            "stream": False,
            "stop": stop or ["###"]
        }
        try:
            r = requests.post(self.api_url_completion, headers=self.headers, json=payload, timeout=60)
            if r.status_code == 200: return r.json()['choices'][0]['text'].strip()
        except Exception as e: print(f"⚠️ Error IA: {e}")
        return ""

    def generate_description(self, prompt: str) -> str:
        full_prompt = f"### Instruction:\nGenera una descripción detallada en español para: {prompt}\n\n### Response:\n"
        return self._call_api(full_prompt, max_tokens=400)

    def translate_to_english(self, text: str) -> str:
        full_prompt = f"### Instruction:\nTranslate to English:\n{text}\n\n### Response:\n"
        return self._call_api(full_prompt, max_tokens=200, stop=["\n"], temperature=0.3)

    def generate_sd_prompt(self, name: str, description: str, level: int) -> str:
        # Director de Arte
        style = "Abstract, Surreal" if level <= 3 else "Realistic, Detailed"
        prompt = f"### Instruction:\nCreate a Stable Diffusion prompt (English, comma separated tags) for: {name}. Description: {description[:200]}. Style: {style}.\n\n### Response:\n"
        return self._call_api(prompt, max_tokens=150, temperature=0.6)

    def generate_entity_json(self, name, tipo, habitat):
        # Generador de Fichas (Tu lógica de prueba)
        print(f" 🧬 [Llama] Creando JSON para {name}...")
        system = f'''Eres un bestiario. Genera JSON válido para:
Nombre: {name} | Tipo: {tipo} | Hábitat: {habitat}
JSON keys: descripcion, tamano, peso, personalidad, peligro (1-5), dieta, rasgos.'''
        
        payload = {
            "mode": "instruct",
            "messages": [{"role": "user", "content": system}],
            "max_tokens": 600,
            "temperature": 0.4
        }
        try:
            r = requests.post(self.api_url_chat, headers=self.headers, json=payload, timeout=90)
            if r.status_code == 200:
                content = r.json()['choices'][0]['message']['content']
                # Limpieza de markdown
                content = re.sub(r'```json|```', '', content).strip()
                return json.loads(content)
        except Exception as e: print(f"⚠️ Error JSON IA: {e}")
        
        return {"descripcion": "Error generando datos."}