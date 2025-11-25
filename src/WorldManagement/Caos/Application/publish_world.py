from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

class PublishWorldUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, world_id_str: str):
        # 1. Recuperar
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        
        if not world:
            raise Exception("Mundo no encontrado")

        # 2. Ejecutar lógica de dominio
        world.publish()
        
        # 3. Guardar cambios
        self.repository.save(world)
        print(f" LOGICA NEGOCIO: Mundo '{world.name}' ha sido PUBLICADO oficialmente.")