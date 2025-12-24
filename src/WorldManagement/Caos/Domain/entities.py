from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from src.Shared.Domain.value_objects import WorldID

class VersionStatus(Enum):
    """
    Representa los posibles estados de una versión o entidad en su ciclo de vida.
    """
    DRAFT = "DRAFT"             # Borrador inicial, no visible para el público.
    PENDING_APPROVAL = "PENDING_APPROVAL" # Pendiente de revisión por un Administrador.
    APPROVED = "APPROVED"      # Validado pero aún no publicado en 'Live'.
    LIVE = "LIVE"              # Datos actuales visibles y oficiales.
    OFFLINE = "OFFLINE"        # Desactivado temporalmente.
    ARCHIVED = "ARCHIVED"      # Versión histórica guardada tras la publicación de una nueva.

@dataclass
class CaosWorld:
    """
    Entidad de Dominio principal del sistema Caos.
    Representa cualquier unidad jerárquica (Universo, Sistema, Planeta, Criatura, etc.).
    
    Esta clase es agnóstica a la persistencia (Django) y se centra en la lógica 
    de negocio pura.
    """
    id: WorldID                  # Identificador Jerárquico (J-ID / WorldID)
    name: str                    # Nombre de la entidad (v20+)
    lore_description: str        # Relato literario o descripción narrativa
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    
    # Metadatos estructurados (JSON): Almacena fichas técnicas generadas por IA (Astrofísica, Biología)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    is_public: bool = False      # Control de visibilidad para usuarios no registrados
    is_locked: bool = False      # Indica si la entidad está protegida contra modificaciones

    def publish(self):
        """Marca esta instancia como la versión oficial actual."""
        self.status = VersionStatus.LIVE
        
    def rename(self, new_name: str):
        """Cambia el nombre de la entidad validando reglas mínimas de dominio."""
        if len(new_name) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres para mantener la calidad narrativa.")
        self.name = new_name
