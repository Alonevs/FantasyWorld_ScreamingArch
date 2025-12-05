# FantasyWorld (Arquitectura Screaming + Django) - v5.0 (Base)

## 📖 Introducción
**FantasyWorld** es una aplicación web integral para la creación, gestión y simulación de mundos de fantasía. Utiliza **Django** como infraestructura robusta y sigue el patrón de **Screaming Architecture** (Arquitectura Limpia) para mantener la lógica de dominio pura y desacoplada.

**Versión Actual:** v5.0 (Base)
**Estado:** Estable / Flujo de Aprobación Estricto / PostgreSQL

## 🚀 Inicio Rápido

### Requisitos
-   Python 3.10+
-   PostgreSQL (Recomendado) o SQLite
-   Entorno Virtual (venv)

### Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/Alonevs/FantasyWorld_ScreamingArch.git
    cd FantasyWorld_ScreamingArch
    ```

2.  **Crear entorno virtual**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Base de Datos**:
    -   Copiar `.env.example` a `.env` (si existe) y configurar credenciales.
    -   Por defecto usa PostgreSQL.

5.  **Migrar y Arrancar**:
    ```bash
    python src/Infrastructure/DjangoFramework/manage.py migrate
    python src/Infrastructure/DjangoFramework/manage.py runserver
    ```

6.  **Acceder**:
    Navega a `http://127.0.0.1:8000`.

## 📚 Documentación
La documentación detallada se encuentra en `/docs`:

-   [**Arquitectura**](docs/ARQUITECTURA.md): Explicación de DDD, Screaming Architecture y estructura.
-   [**Guía de Instalación**](docs/INSTALACION.md): Configuración de PostgreSQL y entorno.
-   [**Flujo Narrativo**](docs/FLUJO_NARRATIVO.md): Cómo crear y aprobar contenido.

## 🛠️ Características Clave v5.0
-   **Aprobación Estricta**: Todo cambio (Crear, Editar, Borrar, Visibilidad) genera una **Propuesta** que debe ser aprobada en el Dashboard.
-   **Screaming Architecture**: Lógica de negocio aislada del Framework.
-   **Sistema ECLAI**: Integración con IA para generación de imágenes.
-   **NanoIDs**: Identificadores únicos seguros para URLs públicas.

## 🤝 Contribuir
Lee la [Guía de Arquitectura](docs/ARQUITECTURA.md) antes de contribuir.
