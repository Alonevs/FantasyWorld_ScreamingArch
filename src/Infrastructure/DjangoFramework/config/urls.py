from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from src.Infrastructure.DjangoFramework.persistence.views.world_views import (
    home, ver_mundo, editar_mundo, borrar_mundo, 
    toggle_lock, toggle_visibilidad, init_hemisferios, escanear_planeta,
    mapa_arbol, comparar_version, ver_metadatos
)
from src.Infrastructure.DjangoFramework.persistence.views.ai_views import analyze_metadata_api
from src.Infrastructure.DjangoFramework.persistence.views.dashboard_views import (
    dashboard, aprobar_propuesta, rechazar_propuesta, publicar_version, 
    restaurar_version, borrar_propuesta, borrar_propuestas_masivo,
    aprobar_narrativa, rechazar_narrativa, publicar_narrativa, restaurar_narrativa, borrar_narrativa_version,
    aprobar_imagen, rechazar_imagen, aprobar_propuestas_masivo
)
from src.Infrastructure.DjangoFramework.persistence.views.media_views import (
    api_preview_foto, api_save_foto, api_update_image_metadata, 
    subir_imagen_manual, set_cover_image, borrar_foto, generar_foto_extra
)
from src.Infrastructure.DjangoFramework.persistence.views.narrative_views import (
    ver_narrativa_mundo, leer_narrativa, editar_narrativa, borrar_narrativa, 
    crear_nueva_narrativa, crear_sub_narrativa, revisar_narrativa_version,
    pre_crear_root, pre_crear_child
)

urlpatterns = [
    # Tailwind (Recarga automática en desarrollo)
    path("__reload__/", include("django_browser_reload.urls")),
    
    # Admin y Autenticación
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # ==========================================
    # CORE (Mundos)
    # ==========================================
    path('', home, name='home'),
    path('mundo/<str:public_id>/', ver_mundo, name='ver_mundo'),
    path('mapa/<str:public_id>/', mapa_arbol, name='mapa_arbol'),
    
    # ==========================================
    # GESTIÓN (Acciones sobre mundos)
    # ==========================================
    path('crear/', home, name='crear_mundo'), # Asumiendo que home maneja creación por POST
    path('metadatos/<str:public_id>/', ver_metadatos, name='ver_metadatos'), # Added path
    path('borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    
    # 🔒 BLOQUEO Y VISIBILIDAD
    path('lock/<str:jid>/', toggle_lock, name='toggle_lock'),
    path('toggle_visible/<str:jid>/', toggle_visibilidad, name='toggle_visibilidad'),
    
    # FOTOS Y MEDIA
    path('escanear/<str:jid>/', escanear_planeta, name='escanear_planeta'),
    path('foto_extra/<str:jid>/', generar_foto_extra, name='generar_foto_extra'),
    path('cover/<str:jid>/<str:filename>/', set_cover_image, name='set_cover_image'),
    path('borrar_foto/<str:jid>/<str:filename>/', borrar_foto, name='borrar_foto'),
    path('init_hemisferios/<str:jid>/', init_hemisferios, name='init_hemisferios'),
    path('subir_foto/<str:jid>/', subir_imagen_manual, name='subir_imagen_manual'),

    # ==========================================
    # DASHBOARD Y CONTROL DE VERSIONES
    # ==========================================
    path('control/', dashboard, name='dashboard'), 
    
    # Acciones de Propuestas (Aprobar/Rechazar)
    path('propuesta/<int:id>/aprobar/', aprobar_propuesta, name='aprobar_propuesta'),
    path('propuesta/<int:id>/rechazar/', rechazar_propuesta, name='rechazar_propuesta'),
    path('propuesta/<int:version_id>/comparar/', comparar_version, name='comparar_version'),
    path('version/<int:version_id>/publicar/', publicar_version, name='publicar_version'),
    path('propuesta/<int:version_id>/borrar/', borrar_propuesta, name='borrar_propuesta'),
    path('propuestas/borrar_masivo/', borrar_propuestas_masivo, name='borrar_propuestas_masivo'),
    path('propuestas/aprobar_masivo/', aprobar_propuestas_masivo, name='aprobar_propuestas_masivo'),
    
    # Rutas legacy
    path('revision/<int:version_id>/', comparar_version, name='revisar_version'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),
    path('narrativa/revision/<int:version_id>/', revisar_narrativa_version, name='revisar_narrativa_version'),

    # Acciones de Narrativas
    path('narrativa/propuesta/<int:id>/aprobar/', aprobar_narrativa, name='aprobar_narrativa'),
    path('narrativa/propuesta/<int:id>/rechazar/', rechazar_narrativa, name='rechazar_narrativa'),
    path('narrativa/version/<int:id>/publicar/', publicar_narrativa, name='publicar_narrativa'),
    path('narrativa/version/<int:id>/restaurar/', restaurar_narrativa, name='restaurar_narrativa'),
    path('narrativa/version/<int:id>/borrar/', borrar_narrativa_version, name='borrar_narrativa_version'),

    # Acciones de Imágenes
    path('imagen/propuesta/<int:id>/aprobar/', aprobar_imagen, name='aprobar_imagen'),
    path('imagen/propuesta/<int:id>/rechazar/', rechazar_imagen, name='rechazar_imagen'),
    # path('imagenes/aprobar_masivo/', aprobar_imagenes_masivo, name='aprobar_imagenes_masivo'), # DEPRECATED

    # ==========================================
    # NARRATIVA
    # ==========================================
    path('narrativa/indice/<str:jid>/', ver_narrativa_mundo, name='ver_narrativa_mundo'),
    path('narrativa/crear/<str:jid>/<str:tipo_codigo>/', crear_nueva_narrativa, name='crear_narrativa'),
    path('narrativa/subcrear/<str:parent_nid>/<str:tipo_codigo>/', crear_sub_narrativa, name='crear_sub_narrativa'),
    path('narrativa/nuevo_root/<str:jid>/<str:tipo_codigo>/', pre_crear_root, name='pre_crear_root'),
    path('narrativa/nuevo_child/<str:parent_nid>/<str:tipo_codigo>/', pre_crear_child, name='pre_crear_child'),
    path('narrativa/<str:nid>/', leer_narrativa, name='leer_narrativa'),
    path('narrativa/editar/<str:nid>/', editar_narrativa, name='editar_narrativa'),
    path('narrativa/borrar/<str:nid>/', borrar_narrativa, name='borrar_narrativa'),

    # Ruta de errores logs
    path('__debug__/', include('debug_toolbar.urls')),

    # ==========================================
    # APIs (AJAX y Fetch)
    # ==========================================
    path('api/preview_foto/<str:jid>/', api_preview_foto, name='api_preview_foto'),
    path('api/save_foto/<str:jid>/', api_save_foto, name='api_save_foto'),
    path('api/update_meta/<str:jid>/', api_update_image_metadata, name='api_update_image_metadata'),
    path('api/ai/analyze-metadata/', analyze_metadata_api, name='analyze_metadata_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)