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
        
        # --- SHARED 00 LOGIC (Global Shared Trunk) ---
        # The '00' branch at the Root level (e.g. 0100...) serves as a repository for Shared Entities.
        # These entities should be visible to ALL cousins at the SAME LEVEL.
        # Logic: If I am at Level L, I should see:
        # 1. My Direct Children (010101 -> 010101XX)
        # 2. Shared Children from Root-00 (0100 -> 0100XX matching my child depth)

        if len(jid) >= 2:
            root_id = jid[:2]
            shared_trunk = root_id + "00"
            
            # Helper to check if we should look for shared items
            # We don't need to look if we ARE inside the shared trunk (already found by starts_with jid)
            # Unless we want to find siblings in the same shared folder? Yes.
            
            # Fetch candidates from Trunk logic
            # We filter in Python or DB? DB is better.
            # We need items starting with shared_trunk AND length == len(jid) + 2
            
            # Note: This replaces the previous "Parent+00" logic which was too local.
            # Now 'onda' (L4) will be found by 'Universo' (L3) because it looks at Root-00.
            
            trunk_descendants = CaosWorldORM.objects.filter(id__startswith=shared_trunk, is_active=True)
            
            # Filter by EXACT Child Level match
            target_len = len(jid) + 2
            
            # Optimization: If we can filter by length in DB. SQLite/Postgres support length lookup?
            # Creating a list ID list is safer.
            # Or filter in python (trunk is usually small compared to full DB, but maybe large for huge worlds).
            # Let's filter in python loop below or add to all_descendants and filter later.
            # Actually, `all_descendants` loop calculates relativity.
            # So just ADDING them is enough?
            # Loop (Line 101) checks:
            # - `is_tuple_ghost` -> continue
            # - `relative_level` logic:
            #   `d.relative_level = level - parent_level`
            #   If `relative_level == 1`, accepted.
            #   If `relative_level > 1` (JUMP), accepted? 
            #   Currently `relative_level` uses `level = len(d.id)//2`.
            #   If I am `Universo` (L3). `onda` (L4). `relative_level = 4 - 3 = 1`.
            #   So it will be accepted as a child!
            
            #   If I am `Abismo` (L2). `onda` (L4). `relative_level = 4 - 2 = 2`.
            #   Is `relative_level > 1` accepted?
            #   My "Rule 4" (which I added then removed) blocked it.
            #   I should Restore Rule 4 to block it in Abismo.
            
            # So: Merge Trunk Descendants + Restore Rule 4.
            all_descendants = all_descendants | trunk_descendants
                
        # Deduplicate (just in case) and Order
        all_descendants = all_descendants.distinct().order_by('id')

        # Strict Workflow: DRAFTS are pending proposals and should NOT be seen in "Live" view.
        # Use Dashboard to review/approve them.
        all_descendants = all_descendants.exclude(status='DRAFT')

        # Privacy Logic (Visibility)
        # Check against Django Superuser OR Profile Rank (Admin/SubAdmin)
        is_global_admin = False
        if user and user.is_authenticated:
             if user.is_superuser or user.is_staff:
                 is_global_admin = True
             elif hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']:
                 is_global_admin = True
        
        # NOTE: We keep DRAFT exclusion global for now as per "Strict Workflow". 
        # But for visibility of LIVE/OFFLINE/LOCKED items:
        if not is_global_admin:
             # Regular users/Collaborators might see their own private content?
             # For now, simplistic approach: If not admin, filter by public.
             # (TODO: Add 'is_author' check for children if needed)
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
        
        # Helper to determine if a node is conceptually a ghost (Aggressive Case-Insensitive)
        def is_conceptually_ghost(node):
            name_lower = node.name.lower()
            is_generic = "nexo" in name_lower or "ghost" in name_lower or "fantasma" in name_lower or node.name in ("Placeholder", "")
            return node.id.endswith("00") and is_generic

        solid_ids = set() # IDs that are Real OR Solid Ghosts
        
        for d in sorted_desc:
            is_ghost = is_conceptually_ghost(d)
            
            if not is_ghost:
                # Real Node: It counts as Content.
                solid_ids.add(d.id)
                # Mark parent as having content
                if len(d.id) > len(jid): 
                   # Implicitly solidifies parents in next pass? 
                   # No, we need explicit propagation or rely on checks.
                   pass
            
            # Propagation Logic: If I am solid, my parent is solid container
            if d.id in solid_ids:
                if len(d.id) > len(jid):
                    pid = d.id[:-2]
                    solid_ids.add(pid) 

        visible_children = []
        
        for d in all_descendants:
            # RULE 1: Ghosts themselves are ALWAYS INVISIBLE now (User Request)
            # regardless of whether they have content. They are just structural glue.
            if is_conceptually_ghost(d):
                continue

            # RULE 2: Transparency Check
            is_shadowed = False
            for l in range(len(jid) + 2, len(d.id), 2):
                intermediate_id = d.id[:l]
                
                ancestor = nodes_map.get(intermediate_id)
                if ancestor:
                    # If ancestor is NOT a ghost, it blocks view (Shadows the child)
                    anc_ghost = is_conceptually_ghost(ancestor)
                    
                    # If ancestor is a Ghost, it is ALWAYS TRANSPARENT now.
                    # It does not block children, because the ghost itself is hidden.
                    # So we only block if ancestor is REAL (not ghost).
                    if not anc_ghost:
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
                    missing_pid = d.id[:(parent_level + 1) * 2] 
                    
                    # If missing parent is a '00' (Ghost Bridge), it's NOT an orphan, it's a Feature (Jump).
                    if missing_pid.endswith("00"):
                        d.missing_parent_id = None
                    else:
                         d.missing_parent_id = missing_pid
                else:
                    d.missing_parent_id = None
                
                # RULE 3: Hide '00' (Shared) children from the Direct Parent view.
                # User Request: "no quiero que se visualice ahi (en hijos de 01)"
                if d.id.startswith(jid + '00'):
                    continue

                # RULE 4: Strict Relative Level 1.
                # "Jerarquia funciona en todas las posibilidades".
                # We strictly ONLY show entities that are exactly 1 level deeper.
                # This fixes:
                # - Hiding L4 ('onda') from L2 ('Abismo') -> Rel = 2.
                # - Hiding L3 ('mi house') from L3 ('Universo') -> Rel = 0 (Siblings).
                # - Showing L3 ('mi house') in L2 ('Abismo') -> Rel = 1.
                if d.relative_level != 1:
                    continue
                
                visible_children.append(d)


        hijos = []
        for h in visible_children:
            h_pid = h.public_id if h.public_id else h.id
            imgs = get_world_images(h.id)
            
            # Buscar portada
            img_url = None
            if imgs:
                cover_img = next((img for img in imgs if img.get('is_cover')), None)
                img_url = cover_img['url'] if cover_img else imgs[0]['url']
            
            level = len(h.id) // 2
            parent_level = len(jid) // 2
            relative_level = level - parent_level
            
            # Check for Jumped/Shared status
            is_jumped = False
            # Check 1: '00' Middle Segment
            if len(h.id) > 2:
                for i in range(len(jid), len(h.id)-2, 2):
                    if h.id[i:i+2] == '00':
                        is_jumped = True
                        break
            
            # Check 2: Level Skip
            if relative_level > 1:
                is_jumped = True

            # Check 3: ID Mismatch (Shared Cousin)
            # If the child ID does not start with the current Page ID, it means it is a Shared/Injected entity.
            # Example: Viewing 0101 (Universo), seeing 010013 (Mi House).
            if not h.id.startswith(jid):
                is_jumped = True

            child_data = {
                'id': h.id, 
                'public_id': h_pid, 
                'name': h.name, 
                'short': h.id[len(jid):], 
                'img': img_url,
                'images': [i['url'] for i in imgs][:5] if imgs else [],
                'level': level,
                'relative_level': relative_level,
                'missing_parent_id': getattr(h, 'missing_parent_id', None),
                'is_jumped': is_jumped
            }
            
            hijos.append(child_data)

        # FINAL SORT: Prioritize Direct Children (False) over Shared/Jumped (True).
        # WITHIN Shared: Sort by Level (Shallower first) then ID.
        # This solves "onda" (L4) appearing before "mi house" (L3).
        hijos.sort(key=lambda x: (x['is_jumped'], x['level'], x['id']))

        # 4. Get Images
        imgs = get_world_images(jid)
        
        # 5. Get Metadata
        meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
        
        # 6. Get Version Info
        last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
        date_live = last_live.created_at if last_live else w.created_at
        
        props = w.versiones.filter(status='PENDING').order_by('-created_at')
        historial = w.versiones.exclude(status='PENDING').order_by('-created_at')

        # 7. Get Schema (to show empty tables in UI)
        schema = None
        try:
            from src.WorldManagement.Caos.Domain.metadata_router import get_schema_for_hierarchy
            level = len(jid) // 2
            schema = get_schema_for_hierarchy(jid, level)
        except Exception as e:
            print(f"Error resolving schema in GetWorldDetails: {e}")

        # 8. Construct Permission Flags
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
            'metadata_schema': schema,
            'imagenes': imgs, 
            'hijos': hijos, 
            'breadcrumbs': generate_breadcrumbs(jid), 
            'propuestas': props, 
            'historial': historial,
            'is_preview': False,
            'can_edit': can_edit
        }
