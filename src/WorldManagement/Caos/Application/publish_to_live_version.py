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
        
        # Actualizamos metadatos
        world.current_version_number = version.version_number
        # Guardamos el nombre del autor (por si se borra el usuario, queda el texto)
        world.current_author_name = version.author.username if version.author else "Desconocido"
        
        world.save()

        # 2. MARCAR ESTA COMO LIVE
        version.status = "LIVE"
        version.save()
        
        # (Sin auto-archivado, las versiones viejas se quedan como historial visible)
        
        print(f" 🚀 Publicada v{version.version_number}. Autor: {world.current_author_name}")