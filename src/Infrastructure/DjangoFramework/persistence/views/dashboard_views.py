from django.shortcuts import render, redirect
from django.contrib import messages
from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosEventLog
from src.WorldManagement.Caos.Application.approve_version import ApproveVersionUseCase
from src.WorldManagement.Caos.Application.reject_version import RejectVersionUseCase
from src.WorldManagement.Caos.Application.publish_to_live_version import PublishToLiveVersionUseCase
from src.WorldManagement.Caos.Application.restore_version import RestoreVersionUseCase

def dashboard(request):
    propuestas = CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at')
    aprobadas = CaosVersionORM.objects.filter(status='APPROVED').order_by('-created_at')
    rechazadas = CaosVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10]
    archivadas = CaosVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:20]
    
    context = {
        'propuestas': propuestas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
        'archivadas': archivadas
    }
    return render(request, 'dashboard.html', context)

def centro_control(request):
    pendientes = CaosVersionORM.objects.filter(status='PENDING').order_by('-created_at')
    aprobados = CaosVersionORM.objects.filter(status='APPROVED').order_by('-created_at')
    rechazados = CaosVersionORM.objects.filter(status='REJECTED').order_by('-created_at')[:10]
    archivados = CaosVersionORM.objects.filter(status='ARCHIVED').order_by('-created_at')[:10]
    logs = CaosEventLog.objects.all()[:20] # Last 20 events
    
    def map_v(v):
        return {
            'id': v.id,
            'version_num': v.version_number,
            'proposed_name': v.proposed_name,
            'author': v.author.username if v.author else 'Sistema',
            'reason': v.change_log,
            'date': v.created_at,
            'nivel_label': 'Mundo'
        }

    context = {
        'pendientes': [map_v(v) for v in pendientes],
        'aprobados': [map_v(v) for v in aprobados],
        'rechazados': [map_v(v) for v in rechazados],
        'archivados': [map_v(v) for v in archivados],
        'logs': logs
    }
    return render(request, 'control_panel.html', context)

def aprobar_propuesta(request, id):
    try:
        # 1. Aprobar (Internal Approval) - PENDING -> APPROVED
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
    try:
        ApproveVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"✅ Versión {v.version_number} aprobada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def rechazar_version(request, version_id):
    try:
        RejectVersionUseCase().execute(version_id)
        v = CaosVersionORM.objects.get(id=version_id)
        messages.warning(request, f"❌ Versión {v.version_number} rechazada.")
        return redirect('ver_mundo', public_id=v.world.public_id if v.world.public_id else v.world.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home')

def restaurar_version(request, version_id):
    try:
        # Restore (Archived -> Pending Proposal for Restoration)
        RestoreVersionUseCase().execute(version_id, request.user)
        
        v = CaosVersionORM.objects.get(id=version_id)
        messages.success(request, f"🔄 Versión {v.version_number} recuperada y movida a PENDIENTE. Apruébala para restaurarla en Live.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('dashboard')

def borrar_propuesta(request, version_id):
    try:
        # Hard Delete
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
            ids = request.POST.getlist('selected_ids')
            if not ids:
                messages.warning(request, "No has seleccionado ninguna propuesta.")
                return redirect('dashboard')
            
            count = CaosVersionORM.objects.filter(id__in=ids).delete()[0]
            messages.success(request, f"🗑️ Se han eliminado {count} propuestas/versiones definitivamente.")
        except Exception as e:
            messages.error(request, f"Error al borrar masivamente: {str(e)}")
    return redirect('dashboard')
