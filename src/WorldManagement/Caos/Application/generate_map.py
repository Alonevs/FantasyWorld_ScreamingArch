import base64
import os
import re
import random
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator
from src.Shared.Domain import eclai_core

class GenerateWorldMapUseCase:
    def __init__(self, repository: CaosRepository, image_service: ImageGenerator):
        self.repository = repository
        self.image_service = image_service
        self.base_folder = os.path.abspath("src/Infrastructure/DjangoFramework/persistence/static/persistence/img")

    def _sanitize(self, name):
        s = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
        return re.sub(r'_+', '_', s)

    def _get_next_version(self, folder_path):
        # Busca cuál es el siguiente número vX disponible (v1, v2, v5...)
        count = 1
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            # Contamos cuantos png hay para saber el numero aprox
            pngs = [f for f in files if f.endswith('.png')]
            count = len(pngs) + 1
        return count

    def execute_single(self, world_id_str: str):
        # --- GENERAR 1 SOLA FOTO (Bajo demanda) ---
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: return

        # 1. Carpeta: SOLO EL ID (Estricto)
        target_folder = os.path.join(self.base_folder, world_id_str)
        os.makedirs(target_folder, exist_ok=True)

        # 2. Nombre: NombreMundo_vX.png
        version = self._get_next_version(target_folder)
        safe_name = self._sanitize(world.name)
        filename = f"{safe_name}_v{version}.png"
        
        # 3. Prompt (Elegimos un estilo aleatorio para variedad)
        estilos = [
            "cinematic lighting, epic composition",
            "mystery atmosphere, dark fog",
            "detailed concept art, rpg style",
            "close up shot, highly detailed"
        ]
        estilo = random.choice(estilos)
        prompt = f"{world.name}, {world.lore_description[:100]}, {estilo}"
        
        print(f" 📸 Generando foto única: {filename}")
        
        img_base64 = self.image_service.generate_concept_art(prompt)
        if img_base64:
            filepath = os.path.join(target_folder, filename)
            with open(filepath, "wb") as fh:
                fh.write(base64.b64decode(img_base64))
            print(f"    ✅ Guardada en: {target_folder}")
            return filename
        return None

    def execute(self, world_id_str: str):
        # --- GENERAR LOTE INICIAL (4 Variaciones) ---
        # Usado al crear el mundo por primera vez
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: return

        target_folder = os.path.join(self.base_folder, world_id_str)
        os.makedirs(target_folder, exist_ok=True)
        
        safe_name = self._sanitize(world.name)
        
        variaciones = [
            "neutral view", "atmospheric view", "dramatic lighting", "detailed texture"
        ]
        
        generated = []
        for i, var in enumerate(variaciones):
            prompt = f"{world.name}, {world.lore_description[:100]}, {var}"
            img_b64 = self.image_service.generate_concept_art(prompt)
            if img_b64:
                fname = f"{safe_name}_init_v{i+1}.png"
                fpath = os.path.join(target_folder, fname)
                with open(fpath, "wb") as fh: fh.write(base64.b64decode(img_b64))
                generated.append(fname)
                print(f"    ✅ Lote inicial: {fname}")
        return generated