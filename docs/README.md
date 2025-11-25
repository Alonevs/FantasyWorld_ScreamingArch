# 📘 Fantasy World Generator v3.5

> **Screaming Architecture + CMS de Mundos + IA Generativa Local**

Este proyecto es un gestor de mundos de fantasía avanzado que desacopla la lógica de negocio del framework (Django), integrando un **CMS de gobierno de datos** (versiones, aprobación, publicación) y generación procedural de historias (Llama 3) y arte (Stable Diffusion).

---

## 🚀 Inicio Rápido

### Prerrequisitos
- **Python 3.11+** (Recomendado 3.11.7)
- **Servidores de IA** (Deben estar corriendo antes de iniciar):
  - **Texto**: Oobabooga Text-Generation-WebUI (Puerto 5000)
  - **Imagen**: Stable Diffusion WebUI (Puerto 7861, args: `--api --nowebui --xformers --port 7861`)

### Instalación y Ejecución

1.  **Activar Entorno Virtual**:
    ```powershell
    .\venv\Scripts\activate
    ```

2.  **Ejecutar Aplicación**:
    * **Modo Web (CMS Completo)**:
        ```powershell
        python src/Infrastructure/DjangoFramework/manage.py runserver
        ```
        Accede a: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

    * **Modo Consola (Test Rápido)**:
        ```powershell
        python main.py
        ```

---

## 🧩 Funcionalidades Clave (v3.5)

### 🌍 Gestión de Mundos & Jerarquía
* **Creación Recursiva:** Soporte para entidades padres (Mundo) e hijos (Abismos, Regiones).
* **IDs Inteligentes (ECLAI v3.0):** Cálculo automático de IDs jerárquicos (`01` -> `0101` -> `0102`).

### ⚖️ Sistema de Gobierno (CMS)
Flujo de trabajo profesional para proteger los datos "Live":
1.  **Propuestas:** Los cambios generan borradores (`PENDING`).
2.  **Centro de Control:** Panel Kanban para revisar, aprobar o rechazar cambios.
3.  **Modo Inspección:** Vista previa de la ficha con los datos propuestos antes de aprobar.
4.  **Publicación:** Despliegue controlado a producción (Live) con historial de autoría.

### 🎨 Arte y Narrativa (IA Local)
* **Lore Automático:** Llama 3 escribe descripciones temáticas.
* **Galería Dinámica:**
    * Generación de 4 variaciones iniciales.
    * Botón **[+ Foto]** para generar bajo demanda.
    * Organización de carpetas por ID (`img/01/`).

---

## 🏗️ Arquitectura del Proyecto

Este proyecto sigue los principios de **Screaming Architecture**. La estructura "grita" su propósito, no su framework.

### Estructura de Carpetas (`src/`)

* **`FantasyWorld/` (Dominio y Aplicación):**
    * `WorldManagement/`: Contiene los Casos de Uso (`CreateWorld`, `ProposeChange`, `ApproveVersion`, `PublishToLive`).
    * `AI_Generation/`: Interfaces agnósticas para conectar con IAs.
* **`Shared/` (Núcleo Común):**
    * `eclai_core.py`: Motor de IDs Jerárquicos ECLAI v3.0.
* **`Infrastructure/` (Implementación):**
    * `DjangoFramework/`: Implementación web y persistencia (ORM).
    * `sd_service.py`: Conector para Stable Diffusion.

---

## 📚 Documentación Adicional

- **[Arquitectura Detallada](docs/ARCHITECTURE.md)**: Explicación profunda del diseño DDD y flujo de datos.
- **[Manual de ECLAI](docs/ECLAI.md)**: Especificación técnica del sistema de identificación J-ID/N-ID.

---
*Proyecto desarrollado con enfoque en mantenibilidad, escalabilidad y soberanía de datos (Local First).*