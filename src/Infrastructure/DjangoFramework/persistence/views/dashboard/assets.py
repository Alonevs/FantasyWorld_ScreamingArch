from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.urls import reverse
from .utils import log_event, is_superuser, is_admin_or_staff
from src.Infrastructure.DjangoFramework.persistence.rbac import admin_only, restrict_explorer
import os
import urllib.parse

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosImageProposalORM, CaosWorldORM, CaosNarrativeORM,
    CaosEventLog, CaosVersionORM, CaosNarrativeVersionORM
)
from django.contrib.auth.models import User
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository

# --- IMAGE ACTIONS ---

@login_required
def aprobar_imagen(request, id):
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or (prop.world and prop.world.author == request.user)):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede aprobar esta imagen.")
        return redirect('dashboard')
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'APPROVED'
        prop.reviewer = request.user
        prop.save()
        messages.success(request, "Imagen Aprobada.")
        log_event(request.user, "APPROVE_IMAGE_PROPOSAL", id)
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def rechazar_imagen(request, id):
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or (prop.world and prop.world.author == request.user)):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede rechazar esta imagen.")
        return redirect('dashboard')
    try:
        feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'REJECTED'
        prop.admin_feedback = feedback
        prop.reviewer = request.user
        prop.save()
        messages.success(request, f"Imagen Rechazada. Feedback: {feedback[:30]}...")
        log_event(request.user, "REJECT_IMAGE", id, details=f"Feedback: {feedback}")
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def archivar_imagen(request, id):
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, prop)
        
        # If it's a DELETE proposal and comes from Admin ('archivar' is 'Mantener' in UI)
        if prop.action == 'DELETE' and (request.user.is_staff or request.user.is_superuser):
            feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
            prop.status = 'REJECTED'
            prop.admin_feedback = feedback or "El administrador ha decidido mantener este elemento."
            prop.save()
            messages.success(request, "Propuesta de borrado rechazada (Elemento Mantenido).")
            log_event(request.user, "KEEP_IMAGE_REJECT_DELETE", id, details=feedback)
        else:
            prop.status = 'ARCHIVED'
            prop.save()
            messages.success(request, "Imagen Archivada.")
            log_event(request.user, "ARCHIVE_IMAGE", id)
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def publicar_imagen(request, id):
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or (prop.world and prop.world.author == request.user)):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede publicar esta imagen.")
        return redirect('dashboard')
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        repo = DjangoCaosRepository()

        if prop.action == 'DELETE':
            # ACTUAL FILE DELETION
            base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
            file_path = os.path.join(base_dir, str(prop.world.id), prop.target_filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                messages.success(request, f"🗑️ Imagen '{prop.target_filename}' borrada definitivamente de LIVE.")
                log_event(request.user, "DELETE_IMAGE_LIVE", prop.world.id, details=f"Archivo: {prop.target_filename}")
            else:
                messages.warning(request, f"⚠️ El archivo '{prop.target_filename}' no existía en el disco, pero la propuesta se ha archivado.")
        else:
            # NORMAL PUBLISH (ADD)
            user_name = prop.author.username if prop.author else "Anónimo"
            repo.save_manual_file(str(prop.world.id), prop.image, username=user_name, title=prop.title)
            messages.success(request, "🚀 Imagen Publicada y Archivada.")
            log_event(request.user, "PUBLISH_IMAGE", id)
        
        prop.status = 'ARCHIVED'
        prop.reviewer = request.user
        prop.save()
    except Exception as e:
        messages.error(request, f"❌ Error: {e}")
        print(f"Error publicar_imagen: {e}")
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def restaurar_imagen(request, id):
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, prop)
        
        prop.status = 'PENDING'
        prop.save()
        messages.success(request, "Imagen restaurada.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def borrar_imagen_definitivo(request, id):
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, prop)
        
        prop.status = 'TRASHED'
        prop.save()
        messages.success(request, "Imagen movida a la papelera.")
    except Exception as e: messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def restaurar_imagen_papelera(request, id):
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'PENDING'
        prop.save()
        messages.success(request, "Imagen restaurada al Dashboard.")
    except Exception as e: messages.error(request, str(e))
    return redirect('ver_papelera')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def batch_revisar_imagenes(request):
    i_ids = []
    if request.method == 'POST':
        i_ids = request.POST.getlist('selected_img_ids')
    if not i_ids:
        ids_str = request.GET.get('ids', '')
        if ids_str: i_ids = ids_str.split(',')
            
    if not i_ids:
        messages.warning(request, "No seleccionaste ninguna imagen.")
        return redirect('dashboard')
        
    proposals = CaosImageProposalORM.objects.filter(id__in=i_ids).exclude(status__in=['ARCHIVED', 'REJECTED']).select_related('world', 'author')
    
    # Pre-calc Delete previews
    for p in proposals:
        if p.action == 'DELETE' and not p.image:
             p.existing_image_url = f"{settings.STATIC_URL}persistence/img/{p.world.id}/{p.target_filename}"
    
    current_ids_csv = ",".join([str(p.id) for p in proposals])
    back_anchor = '#pending-list' # simplified
    
    context = {
        'proposals': proposals,
        'is_superuser': request.user.is_superuser,
        'back_anchor': back_anchor,
        'current_ids_csv': current_ids_csv
    }
    return render(request, 'staff/batch_review_images.html', context)

class ImageProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        is_involved = (request.user == prop.author or (prop.world and request.user == prop.world.author))
        if not (request.user.is_superuser or request.user.is_staff or is_involved):
             return render(request, 'private_access.html', status=403)
             
        old_image_url = None
        if prop.action == 'DELETE' and prop.target_filename:
             old_image_url = f"{settings.STATIC_URL}persistence/img/{prop.world.id}/{prop.target_filename}"
        
        context = {
            'proposal': prop,
            'old_image_url': old_image_url,
            'is_superuser': request.user.is_superuser,
            'is_owner': (prop.world and request.user == prop.world.author)
        }
        return render(request, 'staff/image_proposal_detail.html', context)

# --- TRASH ---

@login_required
def ver_papelera(request):
    # 0. Common Data
    users = User.objects.all().order_by('username')
    f_user = request.GET.get('user')
    
    # 1. Fetch Items
    deleted_worlds = CaosWorldORM.objects.filter(is_active=False).select_related('author')
    deleted_narratives = CaosNarrativeORM.objects.filter(is_active=False).select_related('created_by')
    deleted_images = CaosImageProposalORM.objects.filter(status__in=['TRASHED', 'ARCHIVED']).select_related('author')

    # Propuestas (Versions): Mundos + Metadatos
    deleted_versions = CaosVersionORM.objects.filter(status='ARCHIVED').select_related('world', 'author')
    deleted_narr_versions = CaosNarrativeVersionORM.objects.filter(status='ARCHIVED').select_related('narrative__world', 'author')

    # FILTER BY USER
    if f_user:
        try:
            uid = int(f_user)
            deleted_worlds = deleted_worlds.filter(author_id=uid)
            deleted_narratives = deleted_narratives.filter(created_by_id=uid)
            deleted_images = deleted_images.filter(author_id=uid)
            deleted_versions = deleted_versions.filter(author_id=uid)
            deleted_narr_versions = deleted_narr_versions.filter(author_id=uid)
        except (ValueError, TypeError): pass
    
    # --- AUDIT LOG HYDRATION ---
    # Fetch logs for these items to find WHO deleted them
    all_target_ids = [str(w.id) for w in deleted_worlds] + [str(n.nid) for n in deleted_narratives] + [str(i.id) for i in deleted_images]
    # Fetch latest SOFT_DELETE msg for each
    audit_logs = CaosEventLog.objects.filter(
        target_id__in=all_target_ids, 
        action='SOFT_DELETE'
    ).select_related('user').order_by('target_id', '-timestamp')
    
    # Map target_id -> user_name
    deleter_map = {}
    for log in audit_logs:
        if log.target_id not in deleter_map: # Take first (latest)
            deleter_map[log.target_id] = log.user.username if log.user else "Sistema"

    # 2. Group by Author
    grouped_trash = {}
    
    # Import hierarchy utils
    from src.WorldManagement.Caos.Domain.hierarchy_utils import get_readable_hierarchy

    def add_to_group(item, type_key):
        user_obj = getattr(item, 'author', getattr(item, 'created_by', None))
        # Change "Sistema" -> "Alone" as requested
        # Also check if user_obj is None, use "Alone"
        author_name = user_obj.username if user_obj else "Alone"
        
        if author_name not in grouped_trash:
            grouped_trash[author_name] = {'Mundos': [], 'Narrativas': [], 'Imagenes': [], 'Metadatos': []}
        
        # Ensure all core fields exist to prevent Template lookup errors
        if not hasattr(item, 'nice_location'): item.nice_location = None
        if not hasattr(item, 'nice_level'): item.nice_level = None
        
        grouped_trash[author_name][type_key].append(item)
        
    for w in deleted_worlds: 
        w.deleted_at = getattr(w, 'updated_at', getattr(w, 'created_at', None)) # Approximate
        w.deleted_by_name = deleter_map.get(w.id, "Desconocido")
        # Add Level and Description
        lvl = len(w.id) // 2
        label = get_readable_hierarchy(w.id)
        w.nice_level = f"Nivel {lvl}: {label}"
        w.short_desc = (w.description[:60] + "...") if w.description else ""
        w.prefixed_id = f"w_{w.id}"
        w.type_label = "🌍 MUNDO (Live)"
        w.trash_type = "WORLD_LIVE"
        add_to_group(w, 'Mundos')
        
    for n in deleted_narratives: 
        n.deleted_at = getattr(n, 'updated_at', getattr(n, 'created_at', None))
        n.deleted_by_name = deleter_map.get(n.nid, "Desconocido")
        # Add Context and Description
        n.nice_location = f"Mundo: {n.world.name}" if n.world else ""
        n.short_desc = (n.contenido[:60] + "...") if n.contenido else ""
        n.prefixed_id = f"n_{n.nid}"
        n.type_label = "📜 NARRATIVA (Live)"
        n.trash_type = "NARRATIVE_LIVE"
        add_to_group(n, 'Narrativas')
        
    for i in deleted_images:
        # ... logic for images ...
        try: encoded_filename = urllib.parse.quote(i.target_filename)
        except: encoded_filename = ""
        i.trash_path = f"{settings.STATIC_URL}persistence/img/{i.world.id}/{encoded_filename}" if i.world else ""
        i.deleted_by_name = deleter_map.get(str(i.id), "Desconocido")
        i.nice_location = f"Mundo: {i.world.name}" if i.world else ""
        clean_title = i.title.replace(f"Borrar: {i.target_filename}", "").strip() if i.title else ""
        if i.title and i.title.startswith("Borrar:"): clean_title = i.title.replace("Borrar:", "").strip()
        if clean_title == i.target_filename: clean_title = ""
        i.short_desc = i.reason if i.reason else clean_title
        i.type_key = 'IMAGE'
        i.prefixed_id = f"i_{i.id}"
        i.type_label = "🖼️ IMAGEN"
        i.trash_type = "IMAGE"
        add_to_group(i, 'Imagenes')

    for v in deleted_versions:
        v.deleted_at = v.created_at # Versions don't have soft-delete log usually
        v.type_key = 'WORLD'
        v.nice_location = "Mundo"
        v.short_desc = v.change_log
        group_key = 'Mundos'
        
        # Detect Metadata
        if v.cambios and (v.cambios.get('action') == 'METADATA_UPDATE' or 'metadata' in v.cambios.keys()):
            v.type_key = 'METADATA'
            v.nice_location = "Metadatos"
            v.type_label = "🧬 METADATOS"
            group_key = 'Metadatos'
        else:
            v.type_label = "🌍 MUNDO (Propuesta)"
        
        v.prefixed_id = f"wv_{v.id}"
        v.trash_type = "WORLD_PROP" if v.type_key != 'METADATA' else "METADATA"
        add_to_group(v, group_key)

    for nv in deleted_narr_versions:
        nv.deleted_at = nv.created_at
        nv.type_key = 'NARRATIVE'
        # Safety for missing narrative or world
        nv.nice_location = f"Mundo: {nv.narrative.world.name}" if nv.narrative and nv.narrative.world else ""
        nv.short_desc = nv.change_log
        nv.prefixed_id = f"nv_{nv.id}"
        nv.type_label = "📖 NARRATIVA (Propuesta)"
        nv.trash_type = "NARRATIVE_PROP"
        add_to_group(nv, 'Narrativas')

    # Create Stacked View by Type for the template
    trash_by_type = {
        'Mundos': [],
        'Metadatos': [],
        'Narrativas': [],
        'Imagenes': []
    }
    for auth in grouped_trash.values():
        for t_key, items in auth.items():
            if t_key in trash_by_type:
                trash_by_type[t_key].extend(items)

    context = {
        'grouped_trash': grouped_trash, # Keep for backward compat or author view
        'trash_by_type': trash_by_type, # NEW Stacked View
        'users': users,
        'current_user': int(f_user) if f_user else None,
    }
    return render(request, 'papelera.html', context)

@login_required
def restaurar_entidad_fisica(request, jid):
    try:
        w = get_object_or_404(CaosWorldORM, id=jid)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, w)
        
        w.restore()
        messages.success(request, f"Mundo {w.name} restaurado.")
        log_event(request.user, "RESTORE_WORLD_PHYSICAL", jid)
    except Exception as e: messages.error(request, str(e))
    return redirect('ver_papelera')

@login_required
@admin_only # Only Admins can physically delete
def borrar_mundo_definitivo(request, id):
    try:
        w = get_object_or_404(CaosWorldORM, id=id)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, w)
        
        w.delete()
        messages.success(request, "Mundo eliminado.")
    except Exception as e: messages.error(request, str(e))
    return redirect('ver_papelera')

@login_required
@admin_only
def borrar_narrativa_definitivo(request, nid):
    try:
        n = get_object_or_404(CaosNarrativeORM, nid=nid)
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        check_ownership(request.user, n)
        
        n.delete()
        messages.success(request, "Narrativa eliminada.")
    except Exception as e: messages.error(request, str(e))
    return redirect('ver_papelera')

@login_required
@admin_only
def manage_trash_bulk(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # New unified ID list
        trash_ids = request.POST.getlist('selected_trash_ids')
        
        # Legacy support/fallback (extract from legacy fields if empty)
        if not trash_ids:
             trash_ids += [f"w_{x}" for x in request.POST.getlist('world_ids')]
             trash_ids += [f"n_{x}" for x in request.POST.getlist('narrative_ids')]
             trash_ids += [f"i_{x}" for x in request.POST.getlist('image_ids')]
        
        # Process CSV values (from review page)
        if not trash_ids and request.POST.get('trash_ids_csv'):
             trash_ids = [x for x in request.POST.get('trash_ids_csv').split(',') if x]

        if not trash_ids:
             messages.warning(request, "⚠️ No seleccionaste nada para gestionar.")
             return redirect('ver_papelera')

        # --- STEP 1: ACTIONS ---
        if action == 'hard_delete':
            # Direct physical deletion for multiple items
            counts = {'Worlds': 0, 'Narratives': 0, 'Images': 0, 'Versions': 0}
            
            w_ids = [x.split('_')[1] for x in trash_ids if x.startswith('w_')]
            wv_ids = [x.split('_')[1] for x in trash_ids if x.startswith('wv_')]
            n_ids = [x.split('_')[1] for x in trash_ids if x.startswith('n_')]
            nv_ids = [x.split('_')[1] for x in trash_ids if x.startswith('nv_')]
            i_ids = [x.split('_')[1] for x in trash_ids if x.startswith('i_')]

            if w_ids: counts['Worlds'], _ = CaosWorldORM.objects.filter(id__in=w_ids).delete()
            if wv_ids: counts['Versions'], _ = CaosVersionORM.objects.filter(id__in=wv_ids, status='ARCHIVED').delete()
            if n_ids: counts['Narratives'], _ = CaosNarrativeORM.objects.filter(nid__in=n_ids).delete()
            if nv_ids: counts['Versions'] += CaosNarrativeVersionORM.objects.filter(id__in=nv_ids, status='ARCHIVED').delete()[0]
            if i_ids: counts['Images'], _ = CaosImageProposalORM.objects.filter(id__in=i_ids).delete()

            total = sum(counts.values())
            messages.success(request, f"💀 Borrado definitivo completado. Se han eliminado {total} elementos.")
            log_event(request.user, "TRASH_BULK_HARD_DELETE", f"Eliminación masiva de {total} items.")
            return redirect('ver_papelera')

        elif action == 'review':
            # Segregate by type
            w_live_ids = [x.split('_')[1] for x in trash_ids if x.startswith('w_')]
            w_prop_ids = [x.split('_')[1] for x in trash_ids if x.startswith('wv_')]
            n_live_ids = [x.split('_')[1] for x in trash_ids if x.startswith('n_')]
            n_prop_ids = [x.split('_')[1] for x in trash_ids if x.startswith('nv_')]
            i_ids = [x.split('_')[1] for x in trash_ids if x.startswith('i_')]

            sel_worlds_live = CaosWorldORM.objects.filter(id__in=w_live_ids)
            sel_worlds_prop = CaosVersionORM.objects.filter(id__in=w_prop_ids)
            sel_narr_live = CaosNarrativeORM.objects.filter(nid__in=n_live_ids)
            sel_narr_prop = CaosNarrativeVersionORM.objects.filter(id__in=n_prop_ids)
            sel_images = CaosImageProposalORM.objects.filter(id__in=i_ids)

            # Mark for template
            for x in sel_worlds_live: x.type_label = "Mundo (Live)"; x.prefixed_id = f"w_{x.id}"
            for x in sel_worlds_prop: x.type_label = "Mundo (Propuesta)"; x.prefixed_id = f"wv_{x.id}"
            for x in sel_narr_live: x.type_label = "Narrativa (Live)"; x.prefixed_id = f"n_{x.nid}"
            for x in sel_narr_prop: x.type_label = "Narrativa (Propuesta)"; x.prefixed_id = f"nv_{x.id}"
            for x in sel_images: 
                x.type_label = "Imagen"
                x.prefixed_id = f"i_{x.id}"
                x.trash_path = f"{settings.STATIC_URL}persistence/img/{x.world.id}/{x.target_filename}" if x.world else ""

            context = {
                'total_count': len(trash_ids),
                'items': list(sel_worlds_live) + list(sel_worlds_prop) + list(sel_narr_live) + list(sel_narr_prop) + list(sel_images),
                'trash_ids_csv': ",".join(trash_ids)
            }
            return render(request, 'dashboard/trash_bulk_review.html', context)

        # --- STEP 3: GRANULAR PROCESSING ---
        elif action == 'process_granular':
            stats = {'restored': 0, 'deleted': 0, 'kept': 0}
            
            # Iterate all POST keys
            for key, val in request.POST.items():
                if not key.startswith('action_'): continue
                
                parts = key.split('_')
                if len(parts) < 3: continue
                
                type_code = parts[1] # world, narrative, image
                obj_id = parts[2]
                
                try:
                    if type_code == 'w': # World Live
                        if val == 'restore':
                            CaosWorldORM.objects.get(id=obj_id).restore(); stats['restored'] += 1
                        elif val == 'delete':
                            CaosWorldORM.objects.filter(id=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1

                    elif type_code == 'wv': # World Proposal
                        if val == 'restore':
                            CaosVersionORM.objects.filter(id=obj_id).update(status='PENDING'); stats['restored'] += 1
                        elif val == 'delete':
                            CaosVersionORM.objects.filter(id=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1
                            
                    elif type_code == 'n': # Narrative Live
                        if val == 'restore':
                            CaosNarrativeORM.objects.get(nid=obj_id).restore(); stats['restored'] += 1
                        elif val == 'delete':
                            CaosNarrativeORM.objects.filter(nid=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1

                    elif type_code == 'nv': # Narrative Proposal
                        if val == 'restore':
                            CaosNarrativeVersionORM.objects.filter(id=obj_id).update(status='PENDING'); stats['restored'] += 1
                        elif val == 'delete':
                            CaosNarrativeVersionORM.objects.filter(id=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1

                    elif type_code == 'i': # Image (Proposal)
                        if val == 'restore':
                            CaosImageProposalORM.objects.filter(id=obj_id).update(status='PENDING'); stats['restored'] += 1
                        elif val == 'delete':
                            img = CaosImageProposalORM.objects.filter(id=obj_id).first()
                            if img:
                                try:
                                    file_path = f"persistence/static/persistence/img/{img.world.id}/{img.target_filename}"
                                    if os.path.exists(os.path.join(settings.BASE_DIR, file_path)):
                                        os.remove(os.path.join(settings.BASE_DIR, file_path))
                                except: pass
                                img.delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1
                        
                except Exception as e:
                    print(f"Error processing {key}: {e}")

            messages.success(request, f"✅ Procesado: ♻️ {stats['restored']} Restaurados | 🔥 {stats['deleted']} Eliminados | 📂 {stats['kept']} Mantenidos")
            return redirect('ver_papelera')

    return redirect('ver_papelera')
