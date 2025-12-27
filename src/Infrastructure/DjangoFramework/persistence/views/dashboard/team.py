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
        return User.objects.exclude(username='Xico').select_related('profile').order_by('username')

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
        current_rank = target_u.profile.rank if hasattr(target_u, 'profile') else 'USER'
        admins_group, _ = Group.objects.get_or_create(name='Admins')

        if action == 'up':
            if current_rank == 'USER':
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
                target_u.profile.rank = 'USER'
                messages.warning(request, f"📉 {target_u.username} degradado a EXPLORADOR.")
            target_u.profile.save()
            
    except Exception as e:
        messages.error(request, str(e))
    return redirect('user_management')

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
                
                # Check if orphan (no more bosses) -> Auto-Demote to USER
                if target_profile.bosses.count() == 0:
                    target_profile.rank = 'USER'
                    target_profile.save()
                    messages.warning(request, f"📉 {target_user.username} ha vuelto a ser Usuario (sin jefe).")
                
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

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'staff/user_detail.html'
    
    def test_func(self):
        # Allow Superuser, Admin, or the user themselves
        # Actually any authenticated user might be able to see a public profile? 
        # For now, restrict to Staff logic (Staff, Admin, Superuser)
        user = self.request.user
        if user.is_superuser or user.is_staff: return True
        if hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']: return True
        # Allow viewing own profile
        if str(user.id) == str(self.kwargs.get('pk')): return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_id = self.kwargs.get('pk')
        target_user = get_object_or_404(User, id=target_id)
        
        if not hasattr(target_user, 'profile'):
            UserProfile.objects.create(user=target_user)
            target_user.refresh_from_db()
            
        context['target_user'] = target_user
        # Relationships
        context['bosses'] = target_user.profile.bosses.all()
        context['minions'] = target_user.profile.collaborators.all()
        
        # Stats (Optional simple stats)
        if target_user.is_superuser:
            # Superuser gets credit for Orphans (System Worlds), but filtered for quality (LIVE + Active)
            # "Ghosts" (Deleted/Drafts) are excluded from the public score.
            context['worlds_count'] = CaosWorldORM.objects.filter(
                (Q(author=target_user) | Q(author__isnull=True)) & 
                Q(is_active=True, status='LIVE')
            ).count()
            
            context['narratives_count'] = CaosNarrativeORM.objects.filter(
                (Q(created_by=target_user) | Q(created_by__isnull=True)) &
                Q(is_active=True)
            ).count()
        else:
            context['worlds_count'] = CaosWorldORM.objects.filter(author=target_user, is_active=True).count()
            context['narratives_count'] = CaosNarrativeORM.objects.filter(created_by=target_user, is_active=True).count()
        
        return context
