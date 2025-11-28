from django.contrib import admin
from django.urls import path
from src.Infrastructure.DjangoFramework.persistence.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('control/', centro_control, name='centro_control'),
    path('mundo/<str:jid>/', ver_mundo, name='ver_mundo'),
    path('revision/<int:version_id>/', revisar_version, name='revisar_version'),
    
    path('borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    path('aprobar/<int:version_id>/', aprobar_version, name='aprobar_version'),
    path('rechazar/<int:version_id>/', rechazar_version, name='rechazar_version'),
    path('publicar/<int:version_id>/', publicar_version, name='publicar_version'),
    
    path('foto_extra/<str:jid>/', generar_foto_extra, name='generar_foto_extra'),
    path('texto_extra/<str:jid>/', generar_texto_extra, name='generar_texto_extra'),
    path('toggle_visible/<str:jid>/', toggle_visibilidad, name='toggle_visibilidad'),
    
    # NUEVA RUTA: Borrar foto específica
    # Recibe el ID del mundo y el nombre del archivo
    path('borrar_foto/<str:jid>/<str:filename>/', borrar_foto, name='borrar_foto'),
    path('escanear/<str:jid>/', escanear_planeta, name='escanear_planeta'),
    path('narrativa/<str:nid>/', leer_narrativa, name='leer_narrativa'),
    path('narrativa/editar/<str:nid>/', editar_narrativa, name='editar_narrativa'),
    path('narrativa/crear/<str:jid>/<str:tipo_codigo>/', crear_nueva_narrativa, name='crear_narrativa'),
    path('narrativa/subcrear/<str:parent_nid>/<str:tipo_codigo>/', crear_sub_narrativa, name='crear_sub_narrativa'),
    path('narrativa/indice/<str:jid>/', ver_narrativa_mundo, name='ver_narrativa_mundo'),
    path('narrativa/borrar/<str:nid>/', borrar_narrativa, name='borrar_narrativa'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),
]