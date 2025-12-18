from dataclasses import dataclass, field
from typing import List, Dict
from src.Shared.Domain.value_objects import WorldID

@dataclass
class Creature:
    """
    Entidad de Dominio: Criatura / Fauna.
    No depende de Django ni de la IA. Solo datos puros.
    """
    # Identificadores
    id: WorldID
    parent_id: WorldID # Puntero al mundo padre (Ej: 0101)

    # Biología
    name: str = "Unknown"
    taxonomy: str = "Anomaly"
    description: str = ""

    # Stats (RPG / Lógica)
    danger_level: int = 1
    behavior: str = "Neutral"

    # Visuales (Stable Diffusion Metadata)
    visual_dna: List[str] = field(default_factory=list)
    sd_prompt: str = ""

    def to_metadata_dict(self) -> Dict:
        """Serializa la parte flexible para guardar en el JSONB del ORM"""
        return {
            "biology": {
                "taxonomy": self.taxonomy,
                "description": self.description
            },
            "stats": {
                "danger_level": self.danger_level,
                "behavior": self.behavior
            },
            "visuals": {
                "dna": self.visual_dna,
                "prompt": self.sd_prompt
            }
        }

    @classmethod
    def from_ai_data(cls, data: Dict, parent_id: str):
        """Factory method para crear la entidad desde el JSON sucio de la IA"""
        return cls(
            eclai_id="", # Se asignará en el repositorio al calcular el ID
            parent_eclai_id=parent_id,
            name=data.get('name', 'Unnamed Entity'),
            taxonomy=data.get('taxonomy', 'Unknown'),
            description=data.get('description', 'No data available.'),
            danger_level=data.get('danger_level', 1),
            behavior=data.get('behavior', 'Passive'),
            visual_dna=data.get('visual_dna', []),
            sd_prompt=data.get('sd_prompt', '')
        )
