from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

total_live = CaosWorldORM.objects.filter(status='LIVE').count()
total_visible = CaosWorldORM.objects.filter(status='LIVE', visible_publico=True).count()

print(f"Total LIVE: {total_live}")
print(f"Total LIVE & VISIBLE: {total_visible}")
