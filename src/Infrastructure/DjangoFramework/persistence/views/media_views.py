import os
import json
import base64
import io
from PIL import Image
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosEventLog, CaosImageProposalORM, CaosVersionORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

def resolve_jid(identifier):
    try:
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        pass 
    try:
        return CaosWorldORM.objects.get(id=identifier)
    except CaosWorldORM.DoesNotExist:
        return None

def log_event(user, action, target_id, details=""):
    try:
        u = user if user.is_authenticated else None
        CaosEventLog.objects.create(user=u, action=action, target_id=target_id, details=details)
    except Exception as e: print(f"Log Error: {e}")

@csrf_exempt
def api_preview_foto(request, jid):
    if request.method != 'GET': return JsonResponse({'success': False})
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        b64 = GenerateWorldMapUseCase(DjangoCaosRepository(), StableDiffusionService()).generate_preview(real_jid)
        return JsonResponse({'status': 'ok', 'success': True, 'image': b64})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_save_foto(request, jid):
    print(f"DEBUG: api_save_foto called for jid={jid}")
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        print(f"DEBUG: Resolved world: {w}")
        
        data = json.loads(request.body)
        print("DEBUG: Request body loaded")
        
        user = request.user if request.user.is_authenticated else None
        print(f"DEBUG: User: {user}")
        
        # Robust base64 decoding
        img_str = data.get('image')
        if not img_str:
            print("DEBUG: No image data found")
            return JsonResponse({'status': 'error', 'message': 'No image data'})
            
        if ';base64,' in img_str:
            format, imgstr = img_str.split(';base64,') 
        else:
            imgstr = img_str
        
        print(f"DEBUG: Image string length: {len(imgstr)}")

        # Convert to WebP
        print("DEBUG: Decoding base64...")
        image = Image.open(io.BytesIO(base64.b64decode(imgstr)))
        print(f"DEBUG: Image opened: {image.format} {image.size}")
        
        output = io.BytesIO()
        image.save(output, format='WEBP')
        print("DEBUG: Image saved to WebP buffer")
        
        file_name = f"{data.get('title')}.webp"
        image_data = ContentFile(output.getvalue(), name=file_name)
        print(f"DEBUG: ContentFile created: {file_name}")

        # Create Proposal
        print("DEBUG: Creating CaosImageProposalORM...")
        CaosImageProposalORM.objects.create(
            world=w,
            image=image_data,
            title=data.get('title'),
            author=user,
            status='PENDING',
            action='ADD'
        )
        print("DEBUG: CaosImageProposalORM created")
        
        log_event(request.user, "PROPOSE_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        print("DEBUG: Event logged")
        
        return JsonResponse({'status': 'ok', 'success': True, 'message': 'Imagen enviada a revisión (WebP).'})
    except Exception as e:
        print(f"DEBUG: Exception in api_save_foto: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def api_update_image_metadata(request, jid):
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        repo = DjangoCaosRepository()
        if hasattr(repo, 'update_image_metadata'):
            repo.update_image_metadata(real_jid, data.get('filename'), data.get('title'))
            return JsonResponse({'status': 'ok', 'success': True})
        return JsonResponse({'status': 'error', 'message': 'Repo method missing'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def subir_imagen_manual(request, jid):
    w = resolve_jid(jid)
    real_jid = w.id if w else jid
    redirect_target = jid 
    if w and w.public_id: redirect_target = w.public_id

    if request.method == 'POST' and request.FILES.getlist('imagen_manual'):
        try:
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom_base = request.POST.get('custom_name')
            title_base = request.POST.get('manual_title', 'Sin Título')
            
            files = request.FILES.getlist('imagen_manual')[:5] # Max 5
            
            for i, f in enumerate(files):
                final = title_base
                if len(files) > 1: final = f"{title_base} ({i+1})"
                
                if use_orig: final = f.name.split('.')[0]
                elif custom_base: 
                    final = custom_base
                    if len(files) > 1: final = f"{custom_base}_{i+1}"

                # --- SECURITY CHECK ---
                from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
                try: check_ownership(request.user, w)
                except: 
                    messages.error(request, "⛔ Solo el dueño puede subir imágenes.")
                    return redirect('ver_mundo', public_id=redirect_target)
                # ----------------------

                # DIRECT SAVE
                repo = DjangoCaosRepository()
                name_user = request.user.username
                try:
                    repo.save_manual_file(w.id, f, username=name_user, title=final)
                    messages.success(request, f"✨ Imagen '{final}' guardada directamente.")
                    log_event(request.user, "UPLOAD_PHOTO", real_jid, f"Direct Upload: {final}")
                except Exception as e:
                     messages.error(request, f"Error directo: {e}")
            
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

def set_cover_image(request, jid, filename):
    try:
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
        
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try: check_ownership(request.user, w)
        except: 
            messages.error(request, "⛔ Solo el dueño puede cambiar la portada.")
            return redirect('ver_mundo', public_id=jid)
        # ----------------------
        
        # Calculate next version
        next_v = CaosVersionORM.objects.filter(world=w).count() + 1
        
        CaosVersionORM.objects.create(
            world=w,
            proposed_name=w.name,
            proposed_description=w.description,
            version_number=next_v,
            status='PENDING',
            change_log=f"Propuesta de Portada: {filename}",
            cambios={'action': 'SET_COVER', 'cover_image': filename},
            author=request.user if request.user.is_authenticated else None
        )
        
        log_event(request.user, "PROPOSE_COVER", real_jid, f"Proposed cover: {filename}")
        messages.success(request, "📸 Propuesta de portada creada. Revisa el Dashboard.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error proponiendo portada: {e}")
        return redirect('ver_mundo', public_id=jid)

def borrar_foto(request, jid, filename):
    try: 
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
        
        # --- SECURITY CHECK ---
        from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership
        try: check_ownership(request.user, w)
        except: 
            messages.error(request, "⛔ No tienes permiso para borrar esta imagen.")
            return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
        # ----------------------
        
        # Create Deletion Proposal
        CaosImageProposalORM.objects.create(
            world=w,
            title=f"Borrar: {filename}",
            target_filename=filename,
            action='DELETE',
            status='PENDING',
            author=request.user if request.user.is_authenticated else None
        )
        
        messages.info(request, "🗑️ Borrado pendiente de aprobación.")
        return redirect('ver_mundo', public_id=w.public_id if w.public_id else w.id)
    except Exception as e:
        print(f"Error borrar_foto: {e}")
        return redirect('home')

def generar_foto_extra(request, jid):
    return redirect('ver_mundo', public_id=jid)