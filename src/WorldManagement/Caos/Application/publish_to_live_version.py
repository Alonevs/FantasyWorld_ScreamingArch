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
                old.status = 'HISTORY'
                old.save()
                print(f" 📦 Versión v{old.version_number} archivada como HISTORY.")
        except Exception as e:
            print(f"Error archivando versión anterior: {e}")

        # 0.5 CHECK FOR DELETE ACTION
        if version.cambios and version.cambios.get('action') == 'DELETE':
            print(f" 🗑️ Ejecutando eliminación lógica de mundo '{version.world.name}' (v{version.version_number})")
            # NOTE: Step 0 (above) already archived the previous LIVE version as HISTORY.
            # This ensures we have a backup of the state prior to deletion.
            version.world.soft_delete()
            
            # Mark this proposal as ARCHIVED to indicate it was verified and executed.
            version.status = 'ARCHIVED' 
            version.save()
            return

        # 0.6 CHECK FOR SET_COVER ACTION
        if version.cambios and version.cambios.get('action') == 'SET_COVER':
            version.world.metadata['cover_image'] = version.cambios['cover_image']
            version.world.save()
            version.status = "LIVE"
            version.save()
             # Cleanup logic (optional, but good to archive pending if any)
            print(f" 📸 Portada actualizada para mundo '{version.world.name}' (v{version.version_number})")
        # 0.7 CHECK FOR VISIBILITY ACTION
        if version.cambios and version.cambios.get('action') == 'TOGGLE_VISIBILITY':
            version.world.visible_publico = version.cambios.get('target_visibility', False)
            version.world.save()
            version.status = "LIVE"
            version.save()
            print(f" 👁️ Visibilidad actualizada para mundo '{version.world.name}'")
            return

        # 0.8 CHECK FOR RESTORE ACTION
        if version.cambios and version.cambios.get('action') == 'RESTORE':
            print(f" ♻️ Ejecutando restauración de mundo '{version.world.name}' (v{version.version_number})")
            version.world.restore()
            version.status = "LIVE"
            version.save()
            return

        # 1. APLICAR AL LIVE (Normal Update)
        world = version.world
        world.name = version.proposed_name
        world.description = version.proposed_description
        world.current_version_number = version.version_number
        world.current_author_name = version.author.username if version.author else "Desconocido"
        
        # --- METADATA UPDATE LOGIC ---
        if version.cambios and 'metadata' in version.cambios:
             # Merge or Replace? 
             # The editing logic sends the FULL properties list, so we should probably update/replace.
             # However, we only have 'properties'. We should preserve other metadata fields (like cover_image).
             new_meta = version.cambios['metadata']
             if not world.metadata: world.metadata = {}
             
             # Specific update for properties
             if 'properties' in new_meta:
                 world.metadata['properties'] = new_meta['properties']
                 
             # Or generic update
             # world.metadata.update(new_meta)
             print(f" 💾 Metadatos aplicados al LIVE: {len(new_meta.get('properties', []))} propiedades.")

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