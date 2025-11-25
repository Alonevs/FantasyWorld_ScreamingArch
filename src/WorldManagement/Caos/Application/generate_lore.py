from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.FantasyWorld.AI_Generation.Domain.interfaces import LoreGenerator

class GenerateWorldLoreUseCase:
    def __init__(self, repository: CaosRepository, ai_service: LoreGenerator):
        self.repository = repository
        self.ai_service = ai_service

    def execute(self, world_id_str: str):
        # 1. Recuperar el mundo (Entidad)
        # OJO: world_id_str es "01", pero el repositorio espera un WorldID
        w_id = WorldID(world_id_str)
        world = self.repository.find_by_id(w_id)
        
        if not world:
            print(f"❌ Mundo {world_id_str} no encontrado en DB.")
            return

        # 2. Llamar a la IA
        print(f" 🎤 Pidiendo a la IA (Oobabooga) lore para: {world.name}")
        new_lore = self.ai_service.generate_description(world.name)
        
        # 3. Actualizar la Entidad
        if new_lore:
            world.lore_description = new_lore
            
            # 4. Guardar cambios
            self.repository.save(world)
            print(f" ✨ LORE GENERADO Y GUARDADO.")
            print(f" 📝 Preview: {new_lore[:100]}...")
        else:
            print(" ⚠️ La IA no devolvió texto.")
        
        return new_lore