import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM, CaosWorldORM
from django.db.models import Q

def check_dashboard_visibility():
    print("--- Simulating Dashboard Visibility Logic ---")
    
    # Simulate for user 'Alone' (presumably Admin/Superuser)
    try:
        user = User.objects.get(username='Alone')
    except User.DoesNotExist:
        user = User.objects.filter(is_superuser=True).first()
        print(f"User 'Alone' not found, using '{user.username}'")

    print(f"User: {user.username} | Superuser: {user.is_superuser}")
    
    # LOGIC FROM VIEWS (Simplified)
    is_global_admin = user.is_superuser or (hasattr(user, 'profile') and user.profile.rank == 'SUPERADMIN')
    
    if is_global_admin:
        print(">> Logic: GLOBAL ADMIN (All visible)")
        qs = CaosNarrativeVersionORM.objects.all()
    else:
        print(">> Logic: TERRITORIAL (Filtered)")
        # ... logic copy ...
        visible_ids = [user.id]
        minion_ids = []
        if hasattr(user, 'profile'):
             minion_ids = list(user.profile.collaborators.values_list('user__id', flat=True))
             visible_ids.extend(minion_ids)
        
        print(f"Visible Authors: {visible_ids}")
        
        # Logic from view:
        if minion_ids:
            my_narr = Q(author_id=user.id)
            minion_narr = Q(author_id__in=minion_ids) & (
                Q(narrative__world__author=user) |
                Q(narrative__world__author_id__in=minion_ids)
            )
            n_territorial = my_narr | minion_narr
        else:
            n_territorial = Q(author_id=user.id)
            
        qs = CaosNarrativeVersionORM.objects.filter(n_territorial)

    pending = qs.filter(status='PENDING')
    print(f"Pending Count: {pending.count()}")
    for p in pending:
        print(f" - [v{p.version_number}] {p.proposed_title} (Author: {p.author})")

if __name__ == "__main__":
    check_dashboard_visibility()
