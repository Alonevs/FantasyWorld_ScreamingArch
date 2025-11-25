from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM

class PublishToLiveVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "APPROVED":
            raise Exception("Solo se pueden publicar versiones APROBADAS.")

        # 1. APLICAR AL LIVE
        world = version.world
        world.name = version.proposed_name
        world.description = version.proposed_description
        world.current_version_number = version.version_number # <--- ACTUALIZAMOS CONTADOR
        world.save()

        # 2. MARCAR ESTA COMO LIVE
        version.status = "LIVE"
        version.save()
        
        # 3. LIMPIEZA AUTOMÁTICA (Archivar versiones inferiores obsoletas)
        # Buscamos hermanas pendientes que sean más viejas que la actual
        obsoletas = CaosVersionORM.objects.filter(
            world=world,
            status='PENDING',
            version_number__lt=version.version_number
        )
        count = obsoletas.count()
        obsoletas.update(status='ARCHIVED') # Al hoyo de la historia
        
        print(f" 🚀 Publicada v{version.version_number}. Archivadas {count} propuestas obsoletas.")