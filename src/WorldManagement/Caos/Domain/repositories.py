from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

class CaosRepository(ABC):
    @abstractmethod
    def save(self, world: CaosWorld):
        pass

    @abstractmethod
    def find_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        pass
        
    def get_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        """Alias for find_by_id"""
        return self.find_by_id(world_id)

    @abstractmethod
    def get_by_public_id(self, public_id: str) -> Optional[CaosWorld]:
        pass

    @abstractmethod
    def find_descendants(self, root_id: WorldID) -> List[CaosWorld]:
        pass

    @abstractmethod
    def get_ancestors_by_id(self, entity_id: str) -> List[CaosWorld]:
        """Returns ancestors ordered from furthest (root) to closest (parent)."""
        pass

    # Helper methods for ID generation
    @abstractmethod
    def get_next_child_id(self, parent_id_str: str) -> str:
        pass

    @abstractmethod
    def get_next_narrative_id(self, prefix: str) -> str:
        pass