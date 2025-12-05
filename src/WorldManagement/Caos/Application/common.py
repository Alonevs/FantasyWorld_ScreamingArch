from typing import Optional
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

def resolve_world_id(repository: CaosRepository, identifier: str) -> Optional[CaosWorld]:
    """
    Tries to resolve a World by its identifier.
    Priority:
    1. Public ID (NanoID)
    2. Internal ID (J-ID)
    """
    # 1. Try Public ID
    world = repository.get_by_public_id(identifier)
    if world:
        return world
    
    # 2. Try Internal ID
    try:
        # Validate if it looks like a J-ID (optional, but repository handles it)
        return repository.get_by_id(WorldID(identifier))
    except:
        return None
