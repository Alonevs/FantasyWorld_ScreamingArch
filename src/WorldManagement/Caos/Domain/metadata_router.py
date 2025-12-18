from .metadata import METADATA_SCHEMAS

def get_schema_for_type(type_name: str):
    """Returns a schema based on a type string (e.g., 'PLANETA', 'CRIATURA')."""
    if not type_name: return None
    
    # Normalize
    type_name = type_name.upper().replace('_SCHEMA', '')
    key = f"{type_name}_SCHEMA"
    
    return METADATA_SCHEMAS.get(key)

def get_schema_for_hierarchy(jid: str, level: int):
    # 1. NIVEL 16 (ENTIDADES) - EL GRAN SWITCH
    if level == 16:
        try:
            # Switch Nivel 13 (Indices 24-26 aprox, ajusta según tu ID real)
            # IDs 90-99 son OBJETOS. El resto son CRIATURAS.
            # Assuming standard J-ID format provided by user context.
            cat_id = int(jid[24:26]) 
            if cat_id >= 90: return METADATA_SCHEMAS["OBJETO_SCHEMA"]
            return METADATA_SCHEMAS["CRIATURA_SCHEMA"]
        except:
            return METADATA_SCHEMAS["CRIATURA_SCHEMA"] # Fallback a Biología

    # 2. NIVELES SOCIALES/GEOGRÁFICOS (7-11)
    if 7 <= level <= 11: 
        # Podríamos distinguir Geografía vs Sociedad, pero por ahora usamos un híbrido o Sociedad
        return METADATA_SCHEMAS["GEOGRAFIA_SCHEMA"] if level == 7 else METADATA_SCHEMAS["SOCIEDAD_SCHEMA"]

    # 3. COSMOLOGÍA (1-6)
    if level == 6:
        if jid.startswith("0101") and not jid.startswith("0105"): # Ajustar lógica rama
             return METADATA_SCHEMAS["PLANETA_SCHEMA"]
        return METADATA_SCHEMAS["DIMENSION_SCHEMA"]
    
    # Resto de niveles básicos
    if level == 1: return METADATA_SCHEMAS["CAOS_SCHEMA"]
    if level == 2: return METADATA_SCHEMAS["ABISMO_SCHEMA"]
    if level == 3: return METADATA_SCHEMAS["UNIVERSO_SCHEMA"]
    if level == 4: return METADATA_SCHEMAS["GALAXIA_SCHEMA"]
    if level == 5: return METADATA_SCHEMAS["SISTEMA_SCHEMA"]

    return None
