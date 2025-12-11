# Definición de nombres por Nivel (Longitud // 2)
HIERARCHY_LABELS = {
    1: "CAOS PRIME",
    2: "ABISMO / GESTACIÓN",
    # Rama Física (0101...)
    "PHYSICS": {
        3: "UNIVERSO",
        4: "GALAXIA",
        5: "SISTEMA",
        6: "PLANETA",
        7: "CONTINENTE",
        8: "PAÍS",
        9: "CIUDAD",
        10: "DISTRITO",
        11: "LUGAR",
        13: "RAZA/ESPECIE", # Default biología
        16: "PERSONAJE"
    },
    # Rama Dimensional (0105...)
    "DIMENSIONAL": {
        3: "PLANO MAYOR",
        4: "DOMINIO",
        5: "ESTRUCTURA",
        6: "CAPA / CÍRCULO",
        7: "SECTOR DIMENSIONAL",
        8: "ÁREA",
        9: "ASENTAMIENTO",
        13: "ESPECIE DEMONIACA",
        16: "ENTIDAD"
    }
}

def get_readable_hierarchy(jid):
    level = len(jid) // 2
    
    # Detección de Rama
    branch = "DIMENSIONAL" if (jid.startswith("0102") or jid.startswith("0105")) else "PHYSICS"
    
    # Detección Especial Nivel 13/16 (Objetos vs Biología)
    if level >= 13:
        try:
            # Check indices carefully. 
            # 24:26 means chars at index 24 and 25.
            # JID: "01" (2 chars) -> level 1
            # "0101" (4 chars) -> level 2 ? No, level = len//2
            # User says: Level 13 (indices 24-26 aprox)
            # len = 13*2 = 26.
            # Indices 0..25. 24 and 25 are the 13th pair.
            cat_id = int(jid[24:26]) 
            if cat_id >= 90: return "OBJETO / ARTEFACTO"
        except: pass

    # Retorno básico
    # First check if level is in top-level unique keys (1, 2)
    if level in HIERARCHY_LABELS and isinstance(HIERARCHY_LABELS[level], str):
        return HIERARCHY_LABELS[level]
        
    labels = HIERARCHY_LABELS.get(branch, HIERARCHY_LABELS["PHYSICS"])
    return labels.get(level, f"NIVEL {level}")

def get_available_levels(current_jid):
    """
    Retorna una lista de niveles disponibles para crear hijos desde el nivel actual.
    Ej: Si estoy en Nivel 3 (Universo), puedo crear Nivel 4, pero también saltar a 5, 6, etc.
    """
    current_level = len(current_jid) // 2
    branch_key = "DIMENSIONAL" if (current_jid.startswith("0102") or current_jid.startswith("0105")) else "PHYSICS"
    labels_map = HIERARCHY_LABELS.get(branch_key, HIERARCHY_LABELS["PHYSICS"])
    
    options = []
    
    # Rango de búsqueda: Niveles siguientes hasta un tope razonable (ej: Nivel 16)
    # Start at current_level + 1
    for lvl in range(current_level + 1, 17):
        label = labels_map.get(lvl)
        if label:
            options.append({
                'level': lvl,
                'label': label,
                'is_next': (lvl == current_level + 1)
            })
            
    return options
