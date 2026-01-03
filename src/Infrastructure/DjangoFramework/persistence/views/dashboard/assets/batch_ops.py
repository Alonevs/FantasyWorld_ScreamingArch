from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from src.Infrastructure.DjangoFramework.persistence.models import CaosImageProposalORM

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
