import requests
import json
import re
from typing import Dict, Any
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class Llama3Service(LoreGenerator):
    def __init__(self):
        self.api_url_completion = "http://127.0.0.1:5000/v1/completions"
        self.api_url_chat = "http://127.0.0.1:5000/v1/chat/completions"
        self.headers = {"Content-Type": "application/json"}

    def _call_api(self, prompt, max_tokens=200, temperature=0.7, stop=None):
        payload = {
            "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature,
            "top_p": 0.9, "seed": -1, "stream": False, "stop": stop or ["###", "\n\n"]
        }
        try:
            r = requests.post(self.api_url_completion, headers=self.headers, json=payload, timeout=60)
            if r.status_code == 200: return r.json()['choices'][0]['text'].strip()
        except Exception as e: 
            print(f"⚠️ Error IA Texto: {e}")
        return ""

    def _clean_json(self, raw_text: str) -> Dict:
        try:
            text = re.sub(r'```json|```', '', raw_text).strip()
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"⚠️ Error parseando JSON de Llama. Raw: {raw_text[:50]}...")
            return {}

    def generate_description(self, prompt: str) -> str:
        full_prompt = f"### Instruction:\nDescribe visualmente en español (max 3 frases) el siguiente lugar o concepto: \"{prompt}\".\nNO uses Markdown. NO incluyas imágenes ni enlaces. Solo texto plano.\n### Response:\n"
        response = self._call_api(full_prompt, max_tokens=150, temperature=0.6)
        
        # Sanitize output
        # Remove markdown images ![...]
        response = re.sub(r'!\[.*?\]\(.*?\)', '', response)
        # Remove markdown links [text](url) - keep text? No, usually garbage.
        response = re.sub(r'\[.*?\]\(.*?\)', '', response)
        # Remove raw URLs
        response = re.sub(r'http\S+', '', response)
        
        return response.strip()

    def generate_sd_prompt(self, name: str, description: str) -> str:
        # --- TRADUCTOR VISUAL (ESP -> ING) ---
        print(f" 🔡 [Llama] Traduciendo prompt para: {name}...")
        
        # PROMPT BLINDADO ANTI-ALUCINACIONES
        prompt = f'''### Instruction:
You are a prompt engineer for Stable Diffusion.
Input: "{description}"
Task: Convert the input concept into a comma-separated list of visual keywords in English.
Constraints:
1. Output ONLY the tags.
2. NO markdown, NO images (like ![image]), NO links, NO explanations.
3. Mandatory tags: best quality, 8k, fantasy art, top down view.

### Response:
'''
        # Temperatura baja para ser determinista
        raw_response = self._call_api(prompt, max_tokens=150, temperature=0.3)

        # --- FILTRO DE SEGURIDAD (LOBOTOMÍA) ---
        # Si la IA intenta colarnos un link o imagen, lo interceptamos.
        if "![" in raw_response or "http" in raw_response or "github" in raw_response.lower():
            print(f" ⚠️ ALUCINACIÓN DETECTADA (Link/Imagen): {raw_response[:30]}...")
            print(f" 🛡️ Aplicando Prompt de Emergencia.")
            return f"{name}, fantasy map, cartography, top down view, best quality, 8k, detailed"
            
        return raw_response

    # --- MÉTODO PARA CRIATURAS (JSON ESTRUCTURADO) ---
    def generate_structure(self, system_prompt: str, context_prompt: str) -> Dict[str, Any]:
        print(f" 🧬 [Llama] Generando estructura JSON...")
        payload = {
            "mode": "instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.6 
        }
        try:
            r = requests.post(self.api_url_chat, headers=self.headers, json=payload, timeout=90)
            if r.status_code == 200:
                content = r.json()['choices'][0]['message']['content']
                return self._clean_json(content)
        except Exception as e:
            print(f"⚠️ Error IA Estructura: {e}")
        return {}

    # --- MÉTODO LEGACY (Compatibilidad) ---
    def generate_entity_json(self, name, tipo, habitat):
        # Mantenemos este por si algún código viejo lo llama
        return self.generate_structure(
            f"Genera JSON para: {tipo}. Keys: descripcion, tamano, peso, peligro (1-5), dieta, rasgos.", 
            f"Nombre: {name}. Habitat: {habitat}"
        )
