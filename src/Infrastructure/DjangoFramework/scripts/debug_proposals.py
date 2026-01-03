import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM, CaosWorldORM

def check_pending_proposals():
    print("--- Checking PENDING Proposals in DB ---")
    pending = CaosNarrativeVersionORM.objects.filter(status='PENDING')
    count = pending.count()
    print(f"Total PENDING versions found: {count}")
    
    if count == 0:
        print("WARNING: No pending proposals found in the entire database!")
    
    for p in pending:
        print(f"ID: {p.id} | Ver: {p.version_number} | Title: {p.proposed_title} | Author: {p.author} | World: {p.narrative.world.name if p.narrative else 'N/A'}")

    print("\n--- Checking World Permissions ---")
    worlds = CaosWorldORM.objects.all()
    for w in worlds:
        print(f"World: {w.name} | Author: {w.author} | Allow Proposals: {w.allow_proposals}")

if __name__ == "__main__":
    check_pending_proposals()
