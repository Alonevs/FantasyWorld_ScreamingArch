from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count, Q
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosNarrativeORM, CaosComment, CaosLike
)


class ContentAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Admin dashboard showing all content with interaction statistics.
    Only accessible to admins and superadmins.
    """
    template_name = "staff/content_analytics.html"
    
    def test_func(self):
        """Only allow superadmins and admins"""
        return self.request.user.is_superuser or (
            hasattr(self.request.user, 'profile') and 
            self.request.user.profile.rank in ['ADMIN', 'SUPERADMIN']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Collect all content with statistics
        content_stats = []
        
        # 1. Images from all worlds
        all_worlds = CaosWorldORM.objects.filter(is_active=True).select_related('author')
        
        for world in all_worlds:
            if world.metadata and 'gallery_log' in world.metadata:
                gallery_log = world.metadata['gallery_log']
                for filename, meta in gallery_log.items():
                    entity_key = f"IMG_{filename}"
                    
                    # Count likes and comments
                    likes = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
                    comments = CaosComment.objects.filter(entity_key__iexact=entity_key).count()
                    
                    content_stats.append({
                        'type': 'image',
                        'title': meta.get('title', filename),
                        'filename': filename,
                        'author': meta.get('uploader', 'Unknown'),
                        'world': world.name,
                        'world_id': world.public_id,
                        'likes': likes,
                        'comments': comments,
                        'engagement': likes + comments,
                        'date': meta.get('date', '-'),
                        'thumbnail': f"/static/persistence/img/{world.public_id}/{filename}",
                        'url': f"/mundo/{world.public_id}",
                        'entity_key': entity_key
                    })
        
        # 2. Narratives
        all_narratives = CaosNarrativeORM.objects.filter(is_active=True).select_related('created_by', 'world')
        
        for narrative in all_narratives:
            # Skip if no author
            if not narrative.created_by:
                continue
                
            entity_key = f"NARR_{narrative.public_id}"
            
            likes = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
            comments = CaosComment.objects.filter(entity_key__iexact=entity_key).count()
            
            content_stats.append({
                'type': 'narrative',
                'title': narrative.titulo,
                'filename': None,
                'author': narrative.created_by.username,
                'world': narrative.world.name if narrative.world else '-',
                'world_id': narrative.world.public_id if narrative.world else None,
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': narrative.created_at.strftime("%d/%m/%Y"),
                'thumbnail': None,
                'url': f"/narrativa/{narrative.public_id}",
                'entity_key': entity_key
            })
        
        # 3. Worlds
        for world in all_worlds:
            # Skip if no author
            if not world.author:
                continue
                
            entity_key = f"WORLD_{world.public_id}"
            
            likes = CaosLike.objects.filter(entity_key__iexact=entity_key).count()
            comments = CaosComment.objects.filter(entity_key__iexact=entity_key).count()
            
            content_stats.append({
                'type': 'world',
                'title': world.name,
                'filename': None,
                'author': world.author.username,
                'world': world.name,
                'world_id': world.public_id,
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': world.created_at.strftime("%d/%m/%Y"),
                'thumbnail': None,
                'url': f"/mundo/{world.public_id}",
                'entity_key': entity_key
            })
        
        # Sort by engagement (highest first)
        content_stats.sort(key=lambda x: x['engagement'], reverse=True)
        
        # Add to context
        context['content_stats'] = content_stats
        context['total_content'] = len(content_stats)
        context['total_likes'] = sum(c['likes'] for c in content_stats)
        context['total_comments'] = sum(c['comments'] for c in content_stats)
        context['total_engagement'] = sum(c['engagement'] for c in content_stats)
        
        return context
