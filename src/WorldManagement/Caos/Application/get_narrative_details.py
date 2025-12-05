from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class GetNarrativeDetailsUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, nid: str, user=None):
        # 1. Resolve Narrative
        try:
            # Try public_id first if it looks like a NanoID
            if len(nid) <= 12 and ('-' in nid or '_' in nid):
                try:
                    narr = CaosNarrativeORM.objects.get(public_id=nid)
                except CaosNarrativeORM.DoesNotExist:
                    narr = CaosNarrativeORM.objects.get(nid=nid)
            else:
                narr = CaosNarrativeORM.objects.get(nid=nid)
                
            # --- VERSION 0 (DRAFT) HANDLING ---
            if narr.current_version_number == 0:
                # Only show to author or admin
                is_authorized = user and (user.is_superuser or narr.created_by == user)
                if not is_authorized:
                    print(f"🔒 Acceso denegado a borrador {nid}")
                    return None
                
                # Fetch the pending V1 proposal
                from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
                try:
                    v1 = CaosNarrativeVersionORM.objects.get(narrative=narr, version_number=1)
                    # Swap content for display
                    narr.titulo = v1.proposed_title
                    narr.contenido = v1.proposed_content
                    narr.is_draft = True # Flag for template
                except CaosNarrativeVersionORM.DoesNotExist:
                    # Should not happen if created correctly, but fallback
                    narr.is_draft = True
                    
        except Exception as e:
            print(f"❌ Error al leer narrativa '{nid}': {e}")
            return None

        # 2. Get Context Data
        # Fetch all worlds for mentions/linking (this might be heavy, optimization needed later)
        todas = CaosWorldORM.objects.all().order_by('id')
        
        # Fetch chapters (children)
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
        
        # Only show published chapters (version > 0)
        published_chapters = hijos.filter(current_version_number__gt=0)
        
        return {
            'narr': narr,
            'todas_entidades': todas,
            'published_chapters': published_chapters
        }
