"""
Gestión de usuarios.
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


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "staff/user_management.html"
    context_object_name = 'users'

    def test_func(self):
        # Allow Superuser AND Admins (to see their team)
        return self.request.user.is_superuser or self.request.user.is_staff or \
               (hasattr(self.request.user, 'profile') and self.request.user.profile.rank == 'ADMIN')

    def get_queryset(self):
        return User.objects.exclude(username='Xico').select_related('profile').prefetch_related('profile__bosses__user').order_by('username')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = SubadminCreationForm()
        
        # Inject IDs of my collaborators for UI logic
        if hasattr(self.request.user, 'profile'):
             ctx['my_team_ids'] = set(self.request.user.profile.collaborators.values_list('user__id', flat=True))
        else:
             ctx['my_team_ids'] = set()
        
        # Enrich users with boss names for display
        for u in ctx['users']:
            if hasattr(u, 'profile'):
                u.boss_names = [boss.user.username for boss in u.profile.bosses.all()]
            else:
                u.boss_names = []
             
        return ctx
    
    def post(self, request, *args, **kwargs):
        form = SubadminCreationForm(request.POST)
        if form.is_valid():
            u = form.save()
            messages.success(request, f"Usuario {u.username} creado.")
        else:
            messages.error(request, "Error al crear usuario.")
        return redirect('user_management')
