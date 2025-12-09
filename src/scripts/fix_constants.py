import os
import sys
from pathlib import Path
import django
import json

# Setup path to project root
current_path = Path(__file__).resolve().parent
project_root = current_path.parents[1]
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src' / 'Infrastructure' / 'DjangoFramework'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, MetadataTemplate
import nanoid

def generate_nanoid():
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10)

def fix_constants():
    target_names = [
        "Inframundo", 
        "Plano Bendito", 
        "Mundo Espiritual", 
        "Capilla de los Héroes", 
        "Vacío Abisal"
    ]
    
    print("--- FIXING CONSTANTS HIERARCHY ---")
    
    # 1. DELETE ORPHANS
    deleted_count, _ = CaosWorldORM.objects.filter(name__in=target_names).delete()
    print(f"Deleted {deleted_count} existing constant worlds.")
    
    # 2. FIND ROOT
    # Intenta encontrar por nombre o ID '01'
    root = CaosWorldORM.objects.filter(name__icontains="Caos").first()
    if not root:
        root = CaosWorldORM.objects.filter(id='01').first()
        
    if not root:
        print("CRITICAL: Root 'Caos' not found. Aborting.")
        return

    print(f"Root found: {root.name} (J-ID: {root.id})")
    
    # 3. CREATE CHILDREN
    new_values = []
    
    # Determine base J-ID for children. 
    # Assumes J-ID structure: ParentID + 2 digits (e.g. 01 -> 0101, 0102...)
    # We simply find the max existing child to be safe, or start at 01
    
    # Simple strategy: Root ID + 2 digit index starting from 01
    # Note: real logic might be more complex, but this suffices for POC fixing
    
    for i, name in enumerate(target_names):
        suffix = f"{i+1:02d}"
        new_jid = f"{root.id}{suffix}"
        
        # Check collision just in case
        if CaosWorldORM.objects.filter(id=new_jid).exists():
            print(f"Warning: J-ID {new_jid} exists, skipping creation for {name}")
            existing = CaosWorldORM.objects.get(id=new_jid)
            new_values.append({"name": existing.name, "url": f"/mundo/{existing.public_id}/"})
            continue
            
        new_public_id = generate_nanoid()
        
        child = CaosWorldORM.objects.create(
            id=new_jid,
            public_id=new_public_id,
            name=name,
            description=f"Constante cosmológica vinculada a {root.name}.",
            status="LIVE",
            visible_publico=True,
            current_author_name="Sistema"
        )
        print(f"Created Child: {child.name} (J-ID: {child.id})")
        new_values.append({"name": child.name, "url": f"/mundo/{child.public_id}/"})

    # 4. UPDATE METADATA TEMPLATE
    tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
    if tpl:
        schema = tpl.schema_definition
        # Update the 'constantes' part
        if 'constantes' in schema:
            schema['constantes']['values'] = new_values
            tpl.schema_definition = schema
            tpl.save()
            print("Updated 'CHAOS' MetadataTemplate with new child links.")
        else:
            print("key 'constantes' not found in schema.")
    else:
        print("Template 'CHAOS' not found.")

if __name__ == '__main__':
    fix_constants()
