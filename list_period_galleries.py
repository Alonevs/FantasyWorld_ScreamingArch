
from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
import json

def list_period_galleries():
    periods = TimelinePeriod.objects.all().select_related('world')
    for p in periods:
        print(f"Period: {p.title} (World: {p.world.name} - {p.world.public_id})")
        if p.metadata and 'gallery_log' in p.metadata:
            log = p.metadata['gallery_log']
            for filename in log.keys():
                print(f"  - |{filename}| (Uploader: {log[filename].get('uploader')})")
        else:
            print("  - No gallery_log in metadata")

if __name__ == "__main__":
    list_period_galleries()
