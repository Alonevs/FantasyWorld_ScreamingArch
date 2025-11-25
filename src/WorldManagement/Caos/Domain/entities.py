from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from src.Shared.Domain.value_objects import WorldID

# Definimos los estados posibles
class VersionStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    LIVE = "LIVE"
    ARCHIVED = "ARCHIVED"

# Esta es la clase que faltaba y que el Repositorio busca desesperadamente
@dataclass
class CaosWorld:
    id: WorldID
    name: str
    lore_description: str
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)

    # Lógica de dominio simple
    def publish(self):
        self.status = VersionStatus.LIVE
        
    def rename(self, new_name: str):
        if len(new_name) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        self.name = new_name