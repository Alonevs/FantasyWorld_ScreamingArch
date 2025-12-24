from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld, VersionStatus
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class InitializeHemispheresUseCase:
    """
    Caso de Uso responsable de la inicialización geográfica de un planeta.
    Genera automáticamente los hemisferios Norte y Sur como hijos deterministas (01 y 02),
    inyectando la configuración climática y latitudinal necesaria para el sistema de herencia.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, planet_jid: str):
        """
        Crea los dos hemisferios para un planeta específico.
        
        Args:
            planet_jid: El identificador J-ID del planeta (Debe ser Nivel 6).
        """
        # Validación: Solo los Planetas (Nivel 6, longitud 12) activan esta lógica.
        if len(planet_jid) != 12:
            raise ValueError(f"El ID {planet_jid} no corresponde a un Planeta. La jerarquía requiere Nivel 6.")

        # Generación de Identificadores Deterministas
        # El Norte siempre es el primogénito (01) y el Sur el segundo (02).
        id_norte = f"{planet_jid}01"
        id_sur   = f"{planet_jid}02"

        # Inyección de Metadatos Técnicos (Geoconfiguración)
        # Estos datos permiten calcular el clima de los continentes hijos.
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

        # Instanciación y Persistencia
        # Los hemisferios nacen directamente en estado LIVE ya que son estructuras 
        # fundamentales y automáticas del sistema planetario.
        norte = CaosWorld(
            id=WorldID(id_norte), name="Hemisferio Norte", 
            lore_description="Tierras boreales. Abarca desde el ecuador hasta el polo norte.", 
            status=VersionStatus.LIVE, metadata=meta_norte
        )
        
        sur = CaosWorld(
            id=WorldID(id_sur), name="Hemisferio Sur", 
            lore_description="Tierras australes. Abarca desde el ecuador hasta el polo sur.", 
            status=VersionStatus.LIVE, metadata=meta_sur
        )

        self.repository.save(norte)
        self.repository.save(sur)
        
        print(f" 🌍 Planeta {planet_jid} inicializado con sus dos hemisferios.")
