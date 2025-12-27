from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosWorldORM

class RestoreVersionUseCase:
    """
    Caso de Uso responsable de restaurar (Rollback) la entidad a un estado anterior.
    NUEVA LÓGICA: En lugar de promocionar la versión antigua, crea una NUEVA propuesta
    de cambio basada en los datos de la versión histórica seleccionada.
    """
    def execute(self, version_id: int, user):
        try:
            # 1. Recuperar la versión de origen (Histórica o Archivada)
            origin_version = CaosVersionORM.objects.get(id=version_id)
            world = origin_version.world
            
            # 2. Calcular el siguiente número de versión para el mundo
            # Buscamos el máximo actual y sumamos 1
            from django.db.models import Max
            max_v = CaosVersionORM.objects.filter(world=world).aggregate(Max('version_number'))['version_number__max'] or 0
            next_v = max_v + 1

            # 3. Crear la NUEVA propuesta basada en la antigua
            new_proposal = CaosVersionORM.objects.create(
                world=world,
                proposed_name=origin_version.proposed_name,
                proposed_description=origin_version.proposed_description,
                version_number=next_v,
                status='PENDING',
                change_log=f"Recuperar versión (v{origin_version.version_number})",
                cambios=origin_version.cambios, # Copiamos el JSON de cambios completo
                author=user
            )
            
            print(f" ⏪ Propuesta de restauración creada: Nueva v{next_v} basada en v{origin_version.version_number}.")
            return new_proposal
            
        except CaosVersionORM.DoesNotExist:
            raise Exception("No se ha podido localizar la versión de origen para restaurar.")
