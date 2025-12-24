from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator
from src.Shared.Domain.value_objects import WorldID
import json
import re

class GeneratePlanetMetadataUseCase:
    """
    Caso de Uso especializado en la generación de metadatos planetarios (Astrofísica y Clima).
    Analiza la descripción narrativa para extraer variables técnicas como gravedad, 
    duración del día, composición atmosférica y satélites.
    """
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repo = repository
        self.ai = ai_service

    def execute(self, world_id: str):
        """
        Analiza una entidad de tipo Planeta y actualiza su ficha técnica técnica (Metadata).
        """
        # 1. Cargar la entidad desde el repositorio
        world = self.repo.find_by_id(WorldID(world_id))
        if not world: 
            raise Exception("No se ha encontrado la entidad para el análisis planetario.")

        # 2. Configuración del análisis por IA
        print(f" 🔭 Escaneando datos planetarios de: {world.name}...")
        
        # Instrucciones estrictas para asegurar una respuesta JSON válida
        system_prompt = """
        Rol: Sistema de Base de Datos Astrofísicas.
        Tarea: Convertir el texto de Lore en un objeto JSON técnico.
        Lore de Entrada: "{lore}"
        
        REGLAS ESTRICTAS:
        1. Devuelve ÚNICAMENTE un JSON válido.
        2. NO escribas explicaciones ni código.
        3. Usa claves en minúsculas.
        
        Estructura REQUERIDA:
        {{
            "tipo_entidad": "PLANETA",
            "fisica": {{
                "gravedad": "valor",
                "ciclo_dia": "valor",
                "lunas": ["Luna A", "Luna B"]
            }},
            "clima": {{
                "tipo": "valor",
                "atmosfera": "valor",
                "temperatura_media": "valor"
            }},
            "rasgos": "Resumen breve"
        }}
        """.format(lore=world.lore_description or "Entidad planetaria sin descripción.")
        
        # 3. Invocación al servicio de estructura (IA)
        meta_json = self.ai.generate_structure(system_prompt, "FORMATO JSON:")

        # 4. Actualización y Persistencia
        if meta_json:
            # Inicializamos metadatos si no existen
            if not world.metadata: 
                world.metadata = {}
            
            # Combinamos los nuevos datos técnicos con los existentes
            world.metadata.update(meta_json)
            self.repo.save(world)
            
            print(f" ✅ Metadatos planetarios sincronizados: {json.dumps(meta_json, indent=2)}")
            return meta_json
        
        return None
