# 🏗️ Arquitectura del Sistema

Este proyecto sigue los principios de **Screaming Architecture** (Arquitectura que "Grita") y **Domain-Driven Design (DDD)**.

El objetivo es que la estructura del proyecto comunique claramente su propósito (*Gestión de Mundos de Fantasía*) en lugar de la herramienta que utiliza (*Django*).

## 📐 Principios de Diseño

La arquitectura invierte la dependencia tradicional: **El Framework (Django) es un detalle de implementación**, no el núcleo de la aplicación.

### Las Capas (Layers)

1.  **Domain (Dominio)** 🧠
    * **Ubicación:** `src/FantasyWorld/*/Domain/`
    * **Responsabilidad:** Contiene las reglas de negocio puras, entidades y lógica del universo (ej. reglas de ECLAI).
    * **Dependencias:** Cero. No conoce ni la base de datos ni la web.

2.  **Application (Aplicación)** ⚙️
    * **Ubicación:** `src/FantasyWorld/*/Application/`
    * **Responsabilidad:** Orquesta los **Casos de Uso**. Es el "director de orquesta" que recibe una orden (ej. "Crear Mundo") y llama a las piezas necesarias (Repositorio, IA, Entidad).
    * **Ejemplos:** `CreateWorldUseCase`, `ProposeChangeUseCase`.

3.  **Infrastructure (Infraestructura)** 🔌
    * **Ubicación:** `src/Infrastructure/` y `src/*/Infrastructure/`
    * **Responsabilidad:** Implementaciones concretas de herramientas externas.
    * **Componentes:**
        * **DjangoFramework:** Se usa solo como motor web y ORM (Base de datos).
        * **Servicios IA:** Adaptadores para hablar con Llama 3 y Stable Diffusion.

---

## 📂 Mapa del Código (`src/`)

```text
src/
├── FantasyWorld/               # Contexto Principal (Bounded Context)
│   ├── WorldManagement/        # Módulo: Gestión de Mundos
│   │   ├── Caos/               # Agregado Principal
│   │   │   ├── Application/    # Casos de Uso (Verbos: Create, Publish...)
│   │   │   ├── Domain/         # Entidades (Sustantivos: World, Version)
│   │   │   └── Infrastructure/ # Adaptadores (DjangoRepository)
│   │   └── ...
│   └── AI_Generation/          # Módulo: Generación Procedural
│       ├── Domain/             # Interfaces (LoreGenerator, ImageGenerator)
│       └── Infrastructure/     # Implementaciones Reales (LlamaService, SDService)
│
├── Shared/                     # Núcleo Compartido (Kernel)
│   ├── Domain/
│   │   └── eclai_core.py       # Motor de IDs Jerárquicos v3.0
│
└── Infrastructure/             # Infraestructura Global
    └── DjangoFramework/        # El Framework Web (aislado aquí)
        ├── config/             # settings.py, urls.py
        └── persistence/        # App de Django (Models, Views, Templates)
🔄 Flujo de Datos (Ejemplo: Crear Mundo)
Cuando un usuario pulsa "GENERAR" en la web:

Vista (Django): Recibe el POST HTTP.

Caso de Uso: La vista instancia CreateWorldUseCase y le pasa los datos.

Dominio: El caso de uso llama a eclai_core para calcular el ID 01.

Infraestructura:

Llama a Llama3Service para obtener el texto.

Llama a StableDiffusionService para obtener la imagen.

Llama a DjangoCaosRepository para guardar todo en db.sqlite3.

🤖 Integración de IA
El sistema utiliza un patrón de Puertos y Adaptadores para la IA. El Dominio solo conoce una interfaz (ImageGenerator), lo que nos permite cambiar Stable Diffusion por DALL-E o Midjourney en el futuro sin tocar la lógica de negocio, solo cambiando el archivo de infraestructura.


---

### 2. Archivo: `README.md` (Actualizado y Limpio)
*(Sobrescribe el que tienes en la raíz. Ahora es más ligero y apunta al de arquitectura).*

```markdown
# 📘 Fantasy World Generator v3.5

> **Screaming Architecture + CMS de Mundos + IA Generativa Local**

Plataforma avanzada para la creación, gestión y versionado de mundos de fantasía. Integra Inteligencia Artificial local para generar narrativa (Lore) y arte conceptual, todo bajo una arquitectura de software profesional y desacoplada.

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos
* **Python 3.11+**
* **Oobabooga (Texto):** Puerto 5000.
* **Stable Diffusion (Imagen):** Puerto 7861 (`--api --nowebui`).

### 2. Instalación
```powershell
# Clonar repositorio
git clone [https://github.com/Alonevs/FantasyWorld_ScreamingArch.git](https://github.com/Alonevs/FantasyWorld_ScreamingArch.git)

# Activar entorno
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
3. Ejecución
Panel de Control (Web):

PowerShell

python src/Infrastructure/DjangoFramework/manage.py runserver
📍 Acceder: http://127.0.0.1:8000/

📚 Documentación Técnica
Este proyecto no es un simple script de Django. Está diseñado para ser escalable y mantenible a largo plazo.

👉 LEER ARQUITECTURA DEL SISTEMA

Descubre por qué usamos Screaming Architecture.

Entiende la separación entre Dominio e Infraestructura.

Mapa de carpetas y flujo de datos.

✨ Funcionalidades
Gobierno de Datos: Sistema de aprobación de cambios (Draft -> Pending -> Approved -> Live).

Jerarquía ECLAI: IDs inteligentes que organizan el universo (Mundo 01 -> Abismo 0101).

Galería Dinámica: Generación de variaciones de arte y almacenamiento estructurado.

CMS Completo: Panel de administración personalizado con dashboard, vista previa y herramientas de moderación.

Desarrollado con Python 3.11.7 y Django 5.0.1