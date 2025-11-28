from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator
from src.Shared.Domain.value_objects import WorldID
import json
import re

class GeneratePlanetMetadataUseCase:
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repo = repository
        self.ai = ai_service

    def execute(self, world_id: str):
        # 1. Cargar Mundo
        world = self.repo.find_by_id(WorldID(world_id))
        if not world: raise Exception("Mundo no encontrado")

        # 2. Preparar el Prompt de Análisis
        print(f" 🔭 Escaneando datos planetarios de: {world.name}...")
        
        # PROMPT CORREGIDO: MÁS ESTRICTO
        system_prompt = """
        Role: Database System.
        Task: Convert the input text into a JSON object.
        Input Lore: "{lore}"
        
        RULES:
        1. Output ONLY valid JSON.
        2. DO NOT write Python code (no 'import json', no variables).
        3. DO NOT write explanations.
        4. Starts with {{ and ends with }}.
        
        JSON Structure:
        {{
            "tipo_entidad": "PLANETA",
            "fisica": {{
                "gravedad": "1.0G",
                "ciclo_dia": "24h",
                "lunas": ["Luna 1"]
            }},
            "clima": {{
                "tipo": "Tundra",
                "atmosfera": "Toxic",
                "temperatura_media": "-10C"
            }},
            "rasgos": "Resumen geológico breve"
        }}
        """.format(lore=world.lore_description or "Planeta generico")
        
        # 3. Invocar a Llama 3
        # Usamos un mensaje de usuario simple para detonar la respuesta JSON
        meta_json = self.ai.generate_structure(system_prompt, "JSON OUTPUT:")

        # 4. Guardar
        if meta_json:
            if not world.metadata: world.metadata = {}
            world.metadata.update(meta_json)
            self.repo.save(world)
            print(f" ✅ Metadatos actualizados: {json.dumps(meta_json, indent=2)}")
            return meta_json
        
        return None
