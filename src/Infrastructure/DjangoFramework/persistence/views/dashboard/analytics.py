from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count, Q
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosNarrativeORM, CaosComment, CaosLike, TimelinePeriod, CaosVersionORM
)
from src.Shared.Services.SocialService import SocialService


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
        
        # Categories list
        narratives_list = []
        images_list = []
        metadata_list = []
        periods_list = []
        
        # 1. IMAGES (from all worlds)
        all_worlds = CaosWorldORM.objects.filter(is_active=True).select_related('author')
        for world in all_worlds:
            if world.metadata and 'gallery_log' in world.metadata:
                gallery_log = world.metadata['gallery_log']
                for filename, meta in gallery_log.items():
                    # Handle possible double escaping in DB or different formats
                    entity_key = f"IMG_{filename}"
                    stats = SocialService.get_interactions_count(entity_key)
                    likes = stats['likes']
                    comments = stats['comments']
                    
                    images_list.append({
                        'type': 'image',
                        'title': meta.get('title', filename),
                        'author': meta.get('uploader', 'Unknown'),
                        'world': world.name,
                        'likes': likes,
                        'comments': comments,
                        'engagement': likes + comments,
                        'date': meta.get('date', '-'),
                        'thumbnail': f"/static/persistence/img/{world.public_id}/{filename}",
                        'url': f"/mundo/{world.public_id}",
                    })
        
        # 2. NARRATIVES
        all_narratives = CaosNarrativeORM.objects.filter(is_active=True).select_related('created_by', 'world')
        for narrative in all_narratives:
            if not narrative.created_by: continue
            entity_key = f"NARR_{narrative.public_id}"
            stats = SocialService.get_interactions_count(entity_key)
            likes = stats['likes']
            comments = stats['comments']
            
            narratives_list.append({
                'type': 'narrative',
                'title': narrative.titulo,
                'author': narrative.created_by.username,
                'world': narrative.world.name if narrative.world else '-',
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': narrative.created_at.strftime("%d/%m/%Y"),
                'url': f"/narrativa/{narrative.public_id}",
            })
            
        # 3. METADATOS (Worlds + Metadata Proposals)
        # Add active worlds as base metadata entities
        for world in all_worlds:
            if not world.author: continue
            entity_key = f"WORLD_{world.public_id}"
            stats = SocialService.get_interactions_count(entity_key)
            likes = stats['likes']
            comments = stats['comments']
            
            metadata_list.append({
                'type': 'world',
                'title': world.name,
                'author': world.author.username,
                'world': world.name,
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': world.created_at.strftime("%d/%m/%Y"),
                'url': f"/mundo/{world.public_id}",
            })
            
        # Add metadata proposals (CaosVersionORM type METADATA)
        metadata_proposals = CaosVersionORM.objects.filter(change_type='METADATA').select_related('author', 'world')
        for prop in metadata_proposals:
            entity_key = f"VERS_{prop.id}"
            stats = SocialService.get_interactions_count(entity_key)
            likes = stats['likes']
            comments = stats['comments']
            
            metadata_list.append({
                'type': 'proposal',
                'title': f"Propuesta: {prop.proposed_name or prop.change_log}",
                'author': prop.author.username if prop.author else 'Anon',
                'world': prop.world.name,
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': prop.created_at.strftime("%d/%m/%Y"),
                'url': f"/mundo/{prop.world.public_id}", # Deep link to proposal could be added
            })

        # 4. PERIODOS (TimelinePeriod)
        all_periods = TimelinePeriod.objects.all().select_related('world')
        for period in all_periods:
            entity_key = f"PERIOD_{period.id}"
            stats = SocialService.get_interactions_count(entity_key)
            likes = stats['likes']
            comments = stats['comments']
            
            periods_list.append({
                'type': 'period',
                'title': period.title,
                'author': 'Sistema', # Timeline periods don't always have a direct author
                'world': period.world.name,
                'likes': likes,
                'comments': comments,
                'engagement': likes + comments,
                'date': period.created_at.strftime("%d/%m/%Y"),
                'url': f"/mundo/{period.world.public_id}",
            })

        # Group data for the accordion
        context['categories'] = [
            {
                'id': 'narratives',
                'title': 'NARRATIVAS',
                'icon': '📖',
                'items': sorted(narratives_list, key=lambda x: x['engagement'], reverse=True),
                'count': len(narratives_list),
                'total_likes': sum(n['likes'] for n in narratives_list),
                'total_comments': sum(n['comments'] for n in narratives_list),
                'color': 'purple'
            },
            {
                'id': 'images',
                'title': 'IMÁGENES',
                'icon': '🖼️',
                'items': sorted(images_list, key=lambda x: x['engagement'], reverse=True),
                'count': len(images_list),
                'total_likes': sum(i['likes'] for i in images_list),
                'total_comments': sum(i['comments'] for i in images_list),
                'color': 'blue'
            },
            {
                'id': 'metadata',
                'title': 'METADATOS',
                'icon': '🧬',
                'items': sorted(metadata_list, key=lambda x: x['engagement'], reverse=True),
                'count': len(metadata_list),
                'total_likes': sum(m['likes'] for m in metadata_list),
                'total_comments': sum(m['comments'] for m in metadata_list),
                'color': 'green'
            },
            {
                'id': 'periods',
                'title': 'PERIODOS',
                'icon': '📜',
                'items': sorted(periods_list, key=lambda x: x['engagement'], reverse=True),
                'count': len(periods_list),
                'total_likes': sum(p['likes'] for p in periods_list),
                'total_comments': sum(p['comments'] for p in periods_list),
                'color': 'yellow'
            }
        ]
        
        # General stats
        context['total_content'] = len(narratives_list) + len(images_list) + len(metadata_list) + len(periods_list)
        context['total_likes'] = sum(cat['total_likes'] for cat in context['categories'])
        context['total_comments'] = sum(cat['total_comments'] for cat in context['categories'])
        context['total_engagement'] = context['total_likes'] + context['total_comments']
        
        return context
