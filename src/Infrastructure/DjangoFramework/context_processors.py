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
        
    # --- MESSAGING NOTIFICATIONS ---
    try:
        from src.Infrastructure.DjangoFramework.persistence.models import Message
        unread_count = Message.objects.filter(recipient=request.user, read_at__isnull=True).count()
        context['unread_messages_count'] = unread_count
    except Exception:
        context['unread_messages_count'] = 0
            
    return context

def notifications_context(request):
    """
    Inyecta notificaciones no leídas en el contexto global.
    """
    if not request.user.is_authenticated:
        return {}
    
    from src.Infrastructure.DjangoFramework.persistence.models import CaosNotification
    
    # Solo las 5 más recientes no leídas
    unread = CaosNotification.objects.filter(user=request.user, read_at__isnull=True).order_by('-created_at')
    
    return {
        'unread_notifications': unread[:5],
        'unread_notifications': unread[:5],
        'unread_notifications_count': unread.count(),
        # Add Pending Proposals Count for Persistent Badge
        'pending_proposals_count': get_pending_proposals_count(request.user)
    }

def get_pending_proposals_count(user):
    """Calculates total pending items for the user's dashboard."""
    from django.db.models import Q
    from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNarrativeVersionORM, CaosImageProposalORM, TimelinePeriodVersion
    
    if not user.is_authenticated: return 0
    
    # Logic similar to Workflow.py
    # 1. World Versions
    w_filter = Q(status='PENDING') & (Q(world__author=user) | Q(author=user))
    w_count = CaosVersionORM.objects.filter(w_filter).count()
    
    # 2. Narrative Versions
    n_filter = Q(status='PENDING') & (Q(narrative__world__author=user) | Q(author=user))
    n_count = CaosNarrativeVersionORM.objects.filter(n_filter).count()
    
    # 3. Image Proposals
    i_filter = Q(status='PENDING') & (Q(world__author=user) | Q(author=user))
    i_count = CaosImageProposalORM.objects.filter(i_filter).count()
    
    # 4. Period Versions
    p_filter = Q(status='PENDING') & (Q(period__world__author=user) | Q(author=user))
    p_count = TimelinePeriodVersion.objects.filter(p_filter).count()
    
    return w_count + n_count + i_count + p_count
