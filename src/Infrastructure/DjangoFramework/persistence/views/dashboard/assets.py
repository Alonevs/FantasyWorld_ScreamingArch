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
    CaosEventLog
)
from django.contrib.auth.models import User
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository

# --- IMAGE ACTIONS ---

@login_required
@admin_only
def aprobar_imagen(request, id):
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'APPROVED'
        prop.save()
        messages.success(request, "Imagen Aprobada.")
        log_event(request.user, "APPROVE_IMAGE_PROPOSAL", id)
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
@admin_only
def rechazar_imagen(request, id):
    try:
        feedback = request.POST.get('admin_feedback', '') or request.GET.get('admin_feedback', '')
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'REJECTED'
        prop.admin_feedback = feedback
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
@admin_only
def publicar_imagen(request, id):
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
    
    # Images: TRASHED (from explicit delete) OR ARCHIVED (history versions)
    deleted_images = CaosImageProposalORM.objects.filter(status__in=['TRASHED', 'ARCHIVED']).select_related('author')
    
    # FILTER BY USER
    if f_user:
        try:
            uid = int(f_user)
            deleted_worlds = deleted_worlds.filter(author_id=uid)
            deleted_narratives = deleted_narratives.filter(created_by_id=uid)
            deleted_images = deleted_images.filter(author_id=uid)
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
            grouped_trash[author_name] = {'Mundos': [], 'Narrativas': [], 'Imagenes': []}
        grouped_trash[author_name][type_key].append(item)
        
    for w in deleted_worlds: 
        w.deleted_at = getattr(w, 'updated_at', getattr(w, 'created_at', None)) # Approximate
        w.deleted_by_name = deleter_map.get(w.id, "Desconocido")
        # Add Level and Description
        lvl = len(w.id) // 2
        label = get_readable_hierarchy(w.id)
        w.nice_level = f"Nivel {lvl}: {label}"
        w.short_desc = (w.description[:60] + "...") if w.description else ""
        add_to_group(w, 'Mundos')
        
    for n in deleted_narratives: 
        n.deleted_at = getattr(n, 'updated_at', getattr(n, 'created_at', None))
        n.deleted_by_name = deleter_map.get(n.nid, "Desconocido")
        # Add Context and Description
        n.nice_location = f"Mundo: {n.world.name}" if n.world else ""
        n.short_desc = (n.contenido[:60] + "...") if n.contenido else ""
        add_to_group(n, 'Narrativas')
        
    for i in deleted_images:
        # Improve presentation for template
        try:
             encoded_filename = urllib.parse.quote(i.target_filename)
        except: encoded_filename = ""
        
        i.trash_path = f"{settings.STATIC_URL}persistence/img/{i.world.id}/{encoded_filename}" if i.world else ""
        i.deleted_by_name = deleter_map.get(str(i.id), "Desconocido")
        i.nice_location = f"Mundo: {i.world.name}" if i.world else ""
        
        # LOGIC: Prioritize REASON. 
        # If title is "Borrar: filename", we assume it's redundant if reason is improperly missing or if we just want to avoid the label.
        clean_title = i.title.replace(f"Borrar: {i.target_filename}", "").strip() if i.title else ""
        if i.title and i.title.startswith("Borrar:"): clean_title = i.title.replace("Borrar:", "").strip()
        
        # If the resulting title is same as filename, ignore it
        if clean_title == i.target_filename: clean_title = ""
        
        i.short_desc = i.reason if i.reason else clean_title
        add_to_group(i, 'Imagenes')

    context = {
        'grouped_trash': grouped_trash,
        'users': users,
        'current_user': int(f_user) if f_user else None
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
        w_ids = request.POST.getlist('world_ids')
        n_ids = request.POST.getlist('narrative_ids')
        i_ids = request.POST.getlist('image_ids')
        
        # If coming from Review Page, IDs might be in CSV hidden fields
        if not w_ids and request.POST.get('world_ids_csv'): 
            w_ids = [x for x in request.POST.get('world_ids_csv').split(',') if x]
        if not n_ids and request.POST.get('narrative_ids_csv'): 
            n_ids = [x for x in request.POST.get('narrative_ids_csv').split(',') if x]
        if not i_ids and request.POST.get('image_ids_csv'): 
            i_ids = [x for x in request.POST.get('image_ids_csv').split(',') if x]

        count_w = len(w_ids)
        count_n = len(n_ids)
        count_i = len(i_ids)
        total = count_w + count_n + count_i
        
        if total == 0 and action == 'review':
             messages.warning(request, "⚠️ No seleccionaste nada para gestionar.")
             return redirect('ver_papelera')

        # --- STEP 1: REVIEW SELECTION ---
        if action == 'review':
            # LIMIT CHECK FOR IMAGES? 
            # User said "hasta 5 de una vez" previously.
            # But now says "previsualizacion de todas".
            # I will show all but warn if too many? Or strict limit?
            # "hasta 5" might still apply for DELETION safety.
            # I will pass objects to template.
            
            sel_worlds = CaosWorldORM.objects.filter(id__in=w_ids)
            sel_narratives = CaosNarrativeORM.objects.filter(nid__in=n_ids)
            sel_images = CaosImageProposalORM.objects.filter(id__in=i_ids)
            
            # Reconstruct trash paths for images if needed (though template logic handles it usually)
            for img in sel_images:
                img.trash_path = f"{settings.STATIC_URL}persistence/img/{img.world.id}/{img.target_filename}" if img.world else ""

            context = {
                'total_count': total,
                'sel_worlds': sel_worlds,
                'sel_narratives': sel_narratives,
                'sel_images': sel_images,
                'world_ids_csv': ",".join(w_ids),
                'narrative_ids_csv': ",".join(n_ids),
                'image_ids_csv': ",".join(i_ids)
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
                    if type_code == 'world':
                        if val == 'restore':
                            CaosWorldORM.objects.get(id=obj_id).restore(); stats['restored'] += 1
                        elif val == 'delete':
                            CaosWorldORM.objects.filter(id=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1
                            
                    elif type_code == 'narrative':
                        if val == 'restore':
                            CaosNarrativeORM.objects.get(nid=obj_id).restore(); stats['restored'] += 1
                        elif val == 'delete':
                            CaosNarrativeORM.objects.filter(nid=obj_id).delete(); stats['deleted'] += 1
                        else: stats['kept'] += 1

                    elif type_code == 'image':
                        if val == 'restore':
                            CaosImageProposalORM.objects.filter(id=obj_id).update(status='PENDING'); stats['restored'] += 1
                        elif val == 'delete':
                            # Cleanup file
                            img = CaosImageProposalORM.objects.filter(id=obj_id).first()
                            if img:
                                try:
                                    file_path = f"persistence/static/persistence/img/{img.world.id}/{img.target_filename}"
                                    full_path = os.path.join(settings.BASE_DIR, file_path)
                                    if os.path.exists(full_path): os.remove(full_path)
                                except: pass
                                img.delete(); stats['deleted'] += 1
                        elif val == 'archive':
                            # Explicitly set to ARCHIVED (History)
                             CaosImageProposalORM.objects.filter(id=obj_id).update(status='ARCHIVED'); stats['kept'] += 1
                        else: stats['kept'] += 1
                        
                except Exception as e:
                    print(f"Error processing {key}: {e}")

            messages.success(request, f"✅ Procesado: ♻️ {stats['restored']} Restaurados | 🔥 {stats['deleted']} Eliminados | 📂 {stats['kept']} Mantenidos")
            return redirect('ver_papelera')

    return redirect('ver_papelera')
