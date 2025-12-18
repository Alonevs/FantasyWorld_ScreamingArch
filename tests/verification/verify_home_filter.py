
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

def verify_home_filter():
    # Simulate Query from View (Exact Match)
    ms = CaosWorldORM.objects.exclude(status='DRAFT').exclude(description__isnull=True).exclude(description__exact='').exclude(description__iexact='None').order_by('id')
    
    print(f"Total Visible: {ms.count()}")
    
    visible_names = [m.name for m in ms]
    # print("Visible Entities:")
    # for name in visible_names:
    #     print(f" - {name}")

    failures = False
    
    if "plataforma 1º" in visible_names:
        print("✅ PASS: 'plataforma 1º' is visible.")
    else:
        print("❌ FAIL: 'plataforma 1º' is HIDDEN.")
        failures = True

    if "Universo" in visible_names:
        print("❌ FAIL: 'Universo' (Empty Gap) is visible.")
        failures = True
    else:
        print("✅ PASS: 'Universo' (Empty Gap) is HIDDEN.")
        
    if "Deep Test Country" in visible_names:
        print("ℹ️ NOTE: 'Deep Test Country' is visible (it has a desc).")
        
    if not failures:
        print("\n🏆 ALL TESTS PASSED.")

if __name__ == '__main__':
    verify_home_filter()
