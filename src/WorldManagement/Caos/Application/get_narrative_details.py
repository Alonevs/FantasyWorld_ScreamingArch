from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class GetNarrativeDetailsUseCase:
    """
    Caso de Uso responsable de recuperar el contenido completo de una narrativa.
    Gestiona la transparencia de borradores (mostrando propuestas V1 a autores),
    el contexto de entidades mencionadas y la estructura de capítulos hijos.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, nid: str, user=None):
        # 1. Resolución de la Narrativa (NanoID o NID)
        try:
            # Primero intentamos resolver por el Identificador Público (NanoID)
            try:
                narr = CaosNarrativeORM.objects.get(public_id=nid)
            except:
                # Si no, recurrimos al Identificador Interno Jerárquico (NID)
                narr = CaosNarrativeORM.objects.get(nid=nid)
                
            # --- GESTIÓN DE BORRADORES (V0) ---
            # Si una narrativa tiene versión 0, significa que aún no ha sido aprobada ni publicada.
            if narr.current_version_number == 0:
                # Solo el autor o un administrador pueden ver este contenido "fantasma"
                is_authorized = user and (user.is_superuser or getattr(narr, 'created_by', None) == user)
                if not is_authorized:
                    print(f"🔒 Acceso denegado a narrativa en borrador: {nid}")
                    return None
                
                # Para mostrar el contenido en borrador, recuperamos los textos de la Propuesta V1
                from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM
                try:
                    v1 = CaosNarrativeVersionORM.objects.get(narrative=narr, version_number=1)
                    # "Inyectamos" el título y contenido propuesto en el objeto para que el template lo pinte
                    narr.titulo = v1.proposed_title
                    narr.contenido = v1.proposed_content
                    narr.is_draft = True # Indicador visual para la interfaz
                except CaosNarrativeVersionORM.DoesNotExist:
                    # Caso de seguridad por si la propuesta se perdió: marcamos como borrador vacío
                    narr.is_draft = True
                    
        except Exception as e:
            print(f"❌ Error al recuperar detalles de la narrativa '{nid}': {e}")
            return None

        # 2. Recopilación de Datos de Contexto
        # Obtenemos todas las entidades para posibles menciones o enlaces rápidos
        # TODO: Optimizar si la base de datos de mundos crece demasiado.
        todas = CaosWorldORM.objects.all().order_by('id')
        
        # 3. Resolución de Capítulos (Hijos Jerárquicos)
        # Buscamos todas las narrativas cuyo NID empiece por el NID actual (Estructura de Carpeta)
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
        
        # Filtramos para mostrar solo los capítulos que ya han sido publicados (Versión > 0)
        published_chapters = hijos.filter(current_version_number__gt=0)
        
        return {
            'narr': narr,
            'todas_entidades': todas,
            'published_chapters': published_chapters
        }
