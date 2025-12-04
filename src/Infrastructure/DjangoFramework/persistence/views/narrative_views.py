from django.shortcuts import render, redirect
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM
from src.WorldManagement.Caos.Infrastructure.django_repository import DjangoCaosRepository
from src.WorldManagement.Caos.Application.update_narrative import UpdateNarrativeUseCase
from src.WorldManagement.Caos.Application.delete_narrative import DeleteNarrativeUseCase
from src.WorldManagement.Caos.Application.create_narrative import CreateNarrativeUseCase

def resolve_jid(identifier):
    try:
        return CaosWorldORM.objects.get(public_id=identifier)
    except CaosWorldORM.DoesNotExist:
        pass 
    try:
        return CaosWorldORM.objects.get(id=identifier)
    except CaosWorldORM.DoesNotExist:
        return None

def ver_narrativa_mundo(request, jid):
    try: 
        w = resolve_jid(jid)
        if not w: return redirect('home')
        
        docs = w.narrativas.exclude(tipo='CAPITULO')
        context = {'world': w, 'lores': docs.filter(tipo='LORE'), 'historias': docs.filter(tipo='HISTORIA'), 'eventos': docs.filter(tipo='EVENTO'), 'leyendas': docs.filter(tipo='LEYENDA'), 'reglas': docs.filter(tipo='REGLA'), 'bestiario': docs.filter(tipo='BESTIARIO')}
        return render(request, 'indice_narrativa.html', context)
    except: return redirect('home')

def leer_narrativa(request, nid):
    try:
        if len(nid) <= 12 and ('-' in nid or '_' in nid):
             narr = CaosNarrativeORM.objects.get(public_id=nid)
        else:
             narr = CaosNarrativeORM.objects.get(nid=nid)
    except: return redirect('home')
    
    todas = CaosWorldORM.objects.all().order_by('id')
    hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
    return render(request, 'visor_narrativa.html', {'narr': narr, 'todas_entidades': todas, 'capitulos': hijos})

def editar_narrativa(request, nid):
    if request.method == 'POST':
        try:
            try: n_obj = CaosNarrativeORM.objects.get(public_id=nid)
            except: n_obj = CaosNarrativeORM.objects.get(nid=nid)
            
            UpdateNarrativeUseCase().execute(
                nid=n_obj.nid,
                titulo=request.POST.get('titulo'),
                contenido=request.POST.get('contenido'),
                narrador=request.POST.get('narrador'),
                tipo=request.POST.get('tipo'),
                menciones_ids=request.POST.getlist('menciones')
            )
            messages.success(request, "Narrativa guardada.")
            return redirect('leer_narrativa', nid=nid)
        except Exception as e: print(f"Error: {e}")
    return redirect('leer_narrativa', nid=nid)

def borrar_narrativa(request, nid):
    try:
        try: n = CaosNarrativeORM.objects.get(public_id=nid); real_nid = n.nid; w_pid = n.world.public_id
        except: n = CaosNarrativeORM.objects.get(nid=nid); real_nid = nid; w_pid = n.world.id
        
        DeleteNarrativeUseCase().execute(real_nid)
        return redirect('ver_narrativa_mundo', jid=w_pid)
    except: return redirect('home')

def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=real_jid, tipo_codigo=tipo_codigo, user=user)
        try: new_n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = new_n.public_id if new_n.public_id else new_nid
        except: redir_id = new_nid
        return redirect('leer_narrativa', nid=redir_id)
    except: return redirect('ver_mundo', public_id=jid)

def crear_sub_narrativa(request, parent_nid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        try: p = CaosNarrativeORM.objects.get(public_id=parent_nid); real_parent = p.nid
        except: real_parent = parent_nid
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=None, tipo_codigo=tipo_codigo, parent_nid=real_parent, user=user)
        try: new_n = CaosNarrativeORM.objects.get(nid=new_nid); redir_id = new_n.public_id if new_n.public_id else new_nid
        except: redir_id = new_nid
        return redirect('leer_narrativa', nid=redir_id)
    except: return redirect('leer_narrativa', nid=parent_nid)
