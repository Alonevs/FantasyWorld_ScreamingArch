from typing import Optional
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

def resolve_world_id(repository: CaosRepository, identifier: str) -> Optional[CaosWorld]:
    """
    Intenta resolver una entidad (Mundo/Nivel) a partir de un identificador genérico.
    El sistema prioriza el Identificador Público (NanoID) para URLs, y luego el 
    Identificador Jerárquico (J-ID) para búsquedas internas.
    
    Prioridad de búsqueda:
    1. Identificador Público (NanoID) - Agnosticismo para el usuario.
    2. Identificador Jerárquico (J-ID) - Determinismo interno.
    """
    # 1. Intentar resolver por Identificador Público (NanoID)
    world = repository.get_by_public_id(identifier)
    if world:
        return world
    
    # 2. Intentar resolver por Identificador Interno (J-ID)
    try:
        # El repositorio gestiona la recuperación mediante el value object WorldID
        return repository.get_by_id(WorldID(identifier))
    except:
        # Si fallan ambos, la entidad no existe
        return None
