from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosEventLog

class PublishToLiveVersionUseCase:
    """
    Caso de Uso responsable de elevar una versión aprobada al estado 'LIVE' (En Vivo).
    Aplica los cambios propuestos (nombre, descripción, metadatos) a la entidad principal,
    gestiona el historial archivando las versiones anteriores y maneja acciones especiales
    como borrado lógico, restauración o cambio de visibilidad.
    """
    def execute(self, version_id: int, user=None):
        try:
            version = CaosVersionORM.objects.get(id=version_id)
        except CaosVersionORM.DoesNotExist:
            raise Exception("Versión no encontrada")

        if version.status != "APPROVED":
            raise Exception("Solo se pueden publicar versiones APROBADAS.")

        # 0. GESTIÓN DEL HISTORIAL: ARCHIVAR VERSIÓN 'LIVE' ANTERIOR
        # Antes de publicar la nueva, movemos cualquier versión activa previa al archivo (Historial).
        try:
            old_live = CaosVersionORM.objects.filter(world=version.world, status='LIVE').exclude(id=version.id)
            for old in old_live:
                old.status = 'ARCHIVED'
                old.save()
                print(f" 📦 Versión v{old.version_number} movida al historial (ARCHIVED).")
        except Exception as e:
            print(f"Error archivando versión anterior: {e}")

        # 1. ACCIONES ESPECIALES (Detección por metadato 'action')
        
        # Caso A: Borrado Lógico (Soft Delete)
        if version.cambios and version.cambios.get('action') == 'DELETE':
            print(f" 🗑️ Ejecutando eliminación lógica de mundo '{version.world.name}' (v{version.version_number})")
            # La versión anterior ya fue archivada en el Paso 0 para tener un backup.
            version.world.soft_delete()
            
            # Registro en el log de auditoría
            if user:
                 try: CaosEventLog.objects.create(user=user, action="SOFT_DELETE", target_id=version.world.id, details=f"Aprobada v{version.version_number} (Borrado)")
                 except: pass

            # Marcamos esta propuesta como ARCHIVADA (ejecutada)
            version.status = 'ARCHIVED' 
            version.save()
            return

        # Caso B: Establecer Portada de la Galería
        if version.cambios and version.cambios.get('action') == 'SET_COVER':
            version.world.metadata['cover_image'] = version.cambios['cover_image']
            version.world.save()
            version.status = "LIVE"
            version.save()
            print(f" 📸 Portada actualizada para mundo '{version.world.name}' (v{version.version_number})")
            return

        # Caso C: Cambiar Visibilidad Pública
        if version.cambios and version.cambios.get('action') == 'TOGGLE_VISIBILITY':
            version.world.visible_publico = version.cambios.get('target_visibility', False)
            version.world.save()
            version.status = "LIVE"
            version.save()
            print(f" 👁️ Visibilidad actualizada para mundo '{version.world.name}'")
            return

        # Caso D: Restauración desde la Papelera
        if version.cambios and version.cambios.get('action') == 'RESTORE':
            print(f" ♻️ Ejecutando restauración de mundo '{version.world.name}' (v{version.version_number})")
            version.world.restore()
            version.status = "LIVE"
            version.save()
            return

        # 2. APLICACIÓN DE CAMBIOS ESTÁNDAR (Actualización de Contenido)
        # Sincronizamos la entidad maestra con los datos de la propuesta aprobada.
        world = version.world
        world.name = version.proposed_name
        world.description = version.proposed_description
        world.current_version_number = version.version_number
        world.current_author_name = version.author.username if version.author else "Desconocido"
        
        # --- ACTUALIZACIÓN DE METADATOS (Propiedades) ---
        if version.cambios and 'metadata' in version.cambios:
             # El editor envía la lista completa de propiedades, por lo que actualizamos ese nodo.
             # Preservamos otros campos (como 'cover_image') si existen.
             new_meta = version.cambios['metadata']
             if not world.metadata: world.metadata = {}
             
             if 'properties' in new_meta:
                 world.metadata['properties'] = new_meta['properties']
                 
             print(f" 💾 Metadatos aplicados: {len(new_meta.get('properties', []))} propiedades.")

        # Aseguramos que el estado del mundo sea 'LIVE' tras la publicación
        # REQUERIMIENTO: Si ya estaba en OFFLINE o LOCKED, mantener esa visibilidad.
        if world.status not in ['OFFLINE', 'LOCKED']:
            world.status = "LIVE" 
            
        world.save()

        # Marcamos la versión actual como la ACTIVA
        version.status = "LIVE"
        version.save()
        
        # 3. LIMPIEZA DE PROPUESTAS OBSOLETAS
        # Cualquier propuesta antigua que siga pendiente o aprobada se archiva automáticamente.
        obsoletas = CaosVersionORM.objects.filter(
            world=world,
            version_number__lt=version.version_number,
            status__in=['PENDING', 'APPROVED']
        )
        obsoletas.update(status='ARCHIVED')
        
        print(f" 🚀 Publicación exitosa de v{version.version_number}. Entidad '{world.name}' operativa.")