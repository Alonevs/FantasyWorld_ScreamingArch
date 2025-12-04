from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosWorldORM
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase

class RestoreVersionUseCase:
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperamos la versión antigua
            target_version = CaosVersionORM.objects.get(id=version_id)
            
            # 2. "Revivimos" la versión existente en lugar de crear una copia
            # Esto mantiene el número de versión original (ej: v29)
            target_version.status = 'PENDING'
            
            # 3. Actualizamos el log y el autor de la restauración
            # Usamos el formato solicitado por el usuario
            target_version.change_log = f"ROLLBACK: Restauración forzada desde la versión {target_version.version_number}"
            target_version.author = user
            
            target_version.save()
            
            print(f" ⏪ Restauración completada: v{target_version.version_number} vuelve a estado PENDING.")
            
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada.")
