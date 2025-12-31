from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from src.Infrastructure.DjangoFramework.persistence.utils import (
    generate_breadcrumbs, get_world_images
)
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosNarrativeORM, CaosEpochORM, CaosComment, CaosLike
)
from src.Shared.Services.SocialService import SocialService
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
        
        # Social Stats - Unified using SocialService
        content = SocialService.discover_user_content(target_user)
        
        comments_received = 0
        favorite_reviews = 0
        image_stats = []
        received_comments = []

        # Helper to get world cover once per world
        world_covers = {}
        def get_cached_cover(world_obj):
            if not world_obj: return None
            if world_obj.id in world_covers: return world_covers[world_obj.id]
            
            w_imgs = get_world_images(world_obj.id, world_instance=world_obj)
            cover = next((item for item in w_imgs if item.get('is_cover')), None)
            url = cover['url'] if cover else (w_imgs[0]['url'] if w_imgs else None)
            
            cover_path = f"/static/persistence/img/{url}" if url else None
            world_covers[world_obj.id] = cover_path
            return cover_path
            
        default_thumb = "/static/persistence/img/gallery/default.png"

        # 1. Process Images
        for img in content['images']:
            filename = img['filename']
            world = img['world']
            entity_key = f"IMG_{filename}"
            
            stats = SocialService.get_interactions_count(entity_key)
            comments_received += stats['comments']
            favorite_reviews += stats['likes']
            
            cover_thumb = get_cached_cover(world)

            if stats['engagement'] > 0:
                image_stats.append({
                    'filename': filename,
                    'title': img.get('title', filename),
                    'world': world.name if world else "Histórico",
                    'likes': stats['likes'],
                    'comments': stats['comments'],
                    'date': img.get('meta', {}).get('date', '-'),
                    'url': f"/static/persistence/img/{world.public_id}/{filename}" if world else f"/static/persistence/img/gallery/{filename}",
                    'thumbnail': cover_thumb
                })
                
                # Fetch recent comments
                comments = SocialService.get_comments(entity_key).order_by('created_at') # ASC for chronological
                for comment in comments:
                    received_comments.append({
                        'id': comment.id,
                        'entity_key': entity_key,
                        'type': 'image',
                        'content_title': img.get('title', filename),
                        'content_url': f"/mundo/{world.public_id}" if world else f"/mundo/caos?open_image={filename}",
                        'thumbnail': cover_thumb,
                        'commenter': comment.user.username,
                        'commenter_avatar': comment.user.profile.avatar.url if hasattr(comment.user, 'profile') and comment.user.profile.avatar else None,
                        'comment_text': comment.content,
                        'comment_date': comment.created_at,
                        'is_author': comment.user == target_user,
                        'is_reply': comment.parent_comment is not None
                    })

        # 2. Process Narratives
        # ... (narrative processing remains similar, but we'll merge activity later)

        # 3. Process Activity (All comments where user is author OR recipient of a reply)
        # This covers cases where the user doesn't OWN the content (like Roberto)
        activity = SocialService.get_user_activity(target_user)
        for comment in activity['comments']:
            # Skip if already in received_comments (to avoid duplicates from owned content)
            if any(rc['id'] == comment.id for rc in received_comments):
                continue
                
            info = SocialService.resolve_content_by_key(comment.entity_key)
            if info:
                world = info.get('world')
                cover_thumb = get_cached_cover(world)
                
                # Fallback to the image itself if it's an image comment and cover is missing/broken
                if not cover_thumb and info['type'] == 'image':
                    filename = info.get('filename')
                    if world:
                        # Try world folder
                        cover_thumb = f"/static/persistence/img/{world.id}/{filename}"
                    else:
                        # Try gallery folder
                        cover_thumb = f"/static/persistence/img/gallery/{filename}"
                
                if not cover_thumb:
                    cover_thumb = default_thumb

                content_url = "#"
                if info['type'] == 'image':
                    content_url = f"/mundo/{world.public_id}?open_image={info['filename']}" if world else f"/mundo/caos?open_image={info['filename']}"
                elif info['type'] == 'narrative':
                    content_url = f"/mundo/{world.public_id}" # Narratives link to world currently
                elif info['type'] == 'world':
                    content_url = f"/mundo/{world.public_id}"
                elif info['type'] == 'proposal':
                    content_url = f"/mundo/{world.public_id}?proposal_id={info['id']}" if world else "#"

                received_comments.append({
                    'id': comment.id,
                    'entity_key': comment.entity_key,
                    'type': info['type'],
                    'content_title': info['title'],
                    'content_url': content_url,
                    'thumbnail': cover_thumb,
                    'commenter': comment.user.username,
                    'commenter_avatar': comment.user.profile.avatar.url if hasattr(comment.user, 'profile') and comment.user.profile.avatar else None,
                    'comment_text': comment.content,
                    'comment_date': comment.created_at,
                    'is_author': comment.user == target_user,
                    'is_reply': comment.parent_comment is not None
                })

        # 4. Process Worlds (Metadata/Description Comments & Likes)
        for world in content['worlds']:
            entity_key = f"WORLD_{world.public_id}"
            stats = SocialService.get_interactions_count(entity_key)
            favorite_reviews += stats['likes']
            comments_received += stats['comments']

            cover_thumb = get_cached_cover(world)
            
            # Fetch recent comments
            comments = SocialService.get_comments(entity_key).order_by('created_at')
            for comment in comments:
                received_comments.append({
                    'id': comment.id,
                    'entity_key': entity_key,
                    'type': 'world',
                    'content_title': f"{world.name} (Descripción)",
                    'content_url': f"/mundo/{world.public_id}",
                    'thumbnail': cover_thumb,
                    'commenter': comment.user.username,
                    'commenter_avatar': comment.user.profile.avatar.url if hasattr(comment.user, 'profile') and comment.user.profile.avatar else None,
                    'comment_text': comment.content,
                    'comment_date': comment.created_at,
                    'is_author': comment.user == target_user,
                    'is_reply': comment.parent_comment is not None
                })

        # 4. Process Proposals (Comments)
        for prop in content.get('proposals', []):
            try:
                # Proposals can have comments via Version ID
                entity_key = f"VER_{prop.id}"
                stats = SocialService.get_interactions_count(entity_key)
                comments_received += stats['comments']
                
                # Use current world cover
                cover_thumb = get_cached_cover(prop.entidad) if hasattr(prop, 'entidad') else None
                
                comments = SocialService.get_comments(entity_key).order_by('created_at')
                for comment in comments:
                    received_comments.append({
                        'id': comment.id,
                        'entity_key': entity_key,
                        'type': 'proposal',
                        'content_title': f"Propuesta v{prop.version_number} de {prop.entidad.name if hasattr(prop, 'entidad') else '?'}",
                        'content_url': f"/mundo/{prop.entidad.public_id}?proposal_id={prop.id}" if hasattr(prop, 'entidad') else "#",
                        'thumbnail': cover_thumb,
                        'commenter': comment.user.username,
                        'commenter_avatar': comment.user.profile.avatar.url if hasattr(comment.user, 'profile') and comment.user.profile.avatar else None,
                        'comment_text': comment.content,
                        'comment_date': comment.created_at,
                        'is_author': comment.user == target_user,
                        'is_reply': comment.parent_comment is not None
                    })
            except Exception as e:
                print(f"Error processing proposal comments in profile: {e}")

        # Sort and limit
        image_stats.sort(key=lambda x: x['likes'] + x['comments'], reverse=True)
        received_comments.sort(key=lambda x: x['comment_date'], reverse=True)
        
        context['comments_received'] = comments_received
        context['image_stats'] = image_stats[:10]
        context['received_comments'] = received_comments[:20]
        context['favorite_reviews'] = favorite_reviews
        
        return context
