import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def list_all():
    worlds = CaosWorldORM.objects.filter(is_active=True)
    all_images = {}
    
    for w in worlds:
        if not w.metadata: continue
        
        # Gallery
        gallery = w.metadata.get('gallery_log', {})
        for f in gallery:
            all_images[f] = f"World: {w.name} (Gallery)"
            
        # Cover
        cover = w.metadata.get('cover_image')
        if cover:
            all_images[cover] = f"World: {w.name} (Cover)"
            
        # Timeline
        timeline = w.metadata.get('timeline', {})
        for year, data in timeline.items():
            tg = data.get('gallery_log', {})
            for tf in tg:
                all_images[tf] = f"World: {w.name} (Period {year} Gallery)"
            tc = data.get('cover_image')
            if tc:
                all_images[tc] = f"World: {w.name} (Period {year} Cover)"

    print(f"Total Unique Images in Metadata: {len(all_images)}")
    for img in sorted(all_images.keys()):
        if 'realidades' in img.lower() or 'roberto' in img.lower():
            print(f"{img} -> {all_images[img]}")

if __name__ == "__main__":
    list_all()
