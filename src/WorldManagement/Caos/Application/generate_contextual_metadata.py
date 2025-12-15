import json
from typing import Optional, Dict, Any
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.metadata import (
    METADATA_SCHEMAS, get_schema_for_type, get_schema_for_hierarchy
)


# Derive mapping dynamically from schemas
TYPE_MAPPING = {k.replace('_SCHEMA', ''): k for k in METADATA_SCHEMAS.keys()}

class GenerateContextualMetadataUseCase:
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repo = repository
        self.ai = ai_service

    def execute(self, world_id: str, force_type: Optional[str] = None):
        # 1. Cargar Mundo
        world = self.repo.find_by_id(WorldID(world_id))
        if not world: raise Exception("Mundo no encontrado")

        print(f" 🔭 Analizando metadatos contextuales para: {world.name} (ID: {world_id})...")

        entity_type = None
        schema = None
        
        # 2a. ESTRATEGIA DE JERARQUÍA + RAMAS (Prioridad 1)
        try:
             level = len(world_id) // 2
             schema = get_schema_for_hierarchy(world_id, level)
             
             if schema:
                 print(f" 📏 Detectado Nivel {level} (Rama Determinada). Aplicando esquema jerárquico.")
                 if not world.metadata.get('tipo_entidad'):
                     entity_type = f"NIVEL_{level:02d}" 
        except Exception:
            pass

        # 2b. ESTRATEGIA DE TIPO EXPLICITO (Fallback)
        if not schema:
            entity_type = force_type
            if not entity_type and world.metadata:
                entity_type = world.metadata.get('tipo_entidad')

            # 2c. Clasificación IA (Último recurso)
            if not entity_type:
                entity_type = self._infer_entity_type(world)
                if entity_type:
                    print(f" 🤖 IA clasificó la entidad como: {entity_type}")
                    # NO GUARDAR - Proposal Mode
                    # if not world.metadata: world.metadata = {}
                    # world.metadata['tipo_entidad'] = entity_type
                    # self.repo.save(world)
            
            schema = get_schema_for_type(entity_type) if entity_type else None
        
        # --- NUEVO: Cold Start Logic (Determinista) ---
        lore_content = world.lore_description or world.description or ""
        is_lore_empty = len(lore_content.strip()) < 10

        meta_json = None

        if schema and is_lore_empty:
            # RAMA A: SIN LORE (Modo Inicialización)
            print(f" ❄️ Cold Start: Inicializando metadatos vacíos...")
            datos_nucleo = {k: "Pendiente" for k in schema['campos_fijos'].keys()}
            
            meta_json = {
                "tipo_entidad": entity_type or f"NIVEL_AUTO",
                "datos_nucleo": datos_nucleo,
                "datos_extendidos": {} 
            }
            
        elif schema and not is_lore_empty:
            # RAMA B: CON LORE (Modo Análisis)
            meta_json = self._extract_with_schema(world, entity_type, schema)
            
        elif not schema and not is_lore_empty:
            # Fallback a extracción genérica (Legacy)
            meta_json = self.ai.extract_metadata(lore_content)

        # 5. RETORNO (Proposal Mode - NO SAVE)
        # El usuario debe revisar y guardar manualmente en el Frontend.
        if meta_json:
            # Inyectar el tipo inferido en la propuesta si no venía ya
            if entity_type and 'tipo_entidad' not in meta_json:
                 meta_json['tipo_entidad'] = entity_type
            
            print(f" 📤 Propuesta generada (Sin guardar): {list(meta_json.keys())}")
            return meta_json
        
        return None

    def _infer_entity_type(self, world) -> Optional[str]:
        """Pregunta a la IA qué tipo de entidad es, basándose en las keys de TYPE_MAPPING."""
        possible_types = ", ".join(TYPE_MAPPING.keys())
        prompt = f"""
        Analiza este texto: '{world.lore_description or world.description}'. 
        Basado en el contenido, clasifica esta entidad en uno de estos tipos: [{possible_types}]. 
        Devuelve solo el TIPO.
        """
        try:
            # Usamos edit_text con temperatura 0 para ser determinista
            response = self.ai.edit_text("Eres un clasificador taxonómico estricto.", prompt, temperature=0.1, max_tokens=10)
            clean_type = response.strip().upper().replace('"', '').replace("'", "").replace(".", "")
            
            # Limpiar basura extra si la IA es verbosa
            clean_type = clean_type.split()[0] if " " in clean_type else clean_type

            # Validar que sea un tipo conocido
            if clean_type in TYPE_MAPPING:
                return clean_type
            
            # Intento de corrección parcial
            for t in TYPE_MAPPING.keys():
                if t in clean_type:
                    return t
        except Exception as e:
            print(f"Error infiriendo tipo: {e}")
        
        return None

    def _extract_with_schema(self, world, entity_type, schema) -> Dict:
        """Genera el JSON basándose estrictamente en el esquema del dominio."""
        
        campos_fijos_str = json.dumps(schema['campos_fijos'], indent=2, ensure_ascii=False)
        campos_extra_str = json.dumps(schema.get('campos_ia_extra', []), indent=2, ensure_ascii=False)
        
        system_prompt = f"""
        Eres un Analista de Datos de Worldbuilding. Tu tarea es extraer información técnica del Lore.
        """
        
        user_prompt = f"""
        Texto del Lore: '{world.lore_description or world.description}'
        
        Esquema OBLIGATORIO (Campos Fijos): 
        {campos_fijos_str}
        
        Campos Opcionales Sugeridos (Solo si aplica):
        {campos_extra_str}
        
        INSTRUCCIONES ESTRICTAS DE FORMATO:
            - FORMATO DE CLAVES: Usa 'snake_case' técnico (ej: 'gravedad_media', 'nivel_entropia'). NO uses espacios ni mayúsculas en las claves.
            - VALORES: Concisos (Máximo 3-5 palabras).
            - NO inventes datos si no están en el texto. Usa "Pendiente".
            - NO añadas comentarios ni explicaciones. SOLO EL JSON.
            - DATOS EXTENDIDOS: Si encuentras datos relevantes en el texto que NO están en los Campos Fijos (ej: 'numero_soles', 'minerales_raros', 'anomalias_magicas'), agrégalos a 'datos_extendidos' usando claves snake_case.
            - Devuelve SOLO el JSON con las claves de nivel superior: "tipo_entidad", "datos_nucleo" (Fijos), "datos_extendidos" (Extra).
        """
        
        return self.ai.generate_structure(system_prompt, user_prompt)
