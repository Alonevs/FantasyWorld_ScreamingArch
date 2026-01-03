import os
import django
import sys
from django.db.models import Count

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth import get_user_model
from src.Infrastructure.DjangoFramework.persistence.models import CaosComment

User = get_user_model()

# Replace with the username you are testing with
target_name = "xico"
user = User.objects.filter(username__istartswith=target_name).first()

if not user:
    user = User.objects.first() # Flash fallback

print(f"--- DIAGNOSIS FOR USER: {user.username} (ID: {user.id}) ---")

all_comments = CaosComment.objects.all()
print(f"Total Comments in DB: {all_comments.count()}")

# Group by User
by_user = all_comments.values('user__username').annotate(total=Count('id')).order_by('-total')
print("\nComments by Author:")
for entry in by_user:
    print(f" - {entry['user__username']}: {entry['total']}")

# Group by Status
by_status = all_comments.values('status').annotate(total=Count('id')).order_by('-total')
print("\nComments by Status:")
for entry in by_status:
    print(f" - '{entry['status']}': {entry['total']}")

# Check "Incoming" candidates (Not by user, but possibly on user's stuff)
# heuristic: keys starting with known prefixes
incoming_candidates = all_comments.exclude(user=user)
print(f"\nPotential Incoming Comments (Not by {user.username}): {incoming_candidates.count()}")
print("Sample of Incoming Candidates:")
for c in incoming_candidates[:10]:
    print(f" - ID {c.id} on '{c.entity_key}' (Status: '{c.status}') by {c.user.username}")
