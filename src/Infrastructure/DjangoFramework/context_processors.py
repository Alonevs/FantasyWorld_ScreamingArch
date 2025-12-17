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
    
    # 1. Superuser
    if request.user.is_superuser:
        context.update({
            'role_badge_class': 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.2)]',
            'role_label': 'SUPERADMIN',
            'role_icon': '👑', 
            'show_bar': True
        })
        return context

    # Check for profile
    try:
        profile = request.user.profile
        rank = profile.rank
        
        # 2. Admin (Green)
        if rank == 'ADMIN':
            context.update({
                'role_badge_class': 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]',
                'role_label': 'ADMIN',
                'role_icon': '🛡️',
                'show_bar': True
            })
        # 3. Subadmin (Blue)
        elif rank == 'SUBADMIN':
            context.update({
                'role_badge_class': 'bg-blue-500/10 text-blue-400 border border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.2)]',
                'role_label': 'SUBADMIN',
                'role_icon': '⚔️',
                'show_bar': True
            })
        # 4. Standard User
        else:
            # Maybe show bar for standard users too if they have 'My Work' access? 
            # For now, hiding it as per previous logic, but setting defaults just in case
            context['show_bar'] = False
            
    except Exception:
        # User has no profile or other error
        context['show_bar'] = False
        
    return context
