from django.contrib import admin
from django.urls import path, include
from src.Infrastructure.DjangoFramework.persistence.views import *

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('control/', centro_control, name='centro_control'),
    path('mundo/<str:jid>/', ver_mundo, name='ver_mundo'),
    path('revision/<int:version_id>/', revisar_version, name='revisar_version'),
    
    path('narrativa/<str:nid>/', leer_narrativa, name='leer_narrativa'),
    path('narrativa/editar/<str:nid>/', editar_narrativa, name='editar_narrativa'),
    path('narrativa/crear/<str:jid>/<str:tipo_codigo>/', crear_nueva_narrativa, name='crear_narrativa'),
    path('narrativa/subcrear/<str:parent_nid>/<str:tipo_codigo>/', crear_sub_narrativa, name='crear_sub_narrativa'),
    path('narrativa/indice/<str:jid>/', ver_narrativa_mundo, name='ver_narrativa_mundo'),
    path('narrativa/borrar/<str:nid>/', borrar_narrativa, name='borrar_narrativa'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),
    path('subir_foto/<str:jid>/', subir_imagen_manual, name='subir_imagen_manual'),
    path('cover/<str:jid>/<str:filename>/', set_cover_image, name='set_cover_image'),
    path('init_hemisferios/<str:jid>/', init_hemisferios, name='init_hemisferios'),

    # World Management
    path('mundo/editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    path('mundo/borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('mundo/visibilidad/<str:jid>/', toggle_visibilidad, name='toggle_visibilidad'),
    
    # Version Control
    path('version/aprobar/<int:version_id>/', aprobar_version, name='aprobar_version'),
    path('version/rechazar/<int:version_id>/', rechazar_version, name='rechazar_version'),
    path('version/publicar/<int:version_id>/', publicar_version, name='publicar_version'),

    # Image Management
    path('foto/borrar/<str:jid>/<str:filename>/', borrar_foto, name='borrar_foto'),
    path('api/preview_foto/<str:jid>/', api_preview_foto, name='api_preview_foto'),
    path('api/save_foto/<str:jid>/', api_save_foto, name='api_save_foto'),
]