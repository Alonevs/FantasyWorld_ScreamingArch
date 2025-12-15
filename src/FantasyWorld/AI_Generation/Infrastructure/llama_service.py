import requests
import json
import re
from django.conf import settings
from typing import Dict, Any
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class Llama3Service(LoreGenerator):
    def __init__(self):
        # Use settings or fallback (Base URL)
        base_url = getattr(settings, 'AI_API_BASE_URL', "http://127.0.0.1:7861")
        self.api_url_completion = f"{base_url}/v1/completions"
        self.api_url_chat = f"{base_url}/v1/chat/completions"
        self.timeout = getattr(settings, 'AI_TIMEOUT', 120)
        
        self.headers = {"Content-Type": "application/json"}

    def _call_api(self, prompt, max_tokens=200, temperature=0.7, stop=None):
        payload = {
            "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature,
            "top_p": 0.9, "seed": -1, "stream": False, "stop": stop or ["###", "\n\n"]
        }
        try:
            print(f"📡 [LlamaService] POST {self.api_url_completion}")
            r = requests.post(self.api_url_completion, headers=self.headers, json=payload, timeout=120)
            
            if r.status_code == 200: 
                text = r.json()['choices'][0]['text'].strip()
                print(f"✅ [LlamaService] 200 OK. Recibido {len(text)} chars.")
                # print(f"🔍 RAW: {text[:100]}...") 
                return text
            else:
                print(f"⚠️ [LlamaService] Error Status {r.status_code}: {r.text}")
                
        except Exception as e: 
            print(f"⚠️ [LlamaService] Exception: {e}")
        return ""

    def _clean_json(self, raw_text: str) -> Dict:
        """
        Robust JSON cleaning, now with Regex extraction.
        """
        try:
            # 1. Remove Markdown
            text = re.sub(r'```json|```', '', raw_text).strip()
            
            # 2. Try Standard JSON Load
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 3. Regex Extraction (Find the first outer object)
                # Looks for { ... } across multiple lines
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    potential_json = match.group(0)
                    return json.loads(potential_json)

                # 4. Fallback: Parse as Python Dictionary
                import ast
                clean_data = ast.literal_eval(text)
                if isinstance(clean_data, dict):
                    return clean_data
                elif isinstance(clean_data, list):
                    return {"properties": clean_data}
            except (ValueError, SyntaxError, Exception):
                pass
            
            print(f"⚠️ Error parseando JSON de Llama. Raw: {raw_text[:100]}...")
            return {}

    def extract_metadata(self, description: str, schema: dict = None) -> dict:
        """
        Extracts open-ended metadata properties using Chat API (Llama 3 friendly).
        """
        system_instruction = (
            "Eres un extractor de datos JSON especializado en mundos de fantasía.\n"
            "TAREA: Analiza el TEXTO proporcionado y extrae propiedades clave.\n"
            "REGLAS ESTRICTAS:\n"
            "1. Devuelve SOLO un objeto JSON con esta estructura:\n"
            "{\n"
            "  \"properties\": [\n"
            "    {\"key\": \"NombrePropiedad\", \"value\": \"valor extraído del texto\"},\n"
            "    {\"key\": \"OtraPropiedad\", \"value\": \"otro valor del texto\"}\n"
            "  ]\n"
            "}\n"
            "2. EXTRAE datos del TEXTO, NO inventes ni uses ejemplos.\n"
            "3. Propiedades relevantes: Geografía, Clima, Habitantes, Física, Magia, Peligros, Recursos.\n"
            "4. Si no hay datos claros, devuelve {\"properties\": []}.\n"
            "5. NO escribas introducciones. NO uses Markdown. SOLO JSON válido."
        )
        
        # We reuse the Chat Completion method (generate_structure) 
        # which is much better for Llama 3 than the legacy completion endpoint.
        print(f"📡 [LlamaService] Analizando texto ({len(description)} chars) con Chat API...")
        return self.generate_structure(system_instruction, f"TEXTO A ANALIZAR:\n{description}")
    
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

    def edit_text(self, system_prompt: str, user_text: str) -> str:
        """
        Edits text based on a system instruction using Chat API.
        """
        print(f" ✍️ [Llama] Editando texto ({len(user_text)} chars)...")
        payload = {
            "mode": "instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 2000, # Allow generous output for editing
            "temperature": 0.7 
        }
        try:
            r = requests.post(self.api_url_chat, headers=self.headers, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                content = r.json()['choices'][0]['message']['content']
                return content.strip()
            else:
                print(f"⚠️ [Llama] Error Status {r.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏳ [Llama] Timeout reached after {self.timeout}s.")
            raise Exception(f"⏳ La IA está tardando demasiado (Timeout > {self.timeout}s). Intenta con trozos más pequeños.")
        except Exception as e:
            print(f"⚠️ Error IA Edit: {e}")
        return ""

    # --- MÉTODO LEGACY (Compatibilidad) ---
    def generate_entity_json(self, name, tipo, habitat):
        # Mantenemos este por si algún código viejo lo llama
        return self.generate_structure(
            f"Genera JSON para: {tipo}. Keys: descripcion, tamano, peso, peligro (1-5), dieta, rasgos.", 
            f"Nombre: {name}. Habitat: {habitat}"
        )
