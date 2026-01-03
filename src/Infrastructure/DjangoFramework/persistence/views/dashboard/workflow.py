"""
workflow.py - Compatibilidad hacia atrás

Este archivo ha sido refactorizado y dividido en el paquete 'workflow/'.
Este módulo mantiene la compatibilidad importando todas las funciones
del nuevo paquete.

Para ver la implementación real, consulta:
- views/dashboard/workflow/dashboard.py
- views/dashboard/workflow/world_actions.py
- views/dashboard/workflow/narrative_actions.py
- views/dashboard/workflow/period_actions.py
- views/dashboard/workflow/bulk_operations.py
- views/dashboard/workflow/contributions.py
- views/dashboard/workflow/utils.py

Refactorización realizada: 2026-01-03
"""

# Importar todo del nuevo paquete para mantener compatibilidad
from .workflow import *

# Esto permite que el código existente siga funcionando:
# from .views.dashboard import workflow
# workflow.dashboard(request)
# workflow.aprobar_propuesta(request, id)
# etc.
