"""
Módulo de vistas de mundos.

Este módulo ha sido dividido en submódulos temáticos para mejorar
la organización y mantenibilidad del código.

Organización:
- listing.py: Vistas de listado e índices (home)
- detail.py: Vistas de detalle/lectura (ver_mundo, ver_metadatos, mapa_arbol)
- edit.py: Vistas de edición (editar_mundo, update_avatar)
- actions.py: Acciones sobre mundos (toggle_entity_status, borrar_mundo, etc)
- versions.py: Gestión de versiones (comparar_version, restaurar_version)
- utils.py: Utilidades internas (log_event, get_current_user)
- legacy.py: Funciones deprecadas (init_hemisferios, escanear_planeta)

Todos los exports públicos se mantienen para compatibilidad hacia atrás.
"""

# Exports públicos para mantener compatibilidad con código existente
from .listing import home
from .detail import ver_mundo, ver_metadatos, mapa_arbol
from .edit import editar_mundo, update_avatar
from .actions import toggle_entity_status, borrar_mundo, toggle_visibilidad, toggle_lock
from .versions import comparar_version, restaurar_version
from .legacy import init_hemisferios, escanear_planeta
from .utils import log_event, get_current_user

__all__ = [
    # Listing
    'home',
    # Detail
    'ver_mundo',
    'ver_metadatos',
    'mapa_arbol',
    # Edit
    'editar_mundo',
    'update_avatar',
    # Actions
    'toggle_entity_status',
    'borrar_mundo',
    'toggle_visibilidad',
    'toggle_lock',
    # Versions
    'comparar_version',
    'restaurar_version',
    # Legacy
    'init_hemisferios',
    'escanear_planeta',
    # Utils (internos, pero exportados por si acaso)
    'log_event',
    'get_current_user',
]
