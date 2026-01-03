# FantasyWorld (Arquitectura Screaming + Django) - v0.1 (Base)

## 📖 Introducción
**FantasyWorld** es una aplicación web integral para la creación, gestión y simulación de mundos de fantasía. Utiliza **Django** como infraestructura robusta y sigue el patrón de **Screaming Architecture** (Arquitectura Limpia) para mantener la lógica de dominio pura y desacoplada.

**Versión Actual:** v0.1 (Base)
**Estado:** Desarrollo Activo v0.1 / UI Premium / PostgreSQL

## 🚀 Fase Actual (v0.1)
-   **UI Premium & Responsive**: Header con efecto Glassmorphism, animaciones avanzadas y **Panel Lateral optimizado para móviles**.
-   **Jerarquía de Roles (Eclai-Core)**:
    -   **👑 Superadmin**: Control global total.
    -   **🤝 Admin (Socio)**: Gestión de equipo y aprobación de sus propios "Minions".
    -   **🛡️ SubAdmin**: Colaborador con permisos de edición avanzados.
    -   **🧭 Explorador**: Usuario base con permisos de lectura y propuestas.
-   **Seguridad y Silos**: Los Admins solo gestionan a sus colaboradores asignados, garantizando un entorno de trabajo organizado.
-   **ECLAI Core**: Generación de imágenes y textos con IA.
-   **Flujo de Aprobación**: Todo cambio requiere validación en Dashboard.

## 📚 Documentación (Español)

### 📖 Para Desarrolladores y IAs
Documentación principal en la raíz del proyecto:
-   [**🏛️ ARCHITECTURE.md**](ARCHITECTURE.md): Mapa mental completo del proyecto, flujos críticos y convenciones.
-   [**🔧 REFACTORING_BACKLOG.md**](REFACTORING_BACKLOG.md): Lista priorizada de mejoras de código pendientes.
-   [**🧪 TESTING_GUIDE.md**](TESTING_GUIDE.md): Guía pragmática de testing para proyecto personal.

### 📚 Documentación Adicional
La documentación complementaria está organizada en la carpeta `docs/`:
-   [**📘 Guía Técnica**](docs/technical_guide.md): Arquitectura, Instalación y Lógica J-ID.
-   [**🤖 Arquitectura IA**](docs/ai_architecture.md): Prompts, Auto-Noos y Herencia.
-   [**🧭 Guía de Usuario**](docs/user_guide.md): Flujo de Propuestas, Dashboard y Edición.
-   [**🛡️ Reglas del Agente**](docs/agent_rules.md): Filosofía de desarrollo.
-   [**📝 Cosas que Mirar**](docs/cosas_que_mirar.md): Backlog de refactorizaciones futuras.
-   [**🗺️ Roadmap**](ROADMAP.md): Hoja de ruta del proyecto.

## 🛠️ Características Clave
-   **Screaming Architecture**: Lógica de negocio pura.
-   **NanoIDs**: URLs seguras (`/mundo/JhZCO1vxI7/`).
-   **Sistema de Propuestas**: Integridad de datos garantizada.
-   **Modo "Noos"**: Auto-generación de metadatos basada en narrativa.

## 🤝 Contribuir
Lee la [Guía de Estructura](CODE_STRUCTURE.md) antes de contribuir.
