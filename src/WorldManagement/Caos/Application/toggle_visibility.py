from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

class ToggleWorldVisibilityUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> str:
        """
        Toggles the public visibility of a world.
        Returns the public_id (or id) to redirect to.
        """
        world = resolve_world_id(self.repository, identifier)
        if not world:
            raise ValueError(f"World not found: {identifier}")

        # Toggle visibility
        world.is_public = not world.is_public
        
        # Save changes
        self.repository.save(world)
        
        # Return the best ID for redirection
        # Note: We need to access public_id from the entity, but our entity doesn't store it explicitly 
        # (it's in the ORM). Ideally, the Entity should have it.
        # For now, we return the identifier passed or the ID.
        # To be safe, let's fetch the updated object or just return the ID.
        # The view will handle the redirect.
        return world.id.value
