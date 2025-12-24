from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosWorldORM
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase

class RestoreVersionUseCase:
    """
    Caso de Uso responsable de restaurar (Rollback) la entidad a un estado anterior.
    En lugar de crear una copia de los datos, "promociona" una versión antigua o 
    rechazada de nuevo al estado PENDIENTE para que los administradores la revisen
    y publiquen, devolviendo el mundo a ese estado histórico.
    """
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperar la versión histórica de la base de datos
            target_version = CaosVersionORM.objects.get(id=version_id)
            
            # 2. Re-activar la versión: Cambiamos su estado a PENDING
            # Esto permite que aparezca de nuevo en el Dashboard para ser aprobada/publicada.
            # Mantenemos el número de versión original para trazar el historial correctamente.
            target_version.status = 'PENDING'
            
            # 3. Documentar la acción de restauración
            # Marcamos quién ha iniciado el rollback y por qué.
            target_version.change_log = f"ROLLBACK: Restauración forzada del estado v{target_version.version_number}"
            target_version.author = user
            
            target_version.save()
            
            print(f" ⏪ Restauración iniciada: v{target_version.version_number} vuelve a revisión (PENDING).")
            
        except CaosVersionORM.DoesNotExist:
            raise Exception("No se ha podido localizar la versión histórica para restaurar.")
