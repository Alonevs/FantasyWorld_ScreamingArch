# Manual Técnico: FantasyWorld (Screaming Architecture)

Este documento consolida la información técnica, arquitectónica y lógica del proyecto **FantasyWorld**.

## 1. Contexto del Proyecto
**FantasyWorld** es una plataforma web para la gestión y simulación de mundos de fantasía. Su objetivo es permitir a los usuarios crear universos complejos con coherencia narrativa, utilizando IA para asistir en la generación de contenido.

El sistema migró de una solución a medida a **Django**, adoptando una arquitectura estricta para desacoplar la lógica de negocio del framework web.

---

## 2. Arquitectura (Screaming Architecture)
El proyecto sigue el principio de que la estructura de carpetas debe "gritar" de qué trata la aplicación, no qué framework usa.

### Estructura de Directorios
*   **`src/WorldManagement` (El Núcleo)**:
    *   Aquí vive el DOMINIO. No sabe nada de Django (o muy poco).
    *   **Domain/**: Entidades puras (`World`, `Narrative`), Value Objects.
    *   **Application/**: Casos de Uso (`CreateWorld`, `ProposeChange`). Orquestan la lógica.
    *   **Infrastructure/**: Implementaciones concretas (ej. Repositorios que sí tocan la BD).

*   **`src/Infrastructure/DjangoFramework` (El Detalle)**:
    *   Aquí vive DJANGO. Es un detalle de implementación para la web y la persistencia.
    *   **persistence/**: Modelos ORM (`CaosWorldORM`), Vistas, Templates.
    *   **config/**: `settings.py`, `urls.py`.

### Flujo de Datos
1.  **Vista (Django)** recibe Petición HTTP.
2.  **Vista** llama a un **Caso de Uso** (Application Layer).
3.  **Caso de Uso** pide datos a un **Repositorio** (Interface).
4.  **Repositorio (Django impl)** consulta la BD usando ORM y devuelve **Entidades de Dominio**.
5.  **Caso de Uso** aplica lógica y devuelve resultados a la Vista.

---

## 3. Lógica del Mundo (Sistema J-ID)
Para modelar la contención (Universo > Galaxia > Planeta), usamos **Identificadores Jerárquicos (J-ID)**.

*   **Formato**: String numérico de pares de dígitos (`01`, `0105`, `010502`).
*   **Nivel**: La longitud dividida por 2 indica el nivel de profundidad.
    *   `01` (Len 2) = Nivel 1 (Caos/Raíz).
    *   `0105` (Len 4) = Nivel 2.
*   **Padding (Relleno)**: Si un Dios (Nivel 3) crea un Planeta (Nivel 6) directamente, los niveles intermedios se rellenan con `00`.
    *   `010101` (Nivel 3) -> `010101000001` (Nivel 6).

### Tabla de Niveles Clave
| Nivel | Nombre | Ejemplo |
| :--- | :--- | :--- |
| **01** | CAOS PRIME | La raíz. |
| **03** | UNIVERSO | Contenedor mayor. |
| **06** | PLANETA | Unidad habitable principal. |
| **08** | PAÍS | División política. |
| **09** | CIUDAD | Asentamiento. |
| **16** | PERSONAJE | Entidad individual (Salto especial de 4 dígitos al final). |

---

## 4. Sistema de Permisos y Rangos

La aplicación implementa una jerarquía de acceso granular gestionada a través del perfil de usuario (`UserProfile.RANK_CHOICES`) y grupos de Django.

### Jerarquía de Rangos
- **USER (Explorador)**: Permisos básicos. Crea propuestas que requieren aprobación.
- **SUBADMIN**: Colaborador con capacidad de edición, pero supeditado a un Admin.
- **ADMIN (Socio)**: Líder de equipo.
    - Gestiona propuestas de sus colaboradores asignados.
    - Sus cambios son `LIVE` automáticamente si es el autor.
    - Miembro automático del grupo de Django `Admins`.
- **SUPERUSER**: Acceso global absoluto.

### Lógica de Silos (Permissions)
- Los permisos se validan centralizadamente en `policies.py`.
- Un **Admin** solo puede ver y aprobar propuestas de usuarios que lo tengan como jefe (`collaborators`).
- El acceso a mundos privados está restringido al autor, su equipo y los Superadmins.

### Silos Territoriales (Dashboard)
**Implementado en:** `workflow.py` (líneas 63-115)

Para evitar que los Admins vean propuestas de sus Minions sobre contenido del Sistema/Superuser, se implementó un filtro territorial:

- **Regla**: Un Admin solo ve propuestas de sus colaboradores si el `world.author` del mundo objetivo es:
  - El propio Admin
  - Otro miembro del equipo del Admin
  - **NO** el Superuser o mundos huérfanos (Sistema)

**Ejemplo:**
- María (Minion de Pepe) hace una propuesta sobre un mundo de Alone (Superuser)
- Pepe (Admin) **NO** verá esa propuesta en su Dashboard
- Solo Alone (Superuser) la verá

Esto mantiene la privacidad entre diferentes silos administrativos.

### Gestión de Usuarios
**Implementado en:** `team.py`, `user_management.html`

#### Interfaz de Gestión
- **Dropdown de Rangos**: Los badges de rango (🛡️ ADMIN, 🔭 EXPLORER) son clickeables y muestran opciones de promoción/degradación
- **Badges de Equipo**: Muestra los jefes de cada usuario con badges "👑 Nombre"
- **Botón Reclutar**: Permite a Admins/Superusers añadir usuarios a su equipo
- **Páginas de Perfil**: Vista detallada en `/usuarios/<id>/` con:
  - Estadísticas (mundos, narrativas)
  - Lista de jefes
  - Lista de colaboradores (minions)

#### Filtrado de Estadísticas
Las estadísticas de usuarios solo cuentan contenido **activo y publicado**:
- `is_active=True` (no en papelera)
- `status='LIVE'` (publicado, no borradores)
- Para Superusers: incluye mundos huérfanos (`author=NULL`) como contenido del sistema

### Mis Propuestas Enviadas
**Implementado en:** `workflow.py` (líneas 234-270), `dashboard.html`

Sistema de historial personal de propuestas organizado por tipo de contenido:

#### Agrupación por Tipo
Las propuestas se agrupan en el backend por `type` en lugar de `status`:
```python
my_worlds = [x for x in my_history if x.type == 'WORLD']
my_narratives = [x for x in my_history if x.type == 'NARRATIVE']
my_images = [x for x in my_history if x.type == 'IMAGE']
my_metadata = [x for x in my_history if x.type == 'METADATA']
```

#### Características
- **Oculto para Superusers**: `{% if my_history and not user.is_superuser %}`
- **Secciones Colapsables**: Usa Alpine.js con `x-data` y `x-transition`
- **Componente Reutilizable**: `_my_proposal_card.html` para renderizar cada propuesta
- **Estados Soportados**: PENDING, APPROVED, REJECTED, ARCHIVED, HISTORY

#### Manejo de Status HISTORY
Las propuestas con status `HISTORY` (versiones históricas archivadas) se incluyen automáticamente en el historial personal, permitiendo al usuario revisar versiones antiguas de su trabajo.

---

## 5. Instalación y Setup

### Requisitos
*   Python 3.10+
*   PostgreSQL 14+ (Recomendado)
*   Git

### Pasos
1.  **Clonar**: `git clone ...`
2.  **Entorno Virtual**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    ```
3.  **Dependencias**: `pip install -r requirements.txt`
4.  **Configuración (.env)**:
    Crear `.env` en la raíz con:
    ```ini
    DEBUG=True
    SECRET_KEY=...
    DB_NAME=fantasyworld
    DB_USER=postgres
    DB_PASSWORD=...
    DB_HOST=localhost
    ```
5.  **Base de Datos**:
    ```bash
    python src/Infrastructure/DjangoFramework/manage.py migrate
    python src/Infrastructure/DjangoFramework/manage.py runserver
    ```
