from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from src.Infrastructure.DjangoFramework.persistence.views.world_views import (
    home, ver_mundo, editar_mundo, borrar_mundo, 
    toggle_lock, toggle_visibilidad, init_hemisferios, escanear_planeta,
    mapa_arbol, comparar_version, ver_metadatos,
    toggle_entity_status
)
from src.Infrastructure.DjangoFramework.persistence.views.ai_views import analyze_metadata_api, edit_narrative_api, api_generate_title, api_generate_lore
from src.Infrastructure.DjangoFramework.persistence.views.dashboard.workflow import (
    dashboard, centro_control, aprobar_propuesta, rechazar_propuesta, publicar_version, archivar_propuesta,
    restaurar_version, borrar_propuesta, borrar_propuestas_masivo,
    aprobar_contribucion, rechazar_contribucion,
    aprobar_narrativa, rechazar_narrativa, publicar_narrativa, archivar_narrativa,
    restaurar_narrativa, borrar_narrativa_version, 
    aprobar_periodo, rechazar_periodo, archivar_periodo, publicar_periodo, restaurar_periodo, borrar_periodo,
    ProposalDetailView, aprobar_propuestas_masivo, archivar_propuestas_masivo, publicar_propuestas_masivo
)
from src.Infrastructure.DjangoFramework.persistence.views.dashboard.assets import (
    aprobar_imagen, rechazar_imagen, archivar_imagen, restaurar_imagen, borrar_imagen_definitivo, 
    publicar_imagen, ImageProposalDetailView, batch_revisar_imagenes,
    ver_papelera, restaurar_entidad_fisica, borrar_mundo_definitivo, borrar_narrativa_definitivo, 
    restaurar_imagen_papelera, manage_trash_bulk
)
from src.Infrastructure.DjangoFramework.persistence.views.dashboard.team import (
    UserManagementView, toggle_admin_role, MyTeamView, CollaboratorWorkView, UserDetailView
)
from src.Infrastructure.DjangoFramework.persistence.views.dashboard.history import (
    audit_log_view, version_history_view, version_history_cleanup_view, delete_history_bulk_view
)
from src.Infrastructure.DjangoFramework.persistence.views.media_views import (
    api_preview_foto, api_save_foto, api_update_image_metadata, 
    subir_imagen_manual, set_cover_image, borrar_foto, generar_foto_extra, borrar_fotos_batch
)
from src.Infrastructure.DjangoFramework.persistence.views import review_views # NEW
from src.Infrastructure.DjangoFramework.persistence.views.narrative_views import (
    ver_narrativa_mundo, leer_narrativa, editar_narrativa, borrar_narrativa, 
    crear_nueva_narrativa, crear_sub_narrativa, revisar_narrativa_version,
    pre_crear_root, pre_crear_child, import_narrative_file, autosave_narrative
)

from src.Infrastructure.DjangoFramework.persistence.views.messaging_views import (
    inbox, send_message, mark_as_read, unread_count
)

from src.Infrastructure.DjangoFramework.persistence.views.search_views import global_search
from src.Infrastructure.DjangoFramework.persistence.views import period_api
from src.Infrastructure.DjangoFramework.persistence.views.metadata_views import propose_metadata_update

# Timeline API (old system - snapshots)
from src.Infrastructure.DjangoFramework.persistence.views.timeline_api import (
    create_timeline_proposal, list_timeline_proposals, get_timeline_proposal_detail,
    approve_timeline_proposal, reject_timeline_proposal
)

# Period API (new system - independent periods)
from src.Infrastructure.DjangoFramework.persistence.views.period_api import (
    create_period, propose_period_edit, get_period_detail,
    approve_period_version, reject_period_version, delete_period, list_world_periods,
    activate_period_endpoint
)

urlpatterns = [
    path('api/ai/generate-lore/', api_generate_lore, name='api_generate_lore'),
    path('api/narrativa/autosave/<str:nid>/', autosave_narrative, name='autosave_narrative'),

    # ==========================================
    # BÚSQUEDA
    # ==========================================
    path('buscar/', global_search, name='global_search'),

    # ==========================================
    # MENSAJERÍA
    # ==========================================
    path('mensajes/', inbox, name='inbox'),
    path('mensajes/enviar/', send_message, name='send_message'),
    path('mensajes/enviar/<int:user_id>/', send_message, name='send_message_to'),
    path('mensajes/marcar-leido/<int:message_id>/', mark_as_read, name='mark_as_read'),
    path('api/mensajes/no-leidos/', unread_count, name='unread_count'),

    # Tailwind (Recarga automática en desarrollo)
    path("__reload__/", include("django_browser_reload.urls")),
    
    # Admin y Autenticación
    path('bunker-xico/', admin.site.urls),
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
    path('crear/', home, name='crear_mundo'),
    path('metadatos/<str:public_id>/', ver_metadatos, name='ver_metadatos'),
    path('borrar/<str:jid>/', borrar_mundo, name='borrar_mundo'),
    path('editar/<str:jid>/', editar_mundo, name='editar_mundo'),
    
    # 🔒 BLOQUEO Y VISIBILIDAD
    path('lock/<str:jid>/', toggle_lock, name='toggle_lock'),
    path('toggle_visible/<str:jid>/', toggle_visibilidad, name='toggle_visibilidad'),
    path('toggle_status/<str:jid>/', toggle_entity_status, name='toggle_status'),
    
    # FOTOS Y MEDIA
    path('escanear/<str:jid>/', escanear_planeta, name='escanear_planeta'),
    path('foto_extra/<str:jid>/', generar_foto_extra, name='generar_foto_extra'),
    path('cover/<str:jid>/<str:filename>/', set_cover_image, name='set_cover_image'),
    path('borrar_foto/<str:jid>/<str:filename>/', borrar_foto, name='borrar_foto'),
    path('borrar_fotos_batch/<str:jid>/', borrar_fotos_batch, name='borrar_fotos_batch'),
    path('init_hemisferios/<str:jid>/', init_hemisferios, name='init_hemisferios'),
    path('subir_foto/<str:jid>/', subir_imagen_manual, name='subir_imagen_manual'),

    # ==========================================
    # DASHBOARD Y CONTROL DE VERSIONES
    # ==========================================
    path('control/', dashboard, name='dashboard'), 
    path('control/auditoria/', audit_log_view, name='audit_log'),
    path('control/historial/', version_history_view, name='version_history'),
    path('control/historial/limpiar/', version_history_cleanup_view, name='version_history_cleanup'),
    path('control/historial/eliminar_lote/', delete_history_bulk_view, name='delete_history_bulk'),
    path('papelera/', ver_papelera, name='ver_papelera'),
    path('papelera/restaurar/<str:jid>/', restaurar_entidad_fisica, name='restaurar_entidad_fisica'), 
    path('papelera/borrar_mundo/<str:id>/', borrar_mundo_definitivo, name='borrar_mundo_definitivo'), # HARD DELETE
    path('papelera/borrar_narrativa/<str:nid>/', borrar_narrativa_definitivo, name='borrar_narrativa_definitivo'), # HARD DELETE
    path('papelera/restaurar_imagen/<int:id>/', restaurar_imagen_papelera, name='restaurar_imagen_papelera'), # NEW
    path('papelera/acciones_lote/', manage_trash_bulk, name='manage_trash_bulk'),
    
    # Acciones de Propuestas (Aprobar/Rechazar)
    path('propuesta/<int:id>/aprobar/', aprobar_propuesta, name='aprobar_propuesta'),
    path('propuesta/<int:id>/rechazar/', rechazar_propuesta, name='rechazar_propuesta'),
    path('propuesta/<int:version_id>/comparar/', comparar_version, name='comparar_version'),
    path('version/<int:version_id>/publicar/', publicar_version, name='publicar_version'),
    path('propuesta/<int:id>/archivar/', archivar_propuesta, name='archivar_propuesta'),
    path('propuesta/<int:version_id>/borrar/', borrar_propuesta, name='borrar_propuesta'),
    path('script/version/<int:id>/aprobar/', aprobar_propuesta, name='aprobar_version'), # New Alias
    path('propuestas/borrar_masivo/', borrar_propuestas_masivo, name='borrar_propuestas_masivo'),
    path('propuestas/aprobar_masivo/', aprobar_propuestas_masivo, name='aprobar_propuestas_masivo'),
    path('propuestas/archivar_masivo/', archivar_propuestas_masivo, name='archivar_propuestas_masivo'),
    path('propuestas/publicar_masivo/', publicar_propuestas_masivo, name='publicar_propuestas_masivo'),
    
    # Gestión de Usuarios (Superadmin)
    path('usuarios/', UserManagementView.as_view(), name='user_management'),
    path('usuarios/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('usuarios/<int:user_id>/toggle-role/', toggle_admin_role, name='toggle_admin_role'),
    
    # Team Management
    # Team Management
    path('dashboard/team/', MyTeamView.as_view(), name='my_team'),
    path('dashboard/team/work/<int:user_id>/', CollaboratorWorkView.as_view(), name='collaborator_work'),
    path('dashboard/my-work/', CollaboratorWorkView.as_view(), name='my_work'),
    
    # Rutas legacy
    path('revision/<int:version_id>/', comparar_version, name='revisar_version'),
    path('version/restaurar/<int:version_id>/', restaurar_version, name='restaurar_version'),
    path('narrativa/revision/<int:version_id>/', revisar_narrativa_version, name='revisar_narrativa_version'),

    # Acciones de Narrativas
    path('narrativa/propuesta/<int:id>/aprobar/', aprobar_narrativa, name='aprobar_narrativa'),
    path('narrativa/propuesta/<int:id>/rechazar/', rechazar_narrativa, name='rechazar_narrativa'),
    path('narrativa/propuesta/<int:id>/archivar/', archivar_narrativa, name='archivar_narrativa'),
    path('narrativa/version/<int:id>/publicar/', publicar_narrativa, name='publicar_narrativa'),
    path('narrativa/restaurar/<str:nid>/', restaurar_narrativa, name='restaurar_narrativa'),
    path('narrativa/version/<int:id>/borrar/', borrar_narrativa_version, name='borrar_narrativa_version'),
    
    # Acciones de Periodos (Timeline)
    path('periodo/propuesta/<int:id>/aprobar/', aprobar_periodo, name='aprobar_periodo'),
    path('periodo/propuesta/<int:id>/publicar/', publicar_periodo, name='publicar_periodo'),
    path('periodo/propuesta/<int:id>/rechazar/', rechazar_periodo, name='rechazar_periodo'),
    path('periodo/propuesta/<int:id>/archivar/', archivar_periodo, name='archivar_periodo'),
    path('periodo/propuesta/<int:id>/restaurar/', restaurar_periodo, name='restaurar_periodo'),
    path('periodo/propuesta/<int:id>/borrar/', borrar_periodo, name='borrar_periodo'),

    # Acciones de Imágenes
    path('imagen/propuesta/<int:id>/', ImageProposalDetailView.as_view(), name='revisar_imagen'),
    path('imagen/propuesta/<int:id>/aprobar/', aprobar_imagen, name='aprobar_imagen'),
    path('imagen/propuesta/<int:id>/publicar/', publicar_imagen, name='publicar_imagen'),
    path('imagen/propuesta/<int:id>/rechazar/', rechazar_imagen, name='rechazar_imagen'),
    path('imagen/propuesta/<int:id>/archivar/', archivar_imagen, name='archivar_imagen'),
    path('imagen/propuesta/<int:id>/restaurar/', restaurar_imagen, name='restaurar_imagen'),
    path('imagen/propuesta/<int:id>/borrar/', borrar_imagen_definitivo, name='borrar_imagen_definitivo'),
    path('imagen/revisar_lote/', batch_revisar_imagenes, name='batch_revisar_imagenes'),

    # Acciones de Propuestas Texto
    path('propuesta/<int:id>/', ProposalDetailView.as_view(), name='proposal_detail'),
    path('propuesta/<int:id>/aprobar/', aprobar_contribucion, name='aprobar_contribucion'),
    path('propuesta/<int:id>/rechazar/', rechazar_contribucion, name='rechazar_contribucion'),

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
    path('api/ai/edit-narrative/', edit_narrative_api, name='edit_narrative_api'),
    path('api/ai/generate-title/', api_generate_title, name='api_generate_title'),
    path('api/narrative/import-file/', import_narrative_file, name='import_narrative_file'),
    
    # ==========================================
    # TIMELINE API (Old system - snapshots)
    # ==========================================
    path('api/world/<str:world_id>/timeline/propose/', create_timeline_proposal, name='create_timeline_proposal'),
    path('api/timeline/proposals/', list_timeline_proposals, name='list_timeline_proposals'),
    path('api/timeline/proposal/<int:proposal_id>/', get_timeline_proposal_detail, name='get_timeline_proposal_detail'),
    path('api/timeline/proposal/<int:proposal_id>/approve/', approve_timeline_proposal, name='approve_timeline_proposal'),
    path('api/timeline/proposal/<int:proposal_id>/reject/', reject_timeline_proposal, name='reject_timeline_proposal'),
    
    # ==========================================
    # PERIOD API (New system - independent periods)
    # ==========================================
    path('api/world/<str:world_id>/period/create', create_period, name='create_period'),
    path('api/world/<str:world_id>/periods', list_world_periods, name='list_world_periods'),
    path('api/period/<int:period_id>/', get_period_detail, name='get_period_detail'),
    path('api/period/<int:period_id>/propose', propose_period_edit, name='propose_period_edit'),
    path('api/period/<int:period_id>/activate', activate_period_endpoint, name='activate_period'),
    path('api/period/<int:period_id>/delete', delete_period, name='delete_period'),
    path('api/period/version/<int:version_id>/approve', approve_period_version, name='approve_period_version'),
    path('api/period/version/<int:version_id>/reject', reject_period_version, name='reject_period_version'),
    
    # 🌟 NEW UNIFIED REVIEW VIEW 🌟
    path('revisar/<str:type>/<int:id>/', review_views.review_proposal, name='review_proposal'),

    # ==========================================
    # METADATA API (Independent Proposals)
    # ==========================================
    path('api/metadata/propose/<str:target_type>/<str:target_id>/', 
         propose_metadata_update, name='propose_metadata_update'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)