from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from src.Shared.Domain.value_objects import WorldID

class VersionStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    LIVE = "LIVE"
    OFFLINE = "OFFLINE"
    ARCHIVED = "ARCHIVED"

@dataclass
class CaosWorld:
    id: WorldID
    name: str
    lore_description: str
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    # [NUEVO] Campo Metadata para JSONB (Planetas, Criaturas, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_public: bool = False
    is_locked: bool = False

    def publish(self):
        self.status = VersionStatus.LIVE
        
    def rename(self, new_name: str):
        if len(new_name) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        self.name = new_name
