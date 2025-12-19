from django.db import connection

def run():
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        print("TABLES FOUND:")
        for t in tables:
            print(f"- {t}")
            
        if 'caos_worlds' in tables:
            print("\nCOLUMNS IN caos_worlds:")
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'caos_worlds'")
            for row in cursor.fetchall():
                print(f"  * {row[0]}")
        else:
            print("\nWARNING: caos_worlds NOT FOUND")

if __name__ == "__main__":
    import os
    import django
    import sys
    # Add src/Infrastructure/DjangoFramework to sys.path
    project_root = r'C:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework'
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    run()
