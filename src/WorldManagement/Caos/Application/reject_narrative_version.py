from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class RejectNarrativeVersionUseCase:
    def execute(self, version_id: int, reason: str = ""):
        try:
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            if version.status not in ['PENDING', 'APPROVED']:
                raise Exception("No se puede rechazar esta versión.")
            
            version.status = 'REJECTED'
            if reason:
                version.admin_feedback = reason
            version.save()
            
            # If the rejected version was a CREATION proposal (ADD), delete the parent narrative
            # because it was never approved to exist.
            if version.action == 'ADD':
                print(f" 🗑️ Rechazo de creación: Eliminando narrativa {version.narrative.nid}")
                version.narrative.delete()
            
            print(f" ❌ Versión narrativa v{version.version_number} RECHAZADA.")
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("Versión narrativa no encontrada.")
