# 🏗️ REFACTORING BACKLOG

> **Propósito:** Lista priorizada de refactorizaciones pendientes para mantener el código limpio y sostenible.
> **Uso:** Cuando tengas tiempo o el código se sienta "pesado", elige items de esta lista.

---

## 🔴 PRIORIDAD ALTA (Hacer Pronto)

### ~~1. Centralizar Lógica de Resolución de Portadas~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Refactorizado exitosamente

**Solución implementada:**
- Creadas 2 funciones centralizadas en `utils.py`:
  - `find_cover_image(cover_filename, all_imgs)` - Búsqueda flexible de portadas
  - `get_thumbnail_url(world_id, cover_filename, use_first_if_no_cover)` - URLs con fallback

**Archivos refactorizados:**
- `utils.py` - Añadidas funciones nuevas, refactorizado `get_world_images()`
- `world_views.py` - Refactorizado `comparar_version()`
- `review_views.py` - Refactorizado `review_proposal()`
- `team.py` - Refactorizado `UserRankingView` (mundos y narrativas)

**Resultado:**
- ✅ Eliminadas ~60 líneas de código duplicado
- ✅ Lógica centralizada en 1 lugar
- ✅ Más fácil de mantener y testear
- ✅ Documentado en `ARCHITECTURE.md`

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
