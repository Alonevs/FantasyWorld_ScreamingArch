from .metadata import METADATA_SCHEMAS

"""
Enrutador de Metadatos: Lógica para asignar esquemas técnicos según la jerarquía.
Este módulo traduce la posición en el J-ID (nivel y rama) a un esquema de datos
específico que la IA puede entender y rellenar.
"""

def get_schema_for_type(type_name: str):
    """
    Retorna un esquema basado en un nombre de tipo explícito (ej: 'PLANETA', 'CRIATURA').
    Utilizado principalmente cuando el usuario fuerza un tipo desde el manual.
    """
    if not type_name: return None
    
    # Normalización del nombre para que coincida con las claves del diccionario
    type_name = type_name.upper().replace('_SCHEMA', '')
    key = f"{type_name}_SCHEMA"
    
    return METADATA_SCHEMAS.get(key)

def get_schema_for_hierarchy(jid: str, level: int):
    """
    Aplica la "Lógica de Niveles" para determinar automáticamente el esquema 
    según la posición jerárquica de la entidad en el universo.
    """
    # 1. NIVEL 16 (ENTIDADES FINALES) - EL GRAN SWITCH
    # En este nivel se dividen los seres vivos de los objetos inanimados.
    if level == 16:
        try:
            # Determinamos la categoría usando el segmento del Nivel 13 (posiciones 24-26)
            # IDs del 90 al 99 se reservan para OBJETOS / ARTEFACTOS.
            cat_id = int(jid[24:26]) 
            if cat_id >= 90: 
                return METADATA_SCHEMAS["OBJETO_SCHEMA"]
            # El resto (00-89) se clasifican como CRIATURAS (Biología).
            return METADATA_SCHEMAS["CRIATURA_SCHEMA"]
        except:
            return METADATA_SCHEMAS["CRIATURA_SCHEMA"] # Fallback de seguridad

    # 2. NIVELES SOCIALES Y GEOGRÁFICOS (7-11)
    if 7 <= level <= 11: 
        # El Nivel 7 es típicamente Geografía (Biomas), el resto suelen ser Continentales/Sociales.
        return METADATA_SCHEMAS["GEOGRAFIA_SCHEMA"] if level == 7 else METADATA_SCHEMAS["SOCIEDAD_SCHEMA"]

    # 3. COSMOLOGÍA Y ASTROFÍSICA (1-6)
    if level == 6:
        # Los planetas suelen colgar de la rama física (0101...), 
        # mientras que las dimensiones cuelgan de otras ramas cosmogónicas.
        if jid.startswith("0101") and not jid.startswith("0105"): 
             return METADATA_SCHEMAS["PLANETA_SCHEMA"]
        return METADATA_SCHEMAS["DIMENSION_SCHEMA"]
    
    # Mapeo determinista para los niveles fundamentales del motor.
    if level == 1: return METADATA_SCHEMAS["CAOS_SCHEMA"]
    if level == 2: return METADATA_SCHEMAS["ABISMO_SCHEMA"]
    if level == 3: return METADATA_SCHEMAS["UNIVERSO_SCHEMA"]
    if level == 4: return METADATA_SCHEMAS["GALAXIA_SCHEMA"]
    if level == 5: return METADATA_SCHEMAS["SISTEMA_SCHEMA"]

    return None
