from django.shortcuts import render, redirect
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM, CaosNarrativeORM, CaosNarrativeVersionORM
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
        if not w: 
            print(f"❌ Mundo no encontrado para JID: {jid}")
            messages.error(request, f"Mundo no encontrado: {jid}")
            return redirect('home')
        
        docs = w.narrativas.exclude(tipo='CAPITULO')
        context = {'world': w, 'lores': docs.filter(tipo='LORE'), 'historias': docs.filter(tipo='HISTORIA'), 'eventos': docs.filter(tipo='EVENTO'), 'leyendas': docs.filter(tipo='LEYENDA'), 'reglas': docs.filter(tipo='REGLA'), 'bestiario': docs.filter(tipo='BESTIARIO')}
        return render(request, 'indice_narrativa.html', context)
    except Exception as e: 
        print(f"❌ Error en ver_narrativa_mundo: {e}")
        messages.error(request, f"Error al cargar narrativas: {e}")
        return redirect('home')

def leer_narrativa(request, nid):
    try:
        # Intentar buscar por public_id primero si parece un NanoID (10-12 chars)
        if len(nid) <= 12 and ('-' in nid or '_' in nid):
             try:
                 narr = CaosNarrativeORM.objects.get(public_id=nid)
             except CaosNarrativeORM.DoesNotExist:
                 narr = CaosNarrativeORM.objects.get(nid=nid)
        else:
             narr = CaosNarrativeORM.objects.get(nid=nid)
    except Exception as e:
        print(f"❌ Error al leer narrativa '{nid}': {e}")
        messages.error(request, f"No se encontró la narrativa: {nid}")
        return redirect('home')
    
    todas = CaosWorldORM.objects.all().order_by('id')
    hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr.nid).exclude(nid=narr.nid).order_by('nid')
    return render(request, 'visor_narrativa.html', {'narr': narr, 'todas_entidades': todas, 'capitulos': hijos})

from src.WorldManagement.Caos.Application.propose_narrative_change import ProposeNarrativeChangeUseCase

def editar_narrativa(request, nid):
    if request.method == 'POST':
        try:
            try: n_obj = CaosNarrativeORM.objects.get(public_id=nid)
            except: n_obj = CaosNarrativeORM.objects.get(nid=nid)
            
            # Si hay una razón de cambio, es una PROPUESTA
            change_reason = request.POST.get('change_reason')
            
            if change_reason:
                ProposeNarrativeChangeUseCase().execute(
                    narrative_id=n_obj.nid,
                    new_title=request.POST.get('titulo'),
                    new_content=request.POST.get('contenido'),
                    reason=change_reason,
                    user=request.user if request.user.is_authenticated else None
                )
                messages.success(request, "📝 Propuesta de cambio enviada para revisión.")
                return redirect('dashboard')
            else:
                # Edición directa (Legacy / Admin bypass si se quisiera)
                # Por ahora mantenemos esto si no se envía reason, pero el UI forzará reason
                UpdateNarrativeUseCase().execute(
                    nid=n_obj.nid,
                    titulo=request.POST.get('titulo'),
                    contenido=request.POST.get('contenido'),
                    narrador=request.POST.get('narrador'),
                    tipo=request.POST.get('tipo'),
                    menciones_ids=request.POST.getlist('menciones')
                )
                messages.success(request, "Narrativa guardada directamente.")
                return redirect('leer_narrativa', nid=nid)

        except Exception as e: 
            print(f"Error: {e}")
            messages.error(request, f"Error al editar: {e}")
    return redirect('leer_narrativa', nid=nid)

def borrar_narrativa(request, nid):
    try:
        try: n = CaosNarrativeORM.objects.get(public_id=nid); real_nid = n.nid; w_pid = n.world.public_id
        except: n = CaosNarrativeORM.objects.get(nid=nid); real_nid = nid; w_pid = n.world.id
        
        DeleteNarrativeUseCase().execute(real_nid)
        return redirect('ver_narrativa_mundo', jid=w_pid)
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, f"Error al borrar: {e}")
        return redirect('home')

def revisar_narrativa_version(request, version_id):
    try:
        v = CaosNarrativeVersionORM.objects.get(id=version_id)
        
        # Create a proxy object to mimic CaosNarrativeORM but with proposed data
        class NarrativeProxy:
            def __init__(self, version):
                self.nid = version.narrative.nid
                self.titulo = version.proposed_title
                self.contenido = version.proposed_content
                self.world = version.narrative.world
                self.created_by = version.author
                self.tipo = version.narrative.tipo
                self.narrador = version.narrative.narrador
                self.is_proposal = True
                self.version_id = version.id
        
        narr_proxy = NarrativeProxy(v)
        
        # Reuse the same template
        todas = CaosWorldORM.objects.all().order_by('id')
        hijos = CaosNarrativeORM.objects.filter(nid__startswith=narr_proxy.nid).exclude(nid=narr_proxy.nid).order_by('nid')
        
        messages.info(request, f"👁️ Visualizando PROPUESTA v{v.version_number}. Esto no es la versión live.")
        return render(request, 'visor_narrativa.html', {'narr': narr_proxy, 'todas_entidades': todas, 'capitulos': hijos, 'is_proposal': True})
        
    except Exception as e:
        print(f"Error reviewing narrative version: {e}")
        messages.error(request, f"Error al revisar versión: {e}")
        return redirect('dashboard')

def crear_nueva_narrativa(request, jid, tipo_codigo):
    try:
        repo = DjangoCaosRepository()
        w = resolve_jid(jid)
        real_jid = w.id if w else jid
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=real_jid, tipo_codigo=tipo_codigo, user=user)
        
        messages.success(request, "✨ Nueva narrativa creada. Se ha generado una propuesta v1 en el Dashboard.")
        return redirect('dashboard')
    except Exception as e: 
        print(f"Error creating narrative: {e}")
        return redirect('ver_mundo', public_id=jid)

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
