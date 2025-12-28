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
        # 1. Search in Worlds (including JSONB metadata)
        # We use icontains for basic fields and @> or other operators for JSONB would be nice,
        # but Django's metadata__contains for JSONField works well with Postgres.
        worlds = CaosWorldORM.objects.filter(
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
            
        # 2. Search in Narratives
        narratives = CaosNarrativeORM.objects.filter(
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
