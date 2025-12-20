def admin_bar_context(request):
    """
    Adds admin bar context variables based on user role.
    Redesigned for Dark Theme with Gold/Green/Blue accents.
    """
    if not request.user.is_authenticated:
        return {}
    
    context = {}
    
    # Common Bar Style
    context['bar_style'] = 'bg-[#0a0a0a] border-b border-white/5 shadow-lg'
    
    # --- DASHBOARD / BUZONES ACCESS ---
    is_global_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.rank == 'SUPERADMIN')
    
    if is_global_admin:
        from django.contrib.auth.models import User
        from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM
        
        # Get all active users
        authors = list(User.objects.filter(is_active=True).exclude(username__in=['Xico', 'Alone', 'System']).order_by('username'))
        
        # Add counts
        for author in authors:
            w_p = CaosVersionORM.objects.filter(author_id=author.id, status='PENDING').count()
            n_p = CaosNarrativeVersionORM.objects.filter(author_id=author.id, status='PENDING').count()
            i_p = CaosImageProposalORM.objects.filter(author_id=author.id, status='PENDING').count()
            author.pending_count = w_p + n_p + i_p
        
        context['global_buzones'] = authors

    # --- ROLE BADGES & BAR VISIBILITY ---
    # 1. Superuser flag
    if request.user.is_superuser:
        context.update({
            'role_badge_class': 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.2)]',
            'role_label': 'SUPERADMIN',
            'role_icon': '👑', 
            'show_bar': True
        })
        return context

    # 2. Check for Profile Rank
    try:
        profile = request.user.profile
        rank = profile.rank
        
        if rank == 'ADMIN':
            context.update({
                'role_badge_class': 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]',
                'role_label': 'ADMIN',
                'role_icon': '🛡️',
                'show_bar': True
            })
        elif rank == 'SUBADMIN':
            context.update({
                'role_badge_class': 'bg-blue-500/10 text-blue-400 border border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.2)]',
                'role_label': 'SUBADMIN',
                'role_icon': '⚔️',
                'show_bar': True
            })
        elif rank == 'SUPERADMIN': # Fallback for rank-based superadmin
             context.update({
                'role_badge_class': 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.2)]',
                'role_label': 'SUPERADMIN',
                'role_icon': '👑', 
                'show_bar': True
            })
        else:
            context['show_bar'] = False
            
    except Exception:
        context['show_bar'] = False
        
    return context
