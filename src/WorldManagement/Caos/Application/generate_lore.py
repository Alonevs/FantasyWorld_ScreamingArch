from typing import Optional
from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class GenerateWorldLoreUseCase:
    """
    Caso de Uso responsable de la generación de descripciones literarias (Lore) por IA.
    Utiliza el motor de lenguaje para expandir la narrativa de una entidad basándose 
    únicamente en su nombre (proceso de expansión creativa).
    """
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repository = repository
        self.ai_service = ai_service

    def execute(self, world_id_str: str, current_context: Optional[str] = None, preview_mode: bool = False) -> Optional[str]:
        """
        Ejecuta la solicitud de generación de lore para una entidad específica.
        Si 'current_context' se proporciona, se usa para guiar la generación.
        Si 'preview_mode' es True, no guarda en BD (ideal para el editor).
        """
        # 1. Recuperar la entidad desde el repositorio de dominio
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        
        if not world:
            print(f"❌ Error: La entidad {world_id_str} no existe en la base de datos.")
            return None

        # 2. Construir Contexto de Metadatos (Fase 5 Enhancement)
        metadata_context = ""
        
        # 2a. Si hay texto escrito por el usuario, tiene MÁXIMA prioridad
        if current_context and len(current_context.strip()) > 5:
             metadata_context = f". Basa tu descripción estrictamente en este concepto previo del usuario: '{current_context}'"
        
        # 2b. Si no hay texto de usuario, usar metadatos
        elif world.metadata:
            # Extraer datos relevantes (Clima, Geografía, Cultura, etc.)
            nucleus = world.metadata.get('datos_nucleo', {})
            context_parts = []
            for k, v in nucleus.items():
                if v and v != "Pendiente":
                    context_parts.append(f"{k}: {v}")
            if context_parts:
                metadata_context = ". Contexto técnico: " + ", ".join(context_parts)

        # 3. Invocación al servicio de IA
        print(f" 🎤 Solicitando Lore Contextual para: {world.name} (Context: {len(metadata_context)} chars)")
        prompt = f"{world.name}{metadata_context}"
        new_lore = self.ai_service.generate_description(prompt)
        
        # 4. Persistencia opcional (El API view puede decidir no persistir si es solo para visualización)
        if new_lore and not preview_mode:
            world.lore_description = new_lore
            self.repository.save(world)
            print(f" ✨ Lore generado y persistido.")
        elif new_lore:
            print(f" ✨ Lore generado (Modo Preview).")
        
        return new_lore