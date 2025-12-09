from django.conf import settings
from src.Infrastructure.Utils.FileExtractor import FileExtractor
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.WorldManagement.Caos.Application.propose_narrative_change import ProposeNarrativeChangeUseCase
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM

class NarrativeService:
    """
    Service Layer/Facade for Narrative Operations.
    Centralizes logic to keep Views clean.
    """

    @staticmethod
    def import_text(uploaded_file) -> str:
        """
        Wrapper for FileExtractor.
        """
        return FileExtractor.extract_text_from_file(uploaded_file)

    @staticmethod
    def generate_magic_title(text: str) -> str:
        """
        Generates an epic title using AI.
        """
        if not text or len(text.strip()) < 50:
             raise ValueError("El texto es demasiado corto para generar un título (min 50 chars).")
        
        system_prompt = (
            "Eres un editor de novelas de fantasía experto. Lee el siguiente texto y genera un Título corto, épico y descriptivo (máximo 5-6 palabras). "
            "Devuelve SOLO el título, sin comillas, ni preámbulos, ni explicaciones extra. "
            "Ejemplo de salida: La Caída de los Dioses"
        )
        
        service = Llama3Service()
        title = service.edit_text(system_prompt, text[:2000]) # Context window limit
        
        if not title:
            raise Exception("La IA no devolvió respuesta.")
            
        return title.replace('"', '').replace("Título:", "").strip()

    @staticmethod
    def handle_edit_proposal(user, narrative_identifier, title, content, reason):
        """
        Handles the logic of finding the narrative and submitting a proposal.
        """
        # 1. Resolve Narrative ID (Public ID or Internal ID)
        try:
            n_obj = CaosNarrativeORM.objects.get(public_id=narrative_identifier)
        except CaosNarrativeORM.DoesNotExist:
            try:
                n_obj = CaosNarrativeORM.objects.get(nid=narrative_identifier)
            except CaosNarrativeORM.DoesNotExist:
                raise ValueError(f"Narrativa no encontrada: {narrative_identifier}")
        
        # 2. Execute Use Case
        ProposeNarrativeChangeUseCase().execute(
            narrative_id=n_obj.nid,
            new_title=title,
            new_content=content,
            reason=reason,
            user=user
        )
        return True
