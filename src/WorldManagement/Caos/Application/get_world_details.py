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
            w = CaosWorldORM.objects.get(id=w_domain.id.value)
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
        for h in raw_hijos:
            h_pid = h.public_id if h.public_id else h.id
            imgs = get_world_images(h.id)
            
            # Buscar portada primero, luego primera imagen
            img_url = None
            if imgs:
                # Intentar encontrar la imagen de portada
                cover_img = next((img for img in imgs if img.get('is_cover')), None)
                img_url = cover_img['url'] if cover_img else imgs[0]['url']
            
            hijos.append({
                'id': h.id, 
                'public_id': h_pid, 
                'name': h.name, 
                'short': h.id[len(jid):], 
                'img': img_url
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
