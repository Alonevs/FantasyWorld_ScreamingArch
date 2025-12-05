from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class CreateNarrativeUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None, user = None, title: str = None, content: str = None) -> str:
        """
        Crea una nueva narrativa o sub-narrativa (capítulo).
        Retorna el NID de la nueva narrativa.
        """
        map_tipos = {'L':'LORE', 'H':'HISTORIA', 'C':'CAPITULO', 'E':'EVENTO', 'M':'LEYENDA', 'R':'REGLA', 'B':'BESTIARIO'}
        
        final_title = title if title else f"Nuevo Documento"
        final_content = content if content else "..."

        if parent_nid:
            # Es una sub-narrativa (Capítulo)
            padre = CaosNarrativeORM.objects.get(nid=parent_nid)
            prefix = f"{parent_nid}{tipo_codigo}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            tipo_completo = 'CAPITULO'
            # Create with PLACEHOLDER content and version 0
            CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=padre.world, 
                titulo=f"Borrador: {final_title}", 
                contenido="Contenido pendiente de aprobación...", 
                narrador=padre.narrador, 
                tipo=tipo_completo,
                created_by=user,
                current_version_number=0 # Indicates Draft/Pending
            )
            
            # Create Proposal V1 with REAL content
            from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
            CaosNarrativeVersionORM.objects.create(
                narrative_id=new_nid,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status='PENDING',
                action='ADD',
                change_log="Creación inicial",
                author=user
            )
            return new_nid
        else:
            # Es una narrativa raíz
            world = CaosWorldORM.objects.get(id=world_id)
            prefix = f"{world_id}{tipo_codigo}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            tipo_completo = map_tipos.get(tipo_codigo, 'LORE')
            
            # Create with PLACEHOLDER content and version 0
            narr = CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=world, 
                titulo=f"Borrador: {final_title}", 
                contenido="Contenido pendiente de aprobación...", 
                narrador="???", 
                tipo=tipo_completo,
                created_by=user,
                current_version_number=0 # Indicates Draft/Pending
            )
            
            # Create Proposal V1 with REAL content
            from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
            CaosNarrativeVersionORM.objects.create(
                narrative=narr,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status='PENDING',
                action='ADD',
                change_log="Creación inicial",
                author=user
            )
            
            return new_nid
