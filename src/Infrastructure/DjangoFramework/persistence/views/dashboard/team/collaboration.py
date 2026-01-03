"""
Gestión de equipos y colaboradores.
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


class MyTeamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'staff/my_team.html'

    def test_func(self):
        # Allow Superuser AND Admins AND SubAdmins (to see their team/bosses)
        return self.request.user.is_superuser or self.request.user.is_staff or \
               (hasattr(self.request.user, 'profile') and self.request.user.profile.rank in ['ADMIN', 'SUBADMIN'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            user.refresh_from_db()
            
        # 1. MY TEAM
        context['team_list'] = user.profile.collaborators.select_related('user__profile').prefetch_related('collaborators').all()
             
        # 2. DIRECTORY / SEARCH
        query = self.request.GET.get('q')
        role_filter = self.request.GET.get('role')
        mode = self.request.GET.get('mode')
        
        # SECURITY: Only Admins/Superusers can use 'Directory' mode to add new people.
        if mode == 'directory':
             is_privileged = self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.rank == 'ADMIN')
             if not is_privileged:
                 # If SubAdmin tries directory mode, force disable it.
                 mode = ''
        
        should_list = query or role_filter or mode == 'directory'
        
        if should_list:
            # Show all users except specific system accounts + self
            qs = User.objects.filter(is_active=True).select_related('profile').exclude(id=user.id).exclude(username__in=['Xico', 'Alone', 'System', 'Admin'])
            if query:
                qs = qs.filter(Q(username__icontains=query) | Q(email__icontains=query))
            if role_filter:
                qs = qs.filter(profile__rank=role_filter)
                
            results = qs[:50]
            final_results = []
            my_collabs = set(user.profile.collaborators.values_list('user__id', flat=True))
            
            for r in results:
                if not hasattr(r, 'profile'):
                    UserProfile.objects.create(user=r); r.refresh_from_db()
                
                team_count = r.profile.collaborators.count()
                all_bosses = r.profile.bosses.all()
                boss_names = [b.user.username for b in all_bosses]
                
                final_results.append({
                    'user': r,
                    'is_in_team': r.id in my_collabs,
                    'team_count': team_count,
                    'boss_names': boss_names
                })
            
            context['search_results'] = final_results
            context['search_query'] = query
            context['current_role'] = role_filter
            context['is_directory_mode'] = True
            
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        target_id = request.POST.get('target_id')
        print(f"DEBUG: MyTeamView POST - Action: {action}, Target ID: {target_id}, User: {request.user.username}")
        
        try:
            target_user = User.objects.get(id=target_id)
            target_profile = target_user.profile
            my_profile = request.user.profile
            
            if action == 'add':
                my_profile.collaborators.add(target_profile)
                messages.success(request, f"✅ {target_user.username} añadido a tu equipo.")
                
            elif action == 'remove':
                my_profile.collaborators.remove(target_profile)
                
                # Check if orphan (no more bosses) -> Auto-Demote to EXPLORER
                if target_profile.bosses.count() == 0:
                    target_profile.rank = 'EXPLORER'
                    target_profile.save()
                    messages.warning(request, f"📉 {target_user.username} ha vuelto a ser Explorador (sin jefe).")
                
                messages.warning(request, f"❌ {target_user.username} eliminado de tu equipo.")
                
            elif action == 'promote_admin' and request.user.is_superuser:
                target_profile.rank = 'ADMIN'
                target_profile.save()
                admins_group, _ = Group.objects.get_or_create(name='Admins')
                target_user.groups.add(admins_group)
                messages.success(request, f"💎 {target_user.username} ascendido a ADMIN.")
            
            elif action == 'promote_subadmin':
                if request.user.profile.rank == 'ADMIN':
                    target_profile.rank = 'SUBADMIN'
                    target_profile.save()
                    messages.success(request, f"🛡️ {target_user.username} ascendido a SUBADMIN.")
                else: messages.error(request, "⛔ Solo los Admins pueden nombrar Subadmins.")
            
            elif action == 'demote':
                current_rank = target_profile.rank
                if current_rank == 'ADMIN' and request.user.is_superuser:
                    target_profile.rank = 'SUBADMIN'
                    g = Group.objects.filter(name='Admins').first()
                    if g: target_user.groups.remove(g)
                    messages.warning(request, f"📉 {target_user.username} degradado a SUBADMIN.")
                elif current_rank == 'SUBADMIN':
                    target_profile.rank = 'EXPLORER'
                    messages.warning(request, f"📉 {target_user.username} degradado a EXPLORADOR.")
                target_profile.save()

        except Exception as e: messages.error(request, f"Error: {e}") 
        return redirect('my_team')

class CollaboratorWorkView(LoginRequiredMixin, TemplateView):
    template_name = 'staff/collaborator_work.html'
    
    def get_context_data(self, user_id=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if user_id:
            target_user = get_object_or_404(User, id=user_id)
            # Permission Check
            # 1. Is my Minion? (I am Admin, they are Collab)
            is_my_collab = target_user.profile in self.request.user.profile.collaborators.all()
            # 2. Is my Boss? (I am Minion, they are Boss)
            is_my_boss = target_user.profile in self.request.user.profile.bosses.all()
            
            if not self.request.user.is_superuser and not is_my_collab and not is_my_boss:
                 context['permission_denied'] = True
        else:
            target_user = self.request.user

        context['target_user'] = target_user
        # Assuming simple filter
        context['worlds'] = CaosWorldORM.objects.filter(author=target_user)
        # Using filter logic for narratives
        context['narratives'] = CaosNarrativeORM.objects.filter(created_by=target_user).order_by('-created_at')[:10] # Approximation
        return context
