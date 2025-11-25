import os
from django.shortcuts import render, redirect
from django.conf import settings
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM
from src.Shared.Domain import eclai_core
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.create_world import CreateWorldUseCase
from src.WorldManagement.Caos.Application.publish_world import PublishWorldUseCase
from src.WorldManagement.Caos.Application.generate_lore import GenerateWorldLoreUseCase
from src.WorldManagement.Caos.Application.generate_map import GenerateWorldMapUseCase
from src.FantasyWorld.AI_Generation.Infrastructure.llama_service import Llama3Service
from src.FantasyWorld.AI_Generation.Infrastructure.sd_service import StableDiffusionService

def ver_mundo(request, jid):
    try:
        world_orm = CaosWorldORM.objects.get(id=jid)
    except CaosWorldORM.DoesNotExist:
        return render(request, '404.html', {"jid": jid})

    code_entity = eclai_core.encode_eclai126(jid)
    nid_lore = eclai_core.generar_nid(jid, "L", 1)
    code_lore = eclai_core.encode_eclai126(nid_lore)
    
    # BUSCAR LAS 4 IMÁGENES
    imagenes = []
    img_folder = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img')
    
    # Buscamos map_01_v1.png ... map_01_v4.png
    for i in range(1, 5):
        fname = f'map_{jid}_v{i}.png'
        if os.path.exists(os.path.join(img_folder, fname)):
            imagenes.append(fname)
    
    # Si no hay versiones, buscamos la antigua (map_01.png) por compatibilidad
    if not imagenes:
        fname_old = f'map_{jid}.png'
        if os.path.exists(os.path.join(img_folder, fname_old)):
            imagenes.append(fname_old)

    context = {
        'name': world_orm.name,
        'description': world_orm.description,
        'jid': jid,
        'code_entity': code_entity,
        'nid_lore': nid_lore,
        'code_lore': code_lore,
        'status': world_orm.status,
        'imagenes': imagenes # Pasamos la lista
    }
    return render(request, 'ficha_mundo.html', context)

def home(request):
    if request.method == 'POST':
        nombre_mundo = request.POST.get('world_name', 'Nuevo Mundo')
        desc_base = request.POST.get('world_desc', 'Mundo generado desde web')
        
        # Instancias
        repo = DjangoCaosRepository()
        crear = CreateWorldUseCase(repo)
        publicar = PublishWorldUseCase(repo)
        
        try: ia_texto = Llama3Service()
        except: ia_texto = None
        try: ia_arte = StableDiffusionService()
        except: ia_arte = None
        
        # Borrar ID 01 anterior para demo
        try: CaosWorldORM.objects.get(id="01").delete()
        except: pass

        jid = crear.execute(nombre_mundo, desc_base)
        
        if ia_texto: GenerateWorldLoreUseCase(repo, ia_texto).execute(jid)
        if ia_arte: GenerateWorldMapUseCase(repo, ia_arte).execute(jid) # Generará 4 fotos
            
        publicar.execute(jid)
        return redirect('ver_mundo', jid=jid)

    mundos_orm = CaosWorldORM.objects.all().order_by('-created_at')
    lista_mundos = []
    for m in mundos_orm:
        # Para la portada usamos solo la v1 o la normal
        img_name = f'map_{m.id}_v1.png'
        img_full = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', img_name)
        if not os.path.exists(img_full):
            img_name = f'map_{m.id}.png' # Fallback
            img_full = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', img_name)

        lista_mundos.append({
            'id': m.id,
            'name': m.name,
            'status': m.status,
            'code': eclai_core.encode_eclai126(m.id),
            'has_img': os.path.exists(img_full),
            'img_file': img_name
        })

    return render(request, 'index.html', {'mundos': lista_mundos})