from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import CaosWorld
from src.Shared.Domain.value_objects import WorldID

class CaosRepository(ABC):
    """
    Interface (Puerto) del Repositorio de Caos.
    Define el contrato que cualquier motor de persistencia (ej: Django, Memoria)
    debe cumplir para gestionar las entidades del dominio.
    """
    
    @abstractmethod
    def save(self, world: CaosWorld):
        """Persiste o actualiza una entidad en el almacenamiento."""
        pass

    @abstractmethod
    def find_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        """Busca una entidad por su Identificador Jerárquico (J-ID)."""
        pass
        
    def get_by_id(self, world_id: WorldID) -> Optional[CaosWorld]:
        """Alias para find_by_id."""
        return self.find_by_id(world_id)

    @abstractmethod
    def get_by_public_id(self, public_id: str) -> Optional[CaosWorld]:
        """Busca una entidad por su Identificador Público (NanoID)."""
        pass

    @abstractmethod
    def find_descendants(self, root_id: WorldID) -> List[CaosWorld]:
        """Recupera todos los hijos y nietos de una entidad raíz."""
        pass

    @abstractmethod
    def get_ancestors_by_id(self, entity_id: str) -> List[CaosWorld]:
        """
        Recupera la línea sucesoria de una entidad.
        Retorna los ancestros ordenados desde el más lejano (Raíz) al más cercano (Padre).
        """
        pass

    # --- Herramientas de Gestión de Identificadores ---
    
    @abstractmethod
    def get_next_child_id(self, parent_id_str: str) -> str:
        """Calcula el siguiente J-ID disponible para un nuevo hijo."""
        pass

    @abstractmethod
    def get_next_narrative_id(self, prefix: str) -> str:
        """Calcula el siguiente NID disponible para una narrativa (Lore/Capítulo)."""
        pass