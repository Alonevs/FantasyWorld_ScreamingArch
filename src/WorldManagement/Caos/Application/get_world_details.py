from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
import json

class GetWorldDetailsUseCase:
    """
    Caso de Uso para obtener los detalles completos de una entidad (Mundo/Nivel).
    Se encarga de resolver la jerarquía, gestionar la visibilidad de hijos (incluyendo saltos y compartidos),
    y preparar todos los datos necesarios para la vista de detalle.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str, user=None, period_slug=None):
        # 1. Resolver el ID (puede ser J-ID o NanoID)
        w_domain = resolve_world_id(self.repository, identifier)
        if not w_domain:
            return None

        from django.db.models import Q # Import needed for Federated Logic

        # 2. Obtener el objeto ORM (referencia directa para acceder a relaciones de base de datos)
        # Nota: Idealmente esto debería pasar por DTOs en el repositorio, pero se mantiene así por agilidad actual.
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
        try:
            w = CaosWorldORM.objects.get(id=w_domain.id.value, is_active=True)
        except CaosWorldORM.DoesNotExist:
            return None

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid
        
        # 3. VERIFICAR PERMISO DE ACCESO (Seguridad)
        from src.Infrastructure.DjangoFramework.persistence.policies import can_user_view_world
        if not can_user_view_world(user, w):
            return None # El controlador manejará esto como un 404/403
        
        # Utilidades para gestión de imágenes y migas de pan
        from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images, generate_breadcrumbs
        
        # --- LÓGICA DE DESCENDIENTES (Saltos y Entidades Compartidas) ---
        # 1. Recuperar todos los descendientes activos que empiecen por este J-ID
        all_descendants = CaosWorldORM.objects.filter(id__startswith=jid, is_active=True).exclude(id=jid).order_by('id')
        
        # --- LÓGICA DE TRONCO COMPARTIDO '00' ---
        # La rama '00' en la raíz (ej. 0100...) sirve como repositorio de entidades compartidas.
        # Estas entidades deben ser visibles para todos los "primos" del mismo nivel.
        if len(jid) >= 2:
            root_id = jid[:2]
            shared_trunk = root_id + "00"
            
            # Buscamos entidades en el tronco compartido
            trunk_descendants = CaosWorldORM.objects.filter(id__startswith=shared_trunk, is_active=True)
            
            # Combinamos con los descendientes directos para procesar la visibilidad conjunta
            all_descendants = all_descendants | trunk_descendants
                
        # Eliminar duplicados y ordenar por J-ID
        all_descendants = all_descendants.distinct().order_by('id')

        # Filtro Global: Los BORRADORES (DRAFT) no se ven en la vista Live (solo en el Dashboard)
        all_descendants = all_descendants.exclude(status='DRAFT')

        # 2. Filtrado Base
        # Lógica CENTRALIZADA en policies.py (Misma que Home)
        if user and user.is_authenticated:
             from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
             
             q_filter = get_visibility_q_filter(user)
             all_descendants = all_descendants.filter(q_filter)
        else:
             # Anonimo
             all_descendants = all_descendants.filter(visible_publico=True)

        nodes_map = {d.id: d for d in all_descendants}

        # --- DETERMINACIÓN DE VISIBILIDAD (Hoisting y Transparencia) ---
        # Identificamos qué entidades son visibles directamente desde esta página.
        sorted_desc = sorted(all_descendants, key=lambda x: len(x.id), reverse=True)
        
        # Función auxiliar para identificar "Entidades Fantasma" (estructurales/vacías)
        def is_conceptually_ghost(node):
            name_lower = node.name.lower()
            is_generic = "nexo" in name_lower or "ghost" in name_lower or "fantasma" in name_lower or node.name in ("Placeholder", "")
            return node.id.endswith("00") and is_generic

        solid_ids = set() 
        for d in sorted_desc:
            is_ghost = is_conceptually_ghost(d)
            if not is_ghost:
                solid_ids.add(d.id)
            if d.id in solid_ids:
                if len(d.id) > len(jid):
                    pid = d.id[:-2]
                    solid_ids.add(pid) 

        visible_children = []
        for d in all_descendants:
            # REGLA 1: Los fantasmas son siempre invisibles (solo sirven de pegamento estructural)
            if is_conceptually_ghost(d):
                continue

            # REGLA 2: Transparencia (Si el camino hasta el hijo está compuesto solo por fantasmas, el hijo "sube")
            is_shadowed = False
            for l in range(len(jid) + 2, len(d.id), 2):
                intermediate_id = d.id[:l]
                ancestor = nodes_map.get(intermediate_id)
                if ancestor and not is_conceptually_ghost(ancestor):
                    is_shadowed = True # Un ancestro real bloquea la vista (el hijo pertenece a ese ancestro)
                    break
            
            if not is_shadowed:
                # Calculamos niveles para la interfaz (Badge y Posicionamiento)
                d.visual_level = len(d.id) // 2
                parent_level = len(jid) // 2
                d.relative_level = d.visual_level - parent_level
                
                # REGLA 3: Los hijos compartidos ('00') no se ven en la vista de su padre directo
                if d.id.startswith(jid + '00'):
                    continue

                # REGLA 4: Solo mostramos entidades que están exactamente 1 nivel por debajo (Jerarquía Estricta)
                if d.relative_level != 1:
                    continue
                
                visible_children.append(d)


        # --- PREPARACIÓN DE DATOS DE HIJOS ---
        hijos = []
        for h in visible_children:
            h_pid = h.public_id if h.public_id else h.id
            # Resolución de Imagen de Portada (Pass instance to avoid N+1 and get latest meta)
            imgs = get_world_images(h.id, world_instance=h)
            img_url = None
            if imgs:
                cover_img = next((img for img in imgs if img.get('is_cover')), None)
                img_url = cover_img['url'] if cover_img else imgs[0]['url']
            
            level = len(h.id) // 2
            parent_level = len(jid) // 2
            relative_level = level - parent_level
            
            # Detección de Salto (Is Jumped) para el borde amarillo discontinuo
            is_jumped = False
            # Caso 1: Tiene un segmento '00' intermedio
            if len(h.id) > 2:
                for i in range(len(jid), len(h.id)-2, 2):
                    if h.id[i:i+2] == '00':
                        is_jumped = True
                        break
            # Caso 2: Salto directo de nivel relativo
            if relative_level > 1:
                is_jumped = True
            # Caso 3: Es una entidad compartida (proviene de otra rama)
            if not h.id.startswith(jid):
                is_jumped = True

            # Prepare images list with cover first
            all_h_imgs = [i['url'] for i in imgs] if imgs else []
            if img_url and img_url in all_h_imgs:
                all_h_imgs.remove(img_url)
                all_h_imgs.insert(0, img_url)

            child_data = {
                'id': h.id, 
                'public_id': h_pid, 
                'name': h.name, 
                'short': h.id[len(jid):], 
                'img': img_url,
                'images': all_h_imgs[:5],
                'level': level,
                'relative_level': relative_level,
                'missing_parent_id': getattr(h, 'missing_parent_id', None),
                'is_jumped': is_jumped
            }
            hijos.append(child_data)

        # Orden final: Priorizar hijos directos sobre compartidos, luego por nivel y J-ID
        hijos.sort(key=lambda x: (x['is_jumped'], x['level'], x['id']))

        # 4. Obtener Imágenes de la Entidad actual
        # Filtrar por período si se especifica
        imgs = get_world_images(jid, world_instance=w, period_slug=period_slug)
        # Prioritize cover image in the gallery list
        if imgs:
            imgs.sort(key=lambda x: x.get('is_cover', False), reverse=True)
        
        # 5. Formatear Metadatos (JSON)
        meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
        
        # 6. Información de Versiones y Propuestas
        last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
        date_live = last_live.created_at if last_live else w.created_at
        
        props = w.versiones.filter(status='PENDING').order_by('-created_at')
        historial = w.versiones.exclude(status='PENDING').order_by('-created_at')

        # 7. Resolución del Esquema de Metadatos
        schema = None
        try:
            from src.WorldManagement.Caos.Domain.metadata_router import get_schema_for_hierarchy
            level = len(jid) // 2
            schema = get_schema_for_hierarchy(jid, level)
        except Exception as e:
            print(f"Error resolviendo esquema en GetWorldDetails: {e}")

        # --- FIX: Metadata Wrapper para fusionar Default Schema + Stored Data ---
        class MetadataWrapper:
            def __init__(self, data, schema_fields):
                self.properties = []
                # 1. Normalización de entrada (Soporte para cuando metadata es una Lista pura)
                if isinstance(data, list):
                    for p in data:
                        if isinstance(p, dict) and 'key' in p:
                            self.properties.append(p)
                    self._data = {} # Evita errores de .get() en el resto del init
                else:
                    self._data = data or {}
                
                # 2. Extraer 'properties' si existen en formato dict
                if isinstance(self._data, dict) and 'properties' in self._data:
                    props_list = self._data.get('properties', [])
                    if isinstance(props_list, list):
                        for p in props_list:
                            if p not in self.properties:
                                self.properties.append(p)
                
                # 3. Soporte para Estructura V2 (datos_nucleo / datos_extendidos)
                for key_v2 in ['datos_nucleo', 'datos_extendidos']:
                    field_data = self._data.get(key_v2)
                    if isinstance(field_data, dict):
                        for k, v in field_data.items():
                            if not any(p.get('key') == k for p in self.properties):
                                 self.properties.append({'key': k, 'value': v})
                
                # 4. Fusionar campos faltantes del esquema
                existing_keys = {p.get('key') for p in self.properties if p.get('key')}
                if schema_fields:
                    for k, v in schema_fields.items():
                        if k not in existing_keys:
                            val = 0 if k == 'current_epoch' else ([] if k in ('timeline', 'events') else v)
                            self.properties.append({'key': k, 'value': val, 'action': 'ADD'})

            def __getitem__(self, item):
                return self._data.get(item) if isinstance(self._data, dict) else None
            
            def get(self, item, default=None):
                return self._data.get(item, default) if isinstance(self._data, dict) else default

        schema_fields = schema.get("campos_fijos", {}) if schema else {}
        metadata_wrapper = MetadataWrapper(w.metadata, schema_fields)


        # 8. Cálculo de Permisos (Lógica Boss/Minion M2M)
        is_author = (user and w.author == user)
        is_super = (user and user.is_superuser)
        is_subadmin = False
        try:
            if user and hasattr(user, 'profile'):
                # Si el autor del mundo está en la lista de jefes del usuario (M2M)
                if user.profile.bosses.filter(user=w.author).exists():
                    is_subadmin = True
        except: pass
        
        # FIX CENTRALIZADO: Usar Policy para permisos de edición/propuesta
        from src.Infrastructure.DjangoFramework.persistence.policies import can_user_propose_on
        can_edit = can_user_propose_on(user, w)

        # Authority Check (Boss level: Superuser or Owner)
        has_authority = False
        if user:
            if user.is_superuser: has_authority = True
            elif w.author == user: has_authority = True

        # 9. Construcción del Diccionario de Resultado para el Template

        # 9. Construcción del Diccionario de Resultado para el Template
        return {
            'name': w.name, 
            'description': w.description, 
            'jid': jid, 
            'id_codificado': jid,  # Referencia para compatibilidad JS
            'public_id': safe_pid,
            'status': w.status, 
            'version_live': w.current_version_number,
            'author_live': w.author.username if w.author else 'Alone',
            'created_at': w.created_at, 
            'updated_at': date_live,
            'visible': w.visible_publico, 
            'is_locked': w.is_locked, 
            'nid_lore': w.id_lore, 
            'metadata': meta_str, 
            'metadata_obj': metadata_wrapper, 
            'metadata_schema': schema,
            'imagenes': imgs, 
            'hijos': hijos, 
            'breadcrumbs': generate_breadcrumbs(jid, user=user), 
            'propuestas': props, 
            'historial': historial,
            'is_preview': False,
            'can_edit': can_edit,
            'has_authority': has_authority,
            'is_subadmin': is_subadmin, # Expose for UI logic (AI Button)
            'is_admin_role': user and (user.is_superuser or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']))
        }
