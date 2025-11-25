from typing import Dict, Optional
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

# Simulación de una Base de Datos (Para pruebas rápidas sin SQL)
class InMemoryCaosRepository(CaosRepository):
    def __init__(self):
        self.db: Dict[str, CaosWorld] = {}

    def save(self, world: CaosWorld):
        self.db[str(world.id)] = world
        print(f" [DB] Guardado en memoria: {world.id}")

    def find_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        return self.db.get(str(world_id))