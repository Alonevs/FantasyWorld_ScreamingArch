import os
import django
import sys

# Setup Django Environment
sys.path.append('c:/Users/xico0/Desktop/FantasyWorld_ScreamingArch')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.get_world_narratives import GetWorldNarrativesUseCase

def debug_visibility():
    try:
        user = User.objects.filter(username='Xico').first()
        if not user:
            user = User.objects.filter(is_superuser=True).first()
            print(f"User 'Xico' not found. Using '{user.username}'")

        world = CaosWorldORM.objects.first()
        if not world:
            print("No worlds found.")
            return

        print(f"Checking visibility for World: {world.name} (ID: {world.id}) for User: {user.username}")
        
        repo = DjangoCaosRepository()
        use_case = GetWorldNarrativesUseCase(repo)
        
        # We need to simulate the permissions check that happens inside current implementation of UseCase?
        # UseCase implementation in previous turn:
        # It takes (world_id, user, period_slug)
        
        context = use_case.execute(world.id, user)
        
        if not context:
            print("UseCase returned None.")
            return

        lores = context.get('lores', [])
        print(f"Found {len(lores)} Lores:")
        for l in lores:
            print(f" - {l.titulo} (v{l.current_version_number}) [Typo: {l.tipo}]")
            
        historias = context.get('historias', [])
        print(f"Found {len(historias)} Historias:")
        for h in historias:
            print(f" - {h.titulo} (v{h.current_version_number})")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_visibility()
