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
        self.ai_director = Llama3Service() # Instancia para traducir

    def _sanitize(self, name):
        s = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
        return re.sub(r'_+', '_', s)

    def _get_smart_prompt(self, world):
        # INTENTO DE TRADUCCIÓN / MEJORA DE PROMPT
        nivel = eclai_core.get_level_from_jid_length(len(world.id.value))
        try:
            # Intentamos que Llama genere un prompt técnico en inglés
            smart_prompt = self.ai_director.generate_sd_prompt(world.name, world.lore_description, nivel)
            if smart_prompt and len(smart_prompt) > 10:
                print(f" 🎨 Prompt Ingeniero: '{smart_prompt[:50]}...'")
                return smart_prompt
        except: pass
        
        # FALLBACK: Traducción simple
        try:
            print(" ⚠️ Usando traducción simple...")
            desc_en = self.ai_director.translate_to_english(world.lore_description[:200])
            return f"{world.name}, {desc_en}, fantasy concept art, best quality"
        except:
            return f"{world.name}, fantasy world, masterpiece"

    def _get_next_version(self, folder_path):
        max_v = 0
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                if f.lower().endswith(".png"):
                    match = re.search(r'_v(\d+)\.png$', f)
                    if match:
                        num = int(match.group(1))
                        if num > max_v: max_v = num
        return max_v + 1

    def execute_single(self, world_id_str: str):
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: return

        target_folder = os.path.join(self.base_folder, world_id_str)
        os.makedirs(target_folder, exist_ok=True)

        core_prompt = self._get_smart_prompt(world)
        estilos = ["cinematic lighting", "atmospheric fog", "highly detailed", "dramatic angle"]
        final_prompt = f"{core_prompt}, {random.choice(estilos)}"
        
        print(f" 📸 Generando con prompt: {final_prompt[:60]}...")
        
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