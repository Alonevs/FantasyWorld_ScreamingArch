
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Application.get_home_index import GetHomeIndexUseCase
from django.db.models import Q, Case, When, Value, IntegerField

target_pid = 'JhZCO1vxI7'

print(f"--- TRACING PID: {target_pid} ---")

# Step 0: Raw DB Check
try:
    w = CaosWorldORM.objects.get(public_id=target_pid)
    print(f"[0] Record exists: ID={w.id}, Name='{w.name}', Status={w.status}, Active={w.is_active}")
    print(f"    Description: '{w.description}'")
except CaosWorldORM.DoesNotExist:
    print(f"[0] ERROR: Record does not exist in DB")
    sys.exit(1)

# Step 1: Base Query (mirroring home view)
ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED') \
    .exclude(description__isnull=True).exclude(description__exact='') \
    .exclude(description__iexact='None') \
    .exclude(id__endswith='00', name__startswith='Nexo Fantasma') \
    .exclude(id__endswith='00', name__startswith='Ghost')

if ms.filter(public_id=target_pid).exists():
    print(f"[1] PASSED Base Query")
else:
    print(f"[1] FAILED Base Query (likely empty description or excluded 00 logic)")
    # Check if it was the description
    if not w.description or w.description.lower() == 'none' or w.description == '':
        print(f"    REASON: Empty or 'None' description")
    sys.exit(0)

# Step 2: Permissions (Simulating Superadmin)
# Superadmin passes all filters except the base query
print(f"[2] PASSED Permissions (Simulated Superadmin)")

# Step 3: UseCase Execution
all_entities = list(ms)
usecase = GetHomeIndexUseCase()

# Inside execute() - Step 1: Trunk Grouping
print(f"\n--- USECASE INTERNALS ---")
winners_by_trunk = {}
for m in all_entities:
    trunk_id = m.id
    if '00' in m.id:
        level = len(m.id) // 2
        if level >= 7: trunk_id = m.id
        else: trunk_id = m.id.split('00')[0]
    if trunk_id not in winners_by_trunk: winners_by_trunk[trunk_id] = []
    winners_by_trunk[trunk_id].append(m)

# Find target's trunk
target_trunk = w.id # Because 01 has no 00
print(f"[UC-1] Target trunk: {target_trunk}")
if target_trunk in winners_by_trunk:
    candidates = winners_by_trunk[target_trunk]
    print(f"       Trunk candidates: {[c.id for c in candidates]}")
    candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
    winner = candidates[0]
    print(f"       Winner of trunk: {winner.id} ({winner.name})")
    if winner.public_id == target_pid:
        print(f"       [UC-1] Target PASSED Trunk Winner")
    else:
        print(f"       [UC-1] Target FAILED Trunk Winner (Lost to {winner.id})")
else:
     print(f"       [UC-1] Target trunk NOT FOUND in winners_by_trunk")

# Inside execute() - Step 2: Indexing Groups
pre_list = []
for pid, candidates in winners_by_trunk.items():
    candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
    winner = candidates[0]
    is_ghost = ('00' in winner.id and (len(winner.id)//2) < 7)
    if is_ghost and winner.id != pid: continue
    pre_list.append(winner)

indexed_groups = {}
for m in pre_list:
    if m.id.endswith('00'): continue
    parent_id = m.id[:-2]
    level = len(m.id)
    group_key = (parent_id, level)
    if group_key not in indexed_groups: indexed_groups[group_key] = []
    indexed_groups[group_key].append(m)

target_parent = w.id[:-2]
target_level = len(w.id)
target_key = (target_parent, target_level)
print(f"[UC-2] Target indexing key: {target_key}")

if target_key in indexed_groups:
    group_candidates = indexed_groups[target_key]
    print(f"       Group candidates: {[c.id for c in group_candidates]}")
    # Prioritizing Caos Prime
    group_candidates.sort(key=lambda x: (0 if x.public_id == target_pid else 1, x.id))
    final_winner = group_candidates[0]
    print(f"       Final group winner: {final_winner.id} ({final_winner.name})")
    if final_winner.public_id == target_pid:
        print(f"[UC-2] Target PASSED final indexing")
    else:
        print(f"[UC-2] Target FAILED final indexing")
else:
    print(f"[UC-2] Target group key NOT FOUND in indexed_groups")
