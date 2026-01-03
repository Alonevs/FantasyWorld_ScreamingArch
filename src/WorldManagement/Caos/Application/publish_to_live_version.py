from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosEventLog, CaosNotification

class PublishToLiveVersionUseCase:
    """
    Caso de Uso responsable de elevar una versión aprobada al estado 'LIVE' (En Vivo).
    Aplica los cambios propuestos (nombre, descripción, metadatos) a la entidad principal,
    gestiona el historial archivando las versiones anteriores y maneja acciones especiales
    como borrado lógico, restauración o cambio de visibilidad.
    """
    def execute(self, version_id: int, user=None, reviewer=None):
        effective_user = reviewer or user
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "APPROVED":
            raise Exception("Solo se pueden publicar versiones APROBADAS.")

        # 0. GESTIÓN DEL HISTORIAL: MOVER VERSIÓN 'LIVE' ANTERIOR A HISTORIAL
        # Antes de publicar la nueva, movemos cualquier versión activa previa al Historial real.
        try:
            old_live = CaosVersionORM.objects.filter(world=version.world, status='LIVE').exclude(id=version.id)
            for old in old_live:
                old.status = 'HISTORY' # Cambiado de ARCHIVED a HISTORY
                old.save()
                print(f" 📦 Versión v{old.version_number} movida al historial REAL (HISTORY).")
        except Exception as e:
            print(f"Error moviendo a historial: {e}")

        # 1. ACCIONES ESPECIALES (Detección por metadato 'action')
        
        # Caso A: Borrado Lógico (Soft Delete)
        if version.cambios and version.cambios.get('action') == 'DELETE':
            print(f" 🗑️ Ejecutando eliminación lógica de mundo '{version.world.name}' (v{version.version_number})")
            version.world.soft_delete()
            
            if effective_user:
                 try: CaosEventLog.objects.create(user=effective_user, action="SOFT_DELETE", target_id=version.world.id, details=f"Aprobada v{version.version_number} (Borrado)")
                 except: pass

            # El borrado se considera una acción que termina en ARCHIVED si es una propuesta ejecutada
            version.status = 'ARCHIVED' 
            version.save()
            return

        # Caso B: Establecer Portada de la Galería
        if version.cambios and version.cambios.get('action') == 'SET_COVER':
            version.world.metadata['cover_image'] = version.cambios['cover_image']
            version.world.save()
            version.status = "LIVE"
            version.save()
            return

        # Caso C: Cambiar Visibilidad Pública
        if version.cambios and version.cambios.get('action') == 'TOGGLE_VISIBILITY':
            version.world.visible_publico = version.cambios.get('target_visibility', False)
            version.world.save()
            version.status = "LIVE"
            version.save()
            return

        # Caso D: Restauración desde la Papelera
        if version.cambios and version.cambios.get('action') == 'RESTORE':
            version.world.restore()
            version.status = "LIVE"
            version.save()
            return

        # 2. APLICACIÓN DE CAMBIOS ESTÁNDAR
        world = version.world
        world.name = version.proposed_name
        world.description = version.proposed_description
        world.current_version_number = version.version_number
        world.current_author_name = version.author.username if version.author else "Desconocido"
        
        if version.cambios and 'metadata' in version.cambios:
             new_meta = version.cambios['metadata']
             if not world.metadata: world.metadata = {}
             if 'properties' in new_meta:
                 world.metadata['properties'] = new_meta['properties']

        if world.status not in ['OFFLINE', 'LOCKED']:
            world.status = "LIVE" 
            
        world.save()

        # Marcamos la versión actual como la ACTIVA
        version.status = "LIVE"
        version.save()
        
        # Create Notification for the author
        if version.author:
            CaosNotification.objects.create(
                user=version.author,
                title="🚀 ¡Mundo Publicado!",
                message=f"Tu propuesta para '{version.world.name}' ya está en vivo.",
                url=f"/mundo/{version.world.public_id}/"
            )
        
        # 3. LIMPIEZA DE PROPUESTAS OBSOLETAS
        obsoletas = CaosVersionORM.objects.filter(
            world=world,
            version_number__lt=version.version_number,
            status__in=['PENDING', 'APPROVED']
        )
        obsoletas.update(status='ARCHIVED')
        
        print(f" 🚀 Publicación exitosa de v{version.version_number}. Entidad '{world.name}' operativa.")
