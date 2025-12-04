from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM

class PublishToLiveVersionUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "APPROVED":
            raise Exception("Solo se pueden publicar versiones APROBADAS.")

        # 0. ARQUIVAR VERSIÓN LIVE ANTERIOR
        try:
            old_live = CaosVersionORM.objects.filter(world=version.world, status='LIVE').exclude(id=version.id)
            for old in old_live:
                old.status = 'ARCHIVED'
                old.save()
                print(f" 📦 Versión v{old.version_number} archivada.")
        except Exception as e:
            print(f"Error archivando versión anterior: {e}")

        # 1. APLICAR AL LIVE
        world = version.world
        world.name = version.proposed_name
        world.description = version.proposed_description
        world.current_version_number = version.version_number
        world.current_author_name = version.author.username if version.author else "Desconocido"
        
        # --- CORRECCIÓN: ACTUALIZAR ESTADO DEL MUNDO ---
        world.status = "LIVE" 
        # -----------------------------------------------
        
        world.save()

        # 2. MARCAR VERSIÓN COMO LIVE
        version.status = "LIVE"
        version.save()
        
        # 3. LIMPIEZA (Archivar obsoletas)
        obsoletas = CaosVersionORM.objects.filter(
            world=world,
            version_number__lt=version.version_number,
            status__in=['PENDING', 'APPROVED']
        )
        obsoletas.update(status='ARCHIVED')
        
        print(f" 🚀 Publicada v{version.version_number}. Mundo '{world.name}' ahora está LIVE.")