"""
world_views.py - Compatibilidad hacia atrás

Este archivo ha sido refactorizado y dividido en el paquete 'world/'.
Este módulo mantiene la compatibilidad importando todas las funciones
del nuevo paquete.

Para ver la implementación real, consulta:
- views/world/listing.py
- views/world/detail.py
- views/world/edit.py
- views/world/actions.py
- views/world/versions.py
- views/world/utils.py

Refactorización realizada: 2026-01-03
"""

# Importar todo del nuevo paquete para mantener compatibilidad
from .world import *

# Esto permite que el código existente siga funcionando:
# from .views import world_views
# world_views.home(request)
# world_views.ver_mundo(request, id)
# etc.
