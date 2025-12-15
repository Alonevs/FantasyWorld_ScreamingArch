from src.Shared.Domain.value_objects import WorldID
from src.WorldManagement.Caos.Domain.entities import CaosWorld
from src.WorldManagement.Caos.Domain.repositories import CaosRepository

from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase

class DeepCreationService:
    def __init__(self, repository: CaosRepository):
        self.repository = repository
        self.child_creator = CreateChildWorldUseCase(repository)

    def create_descendant_at_level(self, parent_id: str, target_level: int, name: str, description: str, reason: str, generate_image: bool = False) -> str:
        """
        Crea una entidad descendiente en el nivel objetivo, rellenando huecos intermedios con GAPs.
        """
        current_jid = parent_id
        current_level = len(current_jid) // 2
        
        print(f"🚀 [DeepCreation] Initiating Deep Dive: Level {current_level} -> {target_level}")
        
        # 1. Loop through intermediate levels to create GAPS
        # We start looking for children at current_level + 1
        # If target_level is 8, and current IS 3.
        # We need levels: 4, 5, 6, 7 as GAPS.
        # And finally 8 as the real entity.
        
        for lvl in range(current_level + 1, target_level):
            # Calculate Gap ID length. Level X has 2*X chars.
            # But we rely on parent's automatic child ID generation usually.
            # However, for GAPs, we standardize on suffix '00'.
            
            gap_id = current_jid + "00"
            
            # Verify if it already exists
            gap = self.repository.find_by_id(WorldID(gap_id))
            if not gap:
                print(f"  👻 Creating Bridge GAP at Level {lvl}: {gap_id}")
                gap_world = CaosWorld(
                    id=WorldID(gap_id),
                    name="_GAP_CONTAINER_",
                    lore_description="Estructura interna transparente.",
                    status='LIVE',
                    metadata={"type": "STRUCTURE_GAP"}
                )
                self.repository.save(gap_world)
            else:
                print(f"  👻 Using existing Bridge GAP at Level {lvl}: {gap_id}")
            
            # Advance pointer
            current_jid = gap_id
            
        # 2. Finally, create the target entity under the last GAP
        # The last 'current_jid' is the parent for our target level entity.
        print(f"  ✨ Arrived at parent level {len(current_jid)//2}. Creating final entity '{name}'...")
        
        # We reuse the standard Use Case, BUT we must ensure it doesn't trigger "Level 11 Gap Logic" again
        # if our target was exactly Level 13, and the parent is now Level 11... Wait.
        # If we asked for Level 13 from Level 11.
        # Loop range(12, 13) -> Level 12 GAP.
        # Parent becomes GAP (Level 12).
        # We call create child on Level 12 Gap. 
        # The CreateChildUseCase sees parent len 24 (Level 12), so it treats it normally.
        # It's SAFE. The internal logic in CreateChildUseCase only triggers if parent is len 22.
        
        final_id = self.child_creator.execute(current_jid, name, description, reason, generate_image)
        return final_id
