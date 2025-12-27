import os
import sys
import django

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))
# Removed the prefix 'src.' if 'src' is in path, but usually Django expects the full module path from root.
# Let's try adding the Infrastructure folder specifically if needed, but standard is 'src' as root?
# Actually, manage.py uses 'src.Infrastructure...' so sys.path must include the PARENT of src (getcwd).
# If that failed, it means it can't find 'src'.
# Let's try to be safer.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.Infrastructure.DjangoFramework.settings")
django.setup()

from django.contrib.auth import get_user_model
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile, CaosWorldORM
from src.Infrastructure.DjangoFramework.persistence.policies import can_user_propose_on

User = get_user_model()

def get_or_create_user(username, rank='USER'):
    u, created = User.objects.get_or_create(username=username)
    if created:
        u.set_password('1234')
        u.save()
        print(f"✅ Created User: {username}")
    else:
        print(f"ℹ️ User {username} already exists")
        
    if not hasattr(u, 'profile'):
        UserProfile.objects.create(user=u, rank=rank)
        print(f"  -> Created Profile with Rank: {rank}")
    else:
        u.profile.rank = rank
        u.profile.save()
        print(f"  -> Updated Profile Rank to: {rank}")
    return u

# 1. Create Luis and Roberto
luis = get_or_create_user('Luis', 'USER')
robert = get_or_create_user('Roberto', 'USER')

# 2. Debug 'Pepe' (Admin) on 'Abismo Prime' (Superuser World)
print("\n--- DEBUGGING POLICY ---")
try:
    pepe = User.objects.get(username='Pepe')
    # Buscar Abismo Prime (Id or Name)
    # Assuming the user provided ID or knowing it is from Superuser
    # Let's find ANY world by Alone (Superuser)
    alone = User.objects.get(username='Alone')
    
    # Try to find 'Abismo Prime' or just take first world
    worlds = CaosWorldORM.objects.filter(author=alone)
    if worlds.exists():
        w = worlds.first()
        print(f"Testing with World: '{w.name}' (ID: {w.id}) by {w.author.username}")
        print(f"  - Author is Superuser? {w.author.is_superuser}")
        
        print(f"Testing User: {pepe.username}")
        print(f"  - Rank: {pepe.profile.rank}")
        
        can_prop = can_user_propose_on(pepe, w)
        print(f"💰 RESULT: can_user_propose_on(Pepe, World) = {can_prop}")
        
        if not can_prop:
            print("  ❌ WHY? Checking policy logic manually here...")
            is_admin = pepe.profile.rank in ['ADMIN', 'SUPERADMIN']
            is_orph_or_super = (not w.author) or w.author.is_superuser
            print(f"  - Is Admin Rank? {is_admin}")
            print(f"  - Is Orphan/Super? {is_orph_or_super}")
            
    else:
        print("⚠️ No worlds found for 'Alone' to test.")

except Exception as e:
    print(f"❌ Error during debug: {e}")
