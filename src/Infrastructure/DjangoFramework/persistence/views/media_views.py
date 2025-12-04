import os
import json
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosEventLog
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

def resolve_jid(identifier):
    # Helper duplicated here or imported from world_views if circular import avoided.
    # To avoid circular imports, I'll duplicate this small helper or import from a common util if I had one.
    # Given the constraints, I will duplicate it to be safe and self-contained for now, or import from models if it was a static method.
    # Better: Import from world_views might cause circular import if world_views imports this.
    # world_views imports nothing from here. So I can import resolve_jid from world_views?
    # No, world_views is a view file.
    # I will duplicate it for safety as it is small.
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
    try:
        w = resolve_jid(jid); real_jid = w.id if w else jid
        data = json.loads(request.body)
        user = request.user.username if request.user.is_authenticated else "Anónimo"
        DjangoCaosRepository().save_image(real_jid, data.get('image'), title=data.get('title'), username=user)
        log_event(request.user, "UPLOAD_AI_PHOTO", real_jid, f"Title: {data.get('title')}")
        return JsonResponse({'status': 'ok', 'success': True})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

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

    if request.method == 'POST' and request.FILES.get('imagen_manual'):
        try:
            repo = DjangoCaosRepository()
            use_orig = request.POST.get('use_original_name') == 'true' or request.POST.get('use_original_name') == 'on'
            custom = request.POST.get('custom_name')
            title = request.POST.get('manual_title', 'Sin Título')
            
            final = title
            if use_orig: final = request.FILES['imagen_manual'].name.split('.')[0]
            elif custom: final = custom

            user = request.user.username if request.user.is_authenticated else "Anónimo"
            repo.save_manual_file(real_jid, request.FILES['imagen_manual'], username=user, title=final)
            log_event(request.user, "UPLOAD_MANUAL_PHOTO", real_jid, f"File: {final}")
            messages.success(request, "✅ Imagen subida.")
        except Exception as e: messages.error(request, f"Error: {e}")
    return redirect('ver_mundo', public_id=redirect_target)

def set_cover_image(request, jid, filename):
    try: w=resolve_jid(jid); w.metadata['cover_image']=filename; w.save(); return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')

def borrar_foto(request, jid, filename):
    try: 
        w=resolve_jid(jid); base=os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', w.id)
        if os.path.exists(os.path.join(base, filename)): os.remove(os.path.join(base, filename))
        return redirect('ver_mundo', public_id=w.public_id)
    except: return redirect('home')
# Función "placeholder" que faltaba
def generar_foto_extra(request, jid):
    # Por ahora solo redirige, igual que antes
    return redirect('ver_mundo', public_id=jid)