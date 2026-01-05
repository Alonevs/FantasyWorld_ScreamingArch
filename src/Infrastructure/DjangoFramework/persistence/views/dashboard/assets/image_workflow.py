from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from ..utils import log_event
from src.Infrastructure.DjangoFramework.persistence.models import CaosImageProposalORM, CaosNotification
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
import os

# --- IMAGE ACTIONS ---

@login_required
def aprobar_imagen(request, id):
    """
    Aprueba una propuesta de imagen, cambiando su estado a APPROVED.
    Solo el Autor del mundo (Administrator) o el Superusuario pueden ejecutar esta acción.
    """
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or (prop.world and prop.world.author == request.user)):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede aprobar esta imagen.")
        return redirect('dashboard')
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        prop.status = 'APPROVED'
        prop.reviewer = request.user
        prop.save()

        # Create Notification
        if prop.author:
            CaosNotification.objects.create(
                user=prop.author,
                title="🖼️ Imagen Aprobada",
                message=f"Tu propuesta de imagen para '{prop.world.name if prop.world else 'Global'}' ha sido aprobada.",
                url=f"/dashboard/?type=IMAGE"
            )

        messages.success(request, "Imagen Aprobada.")
        log_event(request.user, "APPROVE_IMAGE_PROPOSAL", id)
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def rechazar_imagen(request, id):
    """
    Rechaza una propuesta de imagen y registra el feedback del administrador.
    La imagen pasa a estado REJECTED y no será visible en el mundo.
    """
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

        # Create Notification
        if prop.author:
            feedback_msg = f" Motivo: {feedback}" if feedback else ""
            CaosNotification.objects.create(
                user=prop.author,
                title="❌ Imagen Rechazada",
                message=f"Tu propuesta de imagen para '{prop.world.name if prop.world else 'Global'}' ha sido rechazada.{feedback_msg}",
                url=f"/dashboard/?type=IMAGE"
            )

        messages.success(request, f"Imagen Rechazada. Feedback: {feedback[:30]}...")
        log_event(request.user, "REJECT_IMAGE", id, details=f"Feedback: {feedback}")
    except Exception as e: messages.error(request, str(e))
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def archivar_imagen(request, id):
    """
    Mueve una propuesta de imagen al archivo (Papelera Soft) o la mantiene si se rechaza un borrado.
    Si la acción era DELETE, actúa como un rechazo del borrado (Keep).
    Si era una propuesta normal, la cambia a estado ARCHIVED.
    """
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
    """
    Ejecuta la publicación física de una imagen en el sistema de archivos (Live).
    - Si es una ADD/EDIT: Guarda el archivo en la carpeta estática del mundo.
    - Si es una DELETE: Elimina físicamente el archivo del disco.
    Tras el éxito, la propuesta pasa a ARCHIVED con el usuario como reviewer.
    """
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or (prop.world and prop.world.author == request.user)):
        messages.error(request, "⛔ Solo el Autor (Administrador) de este mundo puede publicar esta imagen.")
        return redirect('dashboard')
    try:
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        repo = DjangoCaosRepository()

        if prop.action == 'DELETE':
            # SOFT DELETE: Move to .trash folder
            base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
            world_dir = str(prop.world.id)
            img_filename = prop.target_filename
            
            src_path = os.path.join(base_dir, world_dir, img_filename)
            trash_dir = os.path.join(base_dir, world_dir, '.trash')
            
            # Ensure trash dir exists
            if not os.path.exists(trash_dir):
                os.makedirs(trash_dir)
                
            trash_path = os.path.join(trash_dir, img_filename)
            
            if os.path.exists(src_path):
                import shutil
                shutil.move(src_path, trash_path)
                
                # Metadata Cleanup: If this WAS the cover image, clear it
                if prop.world.metadata and prop.world.metadata.get('cover_image') == prop.target_filename:
                    prop.world.metadata['cover_image'] = None
                    prop.world.save()
                    messages.info(request, "ℹ️ La portada del mundo ha sido reseteada porque la imagen fue borrada.")
                
                messages.success(request, f"🗑️ Imagen '{prop.target_filename}' movida a la Papelera.")
                log_event(request.user, "SOFT_DELETE_IMAGE", prop.world.id, details=f"Archivo movido a .trash: {prop.target_filename}")
            else:
                messages.warning(request, f"⚠️ El archivo '{prop.target_filename}' no existía en LIVE, pero la propuesta se ha archivado.")
        else:
            # NORMAL PUBLISH (ADD)
            user_name = prop.author.username if prop.author else "Anónimo"
            period_slug = prop.timeline_period.slug if prop.timeline_period else None
            repo.save_manual_file(str(prop.world.id), prop.image, username=user_name, title=prop.title, period_slug=period_slug)
            messages.success(request, "🚀 Imagen Publicada y Archivada.")
            log_event(request.user, "PUBLISH_IMAGE", id)
        
        prop.status = 'ARCHIVED'
        prop.reviewer = request.user
        prop.save()

        # Create Notification
        if prop.author:
            CaosNotification.objects.create(
                user=prop.author,
                title="🚀 ¡Imagen Publicada!",
                message=f"Tu propuesta de imagen para '{prop.world.name if prop.world else 'Global'}' ya está en vivo.",
                url=f"/mundo/{prop.world.public_id}/" if prop.world else "/mundo/caos"
            )
    except Exception as e:
        messages.error(request, f"❌ Error: {e}")
        print(f"Error publicar_imagen: {e}")
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url == 'batch': return redirect('batch_revisar_imagenes')
    return redirect(next_url) if next_url else redirect('dashboard')

@login_required
def restaurar_imagen(request, id):
    """
    Restaura una imagen desde el estado ARCHIVED/REJECTED a PENDING.
    Permite que la propuesta vuelva al flujo de revisión del Dashboard.
    """
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
    """
    Mueve una imagen al estado TRASHED (Papelera de reciclaje).
    Es el paso previo antes de la eliminación física definitiva de la base de datos.
    """
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
        
        # LOGIC FOR RESTORING A SOFT-DELETED IMAGE
        if prop.action == 'DELETE' and prop.status == 'ARCHIVED':
            # It was a successful delete, so file is in .trash
            base_dir = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
            world_dir = str(prop.world.id)
            img_filename = prop.target_filename
            
            trash_path = os.path.join(base_dir, world_dir, '.trash', img_filename)
            live_path = os.path.join(base_dir, world_dir, img_filename)
            
            if os.path.exists(trash_path):
                import shutil
                # Create live dir if somehow missing
                os.makedirs(os.path.dirname(live_path), exist_ok=True)
                shutil.move(trash_path, live_path)
                
                # We mark the DELETION proposal as REJECTED (meaning "Deletion Reversed")
                prop.status = 'REJECTED' 
                prop.admin_feedback = "Restaurado desde Papelera (Deshacer Borrado)"
                prop.save()
                
                messages.success(request, f"♻️ Imagen '{img_filename}' restaurada correctamente al mundo.")
                log_event(request.user, "UNDELETE_IMAGE", prop.world.id, details=f"Archivo recuperado de .trash: {img_filename}")
                return redirect('ver_papelera')
            else:
                messages.warning(request, "⚠️ No se encontró el archivo en la papelera (.trash). No se puede restaurar.")
                return redirect('ver_papelera')

        # STANDARD RESTORE (For Drafts/Rejected additions)
        prop.status = 'PENDING'
        prop.save()
        messages.success(request, "Propuesta enviada de nuevo a revisión.")
    except Exception as e: messages.error(request, str(e))
    return redirect('ver_papelera')

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
