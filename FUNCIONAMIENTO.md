# Funcionamiento del Sistema (Paso a Paso)

Este documento detalla los flujos de trabajo prácticos disponibles en la versión actual (v0.1) de FantasyWorld. Úsalo como referencia para entender "qué hace el programa" y cómo ejecutar cada acción.

## 1. Gestión de Mundos (Core)

### A. Crear un Nuevo Mundo
1.  **Inicio**: Ve a la página principal (`/`).
2.  **Formulario**: Usa el formulario superior "Proponer Nuevo Mundo".
    *   **Nombre**: Título del mundo.
    *   **Descripción**: Breve resumen.
    *   **Imagen**: Opcional (se puede generar después).
3.  **Acción**: Pulsa "Proponer Mundo".
4.  **Resultado**: 
    *   Se crea una **Propuesta de Creación**.
    *   Aparece un mensaje: "Mundo propuesto... Ve al Dashboard".
    *   El mundo NO es visible públicamente aún (Estado `PENDING`).

### B. Aprobar la Creación (Admin)
1.  Ve al menú **Dashboard** (`/control/`).
2.  Busca la sección **"🌍 Mundos Pendientes"**.
3.  Verás la tarjeta del nuevo mundo. Pulsa **✅ APROBAR**.
4.  **Resultado**: El mundo pasa a estado `LIVE` y aparece en el índice principal.

### C. Visualización de la Ficha
1.  Haz clic en cualquier tarjeta de mundo del Home.
2.  Accederás a la **Ficha del Mundo** (`/mundo/<ID>/`).
    *   **Cabecera**: Título, estado (LIVE/OFFLINE), breadcrumbs.
    *   **Galería**: Imágenes asociadas.
    *   **Selector de Periodo**: Barra para viajar en el tiempo (Pasado/Actual).
    *   **Hijos**: Lista de regiones/lugares dentro de este mundo.

---

## 2. Edición y Propuestas de Cambio

El sistema protege los datos: **nada se cambia directamente**, todo se propone.

### A. Editar Nombre o Descripción
1.  En la Ficha del Mundo, pulsa el botón **✏️ EDITAR ACTUAL** (arriba a la derecha).
2.  Modifica el texto en el formulario.
3.  Pulsa **"Proponer Cambios"**.
4.  El sistema genera una **Versión (vX)** en estado `PENDING`.
5.  Un Admin debe aprobarla en el Dashboard para que sea visible.

### B. Propuesta de Metadatos (Data Estructurada)
1.  En la columna derecha de la Ficha ("Información"), busca el **Visor de Metadatos**.
2.  Pulsa **"⚙️ GESTIONAR"** (o "Editar Metadatos").
3.  Se abre el modal **Gestor de Metadatos**.
    *   Puedes añadir filas manualmente (Clave/Valor).
    *   Puedes pulsar **"🤖 AUTO-NOOS"** para que la IA extraiga datos de la descripción.
4.  Pulsa **"GUARDAR PROPUESTA"**.
5.  Esto crea una propuesta específica de tipo `METADATA` (independiente del texto).

### C. Modo Retoque (Corregir Rechazos)
Si un Admin rechaza tu propuesta:
1.  Ve al Dashboard -> **"🗂️ Mis Propuestas Enviadas"**.
2.  Busca la propuesta con estado `REJECTED`.
3.  Pulsa el botón **"✏️ Retocar"**.
4.  Te llevará de vuelta al editor con **tus datos precargados** (no tienes que empezar de cero).
5.  Corrige lo necesario y vuelve a enviar.

---

## 3. Línea Temporal (Timeline)

Gestiona la historia del mundo no solo en el espacio, sino en el tiempo.

### A. Navegar por Periodos
1.  En la Ficha del Mundo, observa la barra **Cronología** (debajo del título o en el panel lateral).
2.  El botón **⭐ ACTUAL** muestra el estado presente.
3.  Los botones **📜 [Nombre Periodo]** cargan los datos históricos (descripción y metadatos de esa época).

### B. Crear un Nuevo Periodo Histórico
1.  Si tienes permisos, verás un botón **"➕ NUEVO"** en la barra de cronología.
2.  Haz clic y rellena:
    *   **Nombre del Periodo**: Ej. "Era de los Dragones".
    *   **Orden**: Número para ordenar cronológicamente.
3.  Al guardar, se crea un "contenedor" temporal vacío.
4.  Ahora puedes editar la descripción de ese periodo específico pulsando **"✏️ EDITAR PERÍODO"**.

---

## 4. Narrativas

Historias vinculadas al mundo, pero separadas de su descripción técnica.

### A. Crear Narrativa
1.  En la Ficha del Mundo, panel derecho, pulsa **"📖 Narrativa"**.
2.  Pulsa **"📝 Nueva Narrativa"**.
3.  Escribe el título y contenido.
4.  Al guardar, se genera una propuesta de narrativa.

---

## 5. Dashboard de Control (Sala de Máquinas)

El centro de mando en `/control/`.

*   **Auditoría**: Registro de quién hizo qué (`CREATE`, `EDIT`, `APPROVE`).
*   **Bandejas de Entrada**:
    *   Propuestas de Mundos.
    *   Propuestas de Metadatos.
    *   Propuestas de Periodos.
    *   Imágenes para revisar.
*   **Gestión de Equipo** (Solo Admins): Reclutar exploradores y ver su actividad.
*   **Historial y Papelera**: Herramientas para recuperar contenido borrado o versiones antiguas.
