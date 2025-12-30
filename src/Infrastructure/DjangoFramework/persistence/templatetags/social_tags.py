from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def user_avatar_url(user, size=48):
    """
    Retorna la URL del avatar del usuario.
    Si no tiene avatar, genera uno con ui-avatars.com
    
    Uso: {% user_avatar_url user 64 %}
    """
    if hasattr(user, 'profile') and user.profile.avatar:
        return user.profile.avatar.url
    else:
        return f"https://ui-avatars.com/api/?name={user.username}&background=random&color=fff&size={size}&bold=true"


@register.inclusion_tag('components/_avatar.html')
def user_avatar(user, size=48, css_class=""):
    """
    Renderiza un avatar completo con imagen.
    
    Uso: {% user_avatar user size=64 css_class="custom-class" %}
    """
    if hasattr(user, 'profile') and user.profile.avatar:
        avatar_url = user.profile.avatar.url
    else:
        avatar_url = f"https://ui-avatars.com/api/?name={user.username}&background=random&color=fff&size={size}&bold=true"
    
    return {
        'avatar_url': avatar_url,
        'username': user.username,
        'size': size,
        'css_class': css_class
    }
