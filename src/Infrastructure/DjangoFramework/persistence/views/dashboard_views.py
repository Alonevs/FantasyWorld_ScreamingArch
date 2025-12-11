from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import os
from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosEventLog, CaosNarrativeVersionORM, CaosImageProposalORM, CaosWorldORM, CaosNarrativeORM
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

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: print(f"Log Error: {e}")

def dashboard(request):
    # 1. Fetch World Versions
    w_pending = list(CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at'))
    w_approved = list(CaosVersionORM.objects.filter(status='APPROVED').order_by('-created_at'))
    w_rejected = list(CaosVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10])
    w_archived = list(CaosVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:20])

    # 2. Fetch Narrative Versions
    n_pending = list(CaosNarrativeVersionORM.objects.filter(status='PENDING').order_by('-created_at'))
    n_approved = list(CaosNarrativeVersionORM.objects.filter(status='APPROVED').order_by('-created_at'))
    n_rejected = list(CaosNarrativeVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10])
    n_archived = list(CaosNarrativeVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:20])

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
        wid = x.world.id
        x.parent_context = "Raíz (Universo)"
        if len(wid) > 2:
            pid = wid[:-2]
            pname = all_worlds.get(pid, "Desconocido")
            x.parent_context = f"Orbitando: {pname}"
        
        if x.cambios.get('action') == 'SET_COVER':
            x.target_desc = f"📸 Cambio de portada a: {x.cambios.get('cover_image')}"
        elif x.cambios.get('action') == 'TOGGLE_VISIBILITY':
            vis = x.cambios.get('target_visibility')
            x.target_desc = f"👁️ Cambiar a: {'PÚBLICO' if vis else 'PRIVADO'}"
            
        x.target_link = x.world.public_id if x.world.public_id else x.world.id
    
    for x in n_pending + n_approved + n_rejected + n_archived:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.nid
        
        # Determine Narrative Context
        wname = x.narrative.world.name
        x.parent_context = f"Mundo: {wname}"
        
        # Try to find parent narrative title if it's a sub-chapter/node
        nid = x.narrative.nid
        if '.' in nid:
            try:
                parent_nid = nid.rsplit('.', 1)[0]
                # Optimizable: fetch only needed
                parent_n = CaosNarrativeORM.objects.filter(nid=parent_nid).first()
                if parent_n:
                    x.parent_context = f"Mundo: {wname} > {parent_n.titulo}"
            except: pass

    # 4. Merge and Sort
    pending = sorted(w_pending + n_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected, key=lambda x: x.created_at, reverse=True)
    archived = sorted(w_archived + n_archived, key=lambda x: x.created_at, reverse=True)

    # 5. Fetch Event Logs & Categorize
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

    # 6. Fetch Image Proposals
    img_pending = CaosImageProposalORM.objects.filter(status='PENDING').order_by('-created_at')

    context = {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'archived': archived,
        'logs_world': logs_world,
        'logs_narrative': logs_narrative,
        'logs_image': logs_image,
        'logs_other': logs_other,
        'img_pending': img_pending,
    }
    return render(request, 'dashboard.html', context)

def centro_control(request):
    return redirect('dashboard')

# --- WORLD ACTIONS ---

def aprobar_propuesta(request, id):
    try:
        ApproveVersionUseCase().execute(id)
        v = CaosVersionORM.objects.get(id=id)
        log_event(request.user, "WORLD_APPROVE", v.world.id, f"Approved v{v.version_number} of {v.proposed_name}")
        messages.success(request, f"✅ Propuesta v{v.version_number} de '{v.proposed_name}' APROBADA (Lista para Live).")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def rechazar_propuesta(request, id):
    try:
        RejectVersionUseCase().execute(id)
        log_event(request.user, "WORLD_REJECT", f"Version {id}", "Rejected proposal")
        messages.warning(request, "❌ Propuesta rechazada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def publicar_version(request, version_id):
    try:
        PublishToLiveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        log_event(request.user, "WORLD_PUBLISH", v.world.id, f"Published v{v.version_number} to LIVE")
        messages.success(request, f"🚀 Versión {v.version_number} PUBLICADA LIVE.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def aprobar_version(request, version_id): return redirect('aprobar_propuesta', id=version_id)
def rechazar_version(request, version_id): return redirect('rechazar_propuesta', id=version_id)

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
    return redirect('dashboard')

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
                repo = DjangoCaosRepository()
                props = CaosImageProposalORM.objects.filter(id__in=img_ids)
                for prop in props:
                    try:
                        if prop.action == 'DELETE':
                            base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', prop.world.id)
                            target = os.path.join(base, prop.target_filename)
                            if os.path.exists(target): os.remove(target)
                            prop.status = 'APPROVED'; prop.save()
                            count_i += 1
                        else:
                            user_name = prop.author.username if prop.author else "Anónimo"
                            repo.save_manual_file(prop.world.id, prop.image, username=user_name, title=prop.title)
                            prop.status = 'APPROVED'; prop.save()
                            count_i += 1
                    except Exception as e: print(f"Error {e}")
                log_event(request.user, "IMAGE_BULK_APPROVE", "Multiple", f"Approved {count_i} images")

            total = count_w + count_n + count_i
            if total > 0: messages.success(request, f"✅ Apr {total} elementos.")
            else: messages.warning(request, "Nada seleccionado.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('dashboard')

# --- NARRATIVE ACTIONS ---

def aprobar_narrativa(request, id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=id)
        if v.action == 'DELETE':
            narr = v.narrative; title = narr.titulo; narr.delete()
            log_event(request.user, "NARRATIVE_DELETE", f"Title: {title}", "Deleted narrative")
            messages.success(request, f"🗑️ Narrativa '{title}' eliminada definitivamente.")
        else:
            ApproveNarrativeVersionUseCase().execute(id)
            PublishNarrativeToLiveUseCase().execute(id)
            log_event(request.user, "NARRATIVE_APPROVE_PUBLISH", id, f"Approved & Published v{v.version_number}")
            messages.success(request, f"✅ Narrativa APROBADA y PUBLICADA.")
        return redirect('dashboard')
    except Exception as e: 
        messages.error(request, f"Error: {e}"); return redirect('dashboard')

def rechazar_narrativa(request, id):
    try:
        RejectNarrativeVersionUseCase().execute(id)
        log_event(request.user, "NARRATIVE_REJECT", id, "Rejected narrative")
        messages.warning(request, "❌ Narrativa rechazada.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

def publicar_narrativa(request, id):
    try:
        PublishNarrativeToLiveUseCase().execute(id)
        v = CaosNarrativeVersionORM.objects.get(id=id)
        log_event(request.user, "NARRATIVE_PUBLISH", id, f"Published v{v.version_number}")
        messages.success(request, f"🚀 Narrativa v{v.version_number} PUBLICADA LIVE.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, str(e)); return redirect('dashboard')

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

def aprobar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        repo = DjangoCaosRepository()
        if prop.action == 'DELETE':
            base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', prop.world.id)
            target = os.path.join(base, prop.target_filename)
            if os.path.exists(target): os.remove(target)
            prop.status = 'APPROVED'; prop.save()
            log_event(request.user, "IMAGE_DELETE", prop.world.id, f"Deleted image {prop.target_filename}")
            messages.success(request, f"🗑️ Imagen '{prop.target_filename}' borrada.")
        else:
            user_name = prop.author.username if prop.author else "Anónimo"
            repo.save_manual_file(prop.world.id, prop.image, username=user_name, title=prop.title)
            prop.status = 'APPROVED'; prop.save()
            log_event(request.user, "IMAGE_APPROVE", prop.world.id, f"Approved image {prop.title}")
            messages.success(request, f"✅ Imagen '{prop.title}' APROBADA.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

def rechazar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        prop.status = 'REJECTED'; prop.save()
        if prop.image: prop.image.delete()
        prop.delete()
        log_event(request.user, "IMAGE_REJECT", prop.world.id, "Rejected image")
        messages.warning(request, "❌ Imagen rechazada.")
        return redirect('dashboard')
    except Exception as e: messages.error(request, f"Error: {e}"); return redirect('dashboard')

# --- TRASH / PAPELERA ---

def ver_papelera(request):
    try:
        # All inactive worlds
        deleted_items = CaosWorldORM.objects.filter(is_active=False).order_by('-deleted_at')
        return render(request, 'papelera.html', {'deleted_items': deleted_items})
    except Exception as e:
        print(e)
        return redirect('dashboard')

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
