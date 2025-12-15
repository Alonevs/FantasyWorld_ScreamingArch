from datetime import datetime
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class EntityService:
    """
    Servicio Unificado para la gestión del ciclo de vida de Entidades (Creación, etc).
    Centraliza la lógica de UseCases y asegura consistencia.
    """
    def __init__(self):
        self.repo = DjangoCaosRepository()
        self.creator = CreateChildWorldUseCase(self.repo)

    def create_entity(self, parent_id: str, name: str, description: str, reason: str, generate_image: bool = False, target_level: int = None) -> str:
        """
        Crea una nueva entidad hija (o raíz si parent_id es adecuado).
        Usa lógica de Padding y Proposals.
        """
        return self.creator.execute(
            parent_id=parent_id,
            name=name,
            description=description,
            reason=reason,
            generate_image=generate_image,
            target_level=target_level
        )

    def soft_delete_entity(self, jid: str, user=None) -> bool:
        """
        Aplica Soft Delete a una entidad.
        """
        try:
            w = CaosWorldORM.objects.get(id=jid)
            w.soft_delete()
            return True
        except Exception as e:
            print(f"Error Soft Delete: {e}")
            return False
