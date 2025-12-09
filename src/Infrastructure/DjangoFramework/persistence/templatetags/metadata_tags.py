from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.simple_tag
def render_metadata_form(schema, metadata_values=None):
    if not schema or not isinstance(schema, dict):
        return ""
    
    if metadata_values is None:
        metadata_values = {}
        
    html_parts = []
    
    for key, field_def in schema.items():
        field_type = field_def.get('type', 'text')
        label = field_def.get('label', key)
        default_val = field_def.get('default', '')
        
        # Obtener valor actual o default
        current_val = metadata_values.get(key, default_val)
        
        # Contenedor del campo
        html_parts.append(f'<div class="mb-4">')
        html_parts.append(f'<label class="block text-xs text-gray-400 uppercase font-bold mb-1">{label}</label>')
        
        if field_type == 'text':
            html_parts.append(
                f'<input type="text" name="meta_{key}" value="{current_val}" '
                f'class="w-full bg-black border border-gray-700 rounded p-2 text-white focus:border-accent focus:outline-none">'
            )
        
        elif field_type == 'number':
            html_parts.append(
                f'<input type="number" name="meta_{key}" value="{current_val}" '
                f'class="w-full bg-black border border-gray-700 rounded p-2 text-white focus:border-accent focus:outline-none">'
            )
            
        elif field_type == 'smart_link':
            # Para smart_links, mostramos un botón de acción
            action = field_def.get('action', '')
            target = field_def.get('target_type', '')
            html_parts.append(
                f'<div class="p-2 bg-gray-800 rounded border border-gray-700 flex items-center justify-between">'
                f'<span class="text-sm text-gray-300">🔗 Acción: {label}</span>'
                f'<button type="button" class="px-3 py-1 bg-indigo-900/50 hover:bg-indigo-700 text-indigo-200 text-xs rounded border border-indigo-700 transition">Ejecutar</button>'
                f'</div>'
            )
            
        elif field_type == 'static_link':
            url = field_def.get('url', '#')
            html_parts.append(
                f'<a href="{url}" target="_blank" class="block text-center w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-accent rounded transition border border-gray-600 text-sm">'
                f'{label} ↗'
                f'</a>'
            )
            
        elif field_type == 'entity_list':
            values = field_def.get('values', [])
            html_parts.append(f'<details class="group bg-gray-800 rounded border border-gray-700 overflow-hidden">')
            html_parts.append(f'<summary class="flex justify-between items-center p-2 cursor-pointer hover:bg-gray-700 transition list-none text-white text-sm font-bold">')
            html_parts.append(f'<span>{label}</span> <span class="group-open:rotate-180 transition text-xs">▼</span>')
            html_parts.append(f'</summary>')
            html_parts.append(f'<ul class="bg-gray-900 p-2 space-y-1">')
            for v in values:
                v_name = v.get('name', '???')
                v_url = v.get('url', '#')
                html_parts.append(f'<li><a href="{v_url}" class="block px-2 py-1 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded transition">🔗 {v_name}</a></li>')
            html_parts.append(f'</ul>')
            html_parts.append(f'</details>')
            
        html_parts.append('</div>')
        
    return mark_safe("".join(html_parts))

@register.simple_tag
def render_metadata_readonly(schema, metadata_values=None):
    if not schema or not isinstance(schema, dict):
        return ""
    
    if metadata_values is None:
        metadata_values = {}
        
    html_parts = []
    
    for key, field_def in schema.items():
        field_type = field_def.get('type', 'text')
        label = field_def.get('label', key)
        default_val = field_def.get('default', '')
        current_val = metadata_values.get(key, default_val)
        
        # Container
        html_parts.append(f'<div class="mb-3 pl-2 border-l-2 border-gray-800">')
        html_parts.append(f'<div class="text-[10px] text-gray-500 uppercase tracking-widest">{label}</div>')
        
        if field_type in ['text', 'number']:
            html_parts.append(f'<div class="text-sm text-gray-300 font-mono">{current_val}</div>')
            
        elif field_type == 'entity_list':
            values = field_def.get('values', [])
            if values:
                html_parts.append(f'<ul class="mt-1 space-y-1">')
                for v in values:
                    v_name = v.get('name', '???')
                    v_url = v.get('url', '#')
                    html_parts.append(f'<li><a href="{v_url}" class="text-xs text-accent hover:text-white underline decoration-gray-700 transition">{v_name}</a></li>')
                html_parts.append(f'</ul>')
            else:
                 html_parts.append(f'<div class="text-xs text-gray-600 italic">Sin elementos</div>')
        
        elif field_type == 'static_link':
             url = field_def.get('url', '#')
             html_parts.append(f'<a href="{url}" class="text-xs text-indigo-400 hover:text-indigo-300 underline">{label} ↗</a>')
             
        elif field_type == 'smart_link':
             # Smart links often imply action, but in read-only maybe just show status or label
             html_parts.append(f'<div class="text-xs text-gray-600 cursor-default" title="Acción disponible en Edición">⚡ {label}</div>')

        html_parts.append('</div>')
        
    return mark_safe("".join(html_parts))
