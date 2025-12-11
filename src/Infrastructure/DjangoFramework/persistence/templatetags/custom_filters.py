from django import template
register = template.Library()
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) if dictionary else None

@register.filter
def clean_metadata_key(value):
    if not value: return ""
    return str(value).replace('_', ' ').title()