from django.conf import settings
from src.Infrastructure.Utils.FileExtractor import FileExtractor
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.Domain.Services.ContextService import ContextBuilder
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
    def generate_magic_title(text: str, world_id: str = None) -> str:
        """
        Genera un título mágico para un texto dado.
        Ahora con CONCIENCIA SITUACIONAL de la jerarquía.
        """
        if not text:
             raise ValueError("El texto está vacío.")

        # 1. Build Context if world_id provided
        context_prompt = ""
        if world_id:
            context_prompt = ContextBuilder.build_hierarchy_context(world_id)

        # 2. Call AI Service
        service = Llama3Service()
        
        system_prompt = "Eres un Editor de Fantasía experto en dar títulos evocadores y poéticos."
        if context_prompt:
            system_prompt += f"\n{context_prompt}\nUSA el contexto anterior para dar coherencia al título."

        prompt = f"Analiza el siguiente texto y genera UN SOLO título corto, evocador y sin comillas:\n\n{text[:3000]}"
        
        # We reuse 'edit_text' which calls chat completion
        title = service.edit_text(system_prompt, prompt)
        
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
