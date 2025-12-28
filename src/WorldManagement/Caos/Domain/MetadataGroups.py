
class MetadataGroup:
    """
    Agrupación Lógica de Niveles de Coherencia (J-ID).
    Define qué tipo de metadatos se exigen según la profundidad del nivel.
    """
    FOUNDATIONS = "FOUNDATIONS"         # Niveles 01-02 (Caos, Abismo)
    COSMOLOGY = "COSMOLOGY"             # Niveles 03-05 (Universo, Galaxia, Sistema)
    PLANETARY = "PLANETARY"             # Niveles 06-07 (Planeta y su Geografía Global)
    SOCIO_POLITICAL = "SOCIO_POLITICAL" # Niveles 08-10 (Imperios, Reinos, Organizaciones)
    LOCALIZATION = "LOCALIZATION"       # Niveles 11-12 (Lugares físicos, Ciudades, Dungeons)
    BIOLOGICAL = "BIOLOGICAL"           # Niveles 13-15 (Taxonomía, Especies, Familias)
    INDIVIDUAL = "INDIVIDUAL"           # Nivel 16 (Personajes únicos, Objetos únicos)

    @classmethod
    def get_group_for_level(cls, level: int) -> str:
        if 1 <= level <= 2: return cls.FOUNDATIONS
        if 3 <= level <= 5: return cls.COSMOLOGY
        if 6 <= level <= 7: return cls.PLANETARY
        if 8 <= level <= 10: return cls.SOCIO_POLITICAL
        if 11 <= level <= 12: return cls.LOCALIZATION
        if 13 <= level <= 15: return cls.BIOLOGICAL
        if level == 16: return cls.INDIVIDUAL
        return None
