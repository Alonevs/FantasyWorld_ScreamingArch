import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment, CaosWorldORM, CaosNarrativeORM

import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment
from src.Shared.Services.SocialService import SocialService

User = get_user_model()

# Replace with the username you are testing with
target_name = "xico"
user = User.objects.filter(username__istartswith=target_name).first()

if not user:
    user = User.objects.first()
    print(f"User '{target_name}' not found, using '{user.username}' instead.")

print(f"--- Debugging Social Hub for User: {user.username} (ID: {user.id}) ---")

# 1. Discover Content using SocialService
content = SocialService.discover_user_content(user, include_proposals=True)

my_entity_keys = set()
# Process Worlds
for w in content['worlds']:
    my_entity_keys.add(str(w.id)) # JID
    my_entity_keys.add(w.public_id) # Public ID
    my_entity_keys.add(f"WORLD_{w.public_id}") # Prefixed

# Process Narratives
for n in content['narratives']:
    my_entity_keys.add(n.nid)
    my_entity_keys.add(n.public_id)
    if n.public_id: my_entity_keys.add(f"narr_{n.public_id}")

# Process Images
for img in content['images']:
    filename = img['filename']
    my_entity_keys.add(f"IMG_{filename}")
    my_entity_keys.add(f"img_{filename}")
    my_entity_keys.add(filename)
    
# Process Proposals
for p in content['proposals']:
    my_entity_keys.add(f"VER_{p.id}")

# Expand keys to ensure case-insensitive matching (DB keys might be UPPER or mixed)
expanded_keys = set()
for k in my_entity_keys:
    if k:
        expanded_keys.add(k)
        expanded_keys.add(k.upper())
        expanded_keys.add(k.lower())

print(f"Discovered {len(my_entity_keys)} unique Entity Keys (Expanded to {len(expanded_keys)} variants).")
        
# DEBUG: Check specifically for the missing keys found in diagnosis
missing_candidates = ['IMG_CAOS_PRIME_V1.WEBP', 'IMG_00004-3278823691.WEBP', 'IMG_REALIDADES_V1.WEBP']
print("\n--- Checking Missing Candidates in EXPANDED Keys ---")
for cand in missing_candidates:
    print(f"Checking '{cand}':")
    if cand in expanded_keys:
        print(f"  [MATCH] Found exact match in expanded set.")
    else:
        print(f"  [FAIL] Still missing.")

# 2. Check Comments
criterion_on_my_entity = Q(entity_key__in=list(expanded_keys))
criterion_reply_to_me = Q(parent_comment__user=user)

base_query = CaosComment.objects.filter(
    criterion_on_my_entity | criterion_reply_to_me
).exclude(
    user=user # Don't show my own comments
)

total_count = base_query.count()
print(f"Total Comments Visible in Hub: {total_count}")

status_counts = {
    'NEW': base_query.filter(status='NEW').count(),
    'REPLIED': base_query.filter(status='REPLIED').count(),
    'ARCHIVED': base_query.filter(status='ARCHIVED').count(),
    'OTHER': base_query.exclude(status__in=['NEW', 'REPLIED', 'ARCHIVED']).count()
}

print("Status Distribution:")
for k, v in status_counts.items():
    print(f" - {k}: {v}")

print("\n--- Listing Visible Comments ---")
for c in base_query:
    print(f"ID: {c.id} | User: {c.user.username} | Status: {c.status} | Key: {c.entity_key} | Content: {c.content[:30]}...")
    
print("\n--- Done ---")

