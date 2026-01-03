"""
Módulo de vistas de equipo y usuarios.

Este módulo ha sido dividido en submódulos temáticos para mejorar
la organización y mantenibilidad del código.

Organización:
- management.py: Gestión de usuarios (UserManagementView)
- permissions.py: Gestión de permisos/roles (toggle_admin_role)
- collaboration.py: Equipos y colaboradores (MyTeamView, CollaboratorWorkView)
- detail.py: Detalle de usuario (UserDetailView)
- ranking.py: Ranking de usuarios (UserRankingView)

Todos los exports públicos se mantienen para compatibilidad hacia atrás.
"""

# Exports públicos para mantener compatibilidad con código existente
from .management import UserManagementView
from .permissions import toggle_admin_role
from .collaboration import MyTeamView, CollaboratorWorkView
from .detail import UserDetailView
from .ranking import UserRankingView

__all__ = [
    # Management
    'UserManagementView',
    # Permissions
    'toggle_admin_role',
    # Collaboration
    'MyTeamView',
    'CollaboratorWorkView',
    # Detail
    'UserDetailView',
    # Ranking
    'UserRankingView',
]
