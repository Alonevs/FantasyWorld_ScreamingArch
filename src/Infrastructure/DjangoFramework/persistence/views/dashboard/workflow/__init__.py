"""
Módulo de workflow del dashboard.

Este módulo ha sido dividido en submódulos temáticos para mejorar
la organización y mantenibilidad del código.

Organización:
- dashboard.py: Vista principal del dashboard
- world_actions.py: Acciones sobre propuestas de mundos
- narrative_actions.py: Acciones sobre propuestas de narrativas
- period_actions.py: Acciones sobre períodos temporales
- bulk_operations.py: Operaciones masivas
- contributions.py: Gestión de contribuciones de texto
- utils.py: Utilidades compartidas

Todos los exports públicos se mantienen para compatibilidad hacia atrás.
"""

# Dashboard
from .dashboard import dashboard
from .utils import centro_control

# World Actions
from .world_actions import (
    aprobar_propuesta, rechazar_propuesta, publicar_version,
    archivar_propuesta, restaurar_version, borrar_propuesta
)

# Narrative Actions
from .narrative_actions import (
    aprobar_narrativa, rechazar_narrativa, publicar_narrativa,
    archivar_narrativa, restaurar_narrativa, borrar_narrativa_version
)

# Period Actions
from .period_actions import restaurar_periodo

# Bulk Operations
from .bulk_operations import (
    borrar_propuestas_masivo, aprobar_propuestas_masivo,
    archivar_propuestas_masivo, publicar_propuestas_masivo
)

# Contributions
from .contributions import (
    ProposalDetailView, aprobar_contribucion, rechazar_contribucion
)

__all__ = [
    # Dashboard
    'dashboard', 'centro_control',
    # World Actions
    'aprobar_propuesta', 'rechazar_propuesta', 'publicar_version',
    'archivar_propuesta', 'restaurar_version', 'borrar_propuesta',
    # Narrative Actions
    'aprobar_narrativa', 'rechazar_narrativa', 'publicar_narrativa',
    'archivar_narrativa', 'restaurar_narrativa', 'borrar_narrativa_version',
    # Period Actions
    'restaurar_periodo',
    # Bulk Operations
    'borrar_propuestas_masivo', 'aprobar_propuestas_masivo',
    'archivar_propuestas_masivo', 'publicar_propuestas_masivo',
    # Contributions
    'ProposalDetailView', 'aprobar_contribucion', 'rechazar_contribucion',
]
