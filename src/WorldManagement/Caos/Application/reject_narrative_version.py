from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM

class RejectNarrativeVersionUseCase:
    """
    Caso de Uso responsable de rechazar propuestas de cambio o creación en narrativas.
    Si se rechaza una propuesta de CREACIÓN inicial, el sistema elimina el registro
    maestro de la narrativa para mantener limpia la base de datos de contenido no aprobado.
    """
    def execute(self, version_id: int, reason: str = ""):
        try:
            # Recuperar la propuesta de versión
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
            
            # Solo podemos rechazar si no es un estado final (REJECTED/LIVE/ARCHIVED)
            if version.status not in ['PENDING', 'APPROVED']:
                raise Exception(f"No es posible rechazar una versión en estado {version.status}.")
            
            # Cambiar a estado RECHAZADO
            version.status = 'REJECTED'
            
            # Almacenar retroalimentación para el autor
            if reason:
                version.admin_feedback = reason
            version.save()
            
            # REGLA ESPECIAL: Si lo que se rechaza es la propuesta de nacimiento (ADD) de la narrativa,
            # procedemos a borrar el registro maestro ya que nunca llegó a ser oficial.
            if getattr(version, 'action', None) == 'ADD':
                print(f" 🗑️ Rechazo de creación inicial: Eliminando rastro de narrativa {version.narrative.nid}")
                version.narrative.delete()
            
            print(f" ❌ Propuesta de lore v{version.version_number} RECHAZADA.")
            
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("La propuesta de narrativa no existe.")
