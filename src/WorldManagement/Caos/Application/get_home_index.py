class GetHomeIndexUseCase:
    """
    Encapsulates the logic for filtering and indexing the entities displayed on the Home Page.
    Applies two main filters:
    1. Ghost/Version Cleaning (hiding duplicates), with safety for High-Level Jumps (Geography).
    2. Aggressive Indexing (picking one representative per branch) for Geography and Population.
    """

    def execute(self, all_entities):
        """
        Args:
            all_entities (list/QuerySet): The raw list of visible entities (e.g. filtered by permission).
        
        Returns:
            list: The final filtered and sorted list of entities to display.
        """
        winners_by_trunk = {}
        for m in all_entities:
            trunk_id = m.id
            if '00' in m.id:
                # Check Level
                level = len(m.id) // 2
                if level >= 7:
                    # Geography+: Don't collapse (Treat as distinct entity even with '00')
                    trunk_id = m.id
                else:
                    # Cosmology/Core: Collapse '00' (Treat as Version/Ghost of Root)
                    trunk_id = m.id.split('00')[0]
                
            if trunk_id not in winners_by_trunk:
                winners_by_trunk[trunk_id] = []
            winners_by_trunk[trunk_id].append(m)
        
        pre_list = []
        for pid, candidates in winners_by_trunk.items():
            candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
            winner = candidates[0]
            
            # STRICT GHOST CHECK:
            # If the winner is a Ghost (contains '00' and not Geography)
            # AND it is NOT the Trunk ID itself (meaning the Trunk/Root is missing from candidates)
            # Then hide it. (Do not show a Ghost Fragment if the Real Body '01' is hidden)
            is_ghost_structure = ('00' in winner.id and (len(winner.id)//2) < 7)
            if is_ghost_structure and winner.id != pid:
                continue
                
            pre_list.append(winner)

        # 2. Aggressive Index Logic: One Representative Per Branch (01 preference)
        # This fulfills the "usa los primeros de cada tabla 01 (o fallback 02, 03)" for navigation index.
        # Applies to Geography (Level 7-11) AND Population/Characters (Level 12+) as requested.
        
        indexed_groups = {}
        for m in pre_list:
            # Safety: Hide "Pure Ghosts" (Bridges) ending in '00'. 
            # We only want to see the "Jumped Entity" (ending in 01, 02...) which might have '00' in the middle.
            if m.id.endswith('00'):
                continue

            parent_id = m.id[:-2]
            level = len(m.id)
            group_key = (parent_id, level)
            if group_key not in indexed_groups:
                indexed_groups[group_key] = []
            indexed_groups[group_key].append(m)
            
        final_list = []
        for key, candidates in indexed_groups.items():
            # Sort by ID (Lowest ID = 01, then 02...)
            candidates.sort(key=lambda x: x.id)
            final_list.append(candidates[0])

        # Sort final list by ID for display order
        final_list.sort(key=lambda x: x.id)
        
        return final_list
