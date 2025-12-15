
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def dump_worlds():
    worlds = CaosWorldORM.objects.filter(is_active=True).order_by('id')
    with open('dump_worlds.txt', 'w', encoding='utf-8') as f:
        for w in worlds:
            desc = w.description if w.description else "No Desc"
            f.write(f"ID: {w.id} | Name: {w.name} | Len: {len(w.id)} | Desc: {desc[:50]}...\n")

if __name__ == '__main__':
    dump_worlds()
