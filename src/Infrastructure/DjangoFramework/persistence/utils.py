import os
from django.conf import settings
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def generate_breadcrumbs(jid, user=None):
    """
    Genera una lista de 'migas de pan' (breadcrumbs) robusta y procesada.
    Ahora incorpora chequeo de permisos para no 'dar pistas' de mundos restringidos.
    """
    ids = _parse_jid_hierarchy(jid)
    worlds_data = _fetch_worlds_data(ids)
    breadcrumbs = _build_breadcrumb_list(ids, worlds_data, jid, user)
    return _apply_truncation(breadcrumbs)


def _parse_jid_hierarchy(jid: str) -> list:
    """
    Fragmenta el J-ID en niveles lógicos.
    
    Args:
        jid: Identificador jerárquico completo
        
    Returns:
        Lista de IDs parciales representando cada nivel
    """
    ids_to_fetch = []
    current_len = 0
    target_len = len(jid)
    
    while current_len < target_len:
        # Los primeros niveles son de 2 caracteres. El Nivel 16 es de 4.
        step = 4 if current_len >= 30 else 2
        if current_len + step > target_len:
            break
        
        current_len += step
        chunk_id = jid[:current_len]
        ids_to_fetch.append(chunk_id)
    
    return ids_to_fetch


def _fetch_worlds_data(ids: list) -> dict:
    """
    Recupera datos de ancestros en una única consulta optimizada.
    Incluye campos necesarios para el chequeo de permisos (status, visibility, author).
    """
    return {
        w.id: w for w in CaosWorldORM.objects.filter(id__in=ids).select_related('author').only(
            'id', 'name', 'description', 'public_id', 'status', 'visible_publico', 'author'
        )
    }


def _build_breadcrumb_list(ids: list, worlds_data: dict, current_jid: str, user=None) -> list:
    """
    Construye lista de breadcrumbs con filtrado de gaps y SEGURIDAD (RBAC).
    """
    from src.Infrastructure.DjangoFramework.persistence.policies import can_user_view_world
    
    full_list = []
    
    for i, pid in enumerate(ids):
        w_obj = worlds_data.get(pid)
        is_root = (len(pid) <= 2)
        has_data = False
        label = f"Nivel {i+1}"
        link_id = pid  # ID por defecto
        
        if w_obj:
            label = w_obj.name
            desc = w_obj.description
            link_id = w_obj.public_id or pid
            if desc and desc.strip() and desc.lower() != 'none':
                has_data = True
            
            # FILTRO DE SEGURIDAD (RBAC):
            # Si el usuario NO tiene permiso para ver este ancestro, no lo listamos.
            if user and not can_user_view_world(user, w_obj):
                continue
        
        # LÓGICA DE FILTRADO DE GAPS:
        is_ghost_name = "nexo" in label.lower() or "fantasma" in label.lower() or "ghost" in label.lower()
        is_generic_ghost = pid.endswith("00") and is_ghost_name
        is_last = (pid == current_jid)
        
        should_show = (is_root or has_data or is_last)
        if is_generic_ghost and not is_last:
            should_show = False
             
        if should_show:
            full_list.append({'id': link_id, 'label': label})
    
    return full_list


def _apply_truncation(breadcrumbs: list) -> list:
    """
    Aplica truncamiento inteligente si la ruta es muy larga.
    
    Args:
        breadcrumbs: Lista completa de breadcrumbs
        
    Returns:
        Lista truncada si es necesario: [Raíz, ..., Últimos 3]
    """
    if len(breadcrumbs) > 5:
        return [breadcrumbs[0], {'id': None, 'label': '...'}] + breadcrumbs[-3:]
    
    return breadcrumbs


def get_world_images(jid, world_instance=None, period_slug=None):
    """
    Localiza y cataloga las imágenes asociadas a una entidad en el sistema de archivos.
    Cruza los archivos físicos con el 'gallery_log' almacenado en los metadatos de la DB
    para recuperar autores, fechas, títulos y su asociación con Períodos Temporales.
    """
    from pathlib import Path
    import datetime
    
    # Definición de ruta base para el almacenamiento estático
    base_dir = Path(settings.BASE_DIR) / 'persistence' / 'static' / 'persistence' / 'img'
    if not base_dir.exists(): return []

    target = base_dir / jid
    
    # Fallback para estructuras de carpetas legacy (ID_Nombre)
    if not target.exists():
        try:
            for d in base_dir.iterdir():
                if d.is_dir() and d.name.startswith(f"{jid}_"): 
                    target = d
                    break
        except: return []
    
    # Recuperación de metadatos de galería (Evita N+1 usando la instancia si existe)
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
        except: pass

    imgs = []
    if target.exists() and target.is_dir():
        dname = target.name
        try:
            for f in sorted(os.listdir(str(target))):
                if f.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')): 
                    meta = gallery_log.get(f, {})
                    
                    # FILTRADO POR PERÍODO
                    # Si estamos en vista de período, solo mostramos las de ese período.
                    # Si estamos en vista ACTUAL, solo mostramos las que NO tengan período o sean explicitly actual.
                    img_period = meta.get('period')
                    
                    if period_slug and period_slug != 'actual':
                        # Vista de Período Histórico
                        if img_period != period_slug:
                            continue
                    else:
                        # Vista ACTUAL o por defecto
                        if img_period and img_period != 'actual':
                            continue

                    # Lógica de Fecha: Metadata > Fecha modificación archivo > Hoy
                    date_str = meta.get('date', '')
                    if date_str and ' ' in str(date_str):
                        # Limpiamos horas y minutos (cualquier cosa tras el espacio)
                        date_str = str(date_str).split(' ')[0]
                    
                    # Normalización opcional: Convertir YYYY-MM-DD a DD/MM/YYYY si se desea total consistencia
                    if date_str and '-' in date_str and len(date_str) == 10:
                        parts = date_str.split('-')
                        if len(parts[0]) == 4: # YYYY-MM-DD
                            date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                    if not date_str:
                        try:
                            timestamp = os.path.getmtime(os.path.join(str(target), f))
                            date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y')
                        except: date_str = "??/??/????"

                    # Lógica de Autoría: Metadata > Autor del Mundo > "Alone"
                    author_str = meta.get('uploader')
                    if not author_str or author_str == "Sistema":
                         if world_instance and world_instance.author:
                             author_str = world_instance.author.username
                         else: author_str = "Alone"

                    imgs.append({
                        'url': f'{dname}/{f}', 
                        'filename': f,
                        'author': author_str,
                        'date': date_str,
                        'title': meta.get('title', ''),
                        'is_cover': (f == cover_image) # Identifica si es la portada actual
                    })
        except Exception as e:
            print(f"Error procesando galería de {jid}: {e}")
            
    return imgs
