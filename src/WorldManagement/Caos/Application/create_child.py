from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Shared.Domain import eclai_core

class CreateChildWorldUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, parent_id: str, name: str, description: str) -> str:
        print(f" 🐣 Iniciando nacimiento de una nueva entidad en {parent_id}...")

        # 1. Calcular el ID del nuevo hijo
        # El repositorio hace el trabajo sucio de mirar la DB
        new_child_id = self.repository.get_next_child_id(parent_id)
        
        print(f"    Calculado ID: {new_child_id} (Hijo de {parent_id})")

        # 2. Crear la Entidad
        new_world = CaosWorld(
            id=WorldID(new_child_id), 
            name=name, 
            lore_description=description
        )
        
        # 3. Guardar
        self.repository.save(new_world)
        
        # Codificación para mostrar en log
        code = eclai_core.encode_eclai126(new_child_id)
        print(f" ✨ [ECLAI] Sub-Mundo creado: {name}")
        print(f"    └── J-ID: {new_child_id} | CODE: {code}")
        
        return new_child_id