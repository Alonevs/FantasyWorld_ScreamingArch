from typing import List, Dict, Any
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

class GetWorldTreeUseCase:
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> Dict[str, Any]:
        """
        Returns the tree structure for a given root world.
        """
        root = resolve_world_id(self.repository, identifier)
        if not root:
            return None

        # Fetch all descendants
        descendants = self.repository.find_descendants(root.id)
        
        tree_data = []
        base_len = len(root.id.value)
        
        for node in descendants:
            # Calculate depth based on ID length
            # Assuming ID structure: Root(2) -> Child(4) -> Grandchild(6) ...
            depth = (len(node.id.value) - base_len) // 2
            
            # Note: We don't have public_id in the Entity yet (we just added is_public).
            # But the repository implementation of find_descendants *could* populate it if we added it to Entity.
            # For now, we rely on the fact that we might need to fetch it or just use ID.
            # Wait, our Entity definition doesn't have public_id.
            # We should probably add it to Entity for full DDD compliance.
            # But for now, let's just use ID. The view can handle missing public_id or we assume ID is fine for internal tree.
            
            tree_data.append({
                'name': node.name,
                'public_id': node.id.value, # Fallback to ID as we don't have public_id in Entity
                'id_display': node.id.value,
                'indent_px': depth * 30,
                'is_root': node.id.value == root.id.value,
                'status': node.status.value if hasattr(node.status, 'value') else node.status
            })
            
        return {'root_name': root.name, 'tree': tree_data}
