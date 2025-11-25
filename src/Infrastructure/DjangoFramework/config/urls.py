from django.contrib import admin
from django.urls import path
from src.Infrastructure.DjangoFramework.persistence.views import ver_mundo, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),             # <--- Nueva Portada
    path('mundo/<str:jid>/', ver_mundo, name='ver_mundo'),
]