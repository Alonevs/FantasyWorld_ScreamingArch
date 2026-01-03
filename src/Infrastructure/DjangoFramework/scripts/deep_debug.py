import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeVersionORM, CaosVersionORM, CaosNarrativeORM, User

def deep_debug():
    print("=== DEEP DEBUG USERS ===")
    for u in User.objects.all():
        print(f"User: {u.username} (ID: {u.id}) | Superuser: {u.is_superuser}")

    print("\n=== DEEP DEBUG NARRATIVE VERSIONS (ALL) ===")
    n_versions = CaosNarrativeVersionORM.objects.all()
    print(f"Total Narrative Versions: {n_versions.count()}")
    for nv in n_versions:
        print(f"[NV ID: {nv.id}] Ver: {nv.version_number} | Status: '{nv.status}' | Title: '{nv.proposed_title}' | Author: {nv.author} | World Author: {nv.narrative.world.author}")

    print("\n=== DEEP DEBUG WORLD VERSIONS (ALL) ===")
    w_versions = CaosVersionORM.objects.all()
    print(f"Total World Versions: {w_versions.count()}")
    for wv in w_versions:
        print(f"[WV ID: {wv.id}] Ver: {wv.version_number} | Status: '{wv.status}' | Name: '{wv.proposed_name}' | Author: {wv.author} | Change Type: {wv.change_type}")

    print("\n=== DEEP DEBUG NARRATIVES (PENDING CHECK) ===")
    # Check narratives that might be 'ghosts' (version 0 but no version row?)
    narratives = CaosNarrativeORM.objects.all()
    for n in narratives:
        if n.current_version_number == 0 :
            print(f"[N ID: {n.nid}] TITLE: {n.titulo} | CURRENT_VER: {n.current_version_number}")

if __name__ == "__main__":
    deep_debug()
