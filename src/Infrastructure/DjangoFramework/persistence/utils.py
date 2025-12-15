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

    # 2. Obtener nombres y descripciones de la DB en una sola consulta
    worlds_data = {w.id: {'name': w.name, 'desc': w.description} for w in CaosWorldORM.objects.filter(id__in=ids_to_fetch)}
    
    # 3. Construir lista ordenada
    full_list = []
    for i, pid in enumerate(ids_to_fetch):
        w_data = worlds_data.get(pid)
        
        # Validar si es "real" (tiene datos)
        is_root = (len(pid) <= 2)
        has_data = False
        label = f"Nivel {i+1}"
        
        if w_data:
            label = w_data['name']
            desc = w_data['desc']
            # Check content validity
            if desc and desc.strip() and desc.lower() != 'none':
                has_data = True
        
        # LOGICA DE FILTRADO:
        # Solo añadimos si es Root, o si tiene datos reales.
        # Excepción: Si es el ÚLTIMO elemento (la página actual), siempre lo añadimos (filtrarlo sería confuso).
        is_last = (pid == jid)
        
        if is_root or has_data or is_last:
            full_list.append({
                'id': pid, 
                'label': label
            })
        
    # --- SMART TRUNCATION ---
    # Si hay más de 5 elementos, mostramos: Root + ... + Últimos 3 (para asegurar contexto)
    if len(full_list) > 5:
        short_list = [full_list[0], {'id': None, 'label': '...'}] + full_list[-3:]
        return short_list
        
    return full_list

def get_world_images(jid):
    base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    target = os.path.join(base, jid)
    if not os.path.exists(target):
        for d in os.listdir(base):
            if d.startswith(f"{jid}_"): target = os.path.join(base, d); break
    
    # Fetch metadata from DB
    try:
        w = CaosWorldORM.objects.get(id=jid)
        gallery_log = w.metadata.get('gallery_log', {}) if w.metadata else {}
        cover_image = w.metadata.get('cover_image', None) if w.metadata else None  # NUEVO
    except:
        gallery_log = {}
        cover_image = None

    imgs = []
    if os.path.exists(target):
        dname = os.path.basename(target)
        for f in sorted(os.listdir(target)):
            if f.lower().endswith(('.png', '.webp', '.jpg')): 
                meta = gallery_log.get(f, {})
                imgs.append({
                    'url': f'{dname}/{f}', 
                    'filename': f,
                    'author': meta.get('uploader', 'Sistema'),
                    'date': meta.get('date', ''),
                    'title': meta.get('title', ''),
                    'is_cover': (f == cover_image)  # NUEVO: Marcar portada
                })
    return imgs
