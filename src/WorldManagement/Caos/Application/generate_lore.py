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

    def execute(self, world_id_str: str):
        """
        Ejecuta la solicitud de generación de lore para una entidad específica.
        """
        # 1. Recuperar la entidad desde el repositorio de dominio
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        
        if not world:
            print(f"❌ Error: La entidad {world_id_str} no existe en la base de datos.")
            return

        # 2. Invocación al servicio de IA (Abstracción de Llama/Oobabooga)
        print(f" 🎤 Solicitando expansión de Lore por IA para: {world.name}")
        new_lore = self.ai_service.generate_description(world.name)
        
        # 3. Persistencia de los resultados
        if new_lore:
            world.lore_description = new_lore
            
            # Guardamos los cambios a través del repositorio
            self.repository.save(world)
            print(f" ✨ Lore generado y persistido con éxito.")
            print(f" 📝 Vista previa: {new_lore[:100]}...")
        else:
            print(" ⚠️ Advertencia: La IA no proporcionó ningún texto de respuesta.")
        
        return new_lore