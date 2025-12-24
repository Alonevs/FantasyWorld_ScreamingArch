from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Domain.entities import VersionStatus

class ToggleWorldLockUseCase:
    """
    Caso de Uso responsable de conmutar el estado de bloqueo de una entidad.
    Una entidad bloqueada (LOCKED) no permite cambios ni nuevas propuestas de
    modificación hasta que sea desbloqueada por un administrador.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> str:
        """
        Cambia el estado de bloqueo (True/False).
        Retorna el identificador de la entidad para gestionar la redirección.
        """
        # Resolvemos la entidad (soporta NanoID y J-ID)
        world = resolve_world_id(self.repository, identifier)
        if not world:
            raise ValueError(f"No se ha encontrado la entidad: {identifier}")

        # Invertir el estado de bloqueo
        # Nota: El bloqueo es una medida de seguridad administrativa para "congelar" el estado.
        if world.is_locked:
            world.is_locked = False
            print(f" 🔓 Entidad '{world.name}' DESBLOQUEADA.")
        else:
            world.is_locked = True
            print(f" 🔒 Entidad '{world.name}' BLOQUEADA formalmente.")
            
        # Persistir el cambio mediante el repositorio de dominio
        self.repository.save(world)
        
        return world.id.value
