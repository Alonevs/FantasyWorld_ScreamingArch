from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class RestoreNarrativeVersionUseCase:
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperamos la versión antigua
            target_version = CaosNarrativeVersionORM.objects.get(id=version_id)
            
            # 2. "Revivimos" la versión existente
            target_version.status = 'PENDING'
            
            # 3. Actualizamos el log y el autor
            target_version.change_log = f"ROLLBACK: Restauración forzada desde la versión {target_version.version_number}"
            target_version.author = user
            
            target_version.save()
            
            print(f" ⏪ Restauración Narrativa completada: v{target_version.version_number} vuelve a estado PENDING.")
            
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("Versión narrativa no encontrada.")
