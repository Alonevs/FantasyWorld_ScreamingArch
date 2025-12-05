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

        # 2. Get Narratives
        docs = w.narrativas.exclude(tipo='CAPITULO')
        
        # Filter out drafts (version 0) for unauthorized users
        if not user or not user.is_superuser:
            # If user is logged in, they can see their own drafts
            if user and user.is_authenticated:
                from django.db.models import Q
                docs = docs.filter(Q(current_version_number__gt=0) | Q(created_by=user))
            else:
                docs = docs.filter(current_version_number__gt=0)
        
        return {
            'world': w,
            'lores': docs.filter(tipo='LORE'),
            'historias': docs.filter(tipo='HISTORIA'),
            'eventos': docs.filter(tipo='EVENTO'),
            'leyendas': docs.filter(tipo='LEYENDA'),
            'reglas': docs.filter(tipo='REGLA'),
            'bestiario': docs.filter(tipo='BESTIARIO')
        }
