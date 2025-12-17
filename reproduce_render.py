import os
import sys
import django
from django.conf import settings

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), 'src', 'Infrastructure', 'DjangoFramework'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from django.template.loader import render_to_string
from django.http import HttpRequest
from django.contrib.auth.models import User

target_id = "JhZCO1vxI7"

print(f"--- TESTING RENDER ID: {target_id} ---")

try:
    print("1. Getting Context...")
    repo = DjangoCaosRepository()
    context = GetWorldDetailsUseCase(repo).execute(target_id, None)
    
    if not context:
        print("!!! Context is None")
        exit(1)

    print("2. Rendering Template...")
    request = HttpRequest()
    request.user = User.objects.first() or User.objects.create(username='TestUser')
    context['request'] = request
    
    html = render_to_string('ficha_mundo.html', context, request=request)
    print("   SUCCESS: Template rendered.")
    
except Exception as e:
    print(f"!!! CRASH: {e}")
    import traceback
    traceback.print_exc()
