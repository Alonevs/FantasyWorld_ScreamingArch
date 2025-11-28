from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM

class DeleteNarrativeUseCase:
    def execute(self, nid: str) -> str:
        try:
            narrativa = CaosNarrativeORM.objects.get(nid=nid)
            world_id = narrativa.world.id # Guardamos el ID del mundo para volver
            narrativa.delete()
            print(f" 🗑️ Narrativa {nid} eliminada.")
            return world_id
        except CaosNarrativeORM.DoesNotExist:
            raise Exception("Narrativa no encontrada.")
