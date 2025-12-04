from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class RejectNarrativeVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            if version.status not in ['PENDING', 'APPROVED']:
                raise Exception("No se puede rechazar esta versión.")
            
            version.status = 'REJECTED'
            version.save()
            print(f" ❌ Versión narrativa v{version.version_number} RECHAZADA.")
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("Versión narrativa no encontrada.")
