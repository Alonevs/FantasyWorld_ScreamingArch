
# --- USER MANAGEMENT (SUPERUSER ONLY) ---
from django.contrib.auth.models import Group, User
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "staff/user_management.html"
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        
        rich_users = []
        for u in context['users']:
            is_admin_role = admins_group in u.groups.all()
            role = 'Usuario'
            if u.is_superuser: role = 'Superadmin'
            elif is_admin_role: role = 'Admin'
            
            rich_users.append({
                'obj': u,
                'username': u.username,
                'email': u.email,
                'role': role,
                'is_admin_role': is_admin_role,
                'is_superuser': u.is_superuser
            })
        
        context['users'] = rich_users
        return context

@login_required
@user_passes_test(is_superuser)
def toggle_admin_role(request, user_id):
    try:
        target_u = User.objects.get(id=user_id)
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        
        if admins_group in target_u.groups.all():
            target_u.groups.remove(admins_group)
            messages.warning(request, f"⬇️ {target_u.username} ahora es Usuario estándar.")
        else:
            target_u.groups.add(admins_group)
            messages.success(request, f"⬆️ {target_u.username} es ahora ADMIN.")
            
    except Exception as e:
        messages.error(request, str(e))
        
    # Redirect to referer or default
    return redirect('user_management')

# --- PROPOSAL DASHBOARD ---
from django.views import View
from django.db.models import Q
from django.contrib.auth import get_user_model
from src.Infrastructure.DjangoFramework.persistence.models import ContributionProposal, CaosImageProposalORM

class ProposalDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        User = get_user_model()
        status = request.GET.get('status', 'PENDING')
        
        # --- 1. TEXT PROPOSALS ---
        if request.user.is_superuser:
            text_props = ContributionProposal.objects.all().select_related('proposer', 'target_entity')
        else:
            text_props = ContributionProposal.objects.filter(
                Q(target_entity__author=request.user) | Q(proposer=request.user)
            ).select_related('proposer', 'target_entity')

        # --- 2. IMAGE PROPOSALS ---
        if request.user.is_superuser:
            img_props = CaosImageProposalORM.objects.all().select_related('author', 'world')
        else:
            img_props = CaosImageProposalORM.objects.filter(
                Q(world__author=request.user) | Q(author=request.user)
            ).select_related('author', 'world')

        # --- 3. FILTERING ---
        # Filter by Proposer
        proposer_id = request.GET.get('proposer_id')
        if proposer_id:
            text_props = text_props.filter(proposer__id=proposer_id)
            img_props = img_props.filter(author__id=proposer_id)

        # Filter by Target Owner (Mailbox)
        target_author_id = request.GET.get('target_author_id')
        if target_author_id:
            text_props = text_props.filter(target_entity__author__id=target_author_id)
            img_props = img_props.filter(world__author__id=target_author_id)

        # Filter by Status
        if status != 'ALL':
            text_props = text_props.filter(status=status)
            img_props = img_props.filter(status=status)

        # --- 4. NORMALIZE & MERGE ---
        combined = []
        
        for p in text_props:
            combined.append(p)
            
        for p in img_props:
            # Normalize to look like ContributionProposal for template
            p.is_image_proposal = True
            p.contribution_type = 'IMAGE_ADD' if p.action == 'ADD' else 'IMAGE_DELETE'
            p.target_entity = p.world
            p.proposer = p.author
            p.proposed_payload = {
                'title': p.title,
                'filename': p.target_filename,
                'image_url': p.image.url if p.image else None
            }
            combined.append(p)

        # Sort by Date Descending
        combined.sort(key=lambda x: x.created_at, reverse=True)

        context = {
            'proposals': combined,
            'users': User.objects.all(),
            'current_status': status,
            'selected_proposer': int(proposer_id) if proposer_id else '',
            'selected_target': int(target_author_id) if target_author_id else '',
            'is_superuser_view': request.user.is_superuser
        }
        return render(request, 'staff/proposal_dashboard.html', context)

# --- DETAIL & DIFF VIEW ---
from src.Shared.Services.DiffService import DiffService

class ProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        try:
            prop = ContributionProposal.objects.select_related('target_entity', 'proposer').get(id=id)
            
            context = {
                'prop': prop,
                'target_entity': prop.target_entity,
            }
            
            if prop.contribution_type == 'EDIT':
                context['diffs'] = DiffService.compare_entity(prop.target_entity, prop.proposed_payload)
            elif prop.contribution_type == 'CREATE':
                context['preview'] = DiffService.get_create_preview(prop.proposed_payload)
                
            return render(request, 'staff/proposal_detail.html', context)
            
        except ContributionProposal.DoesNotExist:
            messages.error(request, "Propuesta no encontrada.")
            return redirect('dashboard')

class ImageProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        prop = get_object_or_404(CaosImageProposalORM, id=id)
        
        is_involved = (request.user == prop.author or request.user == prop.world.author)
        if not (request.user.is_superuser or request.user.groups.filter(name='Admins').exists() or is_involved):
             return render(request, 'private_access.html', status=403)
             
        old_image_url = None
        if prop.action == 'DELETE' and prop.target_filename:
             old_image_url = f"{settings.STATIC_URL}persistence/img/{prop.target_filename}"
        
        context = {
            'proposal': prop,
            'old_image_url': old_image_url,
            'is_superuser': request.user.is_superuser,
            'is_owner': (request.user == prop.world.author)
        }
        return render(request, 'staff/image_proposal_detail.html', context)

@login_required
def aprobar_imagen(request, id):
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or request.user == prop.world.author or request.user.groups.filter(name='Admins').exists()):
        messages.error(request, "⛔ No tienes permiso.")
        return redirect('dashboard')
        
    _approve_image_logic(request, prop)
    return redirect('proposal_dashboard')

@login_required
def rechazar_imagen(request, id):
    prop = get_object_or_404(CaosImageProposalORM, id=id)
    if not (request.user.is_superuser or request.user == prop.world.author or request.user.groups.filter(name='Admins').exists()):
        messages.error(request, "⛔ No tienes permiso.")
        return redirect('dashboard')
        
    prop.status = 'REJECTED'
    if prop.image: prop.image.delete()
    prop.delete()
    messages.info(request, "❌ Propuesta de imagen rechazada.")
    return redirect('proposal_dashboard')

def _approve_image_logic(request, prop):
    try:
        repo = DjangoCaosRepository()
        if prop.action == 'ADD':
             user_name = prop.author.username if prop.author else "Anónimo"
             if prop.image:
                 repo.save_manual_file(prop.world.id, prop.image, username=user_name, title=prop.title)
             
             prop.status = 'APPROVED'
             prop.save()
             messages.success(request, f"✅ Imagen {prop.title} aprobada.")
             
        elif prop.action == 'DELETE':
             base = os.path.join(settings.BASE_DIR, 'persistence/static/persistence/img', prop.world.id)
             target = os.path.join(base, prop.target_filename)
             if os.path.exists(target): os.remove(target)
             
             w = prop.world
             if w.metadata and 'imagenes' in w.metadata:
                 w.metadata['imagenes'] = [
                     img for img in w.metadata['imagenes'] 
                     if img.get('filename') != prop.target_filename
                 ]
                 w.save()
                 
             prop.status = 'APPROVED'
             prop.save()
             messages.success(request, f"✅ Imagen borrada.")

    except Exception as e:
        messages.error(request, f"Error al procesar imagen: {e}")

@login_required
def aprobar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        if not (request.user.is_superuser or prop.target_entity.author == request.user):
            messages.error(request, "⛔ Sin permiso.")
            return redirect('dashboard')
            
        prop.status = 'APPROVED_WAITING'
        prop.reviewer = request.user
        prop.save()
        messages.success(request, "✅ Validado (Envíado a Staging).")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('dashboard')

@login_required
def rechazar_contribucion(request, id):
    try:
        prop = ContributionProposal.objects.get(id=id)
        if not (request.user.is_superuser or prop.target_entity.author == request.user):
            messages.error(request, "⛔ Sin permiso.")
            return redirect('dashboard')
            
        prop.status = 'REJECTED'
        prop.reviewer = request.user
        prop.save()
        messages.warning(request, "❌ Rechazado.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('dashboard')
