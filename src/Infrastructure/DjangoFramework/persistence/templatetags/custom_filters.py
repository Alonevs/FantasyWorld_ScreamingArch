from typing import Any, Dict, Optional
from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def get_item(dictionary: Optional[Dict[str, Any]], key: str) -> Optional[Any]:
    return dictionary.get(key) if dictionary else None

@register.filter
def clean_metadata_key(value: Optional[str]) -> str:
    if not value: return ""
    return str(value).replace('_', ' ').title()

@register.filter
def user_avatar(user_or_username: Optional[User], jid: Optional[str] = None) -> str:
    from src.Infrastructure.DjangoFramework.persistence.utils import get_user_avatar
    return get_user_avatar(user_or_username, jid=jid)