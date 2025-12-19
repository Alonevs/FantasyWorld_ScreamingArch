from django.db import connection

def run():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'caos_image_proposals'")
        columns = [row[0] for row in cursor.fetchall()]
        print("COLUMNS IN caos_image_proposals:")
        result = ""
        for c in columns:
            print(f"- {c}")
            result += f"{c}\n"
        open('image_cols.txt', 'w').write(result)

if __name__ == "__main__":
    import os
    import django
    import sys
    project_root = r'C:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework'
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    run()
