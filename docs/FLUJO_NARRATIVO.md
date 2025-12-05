# Flujo Narrativo y Sistema de Aprobación

FantasyWorld utiliza un sistema estricto de **Propuestas y Aprobaciones** para mantener la integridad del mundo (Lore, Historia, Capítulos).

## 1. Ciclo de Vida del Contenido

### A. Borrador (Draft)
-   Cuando creas un mundo o capítulo, nace como **Borrador**.
-   **Visibilidad**: Oculto para el público. Visible solo para el autor/admin.
-   **Estado**: `DRAFT` (o versión 0).

### B. Propuesta (Proposal)
-   Para hacer público un cambio (o el contenido inicial), debes **Guardar Cambios**.
-   Esto NO edita el contenido visible inmediatamente. Genera una **Propuesta** (`PENDING`).
-   Las propuestas incluyen: Editar Texto, Cambiar Portada, Cambiar Visibilidad, Borrar.

### C. Aprobación (Live)
-   Un Administrador revisa la propuesta en el **Dashboard** (`/control/`).
-   Al hacer clic en **Aprobar**:
    1.  Los cambios se aplican a la versión "LIVE".
    2.  El contenido se vuelve visible/actualizado públicamente.
    3.  La versión pasa a `APPROVED`.

## 2. Acciones Específicas

-   **Editar Texto**: Genera una nueva versión con el texto propuesto.
-   **Portada (Cover)**: Genera una propuesta de tipo `SET_COVER`.
-   **Visibilidad**: Genera una propuesta `TOGGLE_VISIBILITY` (Público <-> Privado).
-   **Borrar**: Genera una propuesta de eliminación. Si se aprueba, se borra el contenido real.

## 3. Dashboard
El Dashboard es el centro de control.
-   Muestra propuestas pendientes de Mundos y Narrativas.
-   Muestra contexto (ej. "Mundo X > Capítulo Y") para saber qué se está aprobando.
