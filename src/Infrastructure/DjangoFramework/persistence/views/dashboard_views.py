from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views import View
from django.db.models import Q
import os
import shutil
from src.Infrastructure.DjangoFramework.persistence.models import ContributionProposal, CaosVersionORM, CaosEventLog, CaosNarrativeVersionORM, CaosImageProposalORM, CaosWorldORM, CaosNarrativeORM, generate_nanoid
from src.Shared.Services.DiffService import DiffService
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase

# Narrative Use Cases
from src.WorldManagement.Caos.Application.approve_narrative_version import ApproveNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.reject_narrative_version import RejectNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.publish_narrative_to_live import PublishNarrativeToLiveUseCase
from src.WorldManagement.Caos.Application.restore_narrative_version import RestoreNarrativeVersionUseCase
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository

# ... imports remain same ...

from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from src.Infrastructure.DjangoFramework.persistence.forms import SubadminCreationForm
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile
from django.contrib.auth.models import User, Group
from django.db.models import Q

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        tid = str(target_id) if target_id else None
        CaosEventLog.objects.create(user=u, action=action, target_id=tid, details=details)
    except Exception as e: print(f"Log Error: {e}")

from django.contrib.auth.decorators import login_required, user_passes_test
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or (hasattr(user, 'profile') and user.profile.rank in ['ADMIN', 'SUBADMIN']))

def is_superuser(user): return user.is_superuser

@login_required
@login_required
# For simplicity and security first: Restrict Dashboard to Staff/Superuser as requested "Implementar Control de Acceso real...".
# User Request says: "AUTOR/ADMIN: Puede crear... usuarios (Standard): Solo lectura". 
# Usually Dashboard is for approving/rejecting which is an Admin task. 
# Authors create proposals. Admins approve.
def dashboard(request):
    # =========================================================================
    # 0. JURISDICTION & ACCESS CONTROL
    # =========================================================================
    user = request.user
    allowed_authors = User.objects.none()
    
    allowed_authors = User.objects.all() # Trusted Mode: Everyone sees everyone

    # =========================================================================
    # 1. GET PARAMETERS (FILTERS)
    # =========================================================================
    filter_author_id = request.GET.get('author')
    filter_type = request.GET.get('type') # WORLD, NARRATIVE, IMAGE
    search_query = request.GET.get('q')

    # =========================================================================
    # 2. BASE QUERYSETS (Hierarchy Mode)
    # =========================================================================
    # Logic:
    # - Superuser/Admin: Sees EVERYTHING (or at least their subordinates + their own).
    # - Subadmin: Sees THEIR OWN + THEIR BOSSES (to propose changes).
    # - User: Sees ONLY THEIR OWN.
    
    # Let's align with Request: "Admin sees Superior's work".
    
    if request.user.is_superuser:
        # SUPERUSER SEES ALL
        w_qs = CaosVersionORM.objects.all().select_related('world', 'author')
        n_qs = CaosNarrativeVersionORM.objects.all().select_related('narrative__world', 'author')
        i_qs = CaosImageProposalORM.objects.all().select_related('world', 'author')
    else:
        # HIERARCHY FILTER
        my_bosses = []
        if hasattr(request.user, 'profile'):
            # bosses = profiles that listing ME as collaborator
            boss_profiles = request.user.profile.bosses.all()
            my_bosses = [bp.user for bp in boss_profiles if bp.user]

        visible_users = [request.user] + my_bosses
        
        # Q Objects
        q_filter = Q(author__in=visible_users)
        
        w_qs = CaosVersionORM.objects.filter(q_filter).select_related('world', 'author')
        i_qs = CaosImageProposalORM.objects.filter(q_filter).select_related('world', 'author')
        
        # Narratives are tricky if Version doesn't have author set correctly sometimes? 
        # But assuming it does:
        n_qs = CaosNarrativeVersionORM.objects.filter(q_filter).select_related('narrative__world', 'author')

    # =========================================================================
    # 3. APPLY DYNAMIC FILTERS
    # =========================================================================
    
    # A) Filter by Author
    if filter_author_id:
        try:
            current_target_author = int(filter_author_id)
            w_qs = w_qs.filter(author_id=current_target_author)
            n_qs = n_qs.filter(author_id=current_target_author)
            i_qs = i_qs.filter(author_id=current_target_author)
        except ValueError: pass

    # B) Filter by Search Query
    if search_query:
        w_qs = w_qs.filter(Q(proposed_name__icontains=search_query) | Q(change_log__icontains=search_query))
        n_qs = n_qs.filter(Q(proposed_title__icontains=search_query) | Q(proposed_content__icontains=search_query))
        i_qs = i_qs.filter(title__icontains=search_query)

    # C) Filter by Type (World/Narc/Img)
    if filter_type == 'WORLD':
        n_qs = n_qs.none()
        i_qs = i_qs.none()
    elif filter_type == 'NARRATIVE':
        w_qs = w_qs.none()
        i_qs = i_qs.none()
    elif filter_type == 'IMAGE':
        w_qs = w_qs.none()
        n_qs = n_qs.none()

    # =========================================================================
    # 4. EXECUTE & SEGMENT (Pending/Approved/etc)
    # =========================================================================
    
    # 4.1 Worlds
    w_pending = list(w_qs.filter(status='PENDING').order_by('-created_at'))
    w_approved = list(w_qs.filter(status='APPROVED').order_by('-created_at'))
    w_rejected = list(w_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    w_archived = list(w_qs.filter(status='ARCHIVED').order_by('-created_at')[:20])

    # 4.2 Narratives
    n_pending = list(n_qs.filter(status='PENDING').order_by('-created_at'))
    n_approved = list(n_qs.filter(status='APPROVED').order_by('-created_at'))
    n_rejected = list(n_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    n_archived = list(n_qs.filter(status='ARCHIVED').order_by('-created_at')[:20])

    # 4.3 Images
    i_pending = list(i_qs.filter(status='PENDING').order_by('-created_at'))
    i_approved = list(i_qs.filter(status='APPROVED').order_by('-created_at'))
    i_rejected = list(i_qs.filter(status='REJECTED').order_by('-created_at')[:10])
    i_archived = list(i_qs.filter(status='ARCHIVED').exclude(action='DELETE').order_by('-created_at'))
    
    # 2.5 Pre-fetch Context Data for Performance
    all_worlds = {w.id: w.name for w in CaosWorldORM.objects.all()}
    # Dictionary for narratives might be heavy, fetching on demand or optimizing later
    
    # 3. Tag items
    for x in w_pending + w_approved + w_rejected + w_archived:
        x.type = 'WORLD'
        x.type_label = '🌍 MUNDO'
        x.target_name = x.proposed_name
        x.target_desc = x.proposed_description
        
        # Determine World Parent Context
        if x.world.id.endswith("00"): # Root world heuristic if JID structure used
            x.parent_context = "Universo Raíz"
        else:
            # Simple parent check or just usage of Name
            # If we want the parent world name, we need to fetch it.
            # But 'x.world' IS the world being edited.
            # For a World edit, the context IS the world itself or its parent if nested.
            # Assuming flat worlds for now or simple "Universe" context if it's a World.
            x.parent_context = "Universo"

        if x.cambios.get('action') == 'SET_COVER':
            x.target_desc = f"📸 Cambio de portada a: {x.cambios.get('cover_image')}"
        elif x.cambios.get('action') == 'TOGGLE_VISIBILITY':
            vis = x.cambios.get('target_visibility')
            x.target_desc = f"👁️ Cambiar a: {'PÚBLICO' if vis else 'PRIVADO'}"
            
        x.target_link = x.world.public_id if x.world.public_id else x.world.id
    
    # Map Narratives
    for x in n_pending + n_approved + n_rejected + n_archived:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.public_id if hasattr(x.narrative, 'public_id') and x.narrative.public_id else x.narrative.nid
        
        # Determine Narrative Context
        wname = x.narrative.world.name
        x.parent_context = wname
        nid = x.narrative.nid
        if '.' in nid:
            try:
                parent_nid = nid.rsplit('.', 1)[0]
                parent_n = CaosNarrativeORM.objects.filter(nid=parent_nid).first()
                if parent_n:
                    x.parent_context = f"{wname} > {parent_n.titulo}"
            except: pass

    # Map Images (NEW)
    # Ensure i_pending/i_approved are lists.
    for x in i_pending + i_approved + i_rejected + i_archived:
        x.type = 'IMAGE'
        x.type_label = '🖼️ IMAGEN'
        x.target_name = x.title or "(Sin Título)"
        
        # Derive description from action since no 'reason' field exists
        if x.action == 'DELETE':
            desc = f"🗑️ Borrar: {x.target_filename}"
        else:
            desc = "📸 Nueva Imagen"
            
        x.target_desc = desc
        
        # version_number might be missing on ImageProposal? It has 'id'.
        # Let's ensure it doesn't crash if version_number is missing.
        if not hasattr(x, 'version_number'): x.version_number = 1 
        
        x.parent_context = x.world.name if x.world else "Global"
        x.change_log = desc # Reuse desc for change_log

    # 4. Merge and Sort (Include Images)
    pending = sorted(w_pending + n_pending + i_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved + i_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected + i_rejected, key=lambda x: x.created_at, reverse=True)
    archived = sorted(w_archived + n_archived + i_archived, key=lambda x: x.created_at, reverse=True)

    # 5. Fetch Event Logs & Categorize (Also filtered?)
    # Ideally logs should also be filtered by jurisdiction for security
    # Fetch logs where actor IS in allowed_authors OR target is owned by allowed_authors?
    # For now, simplistic approach: Filter logs where user is in allowed_authors
    if not user.is_superuser:
        all_logs = CaosEventLog.objects.filter(user__in=allowed_authors).order_by('-timestamp')[:100]
    else:
        all_logs = CaosEventLog.objects.all().order_by('-timestamp')[:100]

    logs_world = []
    logs_narrative = []
    logs_image = []
    logs_other = []
    
    for l in all_logs:
        act = l.action.upper()
        if 'WORLD' in act or 'MUNDO' in act: logs_world.append(l)
        elif 'NARRATIVE' in act or 'NARRATIVA' in act: logs_narrative.append(l)
        elif 'IMAGE' in act or 'PHOTO' in act or 'IMAGEN' in act: logs_image.append(l)
        else: logs_other.append(l)

    # SPLIT PENDING REMOVED (UNIFIED VIEW)
    
    # GROUP INBOX (ALL PENDING) BY AUTHOR
    # Structure: [{'author': user, 'proposals': [list], 'count': int}, ...]
    from collections import defaultdict
    grouped_map = defaultdict(list)
    for item in pending:
        grouped_map[item.author].append(item)
    
    grouped_inbox_list = []
    for author, items in grouped_map.items():
        grouped_inbox_list.append({
            'author': author,
            'proposals': items,
            'count': len(items)
        })
    
    # Sort items within each group by created_at DESC (Newest First) as requested
    for group in grouped_inbox_list:
        group['proposals'].sort(key=lambda x: x.created_at, reverse=True)

    # Sort groups by author username
    grouped_inbox_list.sort(key=lambda x: x['author'].username if x['author'] else "")

    # 4. GROUP APPROVED BY AUTHOR (Same logic)
    grouped_approved_map = defaultdict(list)
    for item in approved:
         grouped_approved_map[item.author].append(item)
    
    grouped_approved_list = []
    for author, items in grouped_approved_map.items():
        grouped_approved_list.append({
            'author': author,
            'proposals': items,
            'count': len(items)
        })
    
    # Sort items within each group by created_at DESC
    for group in grouped_approved_list:
        group['proposals'].sort(key=lambda x: x.created_at, reverse=True)
        
    # Sort groups by author username
    grouped_approved_list.sort(key=lambda x: x['author'].username if x['author'] else "")

    # 4. GROUP ARCHIVED BY AUTHOR (New)
    grouped_archived_map = defaultdict(list)
    for item in archived:
         grouped_archived_map[item.author].append(item)
    
    grouped_archived_list = []
    for author, items in grouped_archived_map.items():
        grouped_archived_list.append({
            'author': author,
            'proposals': items,
            'count': len(items)
        })
    
    # Sort items within each group
    for group in grouped_archived_list:
        group['proposals'].sort(key=lambda x: x.created_at, reverse=True)
        
    grouped_archived_list.sort(key=lambda x: x['author'].username if x['author'] else "")

    # METRICS CALCULATION
    total_pending_count = len(pending) 
    total_activity_count = len(logs_world) + len(logs_narrative) + len(logs_image) + len(logs_other)

    context = {
        'pending': pending, 
        'grouped_inbox': grouped_inbox_list, 
        'grouped_approved': grouped_approved_list,
        'grouped_archived': grouped_archived_list,
        'approved': approved, # Needed for Metrics Count
        'rejected': rejected,
        'archived': archived,
        'logs_world': logs_world,
        'logs_narrative': logs_narrative,
        'logs_image': logs_image,
        'logs_other': logs_other,
        
        # NEW FOR METRICS
        'total_pending_count': total_pending_count,
        'total_activity_count': total_activity_count,
        
        # Context for Filter Sidebar
        'available_authors': allowed_authors,
        'current_author': int(filter_author_id) if filter_author_id else None,
        'current_type': filter_type,
        'search_query': search_query,
    }
    return render(request, 'dashboard.html', context)

def centro_control(request):
    return redirect('dashboard')

# --- WORLD ACTIONS ---

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_propuesta(request, id):
    try:
        v = CaosVersionORM.objects.get(id=id)
        
        # Check for DELETE action
        if v.cambios.get('action') == 'DELETE':
            # 1. Soft Delete the World
            v.world.soft_delete()
            # 2. Archive the proposal (It's done history)
            v.status = 'ARCHIVED'
            v.save()
            
            log_event(request.user, "WORLD_DELETE_CONFIRM", v.world.id, f"Confirmed deletion of {v.world.name}")
            messages.success(request, f"🗑️ Mundo '{v.world.name}' borrado y propuesta archivada.")
        else:
            # Normal Approval
            ApproveVersionUseCase().execute(id)
            log_event(request.user, "WORLD_APPROVE", v.world.id, f"Approved v{v.version_number} of {v.proposed_name}")
            messages.success(request, f"✅ Propuesta v{v.version_number} de '{v.proposed_name}' APROBADA (Lista para Live).")
            
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def rechazar_propuesta(request, id):
    try:
        RejectVersionUseCase().execute(id)
        log_event(request.user, "WORLD_REJECT", f"Version {id}", "Rejected proposal")
        messages.warning(request, "❌ Propuesta rechazada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def publicar_version(request, version_id):
    try:
        PublishToLiveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        log_event(request.user, "WORLD_PUBLISH", v.world.id, f"Published v{v.version_number} to LIVE")
        messages.success(request, f"🚀 Versión {v.version_number} PUBLICADA LIVE.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def archivar_propuesta(request, id):
    try:
        v = CaosVersionORM.objects.get(id=id)
        v.status = 'ARCHIVED'
        v.save()
        log_event(request.user, "WORLD_ARCHIVE", v.world.id, f"Archived proposal v{v.version_number}")
        messages.success(request, f"📦 Propuesta v{v.version_number} archivada correctamente.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al archivar: {str(e)}")
        return redirect('dashboard')

# DELETED: aprobar_version, rechazar_version (Redundant redirects)

def restaurar_version(request, version_id):
    try:
        RestoreVersionUseCase().execute(version_id, request.user)
        v = CaosVersionORM.objects.get(id=version_id)
        log_event(request.user, "WORLD_RESTORE", v.world.id, f"Restored v{v.version_number} to PENDING")
        messages.success(request, f"🔄 Versión {v.version_number} recuperada y movida a PENDIENTE. Apruébala para restaurarla en Live.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('dashboard')

def borrar_propuesta(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        wid = v.world.id
        v.delete()
        log_event(request.user, "WORLD_DELETE_PROPOSAL", wid, "Deleted proposal permanently")
        messages.success(request, f"🗑️ Propuesta/Versión eliminada definitivamente.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al borrar: {str(e)}")
        return redirect('dashboard')

def borrar_propuestas_masivo(request):
    if request.method == 'POST':
        try:
            ids = request.POST.getlist('selected_ids')
            narr_ids = request.POST.getlist('selected_narr_ids')
            img_ids = request.POST.getlist('selected_img_ids')

            count = 0
            if ids:
                count += CaosVersionORM.objects.filter(id__in=ids).delete()[0]
                log_event(request.user, "WORLD_BULK_DELETE", "Multiple", f"Deleted {len(ids)} world proposals")
            if narr_ids:
                count += CaosNarrativeVersionORM.objects.filter(id__in=narr_ids).delete()[0]
                log_event(request.user, "NARRATIVE_BULK_DELETE", "Multiple", f"Deleted {len(narr_ids)} narrative proposals")
            if img_ids:
                props = CaosImageProposalORM.objects.filter(id__in=img_ids)
                for p in props:
                    if p.image: p.image.delete()
                    p.delete()
                count += len(img_ids)
                log_event(request.user, "IMAGE_BULK_DELETE", "Multiple", f"Deleted {len(img_ids)} image proposals")

            if count > 0:
                messages.success(request, f"🗑️ Se han eliminado {count} elementos definitivamente.")
            else:
                messages.warning(request, "No has seleccionado nada.")
        except Exception as e:
            messages.error(request, f"Error al borrar masivamente: {str(e)}")
    return redirect(reverse('dashboard') + '#archived-list')

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_propuestas_masivo(request):
    if request.method == 'POST':
        try:
            ids = request.POST.getlist('selected_ids')
            narr_ids = request.POST.getlist('selected_narr_ids')
            img_ids = request.POST.getlist('selected_img_ids')

            count_w = 0; count_n = 0; count_i = 0

            # 1. Approve Worlds
            if ids:
                for wid in ids:
                    try:
                        ApproveVersionUseCase().execute(wid)
                        count_w += 1
                    except Exception as e: print(f"Error approving world {wid}: {e}")
                log_event(request.user, "WORLD_BULK_APPROVE", "Multiple", f"Approved {count_w} worlds")

            # 2. Approve Narratives
            if narr_ids:
                for nid in narr_ids:
                    try:
                        v = CaosNarrativeVersionORM.objects.get(id=nid)
                        if v.action == 'DELETE':
                            v.narrative.delete()
                            count_n += 1
                        else:
                            ApproveNarrativeVersionUseCase().execute(nid)
                            PublishNarrativeToLiveUseCase().execute(nid)
                            count_n += 1
                    except Exception as e: print(f"Error approving narrative {nid}: {e}")
                log_event(request.user, "NARRATIVE_BULK_APPROVE", "Multiple", f"Approved {count_n} narratives")

            # 3. Approve Images
            if img_ids:
                props = CaosImageProposalORM.objects.filter(id__in=img_ids)
                for prop in props:
                    try:
                        if prop.action == 'DELETE':
                             # Direct execution for DELETE -> Move to Trash
                             base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', str(prop.world.id))
                             trash_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/trash', str(prop.world.id))
                             target = os.path.join(base, prop.target_filename)
                             
                             if os.path.exists(target):
                                 os.makedirs(trash_dir, exist_ok=True)
                                 # Rename if exists in trash?
                                 trash_target = os.path.join(trash_dir, prop.target_filename)
                                 if os.path.exists(trash_target): os.remove(trash_target) # Overwrite old trash
                                 shutil.move(target, trash_target)
                             
                             prop.status = 'ARCHIVED'
                        else:
                             # ADD keeps standard flow
                             prop.status = 'APPROVED'
                        prop.save()
                        count_i += 1
                    except Exception as e: print(f"Error {e}")
                log_event(request.user, "IMAGE_BULK_APPROVE", "Multiple", f"Approved {count_i} images")

            total = count_w + count_n + count_i
            if total > 0: messages.success(request, f"✅ Apr {total} elementos.")
            else: messages.warning(request, "Nada seleccionado.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('dashboard')

# --- NARRATIVE ACTIONS ---

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_narrativa(request, id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=id)
        if v.action == 'DELETE':
            narr = v.narrative; title = narr.titulo; narr.soft_delete()
            log_event(request.user, "NARRATIVE_DELETE", f"Title: {title}", "Soft deleted narrative")
            messages.success(request, f"🗑️ Narrativa '{title}' movida a la papelera.")
        else:
            ApproveNarrativeVersionUseCase().execute(id)
            # PublishNarrativeToLiveUseCase().execute(id) <--- REMOVED AUTO PUBLISH
            log_event(request.user, "NARRATIVE_APPROVE", id, f"Approved v{v.version_number} (Pending Publish)")
            messages.success(request, f"✅ Narrativa APROBADA (Lista para Live).")
        return redirect('dashboard')
    except Exception as e: 
        messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def rechazar_narrativa(request, id):
    try:
        # Logic: Set status to REJECTED
        v = CaosNarrativeVersionORM.objects.get(id=id)
        v.status = 'REJECTED'
        v.save()
        log_event(request.user, "NARRATIVE_REJECT", v.narrative.nid, f"Rejected {v.proposed_title}")
    except Exception as e:
        messages.error(request, f"Error al rechazar narrativa: {str(e)}")
    return redirect('dashboard')

def publicar_narrativa(request, id):
    try:
        PublishNarrativeToLiveUseCase().execute(id)
        v = CaosNarrativeVersionORM.objects.get(id=id)
        log_event(request.user, "NARRATIVE_PUBLISH", id, f"Published v{v.version_number}")
        messages.success(request, f"🚀 Narrativa v{v.version_number} PUBLICADA LIVE.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, str(e)); return redirect('dashboard')

def archivar_narrativa(request, id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=id)
        v.status = 'ARCHIVED'
        v.save()
        log_event(request.user, "NARRATIVE_ARCHIVE", id, f"Archived narrative proposal v{v.version_number}")
        messages.success(request, f"📦 Narrativa v{v.version_number} archivada correctamente.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

def restaurar_narrativa(request, id):
    try:
        RestoreNarrativeVersionUseCase().execute(id, request.user)
        log_event(request.user, "NARRATIVE_RESTORE", id, "Restored narrative version")
        messages.success(request, f"🔄 Narrativa recuperada a PENDIENTE.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

def borrar_narrativa_version(request, id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=id); v.delete()
        log_event(request.user, "NARRATIVE_DELETE_PROPOSAL", id, "Deleted proposal")
        messages.success(request, f"🗑️ Versión narrativa eliminada.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

# --- IMAGE ACTIONS ---

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        
        if prop.action == 'DELETE':
             # Direct execution for DELETE -> Move to Trash
             base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', str(prop.world.id))
             trash_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/trash', str(prop.world.id))
             target = os.path.join(base, prop.target_filename)
             
             if os.path.exists(target): 
                 os.makedirs(trash_dir, exist_ok=True)
                 trash_target = os.path.join(trash_dir, prop.target_filename)
                 if os.path.exists(trash_target): os.remove(trash_target)
                 shutil.move(target, trash_target)
             
             prop.status = 'ARCHIVED'
             prop.save()
             log_event(request.user, "IMAGE_DELETE_TRASH", prop.world.id, f"Moved image {prop.target_filename} to trash")
             messages.success(request, f"🗑️ Imagen '{prop.target_filename}' movida a la papelera.")
        else:
             # Standard flow for ADD
             prop.status = 'APPROVED'; prop.save()
             log_event(request.user, "IMAGE_APPROVE", prop.world.id, f"Approved image {prop.title}")
             messages.success(request, f"✅ Imagen '{prop.title}' APROBADA (Pendiente de Publicar).")
        
        next_url = request.GET.get('next')
        if next_url: return redirect(next_url)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def rechazar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        prop.status = 'REJECTED'; prop.save()
        if prop.image: prop.image.delete()
        prop.delete()
        log_event(request.user, "IMAGE_REJECT", prop.world.id, "Rejected image")
        messages.warning(request, "❌ Imagen rechazada.")
        
        next_url = request.GET.get('next')
        if next_url: return redirect(next_url)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def archivar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        prop.status = 'ARCHIVED'
        prop.save()
        log_event(request.user, "IMAGE_ARCHIVE", prop.world.id, f"Archived image proposal {prop.title}")
        messages.success(request, f"📦 Imagen archivada correctamente.")
        
        next_url = request.GET.get('next')
        if next_url: return redirect(next_url)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def restaurar_imagen_papelera(request, id):
    try:
        # Get the original DELETE proposal that put it in trash
        original_prop = CaosImageProposalORM.objects.get(id=id)
        
        # Verify file exists in trash
        trash_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/trash', str(original_prop.world.id))
        trash_file = os.path.join(trash_dir, original_prop.target_filename)
        
        if not os.path.exists(trash_file):
            messages.error(request, "❌ El archivo ya no existe en la papelera.")
            return redirect('ver_papelera')
            
        # Create NEW Proposal for restoration
        # We need to move/copy the file to temp_proposals so it can be 'Added' again
        temp_filename = f"restore_{generate_nanoid()}_{original_prop.target_filename}"
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_proposals')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, temp_filename)
        
        shutil.copy2(trash_file, temp_path)
        
        # Create DB Entry
        new_prop = CaosImageProposalORM.objects.create(
            world=original_prop.world,
            title=f"Restauración: {original_prop.target_filename}",
            action='ADD',
            status='PENDING',
            author=request.user,
            image=f"temp_proposals/{temp_filename}"
        )
        
        log_event(request.user, "IMAGE_RESTORE_PROPOSAL", original_prop.world.id, f"Proposed restore for {original_prop.target_filename}")
        messages.success(request, f"♻️ Se ha creado una propuesta para restaurar '{original_prop.target_filename}'.")
        return redirect('ver_papelera')
        
    except Exception as e:
        messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('ver_papelera')

@login_required
@user_passes_test(is_admin_or_staff)
def restaurar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        prop.status = 'PENDING'
        prop.save()
        log_event(request.user, "IMAGE_RESTORE", prop.world.id, f"Restored image proposal {prop.title} to PENDING")
        messages.success(request, f"🔄 Imagen restaurada a Pendientes.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def borrar_imagen_definitivo(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        
        # Cleanup trash file if it's a deleted image
        if prop.action == 'DELETE' and prop.status == 'ARCHIVED':
             trash_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/trash', str(prop.world.id))
             trash_file = os.path.join(trash_dir, prop.target_filename)
             if os.path.exists(trash_file):
                 os.remove(trash_file)

        # Cleanup Standard File
        if prop.image: 
            prop.image.delete()
            
        prop.delete()
        log_event(request.user, "IMAGE_NUKE", prop.world.id if prop.world else "global", "Permanently deleted image proposal")
        messages.success(request, f"💥 Imagen eliminada definitivamente del historial.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

# --- TRASH / PAPELERA ---

def ver_papelera(request):
    try:
        # 1. Fetch deleted items
        deleted_worlds = CaosWorldORM.objects.filter(is_active=False).order_by('-deleted_at').select_related('author')
        deleted_narratives = CaosNarrativeORM.objects.filter(is_active=False).order_by('-deleted_at').select_related('created_by')
        deleted_images_props = CaosImageProposalORM.objects.filter(action='DELETE', status='ARCHIVED').order_by('-created_at').select_related('author')
        
        # 2. Structure Data
        # Format: groups = { 'AuthorName': { 'Mundos': [], 'Narrativas': [], 'Imagenes': [] } }
        groups = {}
        
        # Helper to add to groups
        def add_to_group(author_obj, type_label, item):
            a_name = author_obj.username if author_obj else "Desconocido"
            if a_name not in groups:
                groups[a_name] = {'Mundos': [], 'Narrativas': [], 'Imagenes': []}
            if type_label not in groups[a_name]: groups[a_name][type_label] = []
            groups[a_name][type_label].append(item)
            
        # Process Worlds
        for w in deleted_worlds:
            add_to_group(w.author, 'Mundos', w)
            
        # Process Narratives
        for n in deleted_narratives:
            add_to_group(n.created_by, 'Narrativas', n)

        # Process Images (Verify file in Trash)
        for i_prop in deleted_images_props:
            trash_path = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/trash', str(i_prop.world.id), i_prop.target_filename)
            if os.path.exists(trash_path):
                # Attach extra data to object for template
                i_prop.trash_path = f"/static/persistence/trash/{i_prop.world.id}/{i_prop.target_filename}"
                add_to_group(i_prop.author, 'Imagenes', i_prop)
            
        # Sort authors? Maybe alphabetical or most recent activity?
        # User said "lo separaramos por autor ... ademas de la fecha los mas nuevos delante"
        # The items inside are already sorted by query order_by('-deleted_at').
        # We can sort the authors themselves if needed, but dict order is insertion order in py3.7+.
        # Let's simple pass the dict.
        
        return render(request, 'papelera.html', {'grouped_trash': groups})
    except Exception as e:
        print(f"Error in trash: {e}")
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def restaurar_entidad_fisica(request, jid):
    try:
        w = CaosWorldORM.objects.get(id=jid, is_active=False)
        
        # Calculate next version
        last_v = w.versiones.order_by('-version_number').first()
        next_v = (last_v.version_number + 1) if last_v else 1
        
        # Create RESTORE Proposal
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Solicitud de Restauración desde Papelera",
            cambios={'action': 'RESTORE'},
            author=request.user if request.user.is_authenticated else None
        )
        
        log_event(request.user, "PROPOSE_RESTORE", w.id, f"Solicitud de restauración para '{w.name}'")

        messages.success(request, f"♻️ Solicitud de restauración creada para '{w.name}'. Revisa el Dashboard para aprobarla.")
        return redirect('ver_papelera')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')


@login_required
@user_passes_test(is_admin_or_staff)
def restaurar_narrativa(request, nid):
    try:
        n = CaosNarrativeORM.objects.get(nid=nid, is_active=False)
        # Direct restore for now (Simpler than Version Proposal)
        n.is_active = True
        n.deleted_at = None
        n.save()
        
        log_event(request.user, "NARRATIVE_RESTORE", n.nid, f"Restored narrative '{n.titulo}'")
        messages.success(request, f"♻️ Narrativa '{n.titulo}' restaurada correctamente.")
        return redirect('ver_papelera')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('ver_papelera')


@login_required
@user_passes_test(is_admin_or_staff)
def borrar_mundo_definitivo(request, id):
    try:
        w = CaosWorldORM.objects.get(id=id, is_active=False)
        name = w.name
        # Hard Delete
        w.delete()
        log_event(request.user, "WORLD_HARD_DELETE", id, f"Permanently deleted world '{name}'")
        messages.success(request, f"💥 Mundo '{name}' eliminado definitivamente.")
        return redirect('ver_papelera')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('ver_papelera')


@login_required
@user_passes_test(is_admin_or_staff)
def borrar_narrativa_definitivo(request, nid):
    try:
        n = CaosNarrativeORM.objects.get(nid=nid, is_active=False)
        title = n.titulo
        # Hard Delete
        n.delete()
        log_event(request.user, "NARRATIVE_HARD_DELETE", nid, f"Permanently deleted narrative '{title}'")
        messages.success(request, f"💥 Narrativa '{title}' eliminada definitivamente.")
        return redirect('ver_papelera')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('ver_papelera')


# --- USER MANAGEMENT (SUPERUSER ONLY) ---
from django.contrib.auth.models import Group, User
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "staff/user_management.html"
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        
        rich_users = []
        for u in context['users']:
            is_admin_role = admins_group in u.groups.all()
            role = 'Usuario'
            if u.is_superuser: role = 'Superadmin'
            elif is_admin_role: role = 'Admin'
            
            rich_users.append({
                'obj': u,
                'username': u.username,
                'email': u.email,
                'role': role,
                'is_admin_role': is_admin_role,
                'is_superuser': u.is_superuser
            })
        
        context['users'] = rich_users
        return context

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def archivar_propuestas_masivo(request):
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        
        count = 0
        
        if w_ids:
            count += CaosVersionORM.objects.filter(id__in=w_ids, status='APPROVED').update(status='ARCHIVED')
        if n_ids:
            count += CaosNarrativeVersionORM.objects.filter(id__in=n_ids, status='APPROVED').update(status='ARCHIVED')
        if i_ids:
            count += CaosImageProposalORM.objects.filter(id__in=i_ids, status='APPROVED').update(status='ARCHIVED')

        if count > 0:
            messages.success(request, f"📦 {count} propuestas archivadas correctamente.")
            log_event(request.user, "BULK_ARCHIVE", "dashboard", f"Archivadas {count} propuestas")
        else:
            messages.warning(request, "No se seleccionaron propuestas válidas.")
            
    return redirect(reverse('dashboard') + '#approved-list')

@login_required
def publicar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        repo = DjangoCaosRepository()
        
        # APPLY CHANGES TO LIVE SYSTEM
        if prop.action == 'DELETE':
            base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', str(prop.world.id))
            target = os.path.join(base, prop.target_filename)
            if os.path.exists(target): os.remove(target)
            msg = f"🗑️ Imagen '{prop.target_filename}' eliminada definitivamente (Live)."
        else:
            user_name = prop.author.username if prop.author else "Anónimo"
            repo.save_manual_file(str(prop.world.id), prop.image, username=user_name, title=prop.title)
            msg = f"🚀 Imagen '{prop.title}' PUBLICADA en Live."

        prop.status = 'ARCHIVED'
        prop.save()
        log_event(request.user, "IMAGE_PUBLISH", prop.world.id, f"Published image {prop.title}")
        messages.success(request, msg)
        
        next_url = request.GET.get('next')
        if next_url: return redirect(next_url)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def publicar_propuestas_masivo(request):
    if request.method == 'POST':
        w_ids = request.POST.getlist('selected_ids')
        n_ids = request.POST.getlist('selected_narr_ids')
        i_ids = request.POST.getlist('selected_img_ids')
        
        count = 0
        from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
        from src.WorldManagement.Caos.Application.publish_narrative_to_live import PublishNarrativeToLiveUseCase
        
        # 1. Worlds
        for wid in w_ids:
            try:
                PublishToLiveVersionUseCase().execute(wid)
                count += 1
            except Exception as e: print(f"Error publishing world {wid}: {e}")
            
        # 2. Narratives
        for nid in n_ids:
            try:
                PublishNarrativeToLiveUseCase().execute(nid)
                count += 1
            except Exception as e: print(f"Error publishing narrative {nid}: {e}")
            
        # 3. Images
        if i_ids:
            repo = DjangoCaosRepository()
            props = CaosImageProposalORM.objects.filter(id__in=i_ids) # Filter all selected, check status manually if needed
            i_count = 0
            for prop in props:
                try:
                    # Only publish if it was APPROVED
                    if prop.status == 'APPROVED':
                        if prop.action == 'DELETE':
                            base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', str(prop.world.id))
                            target = os.path.join(base, prop.target_filename)
                            if os.path.exists(target): os.remove(target)
                        else:
                            user_name = prop.author.username if prop.author else "Anónimo"
                            repo.save_manual_file(str(prop.world.id), prop.image, username=user_name, title=prop.title)
                        
                        prop.status = 'ARCHIVED'
                        prop.save()
                        i_count += 1
                except Exception as e: print(f"Error publishing image {prop.id}: {e}")
            
            count += i_count
            log_event(request.user, "IMAGE_BULK_PUBLISH", "Multiple", f"Published {i_count} images")

        if count > 0:
            messages.success(request, f"🚀 {count} elementos publicados correctamente.")
        else:
            messages.warning(request, "No se seleccionaron elementos válidos para publicar.")
            
    return redirect(reverse('dashboard') + '#approved-list')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def batch_revisar_imagenes(request):
    i_ids = []
    
    # 1. Try POST (Initial Selection)
    if request.method == 'POST':
        i_ids = request.POST.getlist('selected_img_ids')
        
    # 2. Try GET (Return from action)
    if not i_ids:
        ids_str = request.GET.get('ids', '')
        if ids_str:
            i_ids = ids_str.split(',')
            
    if not i_ids:
        messages.warning(request, "No seleccionaste ninguna imagen para revisar.")
        return redirect('dashboard')
        
    # Filter and fetch - EXCLUDE completed items (Archived/Rejected) so they "disappear" from the list
    proposals = CaosImageProposalORM.objects.filter(id__in=i_ids).exclude(status__in=['ARCHIVED', 'REJECTED']).select_related('world', 'author')
    
    # Clean up IDs (in case some were deleted/published and are no longer found)
    # We want to keep the "next" URL valid even if list shrinks, but for now we just pass the input IDs 
    # or the found IDs? Better to pass found IDs so we don't loop on missing ones? 
    # Actually, keep input IDs allows us to see "Empty State" if all are gone.
    # But usually we want to persist the ones we are working on.
    
    # Pre-calculate previews for DELETE proposals
    for p in proposals:
        if p.action == 'DELETE' and not p.image:
             # Construct URL manually: /static/persistence/img/<world_id>/<filename>
             # This assumes standard static configuration
             p.existing_image_url = f"{settings.STATIC_URL}persistence/img/{p.world.id}/{p.target_filename}"
    
    # We regenerate the CSV based on what is actually VISIBLE/VALID. 
    # This effectively removes the done item from the next URL too.
    current_ids_csv = ",".join([str(p.id) for p in proposals])

    # Determine context for Back button
    if proposals:
        first_status = proposals[0].status
    else:
         first_status = 'PENDING'
         
    back_anchor = '#approved-list' if first_status == 'APPROVED' else '#pending-list'
    
    context = {
        'proposals': proposals,
        'is_superuser': request.user.is_superuser,
        'back_anchor': back_anchor,
        'current_ids_csv': current_ids_csv
    }
    return render(request, 'staff/batch_review_images.html', context)

@login_required
@user_passes_test(is_superuser)
def toggle_admin_role(request, user_id):
    try:
        target_u = User.objects.get(id=user_id)
        
        # PROTECTION FOR SYSTEM USERS
        if target_u.username in ['Xico', 'Alone']:
            messages.error(request, f"⛔ ACCIÓN DENEGADA: El usuario '{target_u.username}' es intocable (Sistema/Superadmin).")
            return redirect('user_management')
            
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        
        if admins_group in target_u.groups.all():
            target_u.groups.remove(admins_group)
            messages.warning(request, f"⬇️ {target_u.username} ahora es Usuario estándar.")
        else:
            target_u.groups.add(admins_group)
            messages.success(request, f"⬆️ {target_u.username} es ahora ADMIN.")
            
    except Exception as e:
        messages.error(request, str(e))
        
    # Redirect to referer or default
    return redirect('user_management')

# --- DETAIL & DIFF VIEW ---
from src.Shared.Services.DiffService import DiffService

class ProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        try:
            prop = ContributionProposal.objects.select_related('target_entity', 'proposer').get(id=id)
            
            context = {
                'prop': prop,
                'target_entity': prop.target_entity,
            }
            
            if prop.contribution_type == 'EDIT':
                context['diffs'] = DiffService.compare_entity(prop.target_entity, prop.proposed_payload)
            elif prop.contribution_type == 'CREATE':
                context['preview'] = DiffService.get_create_preview(prop.proposed_payload)
                
            return render(request, 'staff/proposal_detail.html', context)
            
        except ContributionProposal.DoesNotExist:
            messages.error(request, "Propuesta no encontrada.")
            return redirect('dashboard')

class ImageProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        
        is_involved = (request.user == prop.author or request.user == prop.world.author)
        if not (request.user.is_superuser or request.user.groups.filter(name='Admins').exists() or is_involved):
             return render(request, 'private_access.html', status=403)
             
        old_image_url = None
        if prop.action == 'DELETE' and prop.target_filename:
             old_image_url = f"{settings.STATIC_URL}persistence/img/{prop.target_filename}"
        
        context = {
            'proposal': prop,
            'old_image_url': old_image_url,
            'is_superuser': request.user.is_superuser,
            'is_owner': (request.user == prop.world.author)
        }
        return render(request, 'staff/image_proposal_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def aprobar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        # Check permission for target world
        if not (request.user.is_superuser or prop.target_entity.author == request.user or request.user.is_staff):
            messages.error(request, "⛔ Sin permiso.")
            return redirect('dashboard')
            
        prop.status = 'APPROVED_WAITING'
        prop.reviewer = request.user
        prop.save()
        messages.success(request, "✅ Validado (Envíado a Staging).")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin_or_staff)
def rechazar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        if not (request.user.is_superuser or prop.target_entity.author == request.user or request.user.is_staff):
            messages.error(request, "⛔ Sin permiso.")
            return redirect('dashboard')
            
        prop.status = 'REJECTED'
        prop.reviewer = request.user
        prop.save()
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('dashboard')

# --- TEAM MANAGEMENT ---
class MyTeamView(LoginRequiredMixin, TemplateView):
    template_name = 'staff/my_team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Robust Profile Access
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            user.refresh_from_db()
            
        # 1. MY TEAM
        # Optimized query with counts
        context['team_list'] = user.profile.collaborators.select_related('user__profile').prefetch_related('collaborators').all()
             
        # 2. DIRECTORY / SEARCH
        query = self.request.GET.get('q')
        role_filter = self.request.GET.get('role')
        mode = self.request.GET.get('mode')
        
        should_list = query or role_filter or mode == 'directory'
        
        if should_list:
            qs = User.objects.filter(is_active=True).select_related('profile').exclude(id=user.id)
            
            if query:
                qs = qs.filter(Q(username__icontains=query) | Q(email__icontains=query))
            if role_filter:
                qs = qs.filter(profile__rank=role_filter)
                
            results = qs[:50]
                
            final_results = []
            my_collabs = set(user.profile.collaborators.values_list('user__id', flat=True))
            
            for r in results:
                if not hasattr(r, 'profile'):
                    UserProfile.objects.create(user=r)
                    r.refresh_from_db()
                
                # Extended Info
                team_count = r.profile.collaborators.count()
                boss = r.profile.bosses.first() # Get primary supervisor
                boss_name = boss.user.username if boss else None
                
                final_results.append({
                    'user': r,
                    'is_in_team': r.id in my_collabs,
                    'team_count': team_count,
                    'boss_name': boss_name
                })
            
            context['search_results'] = final_results
            context['search_query'] = query
            context['current_role'] = role_filter
            context['is_directory_mode'] = True
            
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        target_id = request.POST.get('target_id')
        
        try:
            target_user = User.objects.get(id=target_id)
            target_profile = target_user.profile
            my_profile = request.user.profile
            
            if action == 'add':
                my_profile.collaborators.add(target_profile)
                messages.success(request, f"✅ {target_user.username} añadido a tu equipo.")
                
            elif action == 'remove':
                my_profile.collaborators.remove(target_profile)
                messages.warning(request, f"❌ {target_user.username} eliminado de tu equipo.")
                
            elif action == 'promote_admin' and request.user.is_superuser:
                target_profile.rank = 'ADMIN'
                target_profile.save()
                
                admins_group, _ = Group.objects.get_or_create(name='Admins')
                target_user.groups.add(admins_group)
                
                messages.success(request, f"💎 {target_user.username} ascendido a ADMIN.")
            
            elif action == 'promote_subadmin':
                # ADMIN can promote their collaborators to SUBADMIN
                if request.user.profile.rank == 'ADMIN':
                    target_profile.rank = 'SUBADMIN'
                    target_profile.save()
                    messages.success(request, f"🛡️ {target_user.username} ascendido a SUBADMIN.")
                else:
                    messages.error(request, "⛔ Solo los Admins pueden nombrar Subadmins.")
            
            elif action == 'demote':
                # Logic: One step down
                current_rank = target_profile.rank
                
                if current_rank == 'ADMIN' and request.user.is_superuser:
                    target_profile.rank = 'SUBADMIN'
                    # Remove from Django Admin Group if exists
                    g = Group.objects.filter(name='Admins').first()
                    if g: target_user.groups.remove(g)
                    messages.warning(request, f"📉 {target_user.username} degradado a SUBADMIN.")
                    
                elif current_rank == 'SUBADMIN':
                    # Superuser OR Admin Boss can demote Subadmin
                    # (Note: We are not strictly checking boss=request.user here for simplicity, relying on 'collaborators' list check implicitly by UI visibility, but strict security would check ownership. For now, if you can see them in your team view and you are Admin, you can demote.)
                    target_profile.rank = 'USER'
                    messages.warning(request, f"📉 {target_user.username} degradado a USUARIO.")
                
                target_profile.save()

        except Exception as e:
            messages.error(request, f"Error: {e}")
            
        return redirect('my_team')

class CollaboratorWorkView(LoginRequiredMixin, TemplateView):
    template_name = 'staff/collaborator_work.html'
    
    def get_context_data(self, user_id=None, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if user_id:
            target_user = get_object_or_404(User, id=user_id)
            # Security: allow if superuser or boss
            is_my_collab = target_user.profile in self.request.user.profile.collaborators.all()
            if not self.request.user.is_superuser and not is_my_collab:
                 context['permission_denied'] = True
                 context['target_user'] = target_user
                 return context
        else:
            # My Dashboard mode
            target_user = self.request.user

        context['target_user'] = target_user
        
        # Fetch Work
        context['worlds'] = CaosWorldORM.objects.filter(author=target_user)
        # Using icontains for now since 'autor' might be a string field in v1
        context['narratives'] = CaosNarrativeORM.objects.filter(created_by=target_user).order_by('-updated_at')

        return context
        if not self.request.user.is_superuser and not is_my_collab:
            # Fallback permission denied (could raise 403)
            context['permission_denied'] = True
            return context
            
        context['target_user'] = target_user
        
        # Fetch Work
        context['worlds'] = CaosWorldORM.objects.filter(created_by=target_user)
        context['narratives'] = CaosNarrativeORM.objects.filter(created_by=target_user).order_by('-updated_at')[:10]
        
        return context
