from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
import json

class GetWorldDetailsUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str, user=None):
        # 1. Resolve ID
        w_domain = resolve_world_id(self.repository, identifier)
        if not w_domain:
            return None

        # 2. Get ORM object (for now, until full migration)
        # We need to access related models like versions, images, etc.
        # Ideally this should be done via repository methods returning DTOs,
        # but for this refactor we will return a dict with everything needed for the template.
        
        from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
        try:
            w = CaosWorldORM.objects.get(id=w_domain.id.value, is_active=True)
        except CaosWorldORM.DoesNotExist:
            return None

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid
        
        # Helper for images
        from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images, generate_breadcrumbs
        
        # --- GHOST LOGIC (Transparent '00' Bridges) ---
        # 1. Fetch ALL descendants
        all_descendants = CaosWorldORM.objects.filter(id__startswith=jid, is_active=True).exclude(id=jid).order_by('id')
        
        # Strict Workflow: DRAFTS are pending proposals and should NOT be seen in "Live" view.
        # Use Dashboard to review/approve them.
        all_descendants = all_descendants.exclude(status='DRAFT')

        # Privacy Logic (Visibility)
        if not (user and (user.is_superuser or user.is_staff)):
             all_descendants = all_descendants.filter(visible_publico=True)

        nodes_map = {d.id: d for d in all_descendants}

        # --- SOLIDIFY GHOSTS (Folder Logic) ---
        # Identify Ghosts that contain Real Children and make them SOLID (Visible)
        # This prevents "Hoisted" children from appearing in the wrong list.
        solid_ghost_ids = set()
        
        # Sort by length descending (Deepest first) to propagate solidity up
        sorted_desc = sorted(all_descendants, key=lambda x: len(x.id), reverse=True)
        
        # We need a quick lookup for immediate children existence of a specific ID?
        # Actually, implied logic: If I am Solid, I mark my parent as "Contains Solid".
        # But only if my parent is a Ghost that needs solidifying.
        
        # Helper to determine if a node is conceptually a ghost
        def is_conceptually_ghost(node):
            return node.id.endswith("00") and (node.name.startswith(("Ghost", "Nexo Fantasma")) or node.name in ("Placeholder", ""))

        solid_ids = set() # IDs that are Real OR Solid Ghosts
        
        for d in sorted_desc:
            is_ghost = is_conceptually_ghost(d)
            
            if not is_ghost:
                # Real Node: It counts as Content.
                solid_ids.add(d.id)
                # Mark parent as having content (if parent exists and is within scope)
                # Parent ID is strictly shorter.
                if len(d.id) > len(jid): 
                    # Assuming 2-char step.
                    pid = d.id[:-2]
                    # We add pid to 'needs_check' or 'solid_ids'? 
                    # Actually, if we just check "If d in solid_ids, mark parent".
                    pass
            
            # Propagation Logic
            if d.id in solid_ids:
                # If I am solid, my parent should be solid (if it's a ghost).
                if len(d.id) > len(jid):
                    pid = d.id[:-2]
                    # If we don't know if parent is ghost yet, just mark it as "containing solid".
                    # We can use a separate set "ids_with_content".
                    solid_ids.add(pid) 
                    # Wait, if parent is REAL, it's already in solid_ids (or will be).
                    # If parent is GHOST, adding it to solid_ids makes it Visible.
                    # This achieves exactly what we want.
                    
        # Now solid_ids contains everything that should be visible.
        # But we must be careful not to make '00' visible if it has NO content.

        visible_children = []
        
        for d in all_descendants:
            # RULE 1: Ghosts themselves are INVISIBLE in the list
            # Smart Ghost: Only if '00' AND name implies it's a generated ghost.
            # But if it is in solid_ids (has real content), we SHOW it.
            is_ghost_node = is_conceptually_ghost(d) and (d.id not in solid_ids)
            if is_ghost_node:
                continue

            # RULE 2: Transparency Check
            is_shadowed = False
            for l in range(len(jid) + 2, len(d.id), 2):
                intermediate_id = d.id[:l]
                
                # We check if the ancestor exists in our fetched descendants (or is the root, but root is excluded from all_descendants)
                # If ancestor is in nodes_map, we check if it is SOLID.
                ancestor = nodes_map.get(intermediate_id)
                if ancestor:
                    # If ancestor is NOT a ghost, it blocks view (Shadows the child)
                    anc_raw_ghost = is_conceptually_ghost(ancestor)
                    # If ancestor is a ghost BUT is solid (has content), it ALSO blocks view (acts as folder).
                    # So we ignore it (is transparent) ONLY if it is a NON-SOLID Ghost.
                    
                    anc_is_transparent = anc_raw_ghost and (ancestor.id not in solid_ids)
                    
                    if not anc_is_transparent:
                        is_shadowed = True
                        break
            
            if not is_shadowed:
                # Calculate levels for UI (Badge logic)
                d.visual_level = len(d.id) // 2
                
                # Relative level for context 
                parent_level = len(jid) // 2
                d.relative_level = d.visual_level - parent_level
                
                # Detect Hoisting (Materialization Opportunity)
                # If relative_level > 1, it means we skipped a level.
                if d.relative_level > 1:
                    # The immediate parent that SHOULD exist
                    d.missing_parent_id = d.id[:(parent_level + 1) * 2] 
                else:
                    d.missing_parent_id = None

                visible_children.append(d)

        # SORTING: Prioritize "Real" Branches over "Ghost" Branches (starts with '00')
        visible_children.sort(key=lambda x: (x.id[len(jid):len(jid)+2] == '00', x.id))

        hijos = []
        for h in visible_children:
            h_pid = h.public_id if h.public_id else h.id
            imgs = get_world_images(h.id)
            
            # Buscar portada
            img_url = None
            if imgs:
                cover_img = next((img for img in imgs if img.get('is_cover')), None)
                img_url = cover_img['url'] if cover_img else imgs[0]['url']
            
            # Calculate Absolute Level from JID length
            level = len(h.id) // 2
            
            # Calculate Relative Level (0 based) for indentation
            parent_level = len(jid) // 2
            relative_level = level - parent_level
            
            child_data = {
                'id': h.id, 
                'public_id': h_pid, 
                'name': h.name, 
                'short': h.id[len(jid):], 
                'img': img_url,
                'images': [i['url'] for i in imgs][:5] if imgs else [],
                'level': level,
                'relative_level': relative_level,
                'missing_parent_id': getattr(h, 'missing_parent_id', None)
            }
            
            hijos.append(child_data)

        # 4. Get Images
        imgs = get_world_images(jid)
        
        # 5. Get Metadata
        meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
        
        # 6. Get Version Info
        last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
        date_live = last_live.created_at if last_live else w.created_at
        
        props = w.versiones.filter(status='PENDING').order_by('-created_at')
        historial = w.versiones.exclude(status='PENDING').order_by('-created_at')

        # 7. Construct Permission Flags
        is_author = (user and w.author == user)
        is_super = (user and user.is_superuser)
        is_subadmin = False
        try:
            if user and hasattr(user, 'profile') and user.profile.boss == w.author:
                is_subadmin = True
        except: pass
        
        can_edit = (is_author or is_super or is_subadmin)

        # 8. Construct Result Dict
        return {
            'name': w.name, 
            'description': w.description, 
            'jid': jid, 
            'id_codificado': jid,  # Referencia al J-ID para compatibilidad de componentes JS
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
            'metadata_obj': w.metadata, 
            'imagenes': imgs, 
            'imagenes': imgs, 
            'hijos': hijos, 
            'breadcrumbs': generate_breadcrumbs(jid), 
            'propuestas': props, 
            'historial': historial,
            'is_preview': False,
            'can_edit': can_edit
        }
