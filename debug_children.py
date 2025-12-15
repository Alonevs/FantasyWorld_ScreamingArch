
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from django.contrib.auth.models import User

def debug_children():
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- DIAGNOSTIC START ---\n")
        
        # 1. Check ORM Existence
        ids = ["0101", "010102", "010104"]
        for i in ids:
            try:
                w = CaosWorldORM.objects.get(id=i)
                f.write(f"[{i}] Name: {w.name}\n")
                f.write(f"       Status: {w.status}\n")
                f.write(f"       Visible: {w.visible_publico}\n")
                f.write(f"       DeletedAt: {w.deleted_at}\n")
                f.write(f"       IsActive: {getattr(w, 'is_active', 'N/A')}\n")
            except CaosWorldORM.DoesNotExist:
                f.write(f"[{i}] NOT FOUND IN DB!\n")

        # 2. Check UseCase Logic
        f.write("\n--- USE CASE EXECUTION ---\n")
        repo = DjangoCaosRepository()
        u = User.objects.filter(is_superuser=True).first() or User.objects.first()
        
        try:
            target = "AbismoPrime" 
            try:
                w0101 = CaosWorldORM.objects.get(id="0101")
                f.write(f"AbismoPrime public_id in DB: {w0101.public_id}\n")
                if w0101.public_id: target = w0101.public_id
            except: f.write("AbismoPrime 0101 not found for target logic.\n")
            
            f.write(f"Executing for target: {target} (User: {u})\n")
            
            ctx = GetWorldDetailsUseCase(repo).execute(target, u)
            
            if not ctx:
                f.write("UseCase returned None!\n")
            else:
                hijos = ctx.get('hijos', []) or ctx.get('children', [])
                f.write(f"Children Count in Context: {len(hijos)}\n")
                for h in hijos:
                    f.write(f" -> Child: {h.get('name')} (ID: {h.get('public_id')})\n")
                    
        except Exception as e:
            f.write(f"ERROR IN USE CASE: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("--- DIAGNOSTIC END ---\n")

if __name__ == "__main__":
    debug_children()
