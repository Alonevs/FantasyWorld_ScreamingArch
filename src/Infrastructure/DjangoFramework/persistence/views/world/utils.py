"""
Utilidades internas para vistas de mundos.
"""
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog


from src.Infrastructure.DjangoFramework.persistence.views.view_utils import log_event

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u
