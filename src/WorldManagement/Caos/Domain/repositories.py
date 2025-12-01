from abc import ABC, abstractmethod
from typing import Optional
from .entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

class CaosRepository(ABC):
    @abstractmethod
    def save(self, world: CaosWorld):
        pass

    @abstractmethod
    def find_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        pass
        
    # Nuevo método necesario
    def get_next_child_id(self, parent_id_str: str) -> str:
        pass

    @abstractmethod
    def get_next_narrative_id(self, prefix: str) -> str:
        pass