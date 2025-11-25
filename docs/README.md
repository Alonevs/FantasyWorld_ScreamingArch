# 📘 Fantasy World Generator v3.0

> **Screaming Architecture + Domain-Driven Design + Generative AI**

Este proyecto es un gestor de mundos de fantasía avanzado que desacopla la lógica de negocio del framework, integrando generación procedural de historias (Llama 3) y mapas/retratos (Stable Diffusion).

---

## 🚀 Inicio Rápido

### Prerrequisitos
- **Python 3.11+**
- **Servidores de IA** (Deben estar corriendo antes de iniciar):
  - **Texto**: Oobabooga Text-Generation-WebUI (Puerto 5000)
  - **Imagen**: Stable Diffusion WebUI (Puerto 7861, args: `--api --nowebui --xformers`)

### Instalación y Ejecución

1.  **Activar Entorno Virtual**:
    ```powershell
    .\venv\Scripts\activate
    ```

2.  **Ejecutar Aplicación**:
    *   **Modo Web (Dashboard)**:
        ```powershell
        python src/Infrastructure/DjangoFramework/manage.py runserver
        ```
        Accede a: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

    *   **Modo Consola (Test Rápido)**:
        ```powershell
        python main.py
        ```

---

## 📚 Documentación

- **[Arquitectura del Proyecto](docs/ARCHITECTURE.md)**: Explicación detallada de la estructura "Screaming Architecture", capas (Domain, Application, Infrastructure) y flujo de datos.
- **IDs ECLAI v3.0**: El sistema utiliza un identificador jerárquico único (J-ID) y narrativo (N-ID) para organizar la complejidad del mundo.

## 🧩 Características

- **Arquitectura Limpia**: Lógica de negocio independiente de Django.
- **Generación IA Local**: Privacidad total y control de costes.
- **Persistencia Híbrida**: Repositorios abstractos con implementación en SQLite.
- **Dashboard Interactivo**: Visualización de mundos y galería de arte generado.

## 🛠️ Tecnologías

- **Core**: Python 3.11
- **Web/DB**: Django 5.0
- **AI**: Llama 3, Stable Diffusion
- **Utils**: Pillow, Requests

---
*Proyecto desarrollado con enfoque en mantenibilidad y escalabilidad.*