# Definición de nombres por Nivel (Nivel = Longitud J-ID // 2)
# Esta jerarquía define el "Nombre del Tipo" de cada entidad basado en su posición.

HIERARCHY_LABELS = {
    1: "CAOS",
    2: "ABISMO / GESTACIÓN",
    
    # Rama Física (Estructura tradicional: Mundo, Continente, Ciudad...)
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
        13: "RAZA/ESPECIE",
        16: "PERSONAJE"
    },
    
    # Rama Dimensional (Planos, Círculos, Entidades Demoníacas...)
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


# Etiquetas en plural para las categorías (Vistas de Índice)
PLURAL_HIERARCHY_LABELS = {
    "PHYSICS": {
        1: "CAOS",
        2: "ABISMOS",
        3: "UNIVERSOS",
        4: "GALAXIAS",
        5: "SISTEMAS",
        6: "PLANETAS",
        7: "CONTINENTES",
        8: "PAÍSES",
        9: "CIUDADES",
        10: "DISTRITOS",
        11: "LUGARES",
        12: "RAZAS",
        13: "CLASES",
        14: "SUBCLASES",
        15: "TIPO PERSONAJE",
        16: "PERSONAJES"
    },
    "DIMENSIONAL": {
        3: "PLANOS MAYORES",
        4: "DOMINIOS",
        5: "ESTRUCTURAS",
        6: "CAPAS / CÍRCULOS",
        7: "SECTORES DIMENSIONALES",
        8: "ÁREAS",
        9: "ASENTAMIENTOS",
        13: "ESPECIES DEMONIACAS",
        16: "ENTIDADES"
    }
}

def get_plural_label(level, jid="0101"):
    """
    Retorna la etiqueta en plural correspondiente al nivel y la rama del J-ID proporcionado.
    """
    branch = "DIMENSIONAL" if (jid.startswith("0102") or jid.startswith("0105")) else "PHYSICS"
    labels = PLURAL_HIERARCHY_LABELS.get(branch, PLURAL_HIERARCHY_LABELS["PHYSICS"])
    return labels.get(level, f"CATEGORÍA NIVEL {level}")


# Etiquetas para los encabezados de las listas de hijos según el nivel del PADRE.
# Ejemplo: si el Padre es Nivel 8 (País), sus hijos son 'CIUDADES'.
CHILDREN_LABELS = {
    12: "RAZAS DISPONIBLES",
    13: "CLASES",
    14: "SUBCLASES",
    15: "PERSONAJES",
    6:  "CONTINENTES",
    7:  "PAÍSES / REGIONES",
    8:  "CIUDADES",
    9:  "DISTRITOS",
}

def get_readable_hierarchy(jid):
    """
    Resuelve el nombre legible del nivel jerárquico para un J-ID específico.
    Gestiona la detección de ramas (Física/Dimensional) y casos especiales para niveles profundos.
    """
    level = len(jid) // 2
    
    # Determinar la rama según el prefijo del J-ID
    branch = "DIMENSIONAL" if (jid.startswith("0102") or jid.startswith("0105")) else "PHYSICS"
    
    # Lógica especial para diferenciar Objetos de Biología en niveles profundos (L13+)
    if level >= 13:
        try:
            # Si el par de dígitos en la posición 13 (24:26) es >= 90, se trata de un Objeto
            cat_id = int(jid[24:26]) 
            if cat_id >= 90: return "OBJETO / ARTEFACTO"
        except: pass

    # Resolución del nombre según nivel y rama
    if level in HIERARCHY_LABELS and isinstance(HIERARCHY_LABELS[level], str):
        return HIERARCHY_LABELS[level]
        
    labels = HIERARCHY_LABELS.get(branch, HIERARCHY_LABELS["PHYSICS"])
    return labels.get(level, f"NIVEL {level}")

def get_available_levels(current_jid):
    """
    Retorna los niveles disponibles para la creación de hijos desde la posición actual.
    Soporta la lógica de "Saltos de Jerarquía" permitiendo crear hijos en cualquier nivel inferior.
    """
    current_level = len(current_jid) // 2
    branch_key = "DIMENSIONAL" if (current_jid.startswith("0102") or current_jid.startswith("0105")) else "PHYSICS"
    labels_map = HIERARCHY_LABELS.get(branch_key, HIERARCHY_LABELS["PHYSICS"])
    
    options = []
    
    # Recorremos desde el nivel inmediatamente inferior hasta el máximo permitido (16)
    for lvl in range(current_level + 1, 17):
        # Intentamos obtener la etiqueta para el nivel actual en el bucle
        label = labels_map.get(lvl, HIERARCHY_LABELS.get(lvl))
        if isinstance(label, dict): label = None # Seguridad si la clave existe pero es una rama (dict)
        
        if label:
            options.append({
                'level': lvl,
                'label': label,
                'is_next': (lvl == current_level + 1) # Indica si es el hijo natural (sin salto)
            })
            
    return options

def get_children_label(current_jid):
    """
    Retorna la etiqueta para la sección de hijos basada en el nivel del PADRE actual.
    """
    level = len(current_jid) // 2
    return CHILDREN_LABELS.get(level, "ENTIDADES HIJAS")
