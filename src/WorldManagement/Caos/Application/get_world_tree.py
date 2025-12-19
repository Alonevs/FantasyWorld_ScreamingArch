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
        
        # LOGICAL SORT: Group '00' (Shared) entities with the Firstborn Sibling (01).
        # User request: "posicionarse con sus hijos" (inside Abismo Prime block).
        # We replace '00' with '01' + suffix logic so they sort inside the '01' branch.
        def tree_sort_key(node):
            original = node.id.value
            segments = [original[i:i+2] for i in range(0, len(original), 2)]
            
            # Map '00' segment to '01' to group with Abismo/Firstborn
            # We append '~~' suffix to ensure it sorts AFTER normal children of '01'
            remapped_segments = []
            for s in segments:
                if s == '00':
                    remapped_segments.append('01') # Proxy to Firstborn
                    # We might need extra weight to push to end of 01? 
                    # If we just use '01', 010013 -> 010113. 
                    # If Universe is 010101, then 13 > 01. Natural sort works.
                else:
                    remapped_segments.append(s)
            
            return "".join(remapped_segments)

        descendants.sort(key=tree_sort_key)
        
        tree_data = []
        base_len = len(root.id.value)
        
        for node in descendants:
            node_id_str = node.id.value
            
            # GHOST LOGIC: Hide "00" nodes unless they are materialized (Renamed)
            # AGGRESSIVE FILTER: Any node with "Nexo" or "Ghost" in name is hidden if it ends in 00.
            name_lower = node.name.lower()
            is_ghost_name = "nexo" in name_lower or "ghost" in name_lower or "fantasma" in name_lower or node.name in ("Placeholder", "")
            is_ghost_id = node_id_str.endswith("00")
            
            if is_ghost_id and is_ghost_name:
                continue

            # FILTER DRAFTS
            status_val = node.status.value if hasattr(node.status, 'value') else str(node.status)
            if status_val == 'DRAFT':
                continue

            # Calculate depth based on ID length
            depth = (len(node_id_str) - base_len) // 2
            
            # DETECT JUMP/SHARED (Orphan)
            # If ID contains '00' segment in the MIDDLE (not just end), it is a jump/shared entity.
            # e.g. 010001 -> '00' is at index 2.
            # We check 2-char segments.
            is_jumped = False
            for i in range(0, len(node_id_str)-2, 2):
                if node_id_str[i:i+2] == '00':
                    is_jumped = True
                    break
            
            tree_data.append({
                'name': node.name,
                'public_id': node_id_str, 
                'id_display': f"..{node_id_str[-2:]}" if len(node_id_str) > 2 else node_id_str,
                'indent_px': depth * 30,
                'is_root': node_id_str == root.id.value,
                'status': status_val,
                'visible': node.is_public,
                'is_jumped': is_jumped
            })
            
        return {'root_name': root.name, 'tree': tree_data}
