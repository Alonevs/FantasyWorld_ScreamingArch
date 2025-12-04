from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM

class PublishNarrativeToLiveUseCase:
    def execute(self, version_id: int):
        try:
            version = CaosNarrativeVersionORM.objects.get(id=version_id)
        except CaosNarrativeVersionORM.DoesNotExist:
            raise Exception("Versión narrativa no encontrada")

        if version.status != "APPROVED":
            raise Exception("Solo se pueden publicar versiones APROBADAS.")

        # 0. ARCHIVAR VERSIÓN LIVE ANTERIOR (Si existiera alguna marcada como LIVE en versiones)
        # En este modelo simple, asumimos que lo que está en NarrativeORM es el LIVE.
        # Pero si queremos historial completo, deberíamos marcar la anterior como ARCHIVED.
        # Vamos a crear una versión 'snapshot' de lo que había antes si no existe?
        # Simplificación: Simplemente marcamos las anteriores como ARCHIVED.
        
        old_live = CaosNarrativeVersionORM.objects.filter(narrative=version.narrative, status='LIVE').exclude(id=version.id)
        for old in old_live:
            old.status = 'ARCHIVED'
            old.save()

        # 1. APLICAR AL LIVE (NarrativeORM)
        narrative = version.narrative
        narrative.titulo = version.proposed_title
        narrative.contenido = version.proposed_content
        narrative.current_version_number = version.version_number
        # narrative.updated_by = version.author # Si tuviéramos ese campo
        
        narrative.save()

        # 2. MARCAR VERSIÓN COMO LIVE
        version.status = "LIVE"
        version.save()
        
        # 3. LIMPIEZA (Archivar obsoletas)
        obsoletas = CaosNarrativeVersionORM.objects.filter(
            narrative=narrative,
            version_number__lt=version.version_number,
            status__in=['PENDING', 'APPROVED']
        )
        obsoletas.update(status='ARCHIVED')
        
        print(f" 🚀 Publicada Narrativa v{version.version_number}. '{narrative.titulo}' ahora está LIVE.")
