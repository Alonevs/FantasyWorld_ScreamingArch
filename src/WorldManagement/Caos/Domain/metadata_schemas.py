
# DEFINICIÓN DE ESQUEMAS DE METADATOS (FUENTE DE VERDAD)

SCHEMAS_COSMOLOGIA = {
    # NIVEL 01: CAOS PRIME (Raíz)
    "NIVEL_01": {
        "descripcion": "El origen conceptual.",
        "campos_fijos": {
            "nivel_entropia": "0-100%",
            "color_primordial": "Manifestación visual",
            "tipo_energia": "Energía base (ej: Éter)",
            "consciencia_latente": "Nula/Despierta"
        }
    },
    
    # NIVEL 02: ABISMOS / VACÍO (Gestación)
    "NIVEL_02": {
        "descripcion": "Zona de gestación y convergencia elemental.",
        "campos_fijos": {
            "estado_gestacion": "Activo/Latente",
            "estabilidad_elemental": "Caótica/Equilibrada",
            "presencia_elemental": "Lista elementos",
            "profundidad_existencial": "Nivel 1-10"
        }
    },

    # NIVEL 03: UNIVERSO / REALIDAD (Materia)
    "NIVEL_03_FISICO": {
        "campos_fijos": {
            "leyes_fisicas_activas": "TRUE",
            "constante_magica": "Alta/Baja",
            "estado_expansion": "Expandiendo/Colapsando",
            "edad_cosmica": "Joven/Antigua"
        }
    },
    
    # NIVEL 04: GALAXIA
    "NIVEL_04_FISICO": {
        "campos_fijos": {
            "tipo_morfologia": "Espiral/Elíptica",
            "nucleo_activo": "Agujero Negro/Quasar",
            "civilizacion_dominante": "Escala Kardashev"
        }
    },

    # NIVEL 05: SISTEMA PLANETARIO
    "NIVEL_05_FISICO": {
        "campos_fijos": {
            "tipo_estrella_central": "Enana Roja/Binaria",
            "cantidad_soles": "Número",
            "cantidad_planetas": "Número",
            "zona_habitable": "Amplia/Estrecha"
        }
    },

    # NIVEL 06: PLANETA (La clave)
    "NIVEL_06_FISICO": {
        "campos_fijos": {
            "gravedad": "Valor g (ej: 1.0g)",
            "atmosfera": "Respirable/Toxica",
            "clima_global": "Tropical/Arido",
            "numero_lunas": "Número",
            "cobertura_agua": "Porcentaje"
        }
    }
}

# ------------------------------------------------------------------------------
# BLOQUE 2: DIMENSIONES ALTERNAS (Ramas 0102, 0103, 0105...)
# ------------------------------------------------------------------------------

SCHEMAS_DIMENSIONALES = {
    # Generico para Niveles 3-5 en ramas mágicas
    "DIMENSION_ESTRUCTURA": {
        "campos_fijos": {
            "estabilidad_magica": "Alta/Baja",
            "fuente_poder": "Divina/Infernal/Arcana",
            "acceso_desde_realidad": "Abierto/Sellado"
        }
    },
    
    # Nivel 6 en Infierno = Capa / Círculo
    "NIVEL_06_DIMENSIONAL": {
        "campos_fijos": {
            "densidad_espiritual": "Presión del alma",
            "corrupcion_ambiental": "0-100%",
            "gobernante_capa": "Nombre entidad",
            "ley_sobrenatural": "Regla especial de la capa"
        }
    }
}

# ------------------------------------------------------------------------------
# BLOQUE 3: GEOGRAFÍA Y SOCIEDAD (Niveles 07 - 11)
# ------------------------------------------------------------------------------
# Común para Tierra e Infierno (una ciudad es una ciudad).

SCHEMA_SOCIEDAD = {
    "campos_fijos": {
        "poblacion": "Número estimado",
        "gobierno": "Tipo político",
        "nivel_tecnologico": "Era tecnológica/mágica",
        "defensas": "Nivel 1-10",
        "recurso_principal": "Economía base"
    }
}

# ------------------------------------------------------------------------------
# LOGICA DE SELECCIÓN
# ------------------------------------------------------------------------------

def get_schema_for_hierarchy(jid: str, level: int):
    # Lógica simplificada para el agente
    if 7 <= level <= 11: return SCHEMA_SOCIEDAD
    if level == 1: return SCHEMAS_COSMOLOGIA["NIVEL_01"]
    if level == 2: return SCHEMAS_COSMOLOGIA["NIVEL_02"]
    
    # Detectar rama física (Empieza por 0101...)
    is_physics = jid.startswith("0101") 
    
    if is_physics:
        if level == 3: return SCHEMAS_COSMOLOGIA["NIVEL_03_FISICO"]
        if level == 4: return SCHEMAS_COSMOLOGIA["NIVEL_04_FISICO"]
        if level == 5: return SCHEMAS_COSMOLOGIA["NIVEL_05_FISICO"]
        if level == 6: return SCHEMAS_COSMOLOGIA["NIVEL_06_FISICO"]
    else:
        if level == 6: return SCHEMAS_DIMENSIONALES["NIVEL_06_DIMENSIONAL"]
        # Fallback for intermediate dimensional levels
        if 3 <= level <= 5: return SCHEMAS_DIMENSIONALES["DIMENSION_ESTRUCTURA"]
    
    return {}
