# ==============================================================================
# METADATA.PY - ESQUEMAS MAESTROS Y REGLAS DE HERENCIA V3.0
# ==============================================================================
"""
Este módulo define la "estructura del conocimiento" del universo (Ontología).
Contiene los esquemas técnicos (Schemas) que la IA utiliza para rellenar las 
fichas de datos y las reglas de herencia que permiten que los niveles inferiores
conozcan su contexto ambiental (Clima, Magia, Tecnología).
"""

METADATA_SCHEMAS = {

    # --- 1. COSMOLOGÍA Y ENTORNO (Niveles 1-6) ---
    # Nivel 1: El origen primordial
    "CAOS_SCHEMA": { "campos_fijos": { "nivel_entropia": "0-100%", "tipo_energia": "Nombre energía", "consciencia": "Nula/Latente" } },
    # Nivel 2: Espacio entre mundos
    "ABISMO_SCHEMA": { "campos_fijos": { "estado_gestacion": "Activo/Latente", "elementos_presentes": "Fuego/Vacio", "profundidad": "1-10" } },
    # Nivel 3: El contenedor de leyes
    "UNIVERSO_SCHEMA": { "campos_fijos": { "leyes_fisicas": "TRUE", "magia_ambiental": "Alta/Baja", "expansion": "Estado" } },
    # Nivel 4: Agrupación estelar
    "GALAXIA_SCHEMA": { "campos_fijos": { "morfologia": "Espiral/Eliptica", "nucleo": "Agujero Negro", "civilizacion": "Kardashev" } },
    # Nivel 5: Dominio local
    "SISTEMA_SCHEMA": { "campos_fijos": { "soles": "Cantidad", "planetas": "Cantidad", "zona_habitable": "Si/No" } },
    
    # Nivel 6: EL PADRE FÍSICO (Fuente principal de herencia para seres vivos)
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
    # Bioma local: Define el escenario inmediato de las historias.
    "GEOGRAFIA_SCHEMA": { 
        "campos_fijos": { 
            "bioma_dominante": "Bosque/Desierto/Tundra", # Clave para validación biológica
            "temperatura_media": "Grados C",
            "recursos_naturales": "Hierro/Mana/Agua",
            "peligrosidad_ambiental": "Baja/Extrema"
        } 
    },
    # Estructura social y política.
    "SOCIEDAD_SCHEMA": { 
        "campos_fijos": { 
            "poblacion": "Estimada", 
            "gobierno": "Tipo político", 
            "nivel_tecnologico": "Medieval/Futurista", 
            "idioma_oficial": "Nombre idioma"
        } 
    },

    # --- 4. ENTIDADES FINALES (Nivel 16) ---
    
    # A. RAMA BIOLÓGICA (IDs 00-89): Fauna, Flora y Personajes.
    "CRIATURA_SCHEMA": {
        "descripcion": "Ficha básica de ser vivo.",
        "campos_fijos": {
            "nombre_raza": "Humano/Elfo/Bestia",
            "edad_media": "Esperanza de vida",
            "rol_biologico": "Depredador/Presa/Civilizado",
            "dieta": "Omnívoro/Carnívoro/Energía",
            "habitat_ideal": "Bioma preferido", # Se compara con el bioma heredado
            "nivel_amenaza": "Rango F-S",
            "alineamiento": "Moral (ej: Neutral)"
        },
        "campos_ia_extra": ["Habilidades_Raciales", "Debilidades", "Comportamiento_Social"]
    },
    
    # B. RAMA OBJETOS (IDs 90-99): Artefactos e Items.
    "OBJETO_SCHEMA": {
        "descripcion": "Artefactos, armas o items.",
        "campos_fijos": {
            "tipo_objeto": "Arma/Reliquia/Libro",
            "material_base": "Acero/Mitril/Madera",
            "calidad": "Común/Raro/Legendario",
            "estado_conservacion": "Intacto/Oxidado/Roto",
            "creador_origen": "Cultura o Nombre",
            "historial_portadores": "Registro histórico" 
        },
        "campos_ia_extra": ["Efectos_Magicos", "Requisitos_Uso", "Valor_Estimado"]
    }
}

# --- 5. ESTRATEGIA DE HERENCIA (Reglas en Cascada) ---
# Define qué datos técnicos 'fluyen' desde los ancestros hacia los descendientes.
# Esto evita que la IA tenga que inventar datos globales en niveles locales.
INHERITANCE_RULES = {
    # Herencia FÍSICA: Todo lo que esté dentro de un planeta comparte su física básica.
    "gravedad": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    "atmosfera": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    "ciclo_dia": {"source": "PLANETA_SCHEMA", "targets": ["ALL"]},
    
    # Herencia de ENTORNO: Las criaturas heredan el bioma de la región donde viven.
    "bioma_dominante": {"source": "GEOGRAFIA_SCHEMA", "targets": ["CIUDAD", "LUGAR", "CRIATURA"]},
    
    # Herencia de SOCIEDAD: El idioma y la tecnología fluyen desde el país hacia el individuo.
    "idioma_oficial": {"source": "SOCIEDAD_SCHEMA", "targets": ["CIUDAD", "LUGAR", "CRIATURA"]},
    # Un objeto hereda el nivel tecnológico del lugar donde fue forjado.
    "nivel_tecnologico": {"source": "SOCIEDAD_SCHEMA", "targets": ["CIUDAD", "OBJETO"]} 
}
