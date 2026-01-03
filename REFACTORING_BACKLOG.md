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

### ~~2. Dividir `world_views.py` (882 líneas)~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Refactorizado exitosamente

**Solución implementada:**
Dividido en 8 módulos temáticos dentro de `views/world/`:
- `listing.py` - Vista de inicio (129 líneas)
- `detail.py` - Vistas de detalle (ver_mundo, ver_metadatos, mapa_arbol)
- `edit.py` - Vistas de edición (editar_mundo, update_avatar)
- `actions.py` - Acciones sobre mundos (toggle_entity_status, borrar_mundo, etc)
- `versions.py` - Gestión de versiones (comparar_version, restaurar_version)
- `utils.py` - Utilidades internas (log_event, get_current_user)
- `legacy.py` - Funciones deprecadas (init_hemisferios, escanear_planeta)
- `__init__.py` - Exports públicos para compatibilidad

**Compatibilidad:**
- `world_views.py` ahora es un wrapper que importa del paquete `world/`
- 100% compatible con código existente
- No requiere cambios en `urls.py` ni en otras vistas

**Resultado:**
- ✅ Archivo más grande: ~250 líneas (vs 876 original)
- ✅ Promedio: ~110 líneas por archivo
- ✅ Separación clara de responsabilidades
- ✅ Más fácil de navegar y mantener
- ✅ Documentado en `ARCHITECTURE.md`

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
