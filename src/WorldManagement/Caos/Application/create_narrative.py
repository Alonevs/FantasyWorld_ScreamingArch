from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class CreateNarrativeUseCase:
    """
    Caso de Uso responsable de la creación de nuevas narrativas (Lore, Historias, Leyendas).
    Gestiona la asignación de identificadores jerárquicos (NID), la tipificación del 
    documento y el inicio de su ciclo de vida mediante la propuesta inicial (V1).
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None, user = None, title: str = None, content: str = None, publish_immediately: bool = False) -> str:
        """
        Crea una nueva narrativa raíz o una sub-narrativa (Capítulo/Sección).
        
        Args:
            world_id: ID del mundo al que pertenece.
            tipo_codigo: Código corto o nombre del tipo (LORE, HISTORIA, etc.).
            parent_nid: Opcional. NID del padre si es una sub-narrativa.
            user: Autor de la creación.
            title: Título inicial.
            content: Cuerpo del relato inicial.
            publish_immediately: Booleano para saltar el estado PENDIENTE (solo admins).
        """
        # Mapeo de entradas de usuario a códigos de identificador corto
        input_to_short = {
            'LORE': 'L', 'L': 'L',
            'HISTORIA': 'H', 'H': 'H',
            'CAPITULO': 'C', 'C': 'C',
            'EVENTO': 'E', 'E': 'E',
            'LEYENDA': 'M', 'M': 'M', # M de Mito/Leyenda
            'REGLA': 'R', 'R': 'R',
            'BESTIARIO': 'B', 'B': 'B'
        }
        
        # Mapeo inverso para guardar nombres legibles en la base de datos
        short_to_full = {
            'L': 'LORE', 'H': 'HISTORIA', 'C': 'CAPITULO',
            'E': 'EVENTO', 'M': 'LEYENDA', 'R': 'REGLA', 'B': 'BESTIARIO'
        }

        # Normalización del tipo propuesto
        short_code = input_to_short.get(tipo_codigo.upper(), 'L') 
        full_type = short_to_full.get(short_code, 'LORE')

        # Valores por defecto para nuevos documentos vacíos
        final_title = title if title else f"Nuevo Documento"
        final_content = content if content else "..."

        # Determinación del estado inicial según permisos
        initial_version = 1 if publish_immediately else 0
        initial_status = 'APPROVED' if publish_immediately else 'PENDING'

        # Importamos el modelo de versiones de narrativa
        from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

        if parent_nid:
            # --- CASO A: SUB-NARRATIVA (HIJO) ---
            # heredamos el contexto del padre (Mundo y Narrador)
            try:
                 padre = CaosNarrativeORM.objects.get(nid=parent_nid)
            except:
                 raise ValueError("La narrativa padre especificada no existe.")

            prefix = f"{parent_nid}{short_code}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            # Crear el registro maestro de la narrativa
            narr = CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=padre.world, 
                title=final_title, 
                content=final_content, 
                tipo=full_type,
                current_version_number=initial_version
            )
            
            # Iniciar el historial con la Propuesta V1
            CaosNarrativeVersionORM.objects.create(
                narrative=narr,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status=initial_status,
                change_log="Creación inicial de sub-narrativa",
                author=user
            )
            print(f" 📖 Sub-narrativa '{final_title}' creada con NID: {new_nid}")
            return new_nid
        else:
            # --- CASO B: NARRATIVA RAÍZ ---
            # Vinculada directamente a la Entidad (Mundo/Nivel)
            try:
                world = CaosWorldORM.objects.get(id=world_id)
            except:
                raise ValueError("La entidad vinculada no existe.")

            prefix = f"{world_id}{short_code}"
            new_nid = self.repository.get_next_narrative_id(prefix)
            
            # Crear el registro maestro
            narr = CaosNarrativeORM.objects.create(
                nid=new_nid, 
                world=world, 
                title=final_title, 
                content=final_content, 
                tipo=full_type,
                current_version_number=initial_version
            )
            
            # Iniciar el historial con la Propuesta V1
            CaosNarrativeVersionORM.objects.create(
                narrative=narr,
                proposed_title=final_title,
                proposed_content=final_content,
                version_number=1,
                status=initial_status,
                change_log="Creación inicial de lore",
                author=user
            )
            
            print(f" 📜 Narrativa raíz '{final_title}' creada con NID: {new_nid}")
            return new_nid
