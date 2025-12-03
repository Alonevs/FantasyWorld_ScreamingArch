from django.contrib import admin
from django.urls import path, include
from src.Infrastructure.DjangoFramework.persistence.views import *

urlpatterns = [
    # Tailwind
    path("__reload__/", include("django_browser_reload.urls")),
    
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Core
    path('', home, name='home'),
    path('control/', centro_control, name='centro_control'),
    path('mundo/<str:public_id>/', ver_mundo, name='ver_mundo'),
    path('mapa/<str:public_id>/', mapa_arbol, name='mapa_arbol'),
    
    # Gestión
    path('borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    path('escanear/<str:jid>/', escanear_planeta, name='escanear_planeta'),
    path('foto_extra/<str:jid>/', generar_foto_extra, name='generar_foto_extra'),
    path('toggle_visible/<str:jid>/', toggle_visibilidad, name='toggle_visibilidad'),
    path('cover/<str:jid>/<str:filename>/', set_cover_image, name='set_cover_image'),
    path('borrar_foto/<str:jid>/<str:filename>/', borrar_foto, name='borrar_foto'),
    path('init_hemisferios/<str:jid>/', init_hemisferios, name='init_hemisferios'),
    path('subir_foto/<str:jid>/', subir_imagen_manual, name='subir_imagen_manual'),

    # Versionado
    path('revision/<int:version_id>/', revisar_version, name='revisar_version'),
    path('aprobar/<int:version_id>/', aprobar_version, name='aprobar_version'),
    path('rechazar/<int:version_id>/', rechazar_version, name='rechazar_version'),
    path('publicar/<int:version_id>/', publicar_version, name='publicar_version'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),

    # Narrativa
    path('narrativa/indice/<str:jid>/', ver_narrativa_mundo, name='ver_narrativa_mundo'),
    path('narrativa/crear/<str:jid>/<str:tipo_codigo>/', crear_nueva_narrativa, name='crear_narrativa'),
    path('narrativa/subcrear/<str:parent_nid>/<str:tipo_codigo>/', crear_sub_narrativa, name='crear_sub_narrativa'),
    path('narrativa/<str:nid>/', leer_narrativa, name='leer_narrativa'),
    path('narrativa/editar/<str:nid>/', editar_narrativa, name='editar_narrativa'),
    path('narrativa/borrar/<str:nid>/', borrar_narrativa, name='borrar_narrativa'),

    # APIs
    path('api/preview_foto/<str:jid>/', api_preview_foto, name='api_preview_foto'),
    path('api/save_foto/<str:jid>/', api_save_foto, name='api_save_foto'),
    path('api/update_meta/<str:jid>/', api_update_image_metadata, name='api_update_image_metadata'),
]
