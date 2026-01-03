"""
team.py - Compatibilidad hacia atrás

Este archivo ha sido refactorizado y dividido en el paquete 'team/'.
Este módulo mantiene la compatibilidad importando todas las clases
del nuevo paquete.

Para ver la implementación real, consulta:
- views/dashboard/team/management.py
- views/dashboard/team/permissions.py
- views/dashboard/team/collaboration.py
- views/dashboard/team/detail.py
- views/dashboard/team/ranking.py

Refactorización realizada: 2026-01-03
"""

# Importar todo del nuevo paquete para mantener compatibilidad
from .team import *

# Esto permite que el código existente siga funcionando:
# from .views.dashboard import team
# team.UserManagementView.as_view()
# team.toggle_admin_role(request, user_id)
# etc.
