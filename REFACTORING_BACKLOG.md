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

---

### ~~3. Dividir `team.py` (678 líneas)~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Refactorizado exitosamente

**Solución implementada:**
Dividido en 6 módulos temáticos dentro de `views/dashboard/team/`:
- `management.py` - Gestión de usuarios (UserManagementView)
- `permissions.py` - Gestión de permisos/roles (toggle_admin_role)
- `collaboration.py` - Equipos y colaboradores (MyTeamView, CollaboratorWorkView)
- `detail.py` - Detalle de usuario (UserDetailView)
- `ranking.py` - Ranking de usuarios (UserRankingView)
- `__init__.py` - Exports públicos para compatibilidad

**Compatibilidad:**
- `team.py` ahora es un wrapper que importa del paquete `team/`
- 100% compatible con código existente
- No requiere cambios en `urls.py` ni en otras vistas

**Resultado:**
- ✅ Archivo más grande: ~301 líneas (vs 678 original) - 56% reducción
- ✅ Promedio: ~113 líneas por archivo - 83% reducción
- ✅ Separación clara de responsabilidades
- ✅ Más fácil de navegar y mantener
- ✅ Documentado en `ARCHITECTURE.md`

---

## 🟡 PRIORIDAD MEDIA (Cuando Tengas Tiempo)

### ~~4. Extraer Lógica de Thumbnails~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Completado en Item #1

**Solución implementada:**
Función `get_thumbnail_url()` creada en `utils.py` durante la refactorización de lógica de portadas.

**Funcionalidad:**
- Prioridad: cover_image → primera imagen → placeholder
- Fallback inteligente en 3 niveles
- Usado en `team.py::UserRankingView`

**Código:**
```python
def get_thumbnail_url(world_id, cover_filename=None, use_first_if_no_cover=True):
    """Obtiene URL de thumbnail con fallback inteligente."""
    all_imgs = get_world_images(world_id)
    
    if cover_filename:
        cover_img = find_cover_image(cover_filename, all_imgs)
        if cover_img:
            return f"/static/persistence/img/{cover_img['url']}"
    
    if use_first_if_no_cover and all_imgs:
        return f"/static/persistence/img/{all_imgs[0]['url']}"
    
    return "/static/img/placeholder.png"
```

---

### ~~5. Documentar Flujo de Propuestas~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Documentado en `ARCHITECTURE.md`

**Contenido añadido:**
- Diagrama Mermaid del flujo completo
- Explicación detallada de cada fase
- Ejemplos de código
- Tabla de estados
- Documentación de modo retoque
- Sistema de notificaciones

**Ubicación:** `ARCHITECTURE.md` - Sección "🔄 Flujo de Propuestas (Sistema ECLAI)"

---

### ~~6. Limpiar Código Muerto~~ ✅ COMPLETADO (2026-01-03)
**Estado:** ✅ Limpieza exitosa

**Archivos eliminados:**
- `views/world/legacy.py` - Funciones deprecadas no utilizadas (58 líneas)
  - `init_hemisferios()` - No referenciada en templates
  - `escanear_planeta()` - No referenciada en templates

**URLs eliminadas:**
- `path('init_hemisferios/<str:jid>/', ...)` 
- `path('escanear/< str:jid>/', ...)`

**Imports limpiados:**
- Removidos de `config/urls.py`
- Removidos de `views/world/__init__.py`
- Removidos de `views/world_views.py`

**Resultado:**
- ✅ ~100 líneas de código muerto eliminadas (incluyendo imports masivos no usados)
- ✅ 2 URLs obsoletas removidas
- ✅ Codebase más limpio y mantenible

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

## 📝 Cómo Usar Este Documento

1. **Antes de añadir una feature nueva:** Revisa si hay algo en PRIORIDAD ALTA
2. **Si el código se siente "pesado":** Elige 1 item y refactoriza
3. **Regla 80/20:** Por cada 4 features nuevas, 1 refactorización
4. **Actualiza este documento:** Tacha items completados, añade nuevos

---

## ✅ Completados

_(Añade aquí items que ya refactorizaste)_

- [x] Ejemplo: Centralizar lógica de portadas (Fecha: 2026-01-03)
- [x] **Refactorización del Sistema de Avatares** (Fecha: 2026-01-03)
    - Centralizada lógica en `utils.py:get_user_avatar`.
    - Implementado fallback estable a imágenes de Assets globales con seeding.
    - Sincronización automática de identidad en Lightbox (Fix "Anónimo").

---

**Última actualización:** 2026-01-03
**Mantenido por:** IAs colaboradoras del proyecto
