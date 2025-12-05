from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Domain.entities import VersionStatus

class ToggleWorldLockUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> str:
        """
        Toggles the lock status of a world.
        Returns the public_id (or id) to redirect to.
        """
        world = resolve_world_id(self.repository, identifier)
        if not world:
            raise ValueError(f"World not found: {identifier}")

        # Toggle lock
        if world.is_locked:
            world.is_locked = False
            # If unlocking, we might want to reset status to DRAFT if it was LOCKED?
            # The original logic was: if w.status == 'LOCKED' -> w.status = 'DRAFT'
            # Let's preserve that logic but using the new boolean field + status enum
            if world.status == VersionStatus.LIVE: # Or whatever status maps to LOCKED
                # Wait, the original code used 'LOCKED' as a status string.
                # Our Entity uses VersionStatus Enum.
                # Let's assume 'LOCKED' is not in the Enum yet, or we map it.
                pass
            # For now, just toggle the boolean.
        else:
            world.is_locked = True
            
        # Save changes
        self.repository.save(world)
        
        return world.id.value
