from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.Shared.Domain import eclai_core
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
        
        # 3. Get Children
        len_h = len(jid) + 2
        raw_hijos = CaosWorldORM.objects.filter(id__startswith=jid, id__regex=r'^.{'+str(len_h)+r'}$').order_by('id')
        
        # Filter DRAFTs to ensure Live view only shows approved items
        # if user and not user.is_superuser: (Removed user check to enforce strict view)
        raw_hijos = raw_hijos.exclude(status='DRAFT')
        
        # Helper for images (this logic is currently in utils, we can import it or replicate)
        from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images, generate_breadcrumbs
        
        hijos = []
        hijos = []
        
        # --- DIRECT LINK / PADDED CHILDREN LOGIC ---
        # We need to find all descendants that conceptually belong to THIS parent.
        # This includes:
        # 1. Direct children (len = parent + 2)
        # 2. Deep children (len > parent + 2) whose intermediate ancestors DO NOT EXIST.
        
        # Fetch all descendants
        all_descendants = CaosWorldORM.objects.filter(id__startswith=jid, is_active=True).exclude(id=jid).exclude(status='DRAFT').order_by('id')
        
        # Build a set of existing IDs for fast "parent exists" check
        existing_ids = set(d.id for d in all_descendants)
        existing_ids.add(jid) # Parent exists obviously
        
        visible_children = []
        
        for d in all_descendants:
            # Check "Immediate Parent"
            # If my logical parent exists in the set, then I am NOT a direct child of 'jid' (I belong to them).
            # If my logical parent DOES NOT exist, then I am orphaned -> show me here.
            
            # Determine logical parent ID (slice off last segment)
            # Segments: usually 2 chars. Level 16 (Entity) might be 4 chars.
            # We can try assuming 2 chars removal first.
            # ID: ...0101 -> Parent: ...01 (exists?)
            # ID: ...000001 -> Parent: ...0000 (does not exist?) -> GranParent: ...00 (no) -> JID (yes)
            
            # Simplified logic:
            # Cut off 2 chars. If result exists in `existing_ids` AND result != jid, then this entity has a closer parent.
            # So hide it.
            # If result == jid, show it (direct child).
            # If result not in existing_ids, try cutting 4 chars?
            # Actually, we just need to know if there is ANY ancestor between JID and Child.
            
            # Better approach:
            # Iterate potential ancestors from JID_LEN + 2 up to CHILD_LEN - 2.
            # If any of those IDs exist in `existing_ids`, then this child is shadowed.
            
            is_shadowed = False
            # Check for regular intermediate ancestors (step 2)
            for l in range(len(jid) + 2, len(d.id), 2):
                intermediate_id = d.id[:l]
                if intermediate_id in existing_ids:
                    is_shadowed = True
                    break
            
            if not is_shadowed:
                visible_children.append(d)

        for h in visible_children:
            h_pid = h.public_id if h.public_id else h.id
            imgs = get_world_images(h.id)
            
            # Buscar portada primero, luego primera imagen
            img_url = None
            if imgs:
                cover_img = next((img for img in imgs if img.get('is_cover')), None)
                img_url = cover_img['url'] if cover_img else imgs[0]['url']
            
            # Determine if it's a deep/padded child for UI hint
            is_deep = (len(h.id) > len(jid) + 2) and (len(h.id) != 34) # Exclude standard Level 16 if parent is 15 (len 30->34)
            # Actually level 16 logic: 30 chars -> 34 chars. +4.
            # Just comparing len > len(jid)+2 is decent indicator of "something special" or deep.
            
            hijos.append({
                'id': h.id, 
                'public_id': h_pid, 
                'name': h.name, 
                'short': h.id[len(jid):], 
                'img': img_url,
                'is_hoisted': is_deep
            })

        # 4. Get Images
        imgs = get_world_images(jid)
        
        # 5. Get Metadata
        meta_str = json.dumps(w.metadata, indent=2) if w.metadata else "{}"
        
        # 6. Get Version Info
        last_live = w.versiones.filter(status='LIVE').order_by('-created_at').first()
        date_live = last_live.created_at if last_live else w.created_at
        
        props = w.versiones.filter(status='PENDING').order_by('-created_at')
        historial = w.versiones.exclude(status='PENDING').order_by('-created_at')

        # 7. Construct Result Dict
        return {
            'name': w.name, 
            'description': w.description, 
            'jid': jid, 
            'id_codificado': w.id_codificado,  # NUEVO: Para Auto-Noos correcto
            'public_id': safe_pid,
            'status': w.status, 
            'version_live': w.current_version_number,
            'author_live': getattr(w, 'current_author_name', 'Sistema'),
            'created_at': w.created_at, 
            'updated_at': date_live,
            'visible': w.visible_publico, 
            'is_locked': w.is_locked, 
            'code_entity': eclai_core.encode_eclai126(jid),
            'nid_lore': w.id_lore, 
            'metadata': meta_str, 
            'metadata_obj': w.metadata, 
            'imagenes': imgs, 
            'hijos': hijos, 
            'breadcrumbs': generate_breadcrumbs(jid), 
            'propuestas': props, 
            'historial': historial,
            'is_preview': False
        }
