# FantasyWorld (Arquitectura Screaming + Django) - v5.0 (Base)

## 📖 Introducción
**FantasyWorld** es una aplicación web integral para la creación, gestión y simulación de mundos de fantasía. Utiliza **Django** como infraestructura robusta y sigue el patrón de **Screaming Architecture** (Arquitectura Limpia) para mantener la lógica de dominio pura y desacoplada.

**Versión Actual:** v5.0 (Base)
**Estado:** Desarrollo Activo v5.2 / UI Premium / PostgreSQL

## 🚀 Fase Actual (v5.2)
-   **UI Premium & Responsive**: Header con efecto Glassmorphism, animaciones avanzadas y **Panel Lateral optimizado para móviles**.
-   **Jerarquía de Roles (Eclai-Core)**:
    -   **👑 Superadmin**: Control global total.
    -   **🤝 Admin (Socio)**: Gestión de equipo y aprobación de sus propios "Minions".
    -   **🛡️ SubAdmin**: Colaborador con permisos de edición avanzados.
    -   **🧭 Explorador**: Usuario base con permisos de lectura y propuestas.
-   **Seguridad y Silos**: Los Admins solo gestionan a sus colaboradores asignados, garantizando un entorno de trabajo organizado.
-   **ECLAI Core**: Generación de imágenes y textos con IA.
-   **Flujo de Aprobación**: Todo cambio requiere validación en Dashboard.

## � Documentación (Español)
La documentación ha sido consolidada y traducida:

-   [**📘 Manual Técnico**](MANUAL_TECNICO.md): Arquitectura, Instalación y Lógica J-ID.
-   [**🤖 Manual IA**](MANUAL_IA.md): Prompts, Auto-Noos y Herencia.
-   [**🧭 Guía de Usuario**](GUIA_USUARIO.md): Flujo de Propuestas, Dashboard y Edición.
-   [**🗺️ Roadmap**](ROADMAP.md): Hoja de ruta del proyecto.

## �🛠️ Características Clave
-   **Screaming Architecture**: Lógica de negocio pura.
-   **NanoIDs**: URLs seguras (`/mundo/JhZCO1vxI7/`).
-   **Sistema de Propuestas**: Integridad de datos garantizada.
-   **Modo "Noos"**: Auto-generación de metadatos basada en narrativa.

## 🤝 Contribuir
Lee la [Guía de Estructura](CODE_STRUCTURE.md) antes de contribuir.
