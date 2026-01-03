"""
Vista de ranking de usuarios.
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


class UserRankingView(LoginRequiredMixin, TemplateView):
    template_name = "staff/user_ranking.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_id = self.kwargs.get('pk')
        target_user = get_object_or_404(User, id=target_id)
        context['target_user'] = target_user
        
        # Discover Content
        content = SocialService.discover_user_content(target_user)
        
        ranked_items = []
        
        # Process Worlds (Tarjetas)
        for w in content['worlds']:
            key = f"WORLD_{w.public_id}"
            stats = SocialService.get_interactions_count(key)
            
            # Cover - Use centralized thumbnail helper
            cover_filename = w.metadata.get('cover_image') if w.metadata else None
            thumb = get_thumbnail_url(w.id, cover_filename, use_first_if_no_cover=True)
            
            ranked_items.append({
                'type': 'world',
                'title': w.name,
                'author': w.author.username if w.author else w.current_author_name,
                'date': w.created_at,
                'likes': stats['likes'],
                'comments': stats['comments'],
                'thumbnail': thumb,
                'link': f"/mundo/{w.public_id}",
                'days_active': (timezone.now() - w.created_at).days
            })
            
        # Process Narratives
        for n in content['narratives']:
            key = f"narr_{n.public_id}"
            stats = SocialService.get_interactions_count(key)
            w = n.world
            
            # Cover - Use centralized thumbnail helper
            cover_filename = w.metadata.get('cover_image') if w and w.metadata else None
            thumb = get_thumbnail_url(w.id, cover_filename, use_first_if_no_cover=True) if w else "/static/img/placeholder.png"
            
            ranked_items.append({
                'type': 'narrative',
                'title': n.titulo,
                'author': n.created_by.username,
                'date': n.created_at,
                'likes': stats['likes'],
                'comments': stats['comments'],
                'thumbnail': thumb,
                'link': f"/narrativa/{n.public_id}/" if n.public_id else "#",
                'days_active': (timezone.now() - n.created_at).days
            })


        # Process Images
        processed_images = set()
        for img in content['images']:
            fname = img['filename']
            if fname in processed_images: continue
            processed_images.add(fname)
            
            key = f"IMG_{fname}"
            stats = SocialService.get_interactions_count(key)
            
            w = img.get('world')
            
            # Robust Image Path Resolution: All Project Images are in Static Gallery
            if fname.startswith(('http', '/static/')):
                path = fname
            elif fname.startswith('/media/'):
                # Legacy / Exception check
                path = fname
            else:
                # Default: Everything is in persistence/static/persistence/img/{JID}
                # even "Covers" and "Uploads".
                jid = w.id if w else "00" # Fallback if world is missing (shouldnt happen for images)
                path = f"/static/persistence/img/{jid}/{fname}"
            
            ranked_items.append({
                'type': 'image',
                'title': img.get('title', fname),
                'author': target_user.username,
                'date': w.created_at if w else timezone.now(),
                'likes': stats['likes'],
                'comments': stats['comments'],
                'thumbnail': path,
                'link': f"/mundo/{w.public_id}?open_image={fname}" if w else "#",
                'days_active': (timezone.now() - w.created_at).days if w else 0
            })

        # Separate Lists & Sort
        # Filter logic in template or separate here? Let's separate here for easier sorting
        worlds_rank = sorted([x for x in ranked_items if x['type'] == 'world'], key=lambda x: x['likes'], reverse=True)
        narratives_rank = sorted([x for x in ranked_items if x['type'] == 'narrative'], key=lambda x: x['likes'], reverse=True)
        images_rank = sorted([x for x in ranked_items if x['type'] == 'image'], key=lambda x: x['likes'], reverse=True)
        
        context['worlds_rank'] = worlds_rank
        context['narratives_rank'] = narratives_rank
        context['images_rank'] = images_rank
        
        return context
