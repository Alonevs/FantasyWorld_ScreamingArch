import base64
import os
import re
import random
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service 
from src.Shared.Domain import eclai_core

class GenerateWorldMapUseCase:
    def __init__(self, repository: CaosRepository, image_service: ImageGenerator):
        self.repository = repository
        self.image_service = image_service
        self.base_folder = os.path.abspath("src/Infrastructure/DjangoFramework/persistence/static/persistence/img")
        self.translator = Llama3Service() # Instancia para traducir

    def _sanitize(self, name):
        s = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
        return re.sub(r'_+', '_', s)

    def _get_translated_prompt(self, world):
        # 1. Cogemos la descripción del mundo (Español)
        desc_es = world.lore_description
        if not desc_es: 
            desc_es = f"Un lugar de fantasía llamado {world.name}"
        
        # 2. La pasamos por Llama 3 para que la traduzca y optimice
        try:
            prompt_en = self.translator.generate_sd_prompt(world.name, desc_es)
            if prompt_en and len(prompt_en) > 5:
                print(f" ✨ Prompt Traducido: {prompt_en[:60]}...")
                return prompt_en
        except Exception as e:
            print(f" ⚠️ Fallo Traductor ({e}). Usando fallback.")
        
        # Fallback si Llama falla: Nombre + tags genéricos
        return f"{world.name}, fantasy concept art, masterpiece, best quality"

    def _get_next_version(self, folder_path):
        max_v = 0
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                if f.lower().endswith(".png"):
                    match = re.search(r'_v(\d+)\.png$', f)
                    if match:
                        if int(match.group(1)) > max_v: max_v = int(match.group(1))
        return max_v + 1

    def execute_single(self, world_id_str: str):
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: return None

        target_folder = os.path.join(self.base_folder, world_id_str)
        os.makedirs(target_folder, exist_ok=True)

        # --- PASO CLAVE: OBTENER PROMPT EN INGLÉS ---
        final_prompt = self._get_translated_prompt(world)
        
        # Añadimos estilo aleatorio para variedad
        estilos = ["cinematic lighting", "atmospheric fog", "dramatic shadows", "golden hour"]
        final_prompt = f"{final_prompt}, {random.choice(estilos)}"
        
        # Llamada a SD
        img_base64 = self.image_service.generate_concept_art(final_prompt)
        
        if img_base64:
            version = self._get_next_version(target_folder)
            safe_name = self._sanitize(world.name)
            filename = f"{safe_name}_v{version}.png"
            filepath = os.path.join(target_folder, filename)
            with open(filepath, "wb") as fh: fh.write(base64.b64decode(img_base64))
            print(f"    ✅ Foto guardada: {filename}")
            return filename
        return None