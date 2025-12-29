import os
import sys
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.views.world_views import ver_mundo

factory = RequestFactory()
request = factory.get('/mundo/XVCqUPzDXy/')
request.user = User.objects.first()

try:
    print("Iniciando prueba de ver_mundo...")
    response = ver_mundo(request, 'XVCqUPzDXy')
    print(f"Status Code: {response.status_code}")
except Exception:
    print("¡ERROR DETECTADO!")
    traceback.print_exc()
