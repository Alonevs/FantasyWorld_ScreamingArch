from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld, VersionStatus
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class InitializeHemispheresUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, planet_jid: str):
        # Validación: Solo los Planetas (Nivel 6, 12 caracteres) pueden tener hemisferios
        if len(planet_jid) != 12:
            raise ValueError(f"El ID {planet_jid} no es un Planeta (Debe tener 12 caracteres).")

        # IDs Deterministas (No secuenciales)
        id_norte = f"{planet_jid}01"
        id_sur   = f"{planet_jid}02"

        # Definición de Metadata (Franjas Climáticas)
        meta_norte = {
            "tipo_entidad": "HEMISFERIO",
            "geo_config": { "posicion": "NORTE", "rango_latitud": [0, 90], "polo_magnetico": True },
            "reglas_clima": { "invertir_estaciones": False, "gradiente_temperatura": "NORMAL" },
            "slots_climaticos": ["EQUATORIAL", "TEMPERATE", "POLAR"]
        }

        meta_sur = {
            "tipo_entidad": "HEMISFERIO",
            "geo_config": { "posicion": "SUR", "rango_latitud": [-90, 0], "polo_magnetico": False },
            "reglas_clima": { "invertir_estaciones": True, "gradiente_temperatura": "NORMAL" },
            "slots_climaticos": ["EQUATORIAL", "TEMPERATE", "POLAR"]
        }

        # Creación de Entidades (Nacen en estado LIVE para uso inmediato)
        norte = CaosWorld(
            id=WorldID(id_norte), name="Hemisferio Norte", 
            lore_description="Tierras boreales. Latitud 0° a 90°.", 
            status=VersionStatus.LIVE, metadata=meta_norte
        )
        
        sur = CaosWorld(
            id=WorldID(id_sur), name="Hemisferio Sur", 
            lore_description="Tierras australes. Latitud -90° a 0°.", 
            status=VersionStatus.LIVE, metadata=meta_sur
        )

        self.repository.save(norte)
        self.repository.save(sur)
