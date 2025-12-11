# ==============================================================================
# METADATA.PY - ESQUEMAS MAESTROS V3.0
# ==============================================================================

METADATA_SCHEMAS = {

    # --- 1. COSMOLOGÍA Y ENTORNO (Niveles 1-6) ---
    "CAOS_SCHEMA": { "campos_fijos": { "nivel_entropia": "0-100%", "tipo_energia": "Nombre energía", "consciencia": "Nula/Latente" } },
    "ABISMO_SCHEMA": { "campos_fijos": { "estado_gestacion": "Activo/Latente", "elementos_presentes": "Fuego/Vacio", "profundidad": "1-10" } },
    "UNIVERSO_SCHEMA": { "campos_fijos": { "leyes_fisicas": "TRUE", "magia_ambiental": "Alta/Baja", "expansion": "Estado" } },
    "GALAXIA_SCHEMA": { "campos_fijos": { "morfologia": "Espiral/Eliptica", "nucleo": "Agujero Negro", "civilizacion": "Kardashev" } },
    "SISTEMA_SCHEMA": { "campos_fijos": { "soles": "Cantidad", "planetas": "Cantidad", "zona_habitable": "Si/No" } },
    
    # EL PADRE FÍSICO (Fuente de Herencia Crítica)
    "PLANETA_SCHEMA": { 
        "campos_fijos": { 
            "gravedad": "Valor g (ej: 1.0g)", 
            "atmosfera": "Respirable/Toxica", 
            "clima_global": "Base (ej: Glacial)", 
            "lunas": "Cantidad", 
            "agua": "%" 
        } 
    },

    # --- 2. DIMENSIONES (Rama Alternativa) ---
    "DIMENSION_SCHEMA": { "campos_fijos": { "densidad_espiritual": "Alta/Media", "corrupcion": "0-100%", "ley_dominante": "Regla del plano" } },

    # --- 3. GEOGRAFÍA Y SOCIEDAD (Niveles 7-11) ---
    # Aquí definimos el BIOMA local, que afectará a las criaturas.
    "GEOGRAFIA_SCHEMA": { 
        "campos_fijos": { 
            "bioma_dominante": "Bosque/Desierto/Tundra", # CLAVE PARA BIOLOGÍA
            "temperatura_media": "Grados C",
            "recursos_naturales": "Hierro/Mana/Agua",
            "peligrosidad_ambiental": "Baja/Extrema"
        } 
    },
    "SOCIEDAD_SCHEMA": { 
        "campos_fijos": { 
            "poblacion": "Estimada", 
            "gobierno": "Tipo político", 
            "nivel_tecnologico": "Medieval/Futurista", 
            "idioma_oficial": "Nombre idioma"
        } 
    },

    # --- 4. ENTIDADES FINALES (Nivel 16) - SELECCIÓN POR SWITCH NIVEL 13 ---
    
    # A. RAMA BIOLÓGICA (IDs 00-89) - Seres Vivos
    "CRIATURA_SCHEMA": {
        "descripcion": "Ficha básica de ser vivo.",
        "campos_fijos": {
            "nombre_raza": "Humano/Elfo/Bestia",
            "edad_media": "Esperanza de vida",
            "rol_biologico": "Depredador/Presa/Civilizado",
            "dieta": "Omnívoro/Carnívoro/Energía",
            "habitat_ideal": "Bioma preferido (ej: Bosques)", # Se compara con el Bioma geográfico
            "nivel_amenaza": "Rango F-S",
            "alineamiento": "Moral (ej: Neutral)"
        },
        "campos_ia_extra": ["Habilidades_Raciales", "Debilidades", "Comportamiento_Social"]
    },
    
    # B. RAMA OBJETOS (IDs 90-99) - Cosas Inanimadas
    "OBJETO_SCHEMA": {
        "descripcion": "Artefactos, armas o items.",
        "campos_fijos": {
            "tipo_objeto": "Arma/Reliquia/Libro",
            "material_base": "Acero/Mitril/Madera",
            "calidad": "Común/Raro/Legendario",
            "estado_conservacion": "Intacto/Oxidado/Roto",
            "creador_origen": "Cultura o Nombre",
            "historial_portadores": "Timeline Cronológico" # Para visualización futura
        },
        "campos_ia_extra": ["Efectos_Magicos", "Requisitos_Uso", "Valor_Estimado"]
    }
}

# --- 5. ESTRATEGIA DE HERENCIA (Cascading Rules) ---
# Define qué campos 'bajan' desde el padre hasta el hijo automáticamente.
INHERITANCE_RULES = {
    # FÍSICA (Desde Planeta -> Todo lo de abajo)
    "gravedad": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    "atmosfera": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    "ciclo_dia": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    
    # ENTORNO (Desde Geografía -> Criatura)
    # Una criatura en el desierto hereda el contexto del bioma
    "bioma_dominante": {"source": "GEOGRAFIA_SCHEMA", "targets": ["CIUDAD", "LUGAR", "CRIATURA"]},
    
    # SOCIEDAD (Desde País -> Ciudad -> Personaje)
    "idioma_oficial": {"source": "SOCIEDAD_SCHEMA", "targets": ["CIUDAD", "LUGAR", "CRIATURA"]},
    "nivel_tecnologico": {"source": "SOCIEDAD_SCHEMA", "targets": ["CIUDAD", "OBJETO"]} # Un objeto hereda la tecnología de donde se forjó
}
