# 🏗️ REFACTORING BACKLOG

> **Propósito:** Lista priorizada de refactorizaciones pendientes para mantener el código limpio y sostenible.
> **Uso:** Cuando tengas tiempo o el código se sienta "pesado", elige items de esta lista.

---

## 🔴 PRIORIDAD ALTA (Hacer Pronto)

### 1. Centralizar Lógica de Resolución de Portadas
**Problema:** La lógica de búsqueda de cover_image está duplicada en 3 archivos.
**Archivos afectados:**
- `src/Infrastructure/DjangoFramework/persistence/utils.py` (líneas 228-242)
- `src/Infrastructure/DjangoFramework/persistence/views/world_views.py` (líneas 680-697)
- `src/Infrastructure/DjangoFramework/persistence/views/review_views.py` (líneas 160-172)
- `src/Infrastructure/DjangoFramework/persistence/views/dashboard/team.py` (líneas 595-608, 636-649)

**Solución:**
```python
# Crear en utils.py
def find_cover_image(cover_filename, all_imgs):
    """
    Encuentra imagen de portada con matching case-insensitive y flexible.
    
    Args:
        cover_filename (str): Nombre del archivo de portada
        all_imgs (list): Lista de diccionarios con info de imágenes
        
    Returns:
        dict: Imagen encontrada o None
    """
    if not cover_filename or not all_imgs:
        return None
    
    cover_lower = cover_filename.lower()
    # Exact match (case-insensitive)
    match = next((i for i in all_imgs if i['filename'].lower() == cover_lower), None)
    
    # Fallback: without extension
    if not match:
        c_clean = cover_filename.rsplit('.', 1)[0].lower()
        match = next((i for i in all_imgs if i['filename'].rsplit('.', 1)[0].lower() == c_clean), None)
    
    return match

# Luego reemplazar en todos los archivos por:
cover_img = find_cover_image(cover_filename, all_imgs)
if cover_img:
    thumb = f"/static/persistence/img/{cover_img['url']}"
```

**Beneficio:** Cambios futuros en lógica de portadas solo requieren editar 1 lugar.

---

### 2. Dividir `world_views.py` (882 líneas)
**Problema:** Archivo muy grande, difícil de navegar.
**Solución:** Dividir en módulos temáticos:

```
views/world/
├── __init__.py
├── detail.py       # ver_mundo (líneas 1-455)
├── edit.py         # editar_mundo (líneas 457-640)
├── compare.py      # comparar_version (líneas 642-787)
└── utils.py        # funciones auxiliares
```

**Pasos:**
1. Crear carpeta `views/world/`
2. Mover funciones a archivos correspondientes
3. Actualizar imports en `urls.py`
4. Verificar que todo funciona

**Beneficio:** Más fácil encontrar código, menos scroll.

---

### 3. Dividir `team.py` (707 líneas)
**Problema:** Mezcla gestión de usuarios, ranking, y permisos.
**Solución:**

```
views/dashboard/
├── team.py          # Gestión de equipo (líneas 1-300)
├── ranking.py       # UserRankingView (líneas 572-707)
└── permissions.py   # Toggle roles, permisos (líneas 62-200)
```

---

## 🟡 PRIORIDAD MEDIA (Cuando Tengas Tiempo)

### 4. Extraer Lógica de Thumbnails
**Problema:** Construcción de URLs de thumbnails repetida.
**Solución:**
```python
# En utils.py
def get_thumbnail_url(world, cover_filename=None):
    """
    Obtiene URL de thumbnail para un mundo.
    Prioridad: cover_image > primera imagen > placeholder
    """
    all_imgs = get_world_images(world.id)
    
    # 1. Cover definida
    if cover_filename:
        cover_img = find_cover_image(cover_filename, all_imgs)
        if cover_img:
            return f"/static/persistence/img/{cover_img['url']}"
    
    # 2. Primera imagen disponible
    if all_imgs:
        return f"/static/persistence/img/{all_imgs[0]['url']}"
    
    # 3. Placeholder
    return "/static/img/placeholder.png"
```

---

### 5. Documentar Flujo de Propuestas
**Problema:** No está claro cómo funciona el sistema de propuestas.
**Solución:** Crear diagrama en `ARCHITECTURE.md` (ver archivo separado).

---

### 6. Limpiar Código Muerto
**Archivos a revisar:**
- Buscar funciones no usadas con `grep -r "def nombre_funcion"`
- Buscar imports no usados
- Eliminar comentarios obsoletos

---

## 🟢 PRIORIDAD BAJA (Nice to Have)

### 7. Añadir Type Hints
```python
# ANTES
def get_world_images(jid):
    ...

# DESPUÉS
from typing import List, Dict, Optional

def get_world_images(jid: str) -> List[Dict[str, str]]:
    """
    Obtiene lista de imágenes para un mundo.
    
    Args:
        jid: ID del mundo
        
    Returns:
        Lista de diccionarios con info de cada imagen
    """
    ...
```

---

### 8. Extraer Constantes Mágicas
```python
# ANTES
if user.profile.rank == 'ADMIN':
    ...

# DESPUÉS
# En constants.py
class UserRank:
    EXPLORER = 'EXPLORER'
    SUBADMIN = 'SUBADMIN'
    ADMIN = 'ADMIN'

# Uso
if user.profile.rank == UserRank.ADMIN:
    ...
```

---

## 📝 Cómo Usar Este Documento

1. **Antes de añadir una feature nueva:** Revisa si hay algo en PRIORIDAD ALTA
2. **Si el código se siente "pesado":** Elige 1 item y refactoriza
3. **Regla 80/20:** Por cada 4 features nuevas, 1 refactorización
4. **Actualiza este documento:** Tacha items completados, añade nuevos

---

## ✅ Completados

_(Añade aquí items que ya refactorizaste)_

- [x] Ejemplo: Centralizar lógica de portadas (Fecha: 2026-01-03)

---

**Última actualización:** 2026-01-03
**Mantenido por:** IAs colaboradoras del proyecto
