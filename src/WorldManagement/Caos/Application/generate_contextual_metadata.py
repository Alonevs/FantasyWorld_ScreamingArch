import json
from typing import Optional, Dict, Any
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.metadata import METADATA_SCHEMAS
from src.WorldManagement.Caos.Domain.metadata_router import get_schema_for_type, get_schema_for_hierarchy


# Mapeo dinámico derivado de los esquemas del dominio
TYPE_MAPPING = {k.replace('_SCHEMA', ''): k for k in METADATA_SCHEMAS.keys()}

class GenerateContextualMetadataUseCase:
    """
    Caso de Uso responsable de la extracción e inicialización de metadatos (Auto-Noos).
    Analiza el texto del Lore para rellenar fichas técnicas estructuradas basándose en 
    esquemas de jerarquía o clasificación por IA.
    """
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repo = repository
        self.ai = ai_service

    def execute(self, world_id: str, force_type: Optional[str] = None):
        """
        Inicia el proceso de generación de metadatos.
        Funciona en dos modos:
        - Cold Start: Si no hay texto, inicializa una ficha técnica vacía pero estructurada.
        - Análisis: Si hay texto, extrae los datos técnicos usando el modelo de lenguaje.
        """
        # 1. Cargar la entidad desde el repositorio
        world = self.repo.find_by_id(WorldID(world_id))
        if not world: raise Exception("Entidad no encontrada")

        print(f" 🔭 Analizando metadatos contextuales para: {world.name} (ID: {world_id})...")

        entity_type = None
        schema = None
        
        # 2a. ESTRATEGIA DETERMINISTA (Jerarquía + Ramas)
        # Prioridad 1: Inferir el esquema según el nivel J-ID y la rama (Física/Dimensional).
        try:
             level = len(world_id) // 2
             schema = get_schema_for_hierarchy(world_id, level)
             
             if schema:
                 print(f" 📏 Detectado Nivel {level} (Rama Determinada). Aplicando esquema jerárquico.")
                 if not world.metadata.get('tipo_entidad'):
                      entity_type = f"NIVEL_{level:02d}" 
        except Exception:
            pass

        # 2b. ESTRATEGIA DE FALLBACK (Tipo Explícito o IA)
        if not schema:
            entity_type = force_type # Tipo forzado por el usuario desde el manual
            if not entity_type and world.metadata:
                entity_type = world.metadata.get('tipo_entidad')

            # 2c. Clasificación por IA (Último recurso si no hay datos jerárquicos)
            if not entity_type:
                entity_type = self._infer_entity_type(world)
                if entity_type:
                    print(f" 🤖 IA clasificó la entidad como: {entity_type}")
            
            schema = get_schema_for_type(entity_type) if entity_type else None
        
        # --- LÓGICA DE DETECCIÓN DE ESTADO (Cold Start vs Análisis) ---
        lore_content = world.lore_description or world.description or ""
        is_lore_empty = len(lore_content.strip()) < 10

        meta_json = None

        if schema and is_lore_empty:
            # RAMA A: INICIALIZACIÓN (Sin Lore)
            # Preparamos una ficha vacía con los campos obligatorios del esquema.
            print(f" ❄️ Cold Start: Inicializando metadatos vacíos estructurados...")
            datos_nucleo = {k: "Pendiente" for k in schema['campos_fijos'].keys()}
            
            meta_json = {
                "tipo_entidad": entity_type or f"NIVEL_AUTO",
                "datos_nucleo": datos_nucleo,
                "datos_extendidos": {} 
            }
            
        elif schema and not is_lore_empty:
            # RAMA B: EXTRACCIÓN (Con Lore)
            # Usamos el esquema para guiar a la IA en la extracción de datos técnicos.
            meta_json = self._extract_with_schema(world, entity_type, schema)
            
        elif not schema and not is_lore_empty:
            # Fallback a extracción genérica (Legacy / Sin esquema específico)
            meta_json = self.ai.extract_metadata(lore_content)

        # 5. RETORNO (Modo Propuesta)
        # Los metadatos generados NO se guardan automáticamente.
        # Se devuelven como una propuesta para que el usuario la valide en la interfaz (ECLAI UI).
        if meta_json:
            if entity_type and 'tipo_entidad' not in meta_json:
                 meta_json['tipo_entidad'] = entity_type
            
            print(f" 📤 Propuesta de metadatos generada correctamente.")
            return meta_json
        
        return None

    def _infer_entity_type(self, world) -> Optional[str]:
        """
        Utiliza el LLM para clasificar taxonómicamente la entidad basándose en su descripción.
        """
        possible_types = ", ".join(TYPE_MAPPING.keys())
        prompt = f"""
        Analiza este texto: '{world.lore_description or world.description}'. 
        Basado en el contenido, clasifica esta entidad en uno de estos tipos: [{possible_types}]. 
        Devuelve solo el TIPO en una sola palabra.
        """
        try:
            # Respuesta determinista con temperatura baja
            response = self.ai.edit_text("Eres un clasificador taxonómico estricto.", prompt, temperature=0.1, max_tokens=10)
            clean_type = response.strip().upper().replace('"', '').replace("'", "").replace(".", "")
            
            # Limpieza básica de la respuesta
            clean_type = clean_type.split()[0] if " " in clean_type else clean_type

            if clean_type in TYPE_MAPPING:
                return clean_type
            
            # Búsqueda parcial si la IA añadió texto extra
            for t in TYPE_MAPPING.keys():
                if t in clean_type:
                    return t
        except Exception as e:
            print(f"Error infiriendo tipo por IA: {e}")
        
        return None

    def _extract_with_schema(self, world, entity_type, schema) -> Dict:
        """
        Genera el JSON estructurado basándose estrictamente en las reglas del Dominio (Snake Case, Campos Fijos).
        """
        
        campos_fijos_str = json.dumps(schema['campos_fijos'], indent=2, ensure_ascii=False)
        campos_extra_str = json.dumps(schema.get('campos_ia_extra', []), indent=2, ensure_ascii=False)
        
        system_prompt = f"""
        Eres un Analista de Datos de Worldbuilding. Tu tarea es extraer información técnica del Lore.
        """
        
        user_prompt = f"""
        Texto del Lore: '{world.lore_description or world.description}'
        
        Esquema OBLIGATORIO (Campos Fijos): 
        {campos_fijos_str}
        
        Campos Opcionales Sugeridos:
        {campos_extra_str}
        
        INSTRUCCIONES ESTRICTAS:
            - FORMATO: Claves en 'snake_case' técnico.
            - VALORES: Concisos (Máximo 3-5 palabras).
            - NO inventes datos. Si no existe, usa "Pendiente".
            - DATOS EXTENDIDOS: Añade a 'datos_extendidos' cualquier dato relevante fuera del esquema fijo.
            - Devuelve SOLO el JSON sin texto introductorio.
        """
        
        return self.ai.generate_structure(system_prompt, user_prompt)
