from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

class ToggleWorldVisibilityUseCase:
    """
    Caso de Uso responsable de conmutar la visibilidad pública de una entidad.
    Una entidad con visibilidad desactivada (Oculta) solo será accesible para
    administradores y supervisores.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> str:
        """
        Cambia el estado de visibilidad (Público/Privado).
        Retorna el identificador para gestionar la redirección en la capa de infraestructura.
        """
        # Resolvemos la entidad (soporta NanoID y J-ID)
        world = resolve_world_id(self.repository, identifier)
        if not world:
            raise ValueError(f"No se ha encontrado la entidad: {identifier}")

        # Invertir el estado de visibilidad
        world.is_public = not world.is_public
        
        # Guardar el nuevo estado persistiendo el objeto de dominio
        self.repository.save(world)
        
        print(f" 👁️ Visibilidad de '{world.name}' cambiada a: {'PÚBLICO' if world.is_public else 'PRIVADO'}.")
        
        return world.id.value
