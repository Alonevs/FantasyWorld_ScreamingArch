from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

print("Starting Migration...")
qs = CaosWorldORM.objects.filter(status='LIVE', visible_publico=False)
count = qs.count()
print(f"Found {count} LIVE entities that are hidden. Fixing...")

qs.update(visible_publico=True)

print("Migration Complete. All LIVE entities are now visible.")
