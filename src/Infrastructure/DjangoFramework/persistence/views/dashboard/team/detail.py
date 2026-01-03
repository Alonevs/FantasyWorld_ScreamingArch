"""
Vista detallada de perfil de usuario.
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

        # 5. Process Reviews (Comments with Ratings)
        from django.db.models import Avg
        
        # Helper to categorize entity_type if missing in DB
        def guess_type(key):
            if key.startswith("IMG_"): return 'IMAGE'
            if key.startswith("narr_") or key.startswith("NARR_"): return 'NARRATIVE'
            if key.startswith("WORLD_"): return 'WORLD'
            return 'OTHER'

        # Fetch all comments ON user's content that have a rating
        # We need the keys again
        all_user_keys = []
        for w in content['worlds']: all_user_keys.extend([str(w.id), f"WORLD_{w.public_id}", w.public_id])
        for n in content['narratives']: all_user_keys.extend([n.nid, n.public_id, f"narr_{n.public_id}"])
        for img in content['images']: all_user_keys.extend([f"IMG_{img['filename']}", img['filename']])
        
        raw_reviews = CaosComment.objects.filter(
            entity_key__in=all_user_keys,
            rating__isnull=False
        ).exclude(status='DELETED').order_by('-created_at')
        
        reviews_images = []
        reviews_narratives = []
        total_stars = 0
        review_count = raw_reviews.count()
        
        for r in raw_reviews:
            total_stars += r.rating
            etype = r.entity_type or guess_type(r.entity_key)
            
            # Resolve Context
            info = SocialService.resolve_content_by_key(r.entity_key)
            world = info.get('world') if info else None
            cover = get_cached_cover(world) if world else default_thumb
            
            rv_obj = {
                'id': r.id,
                'rating': r.rating,
                'rating_range': range(r.rating),
                'empty_range': range(5 - r.rating),
                'content': r.content,
                'author': r.user.username,
                'author_avatar': get_user_avatar(r.user),
                'date': r.created_at,
                'entity_name': info.get('title') if info else r.entity_key,
                'thumbnail': cover,
                'link': info.get('link') if info else '#' # Use SocialService link logic if available or construct it
            }
            
            # Refine Link manually if needed as SocialService default might return dict
            if info:
                 if info['type'] == 'image':
                     rv_obj['link'] = f"/mundo/{world.public_id}?open_image={info['filename']}" if world else "#"
                 elif info['type'] == 'narrative':
                     rv_obj['link'] = f"/mundo/{world.public_id}" # Narratives link to world
            
            if etype == 'IMAGE':
                reviews_images.append(rv_obj)
            else:
                reviews_narratives.append(rv_obj) # World reviews go here too for now
                
        avg_rating = round(total_stars / review_count, 1) if review_count > 0 else 0
        
        context['reviews_images'] = reviews_images
        context['reviews_narratives'] = reviews_narratives
        context['review_count'] = review_count
        context['avg_rating'] = avg_rating
        
        # Sort and limit
        image_stats.sort(key=lambda x: x['likes'] + x['comments'], reverse=True)
        received_comments.sort(key=lambda x: x['comment_date'], reverse=True)
        
        context['comments_received'] = comments_received
        context['image_stats'] = image_stats[:10]
        context['received_comments'] = received_comments[:20]
        context['favorite_reviews'] = favorite_reviews
        
        return context
