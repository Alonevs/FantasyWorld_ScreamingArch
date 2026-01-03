"""
Módulo de gestión de assets del dashboard.

Organización:
- image_workflow.py: Workflow de aprobación de imágenes
- trash_management.py: Gestión de papelera y borrado definitivo
- batch_ops.py: Operaciones masivas sobre imágenes

Todos los exports públicos se mantienen para compatibilidad hacia atrás.
"""

# Image Workflow
from .image_workflow import (
    aprobar_imagen, rechazar_imagen, archivar_imagen,
    publicar_imagen, restaurar_imagen, borrar_imagen_definitivo,
    restaurar_imagen_papelera
)

# Trash Management
from .trash_management import (
    ver_papelera, restaurar_entidad_fisica,
    borrar_mundo_definitivo, borrar_narrativa_definitivo,
    manage_trash_bulk
)

# Batch Operations
from .batch_ops import batch_revisar_imagenes

__all__ = [
    # Image Workflow
    'aprobar_imagen', 'rechazar_imagen', 'archivar_imagen',
    'publicar_imagen', 'restaurar_imagen', 'borrar_imagen_definitivo',
    'restaurar_imagen_papelera',
    # Trash Management
    'ver_papelera', 'restaurar_entidad_fisica',
    'borrar_mundo_definitivo', 'borrar_narrativa_definitivo',
    'manage_trash_bulk',
    # Batch Operations
    'batch_revisar_imagenes',
]
