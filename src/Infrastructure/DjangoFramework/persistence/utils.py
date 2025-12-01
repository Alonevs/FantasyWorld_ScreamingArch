import os
from django.conf import settings
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def generate_breadcrumbs(jid):
    """Genera breadcrumbs robustos manejando longitudes variables y nombres reales."""
    breadcrumbs = []
    current_len = 0
    target_len = len(jid)
    
    ids_to_fetch = []
    
    # 1. Calcular todos los IDs de la ruta
    while current_len < target_len:
        # Niveles 1-15 son de 2 chars, Nivel 16 (Entidad) es de 4 chars
        # Si ya estamos en longitud 30 (Nivel 15), el siguiente salto es de 4
        step = 4 if current_len >= 30 else 2
        
        # Protección contra IDs mal formados
        if current_len + step > target_len: break
        
        current_len += step
        chunk_id = jid[:current_len]
        ids_to_fetch.append(chunk_id)

    # 2. Obtener nombres de la DB en una sola consulta
    worlds = {w.id: w.name for w in CaosWorldORM.objects.filter(id__in=ids_to_fetch)}
    
    # 3. Construir lista ordenada
    for i, pid in enumerate(ids_to_fetch):
        # El nivel es el índice + 1
        breadcrumbs.append({
            'id': pid, 
            'label': worlds.get(pid, f"Nivel {i+1}")
        })
        
    return breadcrumbs

def get_world_images(jid):
    base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    target = os.path.join(base, jid)
    if not os.path.exists(target):
        for d in os.listdir(base):
            if d.startswith(f"{jid}_"): target = os.path.join(base, d); break
    imgs = []
    if os.path.exists(target):
        dname = os.path.basename(target)
        for f in sorted(os.listdir(target)):
            if f.lower().endswith(('.png', '.webp', '.jpg')): imgs.append({'url': f'{dname}/{f}', 'filename': f})
    return imgs
