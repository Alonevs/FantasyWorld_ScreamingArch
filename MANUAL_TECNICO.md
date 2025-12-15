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

## 4. Instalación y Setup

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
