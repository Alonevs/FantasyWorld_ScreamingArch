from django.shortcuts import render, redirect
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosEventLog, CaosNarrativeVersionORM, CaosImageProposalORM
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase

# Narrative Use Cases
from src.WorldManagement.Caos.Application.approve_narrative_version import ApproveNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.reject_narrative_version import RejectNarrativeVersionUseCase
from src.WorldManagement.Caos.Application.publish_narrative_to_live import PublishNarrativeToLiveUseCase
from src.WorldManagement.Caos.Application.restore_narrative_version import RestoreNarrativeVersionUseCase

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

    # 3. Tag items
    for x in w_pending + w_approved + w_rejected + w_archived:
        x.type = 'WORLD'
        x.type_label = '🌍 MUNDO'
        x.target_name = x.proposed_name
        x.target_desc = x.proposed_description
        x.target_link = x.world.public_id if x.world.public_id else x.world.id
    
    for x in n_pending + n_approved + n_rejected + n_archived:
        x.type = 'NARRATIVE'
        x.type_label = '📖 NARRATIVA'
        x.target_name = x.proposed_title
        x.target_desc = x.proposed_content
        x.target_link = x.narrative.nid

    # 4. Merge and Sort
    pending = sorted(w_pending + n_pending, key=lambda x: x.created_at, reverse=True)
    approved = sorted(w_approved + n_approved, key=lambda x: x.created_at, reverse=True)
    rejected = sorted(w_rejected + n_rejected, key=lambda x: x.created_at, reverse=True)
    archived = sorted(w_archived + n_archived, key=lambda x: x.created_at, reverse=True)

    # 5. Fetch Event Logs
    logs = CaosEventLog.objects.all().order_by('-timestamp')[:50]

    # 6. Fetch Image Proposals
    img_pending = CaosImageProposalORM.objects.filter(status='PENDING').order_by('-created_at')

    context = {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'archived': archived,
        'logs': logs,
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
        messages.success(request, f"✅ Propuesta v{v.version_number} de '{v.proposed_name}' APROBADA (Lista para Live).")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def rechazar_propuesta(request, id):
    try:
        RejectVersionUseCase().execute(id)
        messages.warning(request, "❌ Propuesta rechazada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def publicar_version(request, version_id):
    try:
        PublishToLiveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"🚀 Versión {v.version_number} PUBLICADA LIVE.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def aprobar_version(request, version_id):
    return redirect('aprobar_propuesta', id=version_id)

def rechazar_version(request, version_id):
    return redirect('rechazar_propuesta', id=version_id)

def restaurar_version(request, version_id):
    try:
        RestoreVersionUseCase().execute(version_id, request.user)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"🔄 Versión {v.version_number} recuperada y movida a PENDIENTE. Apruébala para restaurarla en Live.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('dashboard')

def borrar_propuesta(request, version_id):
    try:
        v = CaosVersionORM.objects.get(id=version_id)
        v.delete()
        messages.success(request, f"🗑️ Propuesta/Versión eliminada definitivamente.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al borrar: {str(e)}")
        return redirect('dashboard')

def borrar_propuestas_masivo(request):
    if request.method == 'POST':
        try:
            # Worlds
            ids = request.POST.getlist('selected_ids')
            # Narratives
            narr_ids = request.POST.getlist('selected_narr_ids')
            # Images
            img_ids = request.POST.getlist('selected_img_ids')

            count = 0
            if ids:
                count += CaosVersionORM.objects.filter(id__in=ids).delete()[0]
            if narr_ids:
                count += CaosNarrativeVersionORM.objects.filter(id__in=narr_ids).delete()[0]
            if img_ids:
                # Delete images from filesystem too if needed, but signals usually handle it or delete() method
                # For now just delete the proposal
                props = CaosImageProposalORM.objects.filter(id__in=img_ids)
                for p in props:
                    if p.image: p.image.delete()
                    p.delete()
                count += len(img_ids)

            if count > 0:
                messages.success(request, f"🗑️ Se han eliminado {count} elementos definitivamente.")
            else:
                messages.warning(request, "No has seleccionado nada.")
                
        except Exception as e:
            messages.error(request, f"Error al borrar masivamente: {str(e)}")
    return redirect('dashboard')

def aprobar_imagenes_masivo(request):
    if request.method == 'POST':
        try:
            img_ids = request.POST.getlist('selected_img_ids')
            if not img_ids:
                messages.warning(request, "No has seleccionado imágenes para aprobar.")
                return redirect('dashboard')
            
            from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
            repo = DjangoCaosRepository()
            
            props = CaosImageProposalORM.objects.filter(id__in=img_ids)
            count = 0
            for prop in props:
                try:
                    user_name = prop.author.username if prop.author else "Anónimo"
                    repo.save_manual_file(prop.world.id, prop.image, username=user_name, title=prop.title)
                    prop.status = 'APPROVED'
                    prop.save()
                    count += 1
                except Exception as e:
                    print(f"Error approving image {prop.id}: {e}")
            
            messages.success(request, f"✅ {count} imágenes aprobadas y publicadas.")
        except Exception as e:
            messages.error(request, f"Error masivo: {str(e)}")
    return redirect('dashboard')

# --- NARRATIVE ACTIONS ---

def aprobar_narrativa(request, id):
    try:
        ApproveNarrativeVersionUseCase().execute(id)
        v = CaosNarrativeVersionORM.objects.get(id=id)
        messages.success(request, f"✅ Narrativa v{v.version_number} '{v.proposed_title}' APROBADA.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def rechazar_narrativa(request, id):
    try:
        RejectNarrativeVersionUseCase().execute(id)
        messages.warning(request, "❌ Narrativa rechazada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

def publicar_narrativa(request, id):
    try:
        PublishNarrativeToLiveUseCase().execute(id)
        v = CaosNarrativeVersionORM.objects.get(id=id)
        messages.success(request, f"🚀 Narrativa v{v.version_number} PUBLICADA LIVE.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')

def restaurar_narrativa(request, id):
    try:
        RestoreNarrativeVersionUseCase().execute(id, request.user)
        v = CaosNarrativeVersionORM.objects.get(id=id)
        messages.success(request, f"🔄 Narrativa v{v.version_number} recuperada a PENDIENTE.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('dashboard')

def borrar_narrativa_version(request, id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=id)
        v.delete()
        messages.success(request, f"🗑️ Versión narrativa eliminada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al borrar: {str(e)}")
        return redirect('dashboard')

# --- IMAGE ACTIONS ---

def aprobar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        # Move logic: Save to final repo
        from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
        repo = DjangoCaosRepository()
        
        user_name = prop.author.username if prop.author else "Anónimo"
        repo.save_manual_file(prop.world.id, prop.image, username=user_name, title=prop.title)
        
        prop.status = 'APPROVED'
        prop.save()
        
        messages.success(request, f"✅ Imagen '{prop.title}' APROBADA y publicada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al aprobar imagen: {str(e)}")
        return redirect('dashboard')

def rechazar_imagen(request, id):
    try:
        prop = CaosImageProposalORM.objects.get(id=id)
        prop.status = 'REJECTED'
        prop.save()
        if prop.image: prop.image.delete()
        prop.delete() 
        
        messages.warning(request, "❌ Imagen rechazada y eliminada.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al rechazar imagen: {str(e)}")
        return redirect('dashboard')
