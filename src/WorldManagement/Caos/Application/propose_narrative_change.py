from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM

class ProposeNarrativeChangeUseCase:
    def execute(self, narrative_id: str, new_title: str, new_content: str, reason: str, user):
        narrative = CaosNarrativeORM.objects.get(nid=narrative_id)
        
        # Fallback to existing values if None or Empty (prevent IntegrityError)
        final_title = new_title if (new_title and new_title.strip()) else narrative.titulo
        final_content = new_content if (new_content and new_content.strip()) else narrative.contenido
        
        # Determine next version number
        # If there are pending versions, take the max + 1, else current + 1
        last_version = narrative.versiones.order_by('-version_number').first()
        next_version = (last_version.version_number + 1) if last_version else (narrative.current_version_number + 1)
        
        CaosNarrativeVersionORM.objects.create(
            narrative=narrative,
            proposed_title=final_title,
            proposed_content=final_content,
            version_number=next_version,
            status='PENDING',
            change_log=reason,
            author=user
        )
        print(f" 📝 Propuesta de narrativa creada: v{next_version} para '{narrative.titulo}'")
