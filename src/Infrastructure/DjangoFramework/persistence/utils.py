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

    # 2. Obtener nombres, descripciones y PUBLIC_ID de la DB en una sola consulta
    worlds_data = {w.id: {'name': w.name, 'desc': w.description, 'public_id': w.public_id} for w in CaosWorldORM.objects.filter(id__in=ids_to_fetch)}
    
    # 3. Construir lista ordenada
    full_list = []
    for i, pid in enumerate(ids_to_fetch):
        w_data = worlds_data.get(pid)
        
        # Validar si es "real" (tiene datos)
        is_root = (len(pid) <= 2)
        has_data = False
        label = f"Nivel {i+1}"
        link_id = pid # Fallback
        
        if w_data:
            label = w_data['name']
            desc = w_data['desc']
            link_id = w_data['public_id'] # Prefer NanoID
            # Check content validity
            if desc and desc.strip() and desc.lower() != 'none':
                has_data = True
        
        # LOGICA DE FILTRADO:
        # Solo añadimos si es Root, o si tiene datos reales.
        # Excepción: Si es el ÚLTIMO elemento (la página actual), siempre lo añadimos (filtrarlo sería confuso).
        is_last = (pid == jid)
        
        if is_root or has_data or is_last:
            full_list.append({
                'id': link_id, 
                'label': label
            })
        
    # --- SMART TRUNCATION ---
    # Si hay más de 5 elementos, mostramos: Root + ... + Últimos 3 (para asegurar contexto)
    if len(full_list) > 5:
        short_list = [full_list[0], {'id': None, 'label': '...'}] + full_list[-3:]
        return short_list
        
    return full_list

def get_world_images(jid, world_instance=None):
    from pathlib import Path
    
    # Use pathlib for robust path handling
    base_dir = Path(settings.BASE_DIR) / 'persistence' / 'static' / 'persistence' / 'img'
    
    # Safety Check: If base_dir doesn't exist, return empty
    if not base_dir.exists():
        return []

    target = base_dir / jid
    
    # Discovery Logic (handling legacy folder names like "ID_Name")
    if not target.exists():
        try:
            for d in base_dir.iterdir():
                if d.is_dir() and d.name.startswith(f"{jid}_"): 
                    target = d
                    break
        except Exception:
            # If iterdir fails (permission, etc), fallback safely
            return []
    
    # Fetch metadata from DB (Use instance if available to avoid N+1)
    gallery_log = {}
    cover_image = None
    
    if world_instance:
        gallery_log = world_instance.metadata.get('gallery_log', {}) if world_instance.metadata else {}
        cover_image = world_instance.metadata.get('cover_image', None) if world_instance.metadata else None
    else:
        try:
            w = CaosWorldORM.objects.get(id=jid)
            gallery_log = w.metadata.get('gallery_log', {}) if w.metadata else {}
            cover_image = w.metadata.get('cover_image', None) if w.metadata else None
        except:
            gallery_log = {}
            cover_image = None

    imgs = []
    if target.exists() and target.is_dir():
        dname = target.name
        try:
            for f in sorted(os.listdir(str(target))): # str(target) for legacy os.listdir compatibility if needed, or target.iterdir()
                 # Using os.listdir for simple name string
                if f.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')): 
                    meta = gallery_log.get(f, {})
                    
                    # DATE LOGIC: Meta > File Creation Time > Today
                    date_str = meta.get('date', '')
                    if not date_str:
                        try:
                            import datetime
                            file_path = os.path.join(str(target), f)
                            timestamp = os.path.getmtime(file_path)
                            dt = datetime.datetime.fromtimestamp(timestamp)
                            date_str = dt.strftime('%d/%m/%Y')
                        except:
                            date_str = "??/??/????"

                    # AUTHOR LOGIC: Meta > World Author > "Alone"
                    author_str = meta.get('uploader')
                    if not author_str or author_str == "Sistema":
                         # Fallback to world author if possible, otherwise 'Alone'
                         if world_instance and world_instance.author:
                             author_str = world_instance.author.username
                         else:
                             author_str = "Alone"

                    imgs.append({
                        'url': f'{dname}/{f}', 
                        'filename': f,
                        'author': author_str,
                        'date': date_str,
                        'title': meta.get('title', ''),
                        'is_cover': (f == cover_image)
                    })
        except Exception as e:
            print(f"Error reading images for {jid}: {e}")
            
    return imgs
