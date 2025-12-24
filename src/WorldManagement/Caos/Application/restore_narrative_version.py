from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class RestoreNarrativeVersionUseCase:
    """
    Caso de Uso responsable de realizar una restauración (Rollback) de una narrativa.
    Permite tomar un estado histórico (aprobado, archivado o rechazado) y 
    re-activarlo como una propuesta PENDIENTE de revisión, facilitando la 
    recuperación de contenido antiguo.
    """
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperar la versión antigua que queremos restaurar
            target_version = CaosNarrativeVersionORM.objects.get(id=version_id)
            
            # 2. Re-activar la versión poniéndola de nuevo en el flujo de aprobación (PENDING)
            target_version.status = 'PENDING'
            
            # 3. Documentar la acción de ROLLBACK en el log de la versión
            target_version.change_log = f"ROLLBACK: Restauración manual desde el histórico v{target_version.version_number}"
            target_version.author = user
            
            target_version.save()
            
            print(f" ⏪ Restauración de lore iniciada: v{target_version.version_number} vuelve a revisión (PENDING).")
            
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("No se ha podido localizar la versión de narrativa para restaurar.")
