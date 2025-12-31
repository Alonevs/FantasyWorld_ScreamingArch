import logging
from django.db.models import Q
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosWorldORM, CaosNarrativeORM, CaosLike, CaosComment, TimelinePeriod, CaosVersionORM, CaosEventLog
)

logger = logging.getLogger(__name__)

class SocialService:
    """
    Unified service for social interactions (likes, comments) and content discovery.
    Provides robust matching for entity keys and exhaustive scanning of user-owned content.
    """

    @staticmethod
    def get_robust_query(entity_key: str) -> Q:
        """
        Creates a Q object that matches an entity_key robustly.
        Handles:
        - Case insensitivity (iexact).
        - Dash encoding artifacts (e.g., '-' vs '\\u002D').
        """
        queries = Q(entity_key__iexact=entity_key)
        
        # Handle dash vs \u002D encoding
        if '-' in entity_key:
            alt_key = entity_key.replace('-', '\\u002D')
            queries |= Q(entity_key__iexact=alt_key)
        elif '\\u002D' in entity_key:
            alt_key = entity_key.replace('\\u002D', '-')
            queries |= Q(entity_key__iexact=alt_key)
            
        return queries

    @staticmethod
    def normalize_key(entity_key: str) -> str:
        """
        Normalizes an entity key for comparison.
        """
        if not entity_key:
            return ""
        return entity_key.lower().replace('\\u002d', '-').replace('\\u002D', '-')

    @staticmethod
    def compare_keys(key1: str, key2: str) -> bool:
        """
        Robustly compares two entity keys.
        """
        return SocialService.normalize_key(key1) == SocialService.normalize_key(key2)

    @staticmethod
    def get_interactions_count(entity_key: str) -> dict:
        """
        Returns total likes and top-level comments for an entity_key.
        """
        if not entity_key:
            return {'likes': 0, 'comments': 0, 'engagement': 0}
            
        query = SocialService.get_robust_query(entity_key)
        likes = CaosLike.objects.filter(query).count()
        comments = CaosComment.objects.filter(query, parent_comment__isnull=True).count()
        
        return {
            'likes': likes,
            'comments': comments,
            'engagement': likes + comments
        }

    @staticmethod
    def get_comments(entity_key: str, parent_only=True):
        """
        Returns a queryset of comments for an entity_key.
        """
        query = SocialService.get_robust_query(entity_key)
        qs = CaosComment.objects.filter(query).select_related('user')
        if parent_only:
            qs = qs.filter(parent_comment__isnull=True)
        return qs.order_by('created_at')

    @staticmethod
    def discover_user_content(target_user: User, include_proposals=True):
        """
        Exhaustively scans the database to find all content attributed to a user.
        Scans:
        - Worlds (as author).
        - Narratives (as creator).
        - Images in World Gallery (as uploader or world author fallback).
        - Images as World Covers.
        - Images in Timeline Periods (Gallery & Cover).
        """
        username = target_user.username
        username_lower = username.lower()
        
        results = {
            'images': [],
            'narratives': [],
            'worlds': [],
            'proposals': []
        }

        # 1. WORLDS
        user_worlds = CaosWorldORM.objects.filter(
            Q(author=target_user) | Q(current_author_name__iexact=username),
            is_active=True
        ).distinct()
        
        for w in user_worlds:
            results['worlds'].append(w)

        # 2. NARRATIVES
        user_narratives = CaosNarrativeORM.objects.filter(
            created_by=target_user,
            is_active=True
        ).select_related('world')
        for n in user_narratives:
            results['narratives'].append(n)

        # 3. IMAGES (The complex part)
        # We need to scan ALL active worlds because a user might have uploaded to someone else's world
        all_active_worlds = CaosWorldORM.objects.filter(is_active=True).select_related('author')
        
        for world in all_active_worlds:
            world_author_matches = (
                (world.author and world.author.username.lower() == username_lower) or 
                (world.current_author_name and world.current_author_name.lower() == username_lower)
            )
            
            if not world.metadata:
                continue
                
            # A. Cover Image
            cover = world.metadata.get('cover_image')
            if cover and world_author_matches:
                # Attribution: If it's a world cover, we attribute it to world author if no specific uploader
                results['images'].append({
                    'filename': cover,
                    'title': f"Portada: {world.name}",
                    'world': world,
                    'type': 'cover'
                })

            # B. Gallery Log
            gallery = world.metadata.get('gallery_log', {})
            for filename, meta in gallery.items():
                uploader = meta.get('uploader', '')
                if uploader.lower() == username_lower:
                    results['images'].append({
                        'filename': filename,
                        'title': meta.get('title', filename),
                        'world': world,
                        'meta': meta,
                        'type': 'gallery'
                    })
                elif not uploader and world_author_matches:
                    # Fallback to world author if no uploader
                    results['images'].append({
                        'filename': filename,
                        'title': meta.get('title', filename),
                        'world': world,
                        'meta': meta,
                        'type': 'gallery'
                    })

            # C. Timeline Periods
            # We also check for images inside the timeline metadata
            timeline = world.metadata.get('timeline', {})
            for year, data in timeline.items():
                # Period Cover
                p_cover = data.get('cover_image')
                if p_cover and world_author_matches:
                    results['images'].append({
                        'filename': p_cover,
                        'title': f"Portada Periodo {year}",
                        'world': world,
                        'type': 'period_cover'
                    })
                
                # Period Gallery
                p_gallery = data.get('gallery_log', {})
                for p_filename, p_meta in p_gallery.items():
                    p_uploader = p_meta.get('uploader', '')
                    if p_uploader.lower() == username_lower:
                        results['images'].append({
                            'filename': p_filename,
                            'title': p_meta.get('title', p_filename),
                            'world': world,
                            'meta': p_meta,
                            'type': 'period_gallery'
                        })

        # 4. HISTORICAL CONTENT (From Event Logs)
        # Scan for any image the user has EVER uploaded or proposed
        historical_logs = CaosEventLog.objects.filter(
            user=target_user,
            action__in=['UPLOAD_PHOTO', 'PROPOSE_COVER', 'PROPOSE_AI_PHOTO', 'RETOUCH_PHOTO']
        ).values_list('details', flat=True)
        
        found_historical_files = set()
        for detail in historical_logs:
            # Extract filename from "Proposed cover: filename", "File: filename", "Title: filename"
            # This is a bit heuristic but better than missing it
            parts = detail.split(':')
            if len(parts) > 1:
                filename = parts[1].strip().split('(')[0].strip()
                if filename.lower().endswith(('.webp', '.png', '.jpg', '.jpeg', '.gif')):
                    found_historical_files.add(filename)
        
        # Add historical files to results if not already present
        existing_files = {img['filename'].lower() for img in results['images']}
        for h_file in found_historical_files:
            if h_file.lower() not in existing_files:
                # We don't have a world or meta for these, but they are Alone's content
                results['images'].append({
                    'filename': h_file,
                    'title': f"Histórico: {h_file}",
                    'world': None,
                    'type': 'historical'
                })

        if include_proposals:
            user_proposals = CaosVersionORM.objects.filter(author=target_user)
            for p in user_proposals:
                results['proposals'].append(p)

        return results

    @staticmethod
    def get_user_activity(target_user):
        """
        Returns all social interactions performed BY or directed TO the target user
        in the context of threads they started.
        """
        from django.db.models import Q
        # Comments sent by the user OR replies to the user's comments
        activity_comments = CaosComment.objects.filter(
            Q(user=target_user) | Q(parent_comment__user=target_user)
        ).order_by('-created_at').distinct()
        
        return {
            'comments': activity_comments
        }

    @staticmethod
    def resolve_content_by_key(entity_key):
        """
        Attempts to find the world and name associated with an entity key.
        """
        key = SocialService.normalize_key(entity_key)
        
        # 1. Image
        if key.startswith('img_'):
            filename = key[4:]
            # Search in all worlds' gallery_log or cover_image
            worlds = CaosWorldORM.objects.filter(
                Q(metadata__gallery_log__has_key=filename) |
                Q(metadata__cover_image=filename)
            ).distinct()
            
            if worlds.exists():
                w = worlds.first()
                title = w.metadata.get('gallery_log', {}).get(filename, {}).get('title', filename)
                return {'type': 'image', 'world': w, 'title': title, 'filename': filename}
            
            # Fallback search in TimelinePeriods
            periods = TimelinePeriod.objects.filter(metadata__gallery_log__has_key=filename).distinct()
            if periods.exists():
                p = periods.first()
                title = p.metadata.get('gallery_log', {}).get(filename, {}).get('title', filename)
                return {'type': 'image', 'world': p.world, 'title': title, 'filename': filename}
            
            # Fallback search in CaosEventLog
            from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog
            log = CaosEventLog.objects.filter(details__icontains=filename).first()
            if log and log.target_id:
                # target_id usually contains the JID
                world = CaosWorldORM.objects.filter(id=log.target_id).first()
                return {'type': 'image', 'world': world, 'title': filename, 'filename': filename}
            
            return {'type': 'image', 'world': None, 'title': filename, 'filename': filename}

        # 2. Narrative
        if key.startswith('narr_'):
            public_id = key[5:]
            n = CaosNarrativeORM.objects.filter(public_id=public_id).first()
            if n:
                return {'type': 'narrative', 'world': n.world, 'title': n.titulo, 'id': public_id}

        # 3. World
        if key.startswith('world_'):
            public_id = key[6:]
            w = CaosWorldORM.objects.filter(public_id=public_id).first()
            if not w: w = CaosWorldORM.objects.filter(id=public_id).first()
            if w:
                return {'type': 'world', 'world': w, 'title': w.name, 'id': w.public_id}

        # 4. Proposal
        if key.startswith('ver_'):
            ver_id = key[4:]
            v = CaosVersionORM.objects.filter(id=ver_id).first()
            if v:
                return {'type': 'proposal', 'world': v.entidad, 'title': f"Propuesta v{v.version_number}", 'id': ver_id}

        return None
