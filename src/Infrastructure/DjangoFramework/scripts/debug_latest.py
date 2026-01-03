import os
import django
import sys

sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosNarrativeVersionORM, CaosNotification, User

def debug_latest():
    print("=== LATEST 5 NARRATIVES ===")
    for n in CaosNarrativeORM.objects.order_by('-created_at')[:5]:
        print(f"[{n.created_at}] NID:{n.nid} Title:{n.titulo} Ver:{n.current_version_number} Author:{n.created_by}")

    print("\n=== LATEST 5 VERSIONS ===")
    for v in CaosNarrativeVersionORM.objects.order_by('-created_at')[:5]:
        print(f"[{v.created_at}] ID:{v.id} Narr:{v.narrative.nid} Title:{v.proposed_title} Status:{v.status} Author:{v.author}")

    print("\n=== LATEST 5 NOTIFICATIONS ===")
    for notif in CaosNotification.objects.order_by('-created_at')[:5]:
        print(f"[{notif.created_at}] User:{notif.user} Title:{notif.title} Read:{notif.read_at}")

if __name__ == "__main__":
    debug_latest()
