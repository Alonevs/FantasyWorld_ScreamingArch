from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class CreateNarrativeUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None) -> str:
        """
        Crea una nueva narrativa o sub-narrativa (capítulo).
        Retorna el NID de la nueva narrativa.
        """
        map_tipos = {'L':'LORE', 'H':'HISTORIA', 'C':'CAPITULO', 'E':'EVENTO', 'M':'LEYENDA', 'R':'REGLA', 'B':'BESTIARIO'}
        
        if parent_nid:
            # Es una sub-narrativa (Capítulo)
            padre = CaosNarrativeORM.objects.get(nid=parent_nid)
            prefix = f"{parent_nid}{tipo_codigo}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            tipo_completo = 'CAPITULO'
            # TODO: Mover creación de ORM al repositorio en el futuro
            CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=padre.world, 
                titulo=f"Nuevo Capítulo ({new_nid[-2:]})", 
                contenido="...", 
                narrador=padre.narrador, 
                tipo=tipo_completo
            )
            return new_nid
        else:
            # Es una narrativa raíz
            world = CaosWorldORM.objects.get(id=world_id)
            prefix = f"{world_id}{tipo_codigo}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            tipo_completo = map_tipos.get(tipo_codigo, 'LORE')
            CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=world, 
                titulo=f"Nuevo {tipo_completo} ({new_nid[-2:]})", 
                contenido="...", 
                narrador="???", 
                tipo=tipo_completo
            )
            return new_nid
