from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class GetWorldNarrativesUseCase:
    """
    Caso de Uso responsable de listar y organizar jerárquicamente todos los 
    documentos de lore (Narrativas) asociados a una entidad.
    Construye una estructura de "bosque" (árboles anidados) y clasifica los 
    documentos raíz por su tipo (Lore, Historia, Leyenda, etc.).
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str, user=None, period_slug=None):
        # 1. Resolución de la Entidad (Mundo/Nivel)
        w_domain = resolve_world_id(self.repository, identifier)
        if not w_domain:
            return None

        try:
            w = CaosWorldORM.objects.get(id=w_domain.id.value)
        except CaosWorldORM.DoesNotExist:
            return None

        # 2. Recuperación de Documentos
        # Obtenemos todas las narrativas vinculadas a este mundo.
        docs = w.narrativas.all()
        
        # FILTRADO POR PERÍODO
        if period_slug and period_slug != 'actual':
            docs = docs.filter(timeline_period__slug=period_slug)
        else:
            # Vista ACTUAL o por defecto (nulo o 'actual')
            from django.db.models import Q
            docs = docs.filter(Q(timeline_period__isnull=True) | Q(timeline_period__slug='actual'))

        # Regla de Negocio: Los borradores (Versión 0) se excluyen de la lista pública.
        # Solo se muestran documentos que tengan al menos una versión aprobada y publicada,
        # a menos que el usuario sea el autor del mundo o un administrador.
        # FILTERING:
        # Show ONLY Published/Live narratives (version > 0).
        # Pending proposals (version 0) are now exclusive to the Dashboard.
        docs = docs.filter(current_version_number__gt=0)
        
        # Calculate 'is_new' attribute for UI Badge (Last 3 days)
        # AND check if user has already seen it
        from django.utils import timezone
        from datetime import timedelta
        threshold = timezone.now() - timedelta(days=3)
        
        visited_ids = set()
        if user and user.is_authenticated:
            # Clean Architecture: Use repository instead of direct ORM access
            visited_ids = self.repository.get_visited_narrative_ids(user)

        for d in docs:
            # is_new only if recent AND NOT visited
            is_recent = d.updated_at >= threshold
            has_seen = (d.public_id in visited_ids) or (d.nid in visited_ids)
            d.is_new = is_recent and not has_seen

        # Convertimos a lista y ordenamos por NID (Identificador Jerárquico)
        # El orden natural del NID asegura que los padres aparezcan antes que sus hijos.
        all_docs = list(docs)
        all_docs.sort(key=lambda x: x.nid)
        
        # 3. Construcción del Bosque Jerárquico (Árboles anidados)
        # Procesamos linealmente usando una pila (stack) para gestionar la profundidad.
        roots = []
        stack = [] # Pila de narrativas que actúan como contenedores actuales
        
        # Inicializamos la lista de hijos para cada nodo
        for d in all_docs:
            d.children = []

        for node in all_docs:
            # Si el nodo actual no es hijo del nodo en la cima de la pila, sacamos elementos.
            while stack:
                potential_parent = stack[-1]
                # Comprobación de contención jerárquica estricta
                if node.nid.startswith(potential_parent.nid) and node.nid != potential_parent.nid:
                    # El nodo actual ES un hijo (Capítulo/Sección) del potencial padre
                    potential_parent.children.append(node)
                    stack.append(node) # El hijo ahora puede ser padre de niveles más profundos
                    break
                else:
                    # No es hijo, el contenedor actual está "cerrado" para este nodo
                    stack.pop()
            
            if not stack:
                # Si la pila está vacía, el nodo es una raíz (Documento Principal)
                roots.append(node)
                stack.append(node)
        
        # 4. Clasificación por Tipo (Categorización en la Interfaz)
        # Los hijos ya están anidados dentro de sus padres, así que solo clasificamos las raíces.
        lores = []
        historias = []
        eventos = []
        leyendas = []
        reglas = []
        bestiario = []
        otros = [] # Categoría de seguridad para tipos desconocidos

        for r in roots:
            if r.tipo == 'LORE': lores.append(r)
            elif r.tipo == 'HISTORIA': historias.append(r)
            elif r.tipo == 'EVENTO': eventos.append(r)
            elif r.tipo == 'LEYENDA': leyendas.append(r)
            elif r.tipo == 'REGLA': reglas.append(r)
            elif r.tipo == 'BESTIARIO': bestiario.append(r)
            else: otros.append(r)

        # Normalización: Si un capítulo aparece como raíz (huérfano), lo tratamos como historia por defecto.
        for r in otros:
             if getattr(r, 'tipo', '') == 'CAPITULO': historias.append(r)
        
        # 5. Obtener objeto del período actual para el contexto
        viewing_period = None
        if period_slug and period_slug != 'actual':
             from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
             viewing_period = TimelinePeriod.objects.filter(world=w, slug=period_slug).first()

        # 6. Calcular permisos para mostrar botones de creación
        is_author = (user and w.author == user)
        is_admin_role = user and (user.is_superuser or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']))
        
        # Check if user can propose on this world
        from src.Infrastructure.DjangoFramework.persistence.policies import can_user_propose_on
        allow_proposals = can_user_propose_on(user, w) if user else False

        return {
            'world': w,
            'lores': lores,
            'historias': historias,
            'eventos': eventos,
            'leyendas': leyendas,
            'reglas': reglas,
            'bestiario': bestiario,
            'viewing_period': viewing_period,
            'is_author': is_author,
            'is_admin_role': is_admin_role,
            'allow_proposals': allow_proposals
        }
