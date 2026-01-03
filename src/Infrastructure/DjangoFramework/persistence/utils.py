import os
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def generate_breadcrumbs(jid: str, user: Optional[User] = None) -> List[Dict[str, Optional[str]]]:
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


def _build_breadcrumb_list(ids: List[str], worlds_data: Dict[str, CaosWorldORM], current_jid: str, user: Optional[User] = None) -> List[Dict[str, Optional[str]]]:
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


def get_world_images(jid: str, world_instance: Optional[CaosWorldORM] = None, period_slug: Optional[str] = None) -> List[Dict[str, Any]]:
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

    # DEBUG LOG Start
    try:
        if cover_image:
            with open("debug_log.txt", "a") as logf:
                logf.write(f"[UTILS] World {jid}: Looking for cover '{cover_image}'\n")
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

                    author_str = meta.get('uploader')
                    if not author_str or author_str in ["Sistema", "Anónimo", "Anonymous", "Unknown"]:
                         if world_instance and world_instance.author:
                             author_str = world_instance.author.username
                         else: author_str = "Alone"
                    
                    # Obtener avatar del usuario
                    avatar_url = ""
                    try:
                        from django.contrib.auth.models import User
                        user_obj = User.objects.filter(username=author_str).first()
                        avatar_url = get_user_avatar(user_obj)
                    except Exception:
                        pass
                    
                    imgs.append({
                        'url': f'{dname}/{f}', 
                        'filename': f.strip(),
                        'author': author_str,
                        'avatar_url': avatar_url,
                        'date': date_str,
                        'title': meta.get('title', ''),
                        'is_cover': False # Post-process verification
                    })
        except Exception as e:
            print(f"Error procesando galería de {jid}: {e}")
    
    # --- SINGLE COVER ENFORCEMENT ---
    if cover_image and imgs:
        # Use centralized cover detection logic
        match = find_cover_image(cover_image, imgs)
        if match:
            match['is_cover'] = True
            
    # --- FALLBACK LOGIC FOR EMPTY PERIODS ---
    # If we requested a specific period but found NO images, 
    # it's better to show 'Actual' images than an empty gallery 
    # (prevents "Broken World" feeling for new Drafts).
    if period_slug and period_slug != 'actual' and not imgs:
        try:
             # Re-scan for 'Actual' images
             imgs_fallback = get_world_images(jid, world_instance, period_slug='actual')
             # Mark them as fallback (optional, for UI)
             for i in imgs_fallback: i['is_fallback'] = True
             imgs = imgs_fallback
        except: pass

    return imgs


def find_cover_image(cover_filename: Optional[str], all_imgs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Encuentra una imagen de portada usando matching case-insensitive y flexible.
    
    Esta función centraliza la lógica de búsqueda de portadas que antes estaba
    duplicada en múltiples archivos (world_views, review_views, team.py).
    
    Estrategia de búsqueda:
    1. Coincidencia exacta (case-insensitive)
    2. Coincidencia sin extensión (case-insensitive) - para casos donde
       metadata tiene "Image" pero archivo es "Image.webp"
    
    Args:
        cover_filename (str): Nombre del archivo de portada a buscar
        all_imgs (list): Lista de diccionarios con información de imágenes.
                        Cada dict debe tener al menos: {'filename': str, 'url': str}
    
    Returns:
        dict: Imagen encontrada con estructura {'filename': str, 'url': str, ...}
        None: Si no se encuentra ninguna coincidencia
    
    Examples:
        >>> imgs = [{'filename': 'Cover.webp', 'url': '01/Cover.webp'}]
        >>> find_cover_image('COVER.WEBP', imgs)
        {'filename': 'Cover.webp', 'url': '01/Cover.webp'}
        
        >>> find_cover_image('Cover', imgs)  # Sin extensión
        {'filename': 'Cover.webp', 'url': '01/Cover.webp'}
        
        >>> find_cover_image('NotFound.jpg', imgs)
        None
    
    Note:
        Esta función es case-insensitive para manejar casos donde metadata
        almacena nombres en mayúsculas (ej: "ABISMOS_PRIME_V1.WEBP") pero
        el archivo real está en formato mixto (ej: "Abismos_Prime_v1.webp").
    """
    if not cover_filename or not all_imgs:
        return None
    
    cover_lower = cover_filename.lower()
    
    # 1. Exact match (case-insensitive)
    match = next((i for i in all_imgs if i['filename'].lower() == cover_lower), None)
    
    # 2. Fallback: without extension (case-insensitive)
    if not match:
        c_clean = cover_filename.rsplit('.', 1)[0].lower()
        match = next((i for i in all_imgs if i['filename'].rsplit('.', 1)[0].lower() == c_clean), None)
    
    return match


def get_thumbnail_url(world_id: str, cover_filename: Optional[str] = None, use_first_if_no_cover: bool = True) -> str:
    """
    Obtiene URL de thumbnail para un mundo con fallback inteligente.
    
    Esta función simplifica la obtención de thumbnails en vistas como
    UserRankingView, aplicando una estrategia de fallback consistente.
    
    Prioridad de fallback:
    1. Cover image definida (si cover_filename proporcionado)
    2. Primera imagen disponible (si use_first_if_no_cover=True)
    3. Placeholder genérico (/static/img/placeholder.png)
    
    Args:
        world_id (str): ID del mundo (ej: "01", "0101")
        cover_filename (str, optional): Nombre del archivo de portada.
                                       Si None, salta al fallback.
        use_first_if_no_cover (bool): Si True, usa primera imagen disponible
                                      cuando no hay cover definida. Default: True
    
    Returns:
        str: URL completa del thumbnail (ej: "/static/persistence/img/01/Cover.webp")
    
    Examples:
        >>> get_thumbnail_url('01', 'Cover.webp')
        '/static/persistence/img/01/Cover.webp'
        
        >>> get_thumbnail_url('01')  # Sin cover, usa primera imagen
        '/static/persistence/img/01/FirstImage.webp'
        
        >>> get_thumbnail_url('99')  # Mundo sin imágenes
        '/static/img/placeholder.png'
        
        >>> get_thumbnail_url('01', use_first_if_no_cover=False)
        '/static/img/placeholder.png'  # Salta primera imagen
    
    Note:
        Esta función llama a get_world_images() internamente, lo cual puede
        ser costoso. Considera cachear resultados si llamas múltiples veces
        para el mismo mundo.
    """
    all_imgs = get_world_images(world_id)
    
    # 1. Try cover image
    if cover_filename:
        cover_img = find_cover_image(cover_filename, all_imgs)
        if cover_img:
            return f"/static/persistence/img/{cover_img['url']}"
    
    # 2. Fallback: first image
    if use_first_if_no_cover and all_imgs:
        return f"/static/persistence/img/{all_imgs[0]['url']}"
    
    # 3. Fallback: placeholder
    return "/static/img/placeholder.png"



def get_user_avatar(user: Optional[User], jid: Optional[str] = None) -> str:
    """
    Obtiene la URL del avatar de un usuario de forma centralizada.
    
    Args:
        user: Objeto User de Django (puede ser None)
        jid: J-ID del mundo para fallback de imagen aleatoria (opcional, no usado actualmente)
    
    Returns:
        str: URL del avatar (foto de perfil, imagen aleatoria, o cadena vacía)
    """
    if not user:
        return ""
    
    # Intentar obtener avatar del perfil
    try:
        if hasattr(user, 'profile') and user.profile and user.profile.avatar:
            return user.profile.avatar.url
    except:
        pass
    
    # Fallback: Usar imagen aleatoria de la carpeta static/persistence/img
    try:
        import random
        from pathlib import Path
        from django.templatetags.static import static
        
        # Ruta a la carpeta de imágenes generadas/subidas
        # BASE_DIR es src/Infrastructure/DjangoFramework/
        img_dir = Path(settings.BASE_DIR) / 'persistence' / 'static' / 'persistence' / 'img'
        
        if img_dir.exists():
            # Buscar archivos de imagen recursivamente en todas las subcarpetas
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                image_files.extend(img_dir.rglob(f'*{ext}'))  # rglob busca recursivamente
                image_files.extend(img_dir.rglob(f'*{ext.upper()}'))
            
            if image_files:
                image_files.sort() # Ensure stable order across restarts
                # Deterministic Randomness based on User ID to ensure stability
                if user and hasattr(user, 'id'):
                    random.seed(user.id)
                    
                random_image = random.choice(image_files)
                # Obtener ruta relativa desde img_dir
                relative_path = random_image.relative_to(img_dir)
                # Retornar URL estática
                return static(f'persistence/img/{relative_path.as_posix()}')
    except Exception as e:
        print(f"Error getting fallback avatar: {e}")
    
    return f"https://ui-avatars.com/api/?name={user.username if user and hasattr(user, 'username') else 'User'}&background=random&color=fff"
