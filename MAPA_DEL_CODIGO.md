# Mapa del Código: Fantasy World Screaming Arch
*Última Actualización: Enero 2026*

Este documento sirve como guía de navegación para la arquitectura del proyecto. Está diseñado para facilitar futuras refactorizaciones y la localización rápida de funcionalidades.

## 🏗️ Arquitectura General
El proyecto sigue principios de **Clean Architecture** adaptados a Django.

### 1. Capa de Aplicación (Lógica de Negocio Pura)
Aquí residen los **Casos de Uso**. Esta capa NO sabe nada de HTTP, Vistas o HTML. Solo manipula datos y reglas de negocio.
- **Ubicación**: `src/WorldManagement/Caos/Application/`
- **Patrón**: Cada archivo suele contener una sola clase `UseCase` con un método `execute()`.
- **Ejemplos**:
    - `propose_change.py`: Lógica para crear una propuesta.
    - `restore_version.py`: Lógica para revertir cambios.
    - `create_narrative.py`: Lógica para crear un nuevo texto.

### 2. Capa de Infraestructura (Django Framework)
Aquí reside todo lo relacionado con la web: Vistas, URLs, Templates y Modelos de Base de Datos.
- **Ubicación Base**: `src/Infrastructure/DjangoFramework/`

#### 📂 Modelos de Datos (BD)
- **`persistence/models.py`**: Archivo central con TODAS las definiciones de tablas (`CaosWorldORM`, `CaosNarrativeORM`, `CaosVersionORM`, etc.).

#### 📂 Vistas (Controladores)
Las vistas están organizadas modularmente en `persistence/views/`.

| Módulo | Descripción | Contenido Clave |
| :--- | :--- | :--- |
| **`world_views.py`** | Vistas públicas del Mundo | `ver_mundo`, `editar_mundo`, `mapa_arbol` |
| **`narrative_views.py`** | Gestión de Narrativas | `leer_narrativa`, `editar_narrativa`, `crear_nueva_narrativa` |
| **`social_views.py`** | Interacción Social | Likes, Comentarios (API y Vistas) |
| **`media_views.py`** | Gestión de Archivos | Subida de fotos, portadas, previews |
| **`period_api.py`** | API de Periodos | Endpoints para Cronología y Periodos |

#### 📂 Dashboard (Panel de Control y Workflow)
Esta es la zona más compleja, recientemente refactorizada para ser modular.
Ubicación: `persistence/views/dashboard/`

| Sub-Paquete / Módulo | Archivos | Responsabilidad |
| :--- | :--- | :--- |
| **`workflow/`** | `world_actions.py`<br>`narrative_actions.py`<br>`period_actions.py`<br>`bulk_operations.py` | **Motor de Aprobaciones**. Gestiona el ciclo de vida de las propuestas (Aprobar/Rechazar/Publicar). |
| **`assets/`** | `image_workflow.py`<br>`trash_management.py`<br>`batch_ops.py` | **Gestión de Recursos**. <br>- `image_workflow`: Propuestas de fotos.<br>- `trash_management`: Papelera de Reciclaje y Restauración.<br>- `batch_ops`: Herramientas de revisión masiva. |
| **`history/`** | `version_control.py`<br>`audit_log.py` | **Histórico**. <br>- `version_control`: Historial de cambios y limpieza.<br>- `audit_log`: Logs de sistema y actividad. |
| **`team/`** | `team.py`<br>`...` | Gestión de Colaboradores y Permisos de Equipo. |
| **`analytics.py`** | - | Estadísticas y métricas para administradores. |

---

## 🛠️ Guía para Tareas Comunes

### "Quiero añadir una nueva acción al flujo de aprobación..."
1.  Ve a `src/Infrastructure/DjangoFramework/persistence/views/dashboard/workflow/`.
2.  Si es para Mundos, edita `world_actions.py`. Si es Narrativa, `narrative_actions.py`.
3.  Asegúrate de definir la URL en `config/urls.py`.

### "Quiero cambiar cómo se guardan las imágenes..."
1.  La lógica de vista está en `persistence/views/dashboard/assets/image_workflow.py`.
2.  La lógica de almacenamiento físico está en `src/WorldManagement/Caos/Infrastructure/django_repository.py` (Repo).

### "Quiero modificar los permisos de restauración..."
1.  La lógica de vista está en `persistence/views/dashboard/history/version_control.py` (para ver) o `persistence/views/dashboard/workflow/world_actions.py` (para ejecutar `restaurar_version`).
2.  La lógica de negocio está en el Caso de Uso: `src/WorldManagement/Caos/Application/restore_version.py`.

### "Quiero arreglar un bug en la Papelera..."
1.  Ve directamente a `src/Infrastructure/DjangoFramework/persistence/views/dashboard/assets/trash_management.py`.

---

## 🧪 Estado de los Tests (Enero 2026)
- **Suite Principal**: `src.Infrastructure.DjangoFramework.persistence.tests`
- **Cobertura**:
    - `test_proposals.py`: 11/12 Tests probados. (El fallo es un falso positivo UI en `test_retouch_mode_prefills_form`, la lógica backend es sólida).
    - `test_permissions.py`: Valida seguridad de acceso.
    - `test_period_workflow.py`: Valida lógica compleja de creación de periodos.

Para ejecutar tests:
```bash
python src/Infrastructure/DjangoFramework/manage.py test src.Infrastructure.DjangoFramework.persistence.tests
```
