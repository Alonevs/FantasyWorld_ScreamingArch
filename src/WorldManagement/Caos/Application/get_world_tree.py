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
            node_id_str = node.id.value
            
            # GHOST LOGIC: Hide "00" nodes unless they are materialized (Renamed)
            is_ghost = node_id_str.endswith("00") and (node.name.startswith(("Ghost", "Nexo Fantasma")) or node.name in ("Placeholder", ""))
            if is_ghost:
                continue

            # FILTER DRAFTS (User "borradas" feedback likely refers to Drafts hidden in main view)
            status_val = node.status.value if hasattr(node.status, 'value') else str(node.status)
            if status_val == 'DRAFT':
                continue

            # Calculate depth based on ID length
            # Assuming ID structure: Root(2) -> Child(4) -> Grandchild(6) ...
            depth = (len(node_id_str) - base_len) // 2
            
            tree_data.append({
                'name': node.name,
                'public_id': node_id_str, 
                'id_display': f"..{node_id_str[-2:]}" if len(node_id_str) > 2 else node_id_str,
                'indent_px': depth * 30,
                'is_root': node_id_str == root.id.value,
                'status': status_val,
                'visible': node.is_public
            })
            
        return {'root_name': root.name, 'tree': tree_data}
