from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class GetWorldNarrativesUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str, user=None):
        # 1. Resolve World
        w_domain = resolve_world_id(self.repository, identifier)
        if not w_domain:
            return None

        try:
            w = CaosWorldORM.objects.get(id=w_domain.id.value)
        except CaosWorldORM.DoesNotExist:
            return None

        # 2. Get All Narratives
        # Fetch everything. We DO NOT exclude CAPITULO here because they might be top level? 
        # Actually usually chapters are children, but if they are orphaned they should appear somewhere.
        docs = w.narrativas.all()
        
        # Filter out drafts (version 0). They only appear in Dashboard or via direct link.
        docs = docs.filter(current_version_number__gt=0)

        # Convert to list for processing
        all_docs = list(docs)
        
        # Sort by NID
        all_docs.sort(key=lambda x: x.nid)
        
        # Build Forest (Unified Tree)
        # We process linearly. Since sorted by NID, potential parents always appear before children.
        roots = []
        stack = [] # list of narratives acting as current open pointers
        
        # Initialize children for everyone
        for d in all_docs:
            d.children = []

        for node in all_docs:
            # Pop from stack if node is not a child of stack top
            while stack:
                potential_parent = stack[-1]
                # Check strict containment: node.nid starts with potential_parent.nid AND is longer
                if node.nid.startswith(potential_parent.nid) and node.nid != potential_parent.nid:
                    # It IS a child.
                    potential_parent.children.append(node)
                    stack.append(node) # This node acts as parent for potential deeper nodes
                    break
                else:
                    # Not a child of this parent
                    stack.pop()
            
            if not stack:
                # It's a root
                roots.append(node)
                stack.append(node)
        
        # Categorize ROOTS by type
        # Children are already nested inside these roots, so we only care about roots for the main lists.
        lores = []
        historias = []
        eventos = []
        leyendas = []
        reglas = []
        bestiario = []
        otros = [] # Fallback

        for r in roots:
            if r.tipo == 'LORE': lores.append(r)
            elif r.tipo == 'HISTORIA': historias.append(r)
            elif r.tipo == 'EVENTO': eventos.append(r)
            elif r.tipo == 'LEYENDA': leyendas.append(r)
            elif r.tipo == 'REGLA': reglas.append(r)
            elif r.tipo == 'BESTIARIO': bestiario.append(r)
            else: otros.append(r) # CAPITULO roots? Should technically be HISTORIA usually.

        # Note: If a root is a CAPITULO, we might want to show it in historias or others. 
        # But usually CAPITULO is child. If it's root, it's orphan or wrong type.
        # Let's add orphans to historias for visibility if needed, or misc.
        # For now, append unknown/other types to 'historias' as generic? Or better 'otros'?
        # Let's map CAPITULO roots to historias to be safe.
        for r in otros:
             if r.tipo == 'CAPITULO': historias.append(r)
        
        return {
            'world': w,
            'lores': lores,
            'historias': historias,
            'eventos': eventos,
            'leyendas': leyendas,
            'reglas': reglas,
            'bestiario': bestiario
        }
