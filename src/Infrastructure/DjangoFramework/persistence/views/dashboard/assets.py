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

from src.Infrastructure.DjangoFramework.persistence.models import (
    CaosImageProposalORM, CaosWorldORM, CaosNarrativeORM
)
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
    if request.GET.get('next') == 'batch': return redirect('batch_revisar_imagenes')
    return redirect('dashboard')

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
    if request.GET.get('next') == 'batch': return redirect('batch_revisar_imagenes')
    return redirect('dashboard')

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
    if request.GET.get('next') == 'batch': return redirect('batch_revisar_imagenes')
    return redirect('dashboard')

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
    if request.GET.get('next') == 'batch': return redirect('batch_revisar_imagenes')
    return redirect('dashboard')

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
    deleted_worlds = CaosWorldORM.objects.filter(is_active=False)
    
    # Images in TRASHED status
    deleted_images = CaosImageProposalORM.objects.filter(status='TRASHED')
    
    # Narratives in DELETED/HISTORY? 
    # For now, let's assume Soft Delete on Narratives sets is_active=False like Worlds?
    # Or rely on Version status? User said "se conserva en el historial".
    # If using CaosNarrativeORM logic:
    deleted_narratives = CaosNarrativeORM.objects.filter(is_active=False)
    
    context = {
        'deleted_worlds': deleted_worlds,
        'deleted_narratives': deleted_narratives, 
        'deleted_images': deleted_images
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
