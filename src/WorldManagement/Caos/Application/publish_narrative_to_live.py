from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM

class PublishNarrativeToLiveUseCase:
    """
    Caso de Uso responsable de aplicar una propuesta de lore aprobada al contenido real ('Live').
    Sincroniza el registro maestro de la narrativa con los textos propuestos, gestiona 
    el archivo de versiones históricas y asegura que el lector siempre vea el contenido aprobado.
    """
    def execute(self, version_id: int):
        # Localizar la versión de narrativa aprobada
        try:
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("La versión de narrativa especificada no existe.")

        # Regla de Negocio: Seguridad del flujo. Solo lo aprobado se publica.
        if version.status != "APPROVED":
            raise Exception("No se puede publicar una versión que no ha sido APROBADA previamente.")

        # 1. GESTIÓN DEL HISTORIAL (ARCHIVADO)
        # Marcamos las versiones que estaban 'LIVE' anteriormente como 'ARCHIVED'.
        old_live = CaosNarrativeVersionORM.objects.filter(narrative=version.narrative, status='LIVE').exclude(id=version.id)
        for old in old_live:
            old.status = 'ARCHIVED'
            old.save()

        # 2. APLICACIÓN AL 'LIVE' (Registro Maestro)
        # Copiamos los textos de la propuesta al objeto principal que ve el usuario.
        narrative = version.narrative
        narrative.titulo = version.proposed_title
        narrative.contenido = version.proposed_content
        narrative.current_version_number = version.version_number
        
        narrative.save()

        # 3. MARCAR LA PROPUESTA COMO ACTIVA
        version.status = "LIVE"
        version.save()
        
        # 4. LIMPIEZA DE PROPUESTAS OBSOLETAS
        # Si había propuestas pendientes de números anteriores, quedan invalidadas.
        obsoletas = CaosNarrativeVersionORM.objects.filter(
            narrative=narrative,
            version_number__lt=version.version_number,
            status__in=['PENDING', 'APPROVED']
        )
        obsoletas.update(status='ARCHIVED')
        
        print(f" 🚀 Lore Publicado exitosamente: v{version.version_number} de '{narrative.titulo}'.")
