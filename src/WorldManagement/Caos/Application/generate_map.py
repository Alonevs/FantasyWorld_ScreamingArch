import base64
import os
import time
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import ImageGenerator

class GenerateWorldMapUseCase:
    def __init__(self, repository: CaosRepository, image_service: ImageGenerator):
        self.repository = repository
        self.image_service = image_service
        # Ruta absoluta (truco para que funcione en cualquier PC)
        self.output_folder = os.path.abspath("src/Infrastructure/DjangoFramework/persistence/static/persistence/img")

    def execute(self, world_id_str: str):
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        if not world: return

        # TUS VARIACIONES (Traídas de app.py)
        variaciones = [
            "neutral expression, looking forward",
            "slight smirk, looking slightly left",
            "serious eyes, looking down",
            "determined gaze, looking to the right"
        ]

        base_prompt = f"{world.name}, {world.lore_description[:100]}"
        generated_files = []

        print(f" 📸 Generando 4 variaciones para {world.name}...")

        for i, expr in enumerate(variaciones):
            # Construimos el prompt único
            full_prompt = f"{base_prompt}, {expr}"
            
            img_base64 = self.image_service.generate_concept_art(full_prompt)
            
            if img_base64:
                # Nombre: map_01_v1.png, map_01_v2.png...
                filename = f"map_{world_id_str}_v{i+1}.png"
                filepath = os.path.join(self.output_folder, filename)
                
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(img_base64))
                
                print(f"    ✅ Guardada: {filename}")
                generated_files.append(filename)
            else:
                print(f"    ⚠️ Falló variación {i+1}")

        return generated_files