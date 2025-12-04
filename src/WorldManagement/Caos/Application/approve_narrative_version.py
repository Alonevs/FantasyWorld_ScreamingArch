from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class ApproveNarrativeVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            if version.status != 'PENDING':
                raise Exception("Solo se pueden aprobar versiones PENDIENTES.")
            
            version.status = 'APPROVED'
            version.save()
            print(f" ✅ Versión narrativa v{version.version_number} APROBADA.")
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("Versión narrativa no encontrada.")
