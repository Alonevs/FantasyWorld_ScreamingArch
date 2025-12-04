from django.contrib import admin
from django.urls import path, include
from django.urls import include, path


# Imports de tus nuevas vistas organizadas
from src.Infrastructure.DjangoFramework.persistence.views.world_views import *
from src.Infrastructure.DjangoFramework.persistence.views.dashboard_views import *
from src.Infrastructure.DjangoFramework.persistence.views.media_views import *
from src.Infrastructure.DjangoFramework.persistence.views.narrative_views import *
from src.Infrastructure.DjangoFramework.persistence.views.world_views import (
    home, ver_mundo, editar_mundo, borrar_mundo, 
    toggle_lock, toggle_visibilidad, init_hemisferios, escanear_planeta,
    mapa_arbol  # <--- ¡Asegúrate de que esta esté aquí!
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
    path('borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    
    # 🔒 BLOQUEO Y VISIBILIDAD (¡Aquí faltaba esto!)
    path('lock/<str:jid>/', toggle_lock, name='toggle_lock'),        # <--- ¡ESTA FALTABA!
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
    # Nota: Usamos 'dashboard' como la principal. 'centro_control' es la antigua.
    path('control/', dashboard, name='dashboard'), 
    
    # Acciones de Propuestas (Aprobar/Rechazar)
    path('propuesta/<int:id>/aprobar/', aprobar_propuesta, name='aprobar_propuesta'),
    path('propuesta/<int:id>/rechazar/', rechazar_propuesta, name='rechazar_propuesta'),
    path('propuesta/<int:version_id>/comparar/', comparar_version, name='comparar_version'),
    path('version/<int:version_id>/publicar/', publicar_version, name='publicar_version'),
    path('propuesta/<int:version_id>/borrar/', borrar_propuesta, name='borrar_propuesta'),
    path('propuestas/borrar_masivo/', borrar_propuestas_masivo, name='borrar_propuestas_masivo'),
    
    # Rutas legacy (por si acaso algún enlace viejo las usa)
    path('revision/<int:version_id>/', comparar_version, name='revisar_version'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),

    # ==========================================
    # NARRATIVA
    # ==========================================
    path('narrativa/indice/<str:jid>/', ver_narrativa_mundo, name='ver_narrativa_mundo'),
    path('narrativa/crear/<str:jid>/<str:tipo_codigo>/', crear_nueva_narrativa, name='crear_narrativa'),
    path('narrativa/subcrear/<str:parent_nid>/<str:tipo_codigo>/', crear_sub_narrativa, name='crear_sub_narrativa'),
    path('narrativa/<str:nid>/', leer_narrativa, name='leer_narrativa'),
    path('narrativa/editar/<str:nid>/', editar_narrativa, name='editar_narrativa'),
    path('narrativa/borrar/<str:nid>/', borrar_narrativa, name='borrar_narrativa'),
      #Ruta de errores logs
    path('__debug__/', include('debug_toolbar.urls')),



    # ==========================================
    # APIs (AJAX y Fetch)
    # ==========================================
    path('api/preview_foto/<str:jid>/', api_preview_foto, name='api_preview_foto'),
    path('api/save_foto/<str:jid>/', api_save_foto, name='api_save_foto'),
    path('api/update_meta/<str:jid>/', api_update_image_metadata, name='api_update_image_metadata'),
]
    