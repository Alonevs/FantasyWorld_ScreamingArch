from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM

class ProposeNarrativeChangeUseCase:
    """
    Caso de Uso responsable de proponer cambios en una narrativa existente.
    Sigue el mismo patrón de snapshots que el sistema de entidades, creando una 
    versión PENDIENTE con los nuevos textos sugeridos para título y contenido.
    """
    def execute(self, narrative_id: str, new_title: str, new_content: str, reason: str, user):
        # Localizar la narrativa mediante su NID
        try:
            narrative = CaosNarrativeORM.objects.get(nid=narrative_id)
        except CaosNarrativeORM.DoesNotExist:
            raise ValueError("La narrativa que intenta modificar no existe.")
        
        # Mantener valores actuales si el proponente deja campos vacíos (Snapshot completo)
        final_title = new_title if (new_title and new_title.strip()) else narrative.titulo
        final_content = new_content if (new_content and new_content.strip()) else narrative.contenido
        
        # Cálculo del número de versión: Siguiente al máximo histórico registrado
        last_version = narrative.versiones.order_by('-version_number').first()
        next_version = (last_version.version_number + 1) if last_version else (narrative.current_version_number + 1)
        
        # Crear la propuesta en el historial
        CaosNarrativeVersionORM.objects.create(
            narrative=narrative,
            proposed_title=final_title,
            proposed_content=final_content,
            version_number=next_version,
            status='PENDING',
            change_log=reason,
            author=user
        )
        
        print(f" 📝 Propuesta de lore v{next_version} generada para '{narrative.titulo}'.")
