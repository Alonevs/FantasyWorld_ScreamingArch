import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM, User

def repair_ghost_proposals():
    print("=== REPAIRING GHOST PROPOSALS ===")
    
    # SYSTEM AUTHOR FALLBACK
    admin = User.objects.filter(is_superuser=True).first()
    
    # 1. Find Narratives with current_version=0 but NO versions in history
    narratives = CaosNarrativeORM.objects.filter(current_version_number=0)
    
    count = 0
    for n in narratives:
        # Check if version exists
        versions_count = n.versiones.count()
        if versions_count == 0:
            print(f" > FIXED: {n.titulo} ({n.nid}) - Had 0 versions. Created V0 Proposal.")
            
            CaosNarrativeVersionORM.objects.create(
                narrative=n,
                proposed_title=n.titulo,
                proposed_content=n.contenido,
                version_number=0, # Proposal is usually ver 0 or 1. Let's stick to logic.
                status='PENDING',
                change_log="Recuperación de propuesta fantasma",
                author=n.created_by if n.created_by else admin
            )
            count += 1
        else:
            print(f" . OK: {n.titulo} has versions.")

    print(f"=== DONE. Repaired {count} narratives. ===")

if __name__ == "__main__":
    repair_ghost_proposals()
