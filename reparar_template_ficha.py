import os
from pathlib import Path

def reparar_template_ficha_error():
    print("🚑 REPARANDO ERROR DE SINTAXIS EN FICHA_MUNDO.HTML...")

    base_templates = Path("src/Infrastructure/DjangoFramework/persistence/templates")
    path_ficha = base_templates / "ficha_mundo.html"

    # CÓDIGO HTML CORREGIDO Y LIMPIO
    html_content = """
{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>ECLAI v3.0 | {{ name }}</title>
    <style>
        body { background-color: #0a0a12; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding: 20px 40px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 15px; background: #0e0e16; padding: 15px 20px; border-radius: 10px; }
        .logo { font-size: 1.5em; font-weight: bold; color: #fff; letter-spacing: 2px; }
        .nav-group { display: flex; gap: 10px; }
        .nav-btn { background: #333; color: #fff; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9em; border: 1px solid #444; cursor: pointer; }
        .nav-btn:hover { background: #555; }
        .nav-btn.special { background: #d633ff; border-color: #d633ff; }
        .nav-btn.special:hover { background: #a569bd; }

        .card { background: #161625; border: 1px solid #2a2a40; border-radius: 15px; max-width: 900px; margin: 0 auto; overflow: hidden; }
        .card-header { background: linear-gradient(90deg, #2b1a45 0%, #1a1a2e 100%); padding: 20px; border-bottom: 2px solid #4a3b69; display: flex; justify-content: space-between; align-items: center; }
        .content { padding: 30px; }
        
        .actions { display: flex; gap: 10px; }
        .btn { padding: 5px 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 0.8em; text-decoration: none; color:#fff; }
        .btn-edit { background: #3498db; }
        .btn-del { background: #e74c3c; }
        
        .gallery { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 15px; margin-bottom: 20px; }
        .gallery img { width: 150px; height: 200px; object-fit: cover; border-radius: 8px; border: 2px solid #333; }
        
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; background: #1f1f33; padding: 15px; border-radius: 10px; }
        .stat-box { display: flex; flex-direction: column; }
        .label { font-size: 0.75em; color: #666; text-transform: uppercase; }
        .value { font-size: 1.1em; font-family: 'Courier New', monospace; color: #00ffcc; font-weight: bold; }
        
        .children-section { margin-top: 40px; border-top: 1px solid #333; padding-top: 20px; }
        .child-card { display: flex; align-items: center; background: #0e0e16; margin-bottom: 10px; padding: 10px; border-radius: 8px; text-decoration: none; color: #fff; border: 1px solid #333; }
        .child-card:hover { border-color: #d633ff; transform: translateX(5px); transition:0.2s; }
        
        .child-form { background: #1f1f33; padding: 15px; border-radius: 8px; margin-top: 20px; display: flex; gap: 10px; }
        .child-form input { background: #0a0a12; border: 1px solid #444; color: #fff; padding: 8px; border-radius: 4px; flex-grow: 1; }
        .child-form button { background: #d633ff; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
        
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; justify-content: center; align-items: center; }
        .modal:target { display: flex; }
        .modal-content { background: #161625; padding: 30px; border-radius: 10px; width: 500px; border: 1px solid #d633ff; }
        .edit-form input, .edit-form textarea { width: 100%; background: #0a0a12; border: 1px solid #444; color: #fff; padding: 10px; margin-top: 5px; }
    </style>
</head>
<body>

    <div class="top-bar">
        <div class="logo">ECLAI v3.0 // SYSTEM</div>
        <div class="nav-group">
            <button class="nav-btn" onclick="history.back()">⬅️ Atrás</button>
            <a href="{% url 'home' %}" class="nav-btn">🏠 Inicio</a>
            <a href="{% url 'centro_control' %}" class="nav-btn special">🎛️ Gestión</a>
        </div>
    </div>

    {% if is_preview %}
    <div style="background:#f39c12; color:#fff; padding:15px; text-align:center; margin-bottom:20px; border-radius:8px; border:2px solid #e67e22; max-width:900px; margin-left:auto; margin-right:auto;">
        <h2 style="margin:0; font-size:1.2em;">⚠️ MODO INSPECCIÓN: VERSIÓN CANDIDATA</h2>
        <p style="margin:5px 0;">Estás viendo una <strong>simulación</strong> de los cambios propuestos por <u>{{ author }}</u>.</p>
        <div style="background:rgba(0,0,0,0.2); display:inline-block; padding:5px 10px; border-radius:4px; margin-bottom:10px;">
            📝 Razón: "<em>{{ change_log }}</em>"
        </div>
        <div style="margin-top:10px; display:flex; justify-content:center; gap:20px;">
            <a href="{% url 'aprobar_version' version_id %}" class="btn" style="background:#27ae60; padding:10px 30px; font-size:1.1em;">✅ APROBAR CAMBIOS</a>
            <a href="{% url 'rechazar_version' version_id %}" class="btn" style="background:#c0392b; padding:10px 30px; font-size:1.1em;">❌ RECHAZAR</a>
            <a href="{% url 'centro_control' %}" class="btn" style="background:#7f8c8d; padding:10px 30px;">Cancelar</a>
        </div>
    </div>
    {% endif %}

    <div class="card">
        <div class="card-header">
            <div>
                <div style="color:#888; font-size:0.9em; margin-bottom:5px;">
                    {% for b in breadcrumbs %} <span>/</span> <a href="{% url 'ver_mundo' b.id %}" style="color:#d633ff; text-decoration:none;">{{ b.id }}</a> {% endfor %}
                </div>
                <h1 style="margin:0; font-size:2em;">{{ name }}</h1>
                <div style="font-size:0.8em; color:#a0a0ff;">STATUS: {{ status }}</div>
            </div>
            
            {% if not is_preview %}
            <div class="actions">
                <a href="#editModal" class="btn btn-edit">✏️ Editar</a>
                <a href="{% url 'borrar_mundo' jid %}" class="btn btn-del" onclick="return confirm('¿Seguro?')">🗑️ Borrar</a>
            </div>
            {% endif %}
        </div>

        <div class="content">
            {% if propuestas %}
            <div style="background:#2c2c44; border:1px solid #f1c40f; padding:15px; border-radius:8px; margin-bottom:20px;">
                <div style="color:#f1c40f; font-weight:bold; margin-bottom:10px;">⚠️ CAMBIOS PENDIENTES DE APROBACIÓN</div>
                {% for p in propuestas %}
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #444; padding-bottom:5px; margin-bottom:5px;">
                    <div><strong>v{{ p.version_number }}</strong>: {{ p.proposed_name }}</div>
                    <div><a href="{% url 'revisar_version' p.id %}" style="color:#3498db; text-decoration:none; margin-right:10px;">👁️ Revisar</a></div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div class="label">Galería</div>
                {% if not is_preview %}
                <a href="{% url 'generar_foto_extra' jid %}" class="btn" style="background:#9b59b6;">🎨 + Foto</a>
                {% endif %}
            </div>
            <div class="gallery">
                {% for img in imagenes %} <img src="{% static 'persistence/img/'|add:img %}"> {% empty %} <div style="color:#555;">Sin fotos.</div> {% endfor %}
            </div>

            <div class="stats-grid">
                <div class="stat-box"><span class="label">J-ID</span><span class="value">{{ jid }}</span></div>
                <div class="stat-box"><span class="label">CODE</span><span class="value" style="color:#d633ff">{{ code_entity }}</span></div>
                <div class="stat-box"><span class="label">Lore ID</span><span class="value">{{ nid_lore }}</span></div>
                <div class="stat-box"><span class="label">CODE</span><span class="value" style="color:#d633ff">{{ code_lore }}</span></div>
            </div>

            <div class="label">Narrativa</div>
            <div style="background:#111; padding:20px; border-left:4px solid #d633ff; font-style:italic; color:#ccc; white-space:pre-wrap;">{{ description }}</div>

            <div class="children-section">
                <div class="label" style="margin-bottom:15px; color:#a0a0ff;">▼ SUB-ENTIDADES ({{ hijos|length }})</div>
                {% for h in hijos %}
                <a href="{% url 'ver_mundo' h.id %}" class="child-card">
                    <img src="{% static 'persistence/img/'|add:h.img %}" style="width:50px; height:50px; object-fit:cover; margin-right:15px; border-radius:4px;" onerror="this.style.display='none'">
                    <div><div style="font-family:'Courier New'; color:#d633ff; font-size:0.8em;">{{ h.id }}</div><div style="font-weight:bold;">{{ h.name }}</div></div>
                </a>
                {% endfor %}
                
                {% if not is_preview %}
                <form method="POST" class="child-form">
                    {% csrf_token %}
                    <input type="text" name="child_name" placeholder="Crear hijo..." required>
                    <input type="text" name="child_desc" placeholder="Desc..." style="width:30%;">
                    <button type="submit">➕ CREAR</button>
                </form>
                {% endif %}
            </div>
        </div>
    </div>

    {% if not is_preview %}
    <div id="editModal" class="modal">
        <div class="modal-content">
            <h2 style="color:#fff; margin-top:0;">Proponer Cambio</h2>
            <form method="POST" action="{% url 'editar_mundo' jid %}" class="edit-form">
                {% csrf_token %}
                <label>Nombre:</label><input type="text" name="name" value="{{ name }}">
                <label>Descripción:</label><textarea name="description" style="height:150px;">{{ description }}</textarea>
                <label style="color:#f1c40f;">Razón:</label><input type="text" name="reason" required>
                <div style="margin-top:20px; text-align:right;">
                    <a href="{% url 'ver_mundo' jid %}" class="btn" style="background:#555;">Cancelar</a>
                    <button type="submit" class="btn" style="background:#d633ff;">🚀 Enviar Propuesta</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""
    with open(path_ficha, "w", encoding="utf-8") as f:
        f.write(html_content.strip())

    print("✅ Ficha HTML reparada. Error de sintaxis 'Unclosed tag if' resuelto.")

if __name__ == "__main__":
    reparar_template_ficha_error()