class MockEntity:
    def __init__(self, id, name):
        self.id = id
        self.name = name

def execute_mock(all_entities):
    winners_by_trunk = {}
    for m in all_entities:
        trunk_id = m.id
        if '00' in m.id:
            level = len(m.id) // 2
            if level >= 7:
                trunk_id = m.id
            else:
                trunk_id = m.id.split('00')[0]
            
        if trunk_id not in winners_by_trunk:
            winners_by_trunk[trunk_id] = []
        winners_by_trunk[trunk_id].append(m)
    
    pre_list = []
    for pid, candidates in winners_by_trunk.items():
        candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
        winner = candidates[0]
        is_ghost_structure = ('00' in winner.id and (len(winner.id)//2) < 7)
        # Note: In the actual code, is_ghost_structure logic might also affect it if it wasn't the trunk_id itself?
        # But '02' is the trunk_id. '0200...' starts with '02'.
        # winner.id != pid check: '0200...' != '02'. So it might continue here too!
        if is_ghost_structure and winner.id != pid:
            print(f"DEBUG: Hiding {winner.name} ({winner.id}) because it is considered a ghost structure of trunk {pid}")
            continue
            
        pre_list.append(winner)

    final_list = []
    indexed_groups = {}
    for m in pre_list:
        if m.id.endswith('00'):
            print(f"DEBUG: Hiding {m.name} ({m.id}) because it ends with '00'")
            continue

        parent_id = m.id[:-2]
        level = len(m.id)
        group_key = (parent_id, level)
        if group_key not in indexed_groups:
            indexed_groups[group_key] = []
        indexed_groups[group_key].append(m)
        
    for key, candidates in indexed_groups.items():
        candidates.sort(key=lambda x: x.id)
        final_list.append(candidates[0])
    
    final_list.sort(key=lambda x: x.id)
    return final_list

caos_prime = MockEntity('020000000000000000000000', 'Caos Prime')
result = execute_mock([caos_prime])
print(f"Result contains: {[m.name for m in result]}")
