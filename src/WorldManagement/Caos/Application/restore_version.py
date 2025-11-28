from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosWorldORM
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase

class RestoreVersionUseCase:
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperamos la versión antigua (la copia de seguridad)
            target_version = CaosVersionORM.objects.get(id=version_id)
            world = target_version.world
            
            # 2. Preparamos la razón del cambio automática
            reason = f"ROLLBACK: Restauración forzada desde la versión {target_version.version_number}"
            
            # 3. Usamos el mecanismo de propuesta existente para crear una nueva versión
            # que sea idéntica a la antigua. ¡Reutilizamos lógica!
            ProposeChangeUseCase().execute(
                world_id=world.id,
                new_name=target_version.proposed_name,
                new_desc=target_version.proposed_description,
                reason=reason,
                user=user
            )
            
            print(f" ⏪ Restauración iniciada: v{target_version.version_number} copiada a nueva propuesta.")
            
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada.")
