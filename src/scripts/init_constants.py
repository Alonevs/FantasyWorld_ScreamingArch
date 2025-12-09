import os
import sys
from pathlib import Path
import django
import random

# Setup path to project root
current_path = Path(__file__).resolve().parent
project_root = current_path.parents[1]
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src' / 'Infrastructure' / 'DjangoFramework'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
import nanoid

def generate_nanoid():
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

def seed_constants():
    world_names = [
        "Inframundo", 
        "Plano Bendito", 
        "Mundo Espiritual", 
        "Capilla de los Héroes", 
        "Vacío Abisal"
    ]
    
    results = []
    
    print("--- SEEDING CONSTANTS ---")
    for name in world_names:
        # Check if exists by name (approximate)
        w = CaosWorldORM.objects.filter(name=name).first()
        if not w:
            new_id = generate_nanoid()
            w = CaosWorldORM.objects.create(
                id=new_id,
                public_id=new_id,
                name=name,
                description=f"Constante cosmológica principal: {name}",
                status="LIVE", # Directly LIVE for constants
                visible_publico=True,
                current_author_name="Sistema"
            )
            print(f"Created: {name} ({w.public_id})")
        else:
            print(f"Exists: {name} ({w.public_id})")
            
        results.append({"name": w.name, "url": f"/mundo/{w.public_id}/"})
        
    return results

if __name__ == '__main__':
    seed_constants()
