from typing import Dict, Any, Optional

# ==========================================
# METADATA.PY - ESQUEMAS MAESTROS V2.0
# ==========================================
# Definición estricta de esquemas. 
# Claves en snake_case.

METADATA_SCHEMAS = {
    # NIVEL 01: CAOS
    "CAOS_SCHEMA": {
        "campos_fijos": {
            "nivel_entropia": "0-100%",
            "color_primordial": "Ej: Violeta",
            "consciencia_latente": "Nula/Despierta",
            "tipo_energia": "Nombre energía base"
        }
    },
    # NIVEL 02: ABISMO (Gestación)
    "ABISMO_SCHEMA": {
        "campos_fijos": {
            "estado_gestacion": "Activo/Latente",
            "estabilidad_elemental": "Caótica/Equilibrada",
            "presencia_elemental": "Lista elementos",
            "profundidad_existencial": "1-10"
        }
    },
    # NIVEL 03: UNIVERSO (Materia)
    "UNIVERSO_SCHEMA": {
        "campos_fijos": {
            "leyes_fisicas_activas": "TRUE/FALSE",
            "constante_magica": "Alta/Baja",
            "estado_expansion": "Expandiendo/Colapsando",
            "edad_cosmica": "Joven/Antigua"
        }
    },
    # NIVEL 04: GALAXIA
    "GALAXIA_SCHEMA": {
        "campos_fijos": {
            "tipo_morfologia": "Espiral/Elíptica",
            "nucleo_activo": "Agujero Negro/Quasar",
            "habitabilidad_media": "Alta/Baja",
            "civilizacion_dominante": "Escala Kardashev"
        }
    },
    # NIVEL 05: SISTEMA PLANETARIO
    "SISTEMA_SCHEMA": {
        "campos_fijos": {
            "tipo_estrella_central": "Enana Roja/Binaria",
            "cantidad_soles": "Número",
            "cantidad_planetas": "Número",
            "cinturon_asteroides": "Si/No"
        }
    },
    # NIVEL 06: PLANETA (Físico)
    "PLANETA_SCHEMA": {
        "campos_fijos": {
            "gravedad": "Valor g (ej: 1.0g)",
            "atmosfera": "Respirable/Toxica",
            "clima_global": "Tropical/Arido",
            "numero_lunas": "Número",
            "cobertura_agua": "Porcentaje"
        }
    },
    # GENÉRICOS
    "GRUPO_DIMENSIONAL": { "campos_fijos": { "densidad_espiritual": "", "corrupcion": "", "elemento_dominante": "" } },
    "GRUPO_SOCIAL": { "campos_fijos": { "poblacion": "", "gobierno": "", "tecnologia": "" } }
}

# ==========================================
# LÓGICA DE SELECCIÓN (ROUTER)
# ==========================================

def get_schema_for_hierarchy(jid: str, level: int) -> Optional[Dict[str, Any]]:
    """
    Selecciona el esquema V2 basado en Nivel y Rama J-ID.
    """
    
    # 1. Convergencia Social (Niveles altos)
    if level >= 8: return METADATA_SCHEMAS.get("GRUPO_SOCIAL")

    # 2. Lógica de Ramas (Niveles 1-7)
    
    # A. RAMA REALIDAD / FÍSICA (010101...)
    if level == 1: return METADATA_SCHEMAS.get("CAOS_SCHEMA")
    
    # Verificar si es rama física (0101...)
    if jid.startswith("0101") and not (jid.startswith("0102") or jid.startswith("0103")):
        if level == 2: return METADATA_SCHEMAS.get("ABISMO_SCHEMA")
        if level == 3: return METADATA_SCHEMAS.get("UNIVERSO_SCHEMA")
        if level == 4: return METADATA_SCHEMAS.get("GALAXIA_SCHEMA")
        if level == 5: return METADATA_SCHEMAS.get("SISTEMA_SCHEMA")
        if level == 6: return METADATA_SCHEMAS.get("PLANETA_SCHEMA")
        if level == 7: return METADATA_SCHEMAS.get("PLANETA_SCHEMA") 
            
    # B. RAMA DIMENSIONAL (0102...)
    if jid.startswith("0102") or jid.startswith("0103"):
        if 2 <= level <= 7:
            return METADATA_SCHEMAS.get("GRUPO_DIMENSIONAL")

    return None

# MAPEO DE TIPOS (Fallback)
TYPE_MAPPING = {
    "CAOS_PRIME": "CAOS_SCHEMA",
    "ABISMO": "ABISMO_SCHEMA",
    "REALIDAD": "UNIVERSO_SCHEMA",
    "GALAXIA": "GALAXIA_SCHEMA",
    "SISTEMA": "SISTEMA_SCHEMA",
    "PLANETA": "PLANETA_SCHEMA",
    "PAIS": "GRUPO_SOCIAL",
    "CIUDAD": "GRUPO_SOCIAL"
}

def get_schema_for_type(entity_type: str) -> Optional[Dict[str, Any]]:
    key = TYPE_MAPPING.get(entity_type.upper())
    if not key:
        # Intento genérico
        if "CIUDAD" in entity_type.upper(): key = "GRUPO_SOCIAL"
        if "PLANETA" in entity_type.upper(): key = "PLANETA_SCHEMA"
        
    return METADATA_SCHEMAS.get(key)
