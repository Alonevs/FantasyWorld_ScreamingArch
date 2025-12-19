import os
import django
import sys
from django.db import connection

def run():
    with connection.cursor() as cursor:
        print("Starting manual SQL fixes...")
        
        # 1. Check and Add reason to caos_image_proposals
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'caos_image_proposals'")
        cols_img = [row[0] for row in cursor.fetchall()]
        if 'reason' not in cols_img:
            print("Adding 'reason' to 'caos_image_proposals'...")
            cursor.execute("ALTER TABLE caos_image_proposals ADD COLUMN reason TEXT DEFAULT '';")
        
        # 2. Check and Add allow_proposals to caos_worlds
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'caos_worlds'")
        cols_worlds = [row[0] for row in cursor.fetchall()]
        if 'allow_proposals' not in cols_worlds:
            print("Adding 'allow_proposals' to 'caos_worlds'...")
            cursor.execute("ALTER TABLE caos_worlds ADD COLUMN allow_proposals BOOLEAN DEFAULT TRUE;")
            
        # 3. Check and Remove id_codificado from caos_worlds
        if 'id_codificado' in cols_worlds:
            print("Removing 'id_codificado' from 'caos_worlds'...")
            cursor.execute("ALTER TABLE caos_worlds DROP COLUMN id_codificado;")
            
        print("Manual SQL fixes completed.")

if __name__ == "__main__":
    project_root = r'C:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework'
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    run()
