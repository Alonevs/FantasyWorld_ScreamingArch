"""
Gestión de permisos y roles.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.utils import timezone

from src.Infrastructure.DjangoFramework.persistence.utils import (
    generate_breadcrumbs, get_world_images, get_thumbnail_url
)
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosNarrativeORM, CaosEpochORM, CaosComment, CaosLike
)
from src.Shared.Services.SocialService import SocialService
from src.Infrastructure.DjangoFramework.persistence.forms import SubadminCreationForm
from ..utils import is_superuser, is_admin_or_staff


@login_required
def toggle_admin_role(request, user_id):
    # 0. BASE PERMISSION: Only Superuser or Admin can reach this action
    is_privileged = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank == 'ADMIN')
    if not is_privileged:
        messages.error(request, "⛔ Acceso Denegado.")
        return redirect('home')

    try:
        target_u = User.objects.get(id=user_id)
        
        # 1. PROTECT SYSTEM / SUPERUSERS (Untouchable)
        if target_u.is_superuser or target_u.username in ['Xico', 'Alone']:
            messages.error(request, f"⛔ EL usuario '{target_u.username}' es inmune.")
            return redirect('user_management')

        # 2. ADMIN IMMUNITY (Admins cannot demote themselves or other Admins)
            if is_target_admin:
                messages.error(request, "⛔ No puedes modificar el rango de otros Administradores.")
                return redirect('user_management')
            
            # SCOPE CHECK: target_u MUST be in my team (collaborators)
            if hasattr(request.user, 'profile'):
                 # Check if target is in my list of collaborators
                 if not request.user.profile.collaborators.filter(id=target_u.profile.id).exists():
                      messages.error(request, f"⛔ {target_u.username} NO es parte de tu equipo directo.")
                      return redirect('user_management')
            
        # 3. DIRECTIONAL LOGIC
        action = request.GET.get('action') # 'up' or 'down'
        current_rank = target_u.profile.rank if hasattr(target_u, 'profile') else 'EXPLORER'
        admins_group, _ = Group.objects.get_or_create(name='Admins')

        if action == 'up':
            if current_rank == 'EXPLORER':
                target_u.profile.rank = 'SUBADMIN'
                messages.success(request, f"🛡️ {target_u.username} ascendido a SUBADMIN.")
            elif current_rank == 'SUBADMIN':
                # SECURITY: Only Superuser can promote to ADMIN
                if not request.user.is_superuser:
                    messages.error(request, "⛔ Solo el Superadmin puede nombrar Administradores.")
                    return redirect('user_management')

                target_u.profile.rank = 'ADMIN'
                target_u.groups.add(admins_group)
                messages.success(request, f"💎 {target_u.username} ascendido a ADMIN.")
            target_u.profile.save()
            
        elif action == 'down':
            if current_rank == 'ADMIN':
                target_u.profile.rank = 'SUBADMIN'
                target_u.groups.remove(admins_group)
                messages.warning(request, f"📉 {target_u.username} degradado a SUBADMIN.")
            elif current_rank == 'SUBADMIN':
                target_u.profile.rank = 'EXPLORER'
                messages.warning(request, f"📉 {target_u.username} degradado a EXPLORADOR.")
            target_u.profile.save()
            
    except Exception as e:
        messages.error(request, str(e))
    return redirect('user_management')
