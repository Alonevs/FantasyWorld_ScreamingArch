from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class CreateNarrativeUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None, user = None, title: str = None, content: str = None, publish_immediately: bool = False) -> str:
        """
        Crea una nueva narrativa o sub-narrativa (capítulo).
        Retorna el NID de la nueva narrativa.
        """
        """
        Crea una nueva narrativa o sub-narrativa (capítulo).
        Retorna el NID de la nueva narrativa.
        """
        # Map inputs to Short Codes
        input_to_short = {
            'LORE': 'L', 'L': 'L',
            'HISTORIA': 'H', 'H': 'H',
            'CAPITULO': 'C', 'C': 'C',
            'EVENTO': 'E', 'E': 'E',
            'LEYENDA': 'M', 'M': 'M', # M for Myth/Leyenda
            'REGLA': 'R', 'R': 'R',
            'BESTIARIO': 'B', 'B': 'B'
        }
        
        # Map Short Codes to Full Types (DB)
        short_to_full = {
            'L': 'LORE', 'H': 'HISTORIA', 'C': 'CAPITULO',
            'E': 'EVENTO', 'M': 'LEYENDA', 'R': 'REGLA', 'B': 'BESTIARIO'
        }

        # Normalize input
        short_code = input_to_short.get(tipo_codigo.upper(), 'L') # Default to LORE
        full_type = short_to_full.get(short_code, 'LORE')

        final_title = title if title else f"Nuevo Documento"
        final_content = content if content else "..."

        # Determine initial state
        initial_version = 1 if publish_immediately else 0
        initial_status = 'PUBLISHED' if publish_immediately else 'PENDING'
        approver = user if publish_immediately else None

        if parent_nid:
            # Es una sub-narrativa (Hijo)
            try:
                 padre = CaosNarrativeORM.objects.get(nid=parent_nid)
            except:
                 # Fallback if parent_nid is already a prefix or not found?
                 # Assuming valid NID passed or error will raise
                 padre = CaosNarrativeORM.objects.get(nid=parent_nid)

            prefix = f"{parent_nid}{short_code}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            # Create with REAL content
            narr = CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=padre.world, 
                titulo=final_title, 
                contenido=final_content, 
                narrador=padre.narrador, 
                tipo=full_type,
                created_by=user,
                current_version_number=initial_version
            )
            
            # Create Proposal V1
            from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
            CaosNarrativeVersionORM.objects.create(
                narrative=narr,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status=initial_status,
                action='ADD',
                change_log="Creación inicial",
                author=user
            )
            return new_nid
        else:
            # Es una narrativa raíz
            world = CaosWorldORM.objects.get(id=world_id)
            # Use Short Code for cleaner, shorter IDs
            prefix = f"{world_id}{short_code}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            # Create with REAL content
            narr = CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=world, 
                titulo=final_title, 
                contenido=final_content, 
                narrador="???", 
                tipo=full_type,
                created_by=user,
                current_version_number=initial_version
            )
            
            # Create Proposal V1
            from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
            CaosNarrativeVersionORM.objects.create(
                narrative=narr,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status=initial_status,
                action='ADD',
                change_log="Creación inicial",
                author=user
            )
            
            return new_nid
