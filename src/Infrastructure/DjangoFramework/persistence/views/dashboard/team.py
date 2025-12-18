from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from src.Infrastructure.DjangoFramework.persistence.models import UserProfile, CaosWorldORM, CaosNarrativeORM
from src.Infrastructure.DjangoFramework.persistence.forms import SubadminCreationForm
from .utils import is_superuser, is_admin_or_staff

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "staff/user_management.html"
    context_object_name = 'users'

    def test_func(self):
        # Allow Superuser AND Admins (to see their team)
        return self.request.user.is_superuser or self.request.user.is_staff or \
               (hasattr(self.request.user, 'profile') and self.request.user.profile.rank == 'ADMIN')

    def get_queryset(self):
        return User.objects.all().select_related('profile').order_by('username')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = SubadminCreationForm()
        return ctx
    
    def post(self, request, *args, **kwargs):
        form = SubadminCreationForm(request.POST)
        if form.is_valid():
            u = form.save()
            messages.success(request, f"Usuario {u.username} creado.")
        else:
            messages.error(request, "Error al crear usuario.")
        return redirect('user_management')
    
@login_required
@user_passes_test(is_superuser)
def toggle_admin_role(request, user_id):
    try:
        target_u = User.objects.get(id=user_id)
        if target_u.username in ['Xico', 'Alone']:
            messages.error(request, f"⛔ ACCIÓN DENEGADA: El usuario '{target_u.username}' es intocable.")
            return redirect('user_management')
            
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        
        if admins_group in target_u.groups.all():
            target_u.groups.remove(admins_group)
            if hasattr(target_u, 'profile'):
                target_u.profile.rank = 'USER' # Sync rank
                target_u.profile.save()
            messages.warning(request, f"⬇️ {target_u.username} ahora es Usuario estándar.")
        else:
            target_u.groups.add(admins_group)
            if hasattr(target_u, 'profile'):
                target_u.profile.rank = 'ADMIN' # Sync rank
                target_u.profile.save()
            messages.success(request, f"⬆️ {target_u.username} es ahora ADMIN.")
            
    except Exception as e:
        messages.error(request, str(e))
    return redirect('user_management')

class MyTeamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'staff/my_team.html'

    def test_func(self):
        # Allow Superuser AND Admins only
        return self.request.user.is_superuser or self.request.user.is_staff or \
               (hasattr(self.request.user, 'profile') and self.request.user.profile.rank == 'ADMIN')

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
        
        should_list = query or role_filter or mode == 'directory'
        
        if should_list:
            qs = User.objects.filter(is_active=True).select_related('profile').exclude(id=user.id)
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
                boss = r.profile.bosses.first()
                boss_name = boss.user.username if boss else None
                
                final_results.append({
                    'user': r,
                    'is_in_team': r.id in my_collabs,
                    'team_count': team_count,
                    'boss_name': boss_name
                })
            
            context['search_results'] = final_results
            context['search_query'] = query
            context['current_role'] = role_filter
            context['is_directory_mode'] = True
            
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        target_id = request.POST.get('target_id')
        
        try:
            target_user = User.objects.get(id=target_id)
            target_profile = target_user.profile
            my_profile = request.user.profile
            
            if action == 'add':
                my_profile.collaborators.add(target_profile)
                messages.success(request, f"✅ {target_user.username} añadido a tu equipo.")
                
            elif action == 'remove':
                my_profile.collaborators.remove(target_profile)
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
                    target_profile.rank = 'USER'
                    messages.warning(request, f"📉 {target_user.username} degradado a USUARIO.")
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
            is_my_collab = target_user.profile in self.request.user.profile.collaborators.all()
            if not self.request.user.is_superuser and not is_my_collab:
                 context['permission_denied'] = True
        else:
            target_user = self.request.user

        context['target_user'] = target_user
        # Assuming simple filter
        context['worlds'] = CaosWorldORM.objects.filter(author=target_user)
        # Using filter logic for narratives
        context['narratives'] = CaosNarrativeORM.objects.filter(created_by=target_user).order_by('-created_at')[:10] # Approximation
        return context
