import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosVersionORM, CaosNarrativeORM, CaosEventLog, MetadataTemplate
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
# IMPORTE Q
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import Http404
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.create_child import CreateChildWorldUseCase
from src.WorldManagement.Caos.Application.propose_change import ProposeChangeUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.WorldManagement.Caos.Application.generate_creature_usecase import GenerateCreatureUseCase
from src.WorldManagement.Caos.Application.initialize_hemispheres import InitializeHemispheresUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
from django.contrib.auth.decorators import login_required, user_passes_test
from src.FantasyWorld.Domain.Services.EntityService import EntityService
from src.WorldManagement.Caos.Application.common import resolve_world_id
from src.WorldManagement.Caos.Application.toggle_visibility import ToggleWorldVisibilityUseCase
from src.WorldManagement.Caos.Application.toggle_lock import ToggleWorldLockUseCase
from src.WorldManagement.Caos.Application.get_world_tree import GetWorldTreeUseCase
from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.Infrastructure.DjangoFramework.persistence.utils import generate_breadcrumbs, get_world_images
from .view_utils import resolve_jid_orm, check_world_access, get_admin_status, get_metadata_diff


from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy

def log_event(user, action, target_id, details=""):
    """
    Registra eventos de auditoría en la base de datos (CaosEventLog).
    Sirve para rastrear quién hizo qué y sobre qué entidad.
    """
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: 
        print(f"Error al registrar evento: {e}")

def get_current_user(request):
    if request.user.is_authenticated: return request.user
    u, _ = User.objects.get_or_create(username='Admin')
    return u

# Se eliminó resolve_jid local, usando resolve_jid_orm en su lugar
from django.db.models.functions import Length

def home(request):
    """
    Vista de Inicio: El Portal Central del Universo.
    Muestra el índice de mundos habitables aplicando la 'Indexación Agresiva'.
    Filtra entidades fantasma, borradores ocultos y aplica visibilidad por roles (Soberanía).
    """
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        repo = DjangoCaosRepository()
        # Para la creación, el autor es el usuario actual
        try:
            jid = CreateWorldUseCase(repo).execute(
                name=request.POST.get('world_name'), 
                description=request.POST.get('world_desc'),
                author=request.user
            )
            w = CaosWorldORM.objects.get(id=jid)
            w.author = request.user
            w.save()
            messages.success(request, "✨ Mundo propuesto. Ve al Dashboard para aprobarlo.")
        except Exception as e:
            messages.error(request, f"Error al proponer mundo: {str(e)}")
            
        return redirect('dashboard')
    
    # Mostrar mundos 'LIVE' (y 'DRAFTS' para el Autor/Superusuario)
    # 1. Base: Excluir borrados, inválidos y DRAFTS (Flujo Estricto)
    # 1. Base: Excluir solo lo que está en la papelera (soft-delete)
    # El resto de estados (DRAFT, OFFLINE) se filtran por permisos más abajo.
    ms = CaosWorldORM.objects.filter(is_active=True).exclude(status='DELETED')
    
    # Exclusión de descripciones vacías, EXCEPTO para Caos Prime (JhZCO1vxI7)
    ms = ms.exclude(
        Q(description__isnull=True) | Q(description__exact='') | Q(description__iexact='None'),
        ~Q(public_id='JhZCO1vxI7')
    )
    
    ms = ms.exclude(id__endswith='00', name__startswith='Nexo Fantasma') \
        .exclude(id__endswith='00', name__startswith='Ghost')
    
    # Regla Especial (01XX): Ocultar hijos directos de Caos Prime para no-Admins en el Home
    is_privileged = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank == 'ADMIN')
    if not is_privileged:
        ms = ms.exclude(id__regex=r'^01[0-9]{2}$')

    ms = ms.prefetch_related('versiones', 'narrativas') \
        .order_by(
            Case(
                When(public_id='JhZCO1vxI7', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            'name'  # Secondary sort by name
        )

    # 2. Lógica de Visibilidad Centralizada
    from src.Infrastructure.DjangoFramework.persistence.policies import get_visibility_q_filter
    
    q_filter = get_visibility_q_filter(request.user)
    ms = ms.filter(q_filter)

    # LÓGICA REPRESENTATIVA:
    # Objetivo: Ocultar "Fantasmas" (Versiones) pero MOSTRAR "Hermanos".
    # Un Fantasma se define por tener '00' en su linaje (ej. 01010001 es un fantasma de 010101).
    # Los Hermanos reales (010101, 010102) NO deben agruparse.
    

    # --- LÓGICA DE ÍNDICE DE INICIO REFRACTORIZADA ---
    # Caso de Uso: GetHomeIndexUseCase
    # Maneja: Limpieza de fantasmas, colapso de versiones e indexación agresiva para Geografía/Población.
    
    from src.WorldManagement.Caos.Application.get_home_index import GetHomeIndexUseCase
    use_case = GetHomeIndexUseCase()
    final_list = use_case.execute(ms)

    l = []
    background_images = []
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_plural_label

    for m in final_list:
        # Pasar world_instance=m para evitar re-consultar metadatos (N+1 fix)
        imgs = get_world_images(m.id, world_instance=m)
        if imgs:
            imgs.sort(key=lambda x: x.get('is_cover', False), reverse=True)
        cover = imgs[0]['url'] if imgs else None
        if m.metadata and 'cover_image' in m.metadata:
            target = m.metadata['cover_image']
            found = next((i for i in imgs if i['filename'] == target), None)
            if found: cover = found['url']
        
        if cover:
            background_images.append(cover)
 
        # Recolectar hasta 5 imágenes para el slideshow (Priorizando PORTADA)
        entity_images = [i['url'] for i in imgs] if imgs else []
        if cover and cover in entity_images:
            entity_images.remove(cover)
            entity_images.insert(0, cover)
        entity_images = entity_images[:5]
        
        # SOBRESCRITURA VISUAL DE NOMBRE (Solicitado: "solo visual")
        # Si es Nivel 1 (id="01..."), mostrar "CAOS". Nivel 2 -> "ABISMOS", etc.
        visual_name = get_plural_label(len(m.id)//2, m.id)
        # Manejar singularización o sobrescrituras específicas si es necesario
        if len(m.id)//2 == 1: visual_name = "CAOS"

        pid = m.public_id if m.public_id else m.id
        l.append({
            'id': m.id, 
            'public_id': pid, 
            'name': visual_name, 
            'real_name': m.name, # Mantener original para tooltips o alt
            'status': m.status, 
            'img_file': cover,
            'img': cover, # Fallback/Primary key
            'images': entity_images, 
            'has_img': bool(cover), 
            'visible': m.visible_publico,
            'is_locked': m.status == 'LOCKED',
            'author': m.author,
            'level': len(m.id)//2,
        })
    
    import random
    random.shuffle(background_images)
    
    return render(request, 'index.html', {'mundos': l, 'background_images': background_images[:10]})


def ver_mundo(request, public_id):
    """
    Ficha de Entidad: Muestra el Lore, Metadatos Estructurados y Galería.
    Permite la creación de entidades hijas ('Sugerencia de Creación') 
    y gestiona la normalización de metadatos para el frontend.
    """
    w_orm = resolve_jid_orm(public_id)
    if not w_orm:
        return render(request, '404.html', {"jid": public_id}, status=404)
    
    can_access, is_author_or_team = check_world_access(request, w_orm)
    if not can_access:
        return render(request, 'private_access.html', status=403)
    
    repo = DjangoCaosRepository()
    
    # 1. Manejar POST (Creación)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Resolver ID para el padre (necesario para la creación)
        w = resolve_jid_orm(public_id)
        if not w: return redirect('home') # Debería manejarse mejor
        
        # --- CHEQUEO DE SEGURIDAD ---
        # Permitir propuestas de cualquier usuario autenticado (Estado será PENDING)
        # Eliminamos el check_ownership() estricto aquí para habilitar el flujo de "Sugerencia/Propuesta".
        # ----------------------------

        jid = w.id
        safe_pid = w.public_id if w.public_id else jid

        c_name = request.POST.get('child_name')
        if c_name:
            c_desc = request.POST.get('child_desc', "")
            reason = request.POST.get('reason', "Creación vía Wizard")
            use_ai = request.POST.get('use_ai_gen') == 'on'
            
            target_level_str = request.POST.get('target_level')
            target_level = int(target_level_str) if target_level_str else None
            
            # Usar EntityService para creación unificada
            service = EntityService()
            new_id = service.create_entity(
                parent_id=jid, 
                name=c_name, 
                description=c_desc, 
                reason=reason, 
                generate_image=use_ai, 
                target_level=target_level
            )
            
            try:
                if target_level and target_level > (len(jid)//2 + 1):
                     messages.success(request, f"✨ Entidad profunda creada con Salto (Nivel {target_level}).")
                else:
                     messages.success(request, "✨ Entorno propuesto (y su imagen). Ve al Dashboard para aprobarlo.")
                return redirect('dashboard')
            except:
                return redirect('dashboard')

    # --- PERIOD SUPPORT (New Timeline System) ---
    from src.Infrastructure.DjangoFramework.persistence.models import TimelinePeriod
    from src.Shared.Services.TimelinePeriodService import TimelinePeriodService
    
    # Resolver Entidad ORM para el servicio de períodos
    w_orm = resolve_jid_orm(public_id)
    if not w_orm: raise Http404

    # Obtener slug del período solicitado (por defecto: 'actual')
    period_slug = request.GET.get('period', 'actual')
    
    # Obtener todos los períodos de esta entidad
    all_periods = TimelinePeriodService.get_periods_for_world(w_orm)
    
    # Obtener el período actual (ACTUAL)
    current_period = TimelinePeriodService.get_current_period(w_orm)
    
    # Determinar qué período mostrar
    if period_slug == 'actual' or not period_slug:
        viewing_period = current_period
    else:
        viewing_period = all_periods.filter(slug=period_slug).first()
        if not viewing_period:
            # Si el slug no existe, redirigir a ACTUAL
            messages.warning(request, f"Período '{period_slug}' no encontrado. Mostrando ACTUAL.")
            return redirect('ver_mundo', public_id=public_id)

    # 2. Manejar GET (Visualización) mediante Caso de Uso
    # PASAMOS EL PERIOD_SLUG PARA FILTRAR IMÁGENES
    context = GetWorldDetailsUseCase(repo).execute(public_id, request.user, period_slug=period_slug)
    
    if not context:
        return render(request, '404.html', {"jid": public_id})

    # --- CANONICALIZACIÓN DE URL (ID Antiguo -> NanoID) ---
    if context['public_id'] and context['public_id'] != public_id:
        return redirect('ver_mundo', public_id=context['public_id'])
    # ------------------------------------------------------

    # Si estamos viendo un período que NO es ACTUAL, sobrescribir descripción
    if viewing_period and not viewing_period.is_current:
        context['description'] = viewing_period.description
        context['is_period_view'] = True
        context['viewing_period'] = viewing_period
        
        # Sobrescribir metadatos para mostrar los del periodo
        if viewing_period.metadata:
            from .view_utils import get_metadata_properties_dict
            context['props'] = get_metadata_properties_dict(viewing_period.metadata)
            

    else:
        context['is_period_view'] = False
        context['viewing_period'] = current_period
    
    # Pasar períodos al contexto para el selector
    context['timeline_periods'] = all_periods.exclude(is_current=True).order_by('order')
    context['current_period_slug'] = period_slug
    # ---------------------------------

    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy, get_children_label # Importar helpers
    context['hierarchy_label'] = get_readable_hierarchy(context['jid'])
    context['children_label'] = get_children_label(context['jid']) # NUEVO: Pasar etiqueta para el grid
    context['status_str'] = w_orm.status
    context['author_live_user'] = w_orm.author
    
    # CHEQUEO DE PERMISOS
    # NOTA: Los permisos (can_edit, is_admin_role, etc.) ya vienen calculados 
    # robustamente desde GetWorldDetailsUseCase (que usa policies.py).
    # NO debemos sobrescribirlos aquí con lógica simplificada.
    
    # is_admin ya se calcula en el usecase como 'is_admin_role'
    # allow_proposals no se usa mucho, pero si se usara, debería venir del use case intentando unificar.
    # Por seguridad, solo inyectamos lo que NO venga del use case.
    
    if 'can_edit' not in context: # Fallback por si acaso
         context['can_edit'] = is_author_or_team
    # ---------------------------------
    
    # --- OPCIONES DE CREACIÓN PROFUNDA ---
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_available_levels
    context['available_levels'] = get_available_levels(context['jid'])
    # -------------------------------------


    return render(request, 'ficha_mundo.html', context)

@login_required
def editar_mundo(request, jid):
    """
    Editor de Entidad: Interfaz para proponer cambios de lore o metadatos técnicos.
    Implementa el flujo de propuestas 'ECLAI' y soporta el modo 'Retoque'
    para corregir versiones rechazadas.
    """
    # Usar helper robusto que intenta Dominio primero, luego PublicID/ID
    w_orm = resolve_jid_orm(jid)
    if not w_orm: return redirect('home')
    
    real_jid = w_orm.id # Ya tenemos el objeto ORM

    # Antigua lógica de retoque eliminada (movida al final para robustez del contexto)
    
    # CHEQUEO DE BLOQUEO
    # El Bypass de Admin solo debe aplicar si tiene acceso de edición legítimo.
    # Como estamos en 'editar_mundo', debemos comprobar si realmente tiene derechos.
    # Nota: 'editar_mundo' aún no llama a check_world_access. Debería.
    
    can_access, is_author_or_team = check_world_access(request, w_orm)
    if not is_author_or_team:
         messages.error(request, "⛔ No tienes permisos para editar este mundo.")
         return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    is_admin_bypass = is_author_or_team # Contains Superuser, Admin, Boss-Collab logic
    
    if w_orm.status == 'LOCKED' and not is_admin_bypass:
        messages.error(request, "⛔ Este mundo está BLOQUEADO por el Autor. No se permiten propuestas.")
        return redirect('ver_mundo', public_id=w_orm.public_id if w_orm.public_id else w_orm.id)

    if request.method == 'POST':
        try:
            w = resolve_jid_orm(jid); real_jid = w.id if w else jid
            desc = request.POST.get('description')
            action_type = request.POST.get('action_type', 'EDIT_WORLD')
            
            metadata_prop = None
            reason = request.POST.get('reason', 'Actualización de Metadatos')
 
            # Manejar Propuesta de Metadatos
            if action_type == 'METADATA_PROPOSAL':
                # NUEVA LÓGICA DINÁMICA (Arrays)
                prop_keys = request.POST.getlist('prop_keys[]')
                prop_values = request.POST.getlist('prop_values[]')
                
                metadata_prop = {'properties': []}
                
                # Unirlos (zip)
                if prop_keys and prop_values:
                    for k, v in zip(prop_keys, prop_values):
                        if k.strip(): # Ignorar claves vacías
                            metadata_prop['properties'].append({'key': k.strip(), 'value': v.strip()})
                
                print(f"📝 [Edición Manual] Enviando Propuesta de Metadatos: {len(metadata_prop['properties'])} elementos.")
                print(f"   Contenido: {metadata_prop}")
                
                # Al editar metadatos, podríamos mantener nombre/desc como están (o usar campos ocultos)
                # Por seguridad, simplemente pasamos None para mantener los valores existentes en el Caso de Uso
                ProposeChangeUseCase().execute(real_jid, None, None, reason, get_current_user(request), metadata_proposal=metadata_prop)
                messages.success(request, f"🔮 Propuesta de METADATOS enviada (v{CaosVersionORM.objects.filter(world_id=real_jid).count() + 1}).")
                log_event(request.user, "PROPOSE_METADATA", real_jid, f"Razón: {reason}")
            else:
                # Edición Regular
                if request.POST.get('use_ai_edit') == 'on':
                    try: desc = Llama3Service().generate_description(f"Nombre: {request.POST.get('name')}. Concepto: {desc}") or desc
                    except: pass
                ProposeChangeUseCase().execute(real_jid, request.POST.get('name'), desc, request.POST.get('reason'), get_current_user(request))
                log_event(request.user, "PROPOSE_CHANGE", real_jid, f"Reason: {request.POST.get('reason')}")
            
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        except Exception as e: 
            print(f"Error de edición: {e}")
            return redirect('home')
 
    # --- GET: RENDERIZAR FORMULARIO DE EDICIÓN ---
    from src.WorldManagement.Caos.Application.get_world_details import GetWorldDetailsUseCase
    try:
        # 1. Obtener Contexto Base
        repo = DjangoCaosRepository()
        use_case = GetWorldDetailsUseCase(repo)
        context = use_case.execute(real_jid, request.user)
        
        # 2. Activar Modo Edición
        context['edit_mode'] = True
        
        # 3. Aplicar Sobrescrituras de Retoque (lógica movida aquí por robustez)
        src_version_id = request.GET.get('src_version')
        if src_version_id:
            try:
                v_src = CaosVersionORM.objects.get(id=src_version_id)
                # Verificar propiedad/relación
                can_retouch = (v_src.author == request.user) or is_admin_bypass
                
                if v_src.world.id == real_jid and can_retouch:
                    context['name'] = v_src.proposed_name
                    context['description'] = v_src.proposed_description
                    context['is_retouch_mode'] = True
                    context['can_edit'] = True # Forzar visibilidad del botón Editar
                    messages.info(request, f"✏️ Retomando propuesta rechazada v{v_src.version_number}. Datos cargados.")
            except Exception as e:
                print(f"Error cargando src_version en GET: {e}")
 
        return render(request, 'ficha_mundo.html', context)
    except Exception as e:
        print(f"Error renderizando vista de edición: {e}")
        return redirect('home')



@login_required
def toggle_entity_status(request, jid):
    w = resolve_jid_orm(jid)
    if not w:
        raise Http404("Entidad no encontrada")

    # 1. Verificar Permisos (Superuser o Autor)
    if request.user.is_superuser or w.author == request.user:
        # 2. Cambiar Estado
        if w.status == 'LIVE':
            w.status = 'OFFLINE'
        else:
            w.status = 'LIVE'
        w.save()
        messages.success(request, f"Estado actualizado a: {w.status}")
    else:
        messages.error(request, "Permiso denegado.")

    # 3. REDIRECCIÓN ROBUSTA
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def borrar_mundo(request, jid): 
    try: 
        # Búsqueda Robusta
        # Búsqueda Robusta usando helper estandarizado
        w = resolve_jid_orm(jid)
        if not w:
            messages.error(request, "Entidad no encontrada")
            return redirect('home')
        
        check_ownership(request.user, w) # Chequeo de Seguridad
        
        # Determinar siguiente número de versión
        last_v = w.versiones.order_by('-version_number').first()
        next_v = (last_v.version_number + 1) if last_v else 1
        
        # Crear Propuesta de ELIMINACIÓN
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log="Solicitud de Eliminación",
            cambios={'action': 'DELETE'},
            author=get_current_user(request)
        )
        
        messages.warning(request, "🗑️ Solicitud de eliminación creada. Ve al Dashboard para confirmar.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error solicitando eliminación: {e}")
        return redirect('home')

@login_required
def toggle_visibilidad(request, jid):
    try: 
        repo = DjangoCaosRepository()
        w_domain = resolve_world_id(repo, jid)
        w = CaosWorldORM.objects.get(id=w_domain.id.value)
        check_ownership(request.user, w) # Chequeo de Seguridad
        
        next_v = CaosVersionORM.objects.filter(world=w).count() + 1
        current_vis = w.visible_publico
        target_vis = not current_vis
        
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Solicitud cambio visibilidad: {'PÚBLICO' if target_vis else 'PRIVADO'}",
            cambios={'action': 'TOGGLE_VISIBILITY', 'target_visibility': target_vis},
            author=get_current_user(request)
        )
        
        messages.success(request, "👁️ Solicitud de cambio de visibilidad creada.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error cambiando visibilidad: {e}")
        return redirect('home')

def restaurar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        RestoreVersionUseCase().execute(version_id, get_current_user(request))
        messages.success(request, "✅ Restaurada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except: return redirect('home')

def comparar_version(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        w = v.world
        # Renderizamos la ficha pero con los datos de la versión
        jid = w.id
        safe_pid = w.public_id if w.public_id else jid
        
        imgs = get_world_images(jid)
        
        # Metadata Handling for Preview
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        # Calculate Metadata Version
        # Count all previous versions of this world that had metadata changes
        meta_count = CaosVersionORM.objects.filter(
            world=w, 
            version_number__lte=v.version_number
        ).filter(
            Q(cambios__has_key='metadata') | Q(cambios__action='METADATA_UPDATE')
        ).count()
        
        # Special case: if this version doesn't have metadata changes but we are previewing it,
        # we still show the metadata at that point in time (V count).
        
        # Prepare Decorated Metadata List for Template
        # v.cambios might have 'metadata' key (which is a dict with 'properties')
        proposed_meta = v.cambios.get('metadata', {}) if v.cambios else {}
        live_meta = w.metadata if w.metadata else {}
        
        from .view_utils import get_metadata_properties_dict
        proposed_props = get_metadata_properties_dict(proposed_meta)
        live_props = get_metadata_properties_dict(live_meta)
        
        diff_results = get_metadata_diff(live_meta, proposed_meta) if proposed_meta else []
        diff_map = {d['key']: d for d in diff_results}
        
        metadata_list = []
        # If we have a proposal, show it with decorations 
        # (Fall back to live properties for those not changed if it was an update? 
        # Actually usually it's a full replacement in this system).
        
        # We decide what to show based on all available keys
        all_keys = sorted(set(proposed_props.keys()) | set(live_props.keys()))
        
        for key in all_keys:
            action = diff_map.get(key, {}).get('action', 'NORMAL')
            val = proposed_props.get(key, live_props.get(key))
            
            # If it was deleted, show old value
            if action == 'DELETE':
                val = live_props.get(key)
                
            metadata_list.append({
                'key': key,
                'value': val,
                'action': action
            })
            
        # Prepare Context with Permissions
        is_admin, is_team_member = get_admin_status(request.user)
        
        context = {
            'name': v.proposed_name,
            'description': v.proposed_description,
            'jid': jid, 'public_id': safe_pid,
            'status': f"PREVIEW v{v.version_number} ({v.status})",
            'version_live': w.current_version_number,
            'author_live': v.author.username if v.author else "Desconocido",
            'created_at': v.created_at, 'updated_at': v.created_at,
            'visible': False, 
            'nid_lore': w.id_lore,
            'metadata_obj': {'properties': metadata_list},
            'metadata_version': f"V{meta_count}" if meta_count > 0 else "V0",
            'is_preview': True, 
            'preview_version_id': v.id,
            'breadcrumbs': generate_breadcrumbs(jid),
            'imagenes': imgs, 'hijos': [],
            
            # Permisos y Estados para UI
            'status_str': 'PREVIEW',
            'author_live_user': v.author,
            'is_author': is_author_or_team,
            'is_admin_role': is_admin,
            'can_edit': False, # No editar durante previsualización
            'allow_proposals': False, # No proponer sobre una previsualización
            'user_role': request.user.profile.rank_value if hasattr(request.user, 'profile') else 0
        }
        
        # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
        context['hierarchy_label'] = get_readable_hierarchy(jid)
        # ------------------------------------------
        
        messages.info(request, f"👀 Viendo PREVISUALIZACIÓN de versión {v.version_number}")
        return render(request, 'ficha_mundo.html', context)
    except Exception as e: 
        print(e)
        return redirect('home')

@login_required
def init_hemisferios(request, jid):
    try: 
        w=resolve_jid_orm(jid)
        w_orm = CaosWorldORM.objects.get(id=w.id)
        check_ownership(request.user, w_orm)
        InitializeHemispheresUseCase(DjangoCaosRepository()).execute(w.id); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def escanear_planeta(request, jid): return redirect('ver_mundo', public_id=jid)

def mapa_arbol(request, public_id):
    try:
        repo = DjangoCaosRepository()
        # Chequeo de Seguridad
        w_orm = resolve_jid_orm(public_id)
        if not w_orm: return redirect('home')
        
        can_access, _ = check_world_access(request, w_orm)
        if not can_access: 
             return render(request, 'private_access.html', status=403)

        result = GetWorldTreeUseCase(repo).execute(public_id)
        if not result: return redirect('home')
        return render(request, 'mapa_arbol.html', result)
    except Http404: raise
    except: return redirect('ver_mundo', public_id=public_id)

@login_required
def toggle_lock(request, jid):
    
    w_orm = resolve_jid_orm(jid)
    if not w_orm:
        raise Http404("Entidad no encontrada")

    # CHEQUEO DE PERMISOS: Solo el Autor o Superusuario
    # (Admins no pueden bloquear mundos ajenos, solo Superusuarios)
    can_lock = request.user.is_superuser or (w_orm.author == request.user)
        
    if not can_lock:
        messages.error(request, "⛔ Solo el Autor o Superadmin pueden bloquear.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # Lógica de Bloqueo
    if w_orm.status == 'LOCKED':
        w_orm.status = 'OFFLINE' # Desbloquear a estado seguro
        messages.success(request, "🔓 Mundo desbloqueado (OFFLINE).")
    else:
        w_orm.status = 'LOCKED'
        messages.warning(request, "🔒 Mundo BLOQUEADO.")
    
    w_orm.save()
    
    # CRÍTICO: Redirigir a la página desde donde se hizo clic
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# @login_required (Eliminado para acceso público LIVE)
def ver_metadatos(request, public_id):
    w = resolve_jid_orm(public_id)
    if not w: return redirect('home')

    # Chequeo de Seguridad
    can_access, _ = check_world_access(request, w)
    if not can_access: 
        return render(request, 'private_access.html', status=403)
    
    context = {
        'name': w.name,
        'public_id': w.public_id,
        'jid': w.id,
        'metadata_template': None
    }
    
    # --- INYECCIÓN DE ETIQUETA DE JERARQUÍA ---
    context['hierarchy_label'] = get_readable_hierarchy(w.id)
    # ------------------------------------------
    
    # Cargar Metadatos (Reutilizar lógica)
    if w.id == "01" or "Caos" in w.name:
         tpl = MetadataTemplate.objects.filter(entity_type='CHAOS').first()
         if tpl:
             context['metadata_template'] = {
                'entity_type': tpl.entity_type,
                'schema': tpl.schema_definition,
                # En la aplicación real, recuperar los valores de metadatos almacenados de w.metadata
             }
             context['metadata_obj'] = {} 
    
    return render(request, 'ver_metadatos.html', context)

