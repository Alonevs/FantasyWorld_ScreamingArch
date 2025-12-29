from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results_worlds = []
    results_narratives = []
    
    if query:
        from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
        vis_q = get_visibility_q_filter(request.user)
        
        # 1. Search in Worlds (including JSONB metadata)
        worlds = CaosWorldORM.objects.filter(vis_q).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(metadata__icontains=query) # Deep search in JSONB
        ).filter(is_active=True).distinct()[:20]
        
        for w in worlds:
            results_worlds.append({
                'id': w.id,
                'name': w.name,
                'type': 'Mundo',
                'url': f"/mundo/{w.id}/", # Adjust if using public_id
                'match': 'Metadata' if query.lower() in str(w.metadata).lower() else 'Nombre/Desc'
            })
            
        # 2. Search in Narratives (Filter by Parent World Visibility)
        # Re-prefixing world visibility filter for narratives
        # We need to ensure we can see the world 'n.world'
        narratives_vis_q = Q()
        if not request.user.is_superuser:
            # We filter by the visibility of the related world
            # Note: get_visibility_q_filter returns Q objects for CaosWorldORM.
            # We can use it with 'world__' prefix.
            from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
            world_q = get_visibility_q_filter(request.user)
            
            # Reconstruct Q with world__ prefix
            # This is a bit manual but safe.
            narratives_vis_q = Q(world__in=CaosWorldORM.objects.filter(world_q))

        narratives = CaosNarrativeORM.objects.filter(narratives_vis_q).filter(
            Q(titulo__icontains=query) |
            Q(contenido__icontains=query)
        ).filter(is_active=True).distinct()[:20]
        
        for n in narratives:
            results_narratives.append({
                'id': n.nid,
                'name': n.titulo,
                'type': 'Narrativa',
                'url': f"/narrativa/{n.nid}/" # Adjust slug/id logic
            })

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'worlds': results_worlds,
            'narratives': results_narratives
        })

    return render(request, 'search/global_results.html', {
        'query': query,
        'worlds': results_worlds,
        'narratives': results_narratives
    })
