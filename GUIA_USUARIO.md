# Guía de Usuario y Flujo de Trabajo

Esta guía explica cómo interactuar con FantasyWorld para crear y aprobar contenido de manera segura.

## 1. El Concepto de "Propuesta"
Para proteger la integridad del mundo, **ningún cambio es inmediato**.
Todo cambio (Crear, Editar, Borrar, Cambiar Visibilidad) genera una **PROPUESTA** (`PENDING`) una vez guardado.

1.  **Borrador (Draft)**: Solo visible para ti. Estás editando.
2.  **Pendiente (Pending)**: Has enviado los cambios. Esperando aprobación.
3.  **Aprobado/Live**: El contenido es oficial y visible (según permisos).
4.  **Archivado**: Versiones antiguas superadas por nuevas ediciones.

## 2. Jerarquía de Usuarios y Equipo
FantasyWorld utiliza un sistema de rangos para distribuir la responsabilidad:

-   **Superadmin**: El arquitecto global. Aprueba todo y gestiona la jerarquía.
-   **Admin (Socio)**: Líder de un equipo. Puede aprobar las propuestas de sus SubAdmins y gestionar su propio contenido.
-   **SubAdmin**: Colaborador de confianza. Puede crear contenido avanzado pero sus cambios suelen requerir validación.
-   **Explorador**: Usuario estándar que puede realizar propuestas de mejora.

> [!NOTE]
> **Sistema de Silos**: Un Admin no puede interferir en el trabajo de otro equipo a menos que sea Superadmin.

## 2. Acciones Comunes

### Crear / Editar
1.  Editas el texto o nombre.
2.  Pulsas "Guardar".
3.  El sistema confirma: "Propuesta enviada".
4.  Debes ir al **Dashboard** para aprobarla (si eres Admin).

### Borrar (Soft Delete)
Nada se borra realmente.
1.  Solicitas borrar una entidad.
2.  Desaparece de la vista pública.
3.  Va a la **Papelera**.
4.  Desde la Papelera, puedes solicitar "Restaurar". Esto crea una propuesta de Tipo `RESTORE` que debe aprobarse.

### Visibilidad
1.  Entra en la ficha del mundo.
2.  Pulsa el botón de "Ojo" (Visibilidad).
3.  Esto crea una propuesta para cambiar de Público a Privado (o viceversa).

## 3. Dashboard (Centro de Control)
Es la sala de máquinas `/control/`. Aquí verás:
*   Lista de Nuevos Mundos pendientes.
*   Lista de Ediciones de Narrativa pendientes.
*   Cambios de Metadatos.

Como Admin o Superadmin, tu trabajo es revisar y pulsar **✅ APROBAR** para que los cambios se hagan realidad. Recuerda que solo verás las propuestas de los colaboradores que tengas asignados (tu equipo).

## 4. Navegación Móvil
El nuevo **Header Premium** incluye un menú hamburguesa en la parte superior izquierda en dispositivos móviles. Desde allí puedes acceder rápidamente a tu trabajo, al dashboard o a la gestión de tu equipo sin que la pantalla se sature de botones.
