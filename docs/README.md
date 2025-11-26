# 🪐 Fantasy World Generator v4.5 (CMS & AI-Powered)

> **Sistema de Gestión de Mundos Persistentes con Generación Procedural Asistida por IA**

![Status](https://img.shields.io/badge/Status-Active_Development-green)
![Python](https://img.shields.io/badge/Python-3.11.7-blue)
![Django](https://img.shields.io/badge/Django-5.0.1-092E20)
![Architecture](https://img.shields.io/badge/Architecture-Screaming_%2F_DDD-orange)
![AI](https://img.shields.io/badge/AI-Llama3_%2B_StableDiffusion-purple)

Este proyecto es una plataforma **CMS (Content Management System)** diseñada para arquitectos de mundos (Worldbuilders). A diferencia de wikis tradicionales, este sistema integra inteligencia artificial local para asistir en la creación de narrativa y arte conceptual, manteniendo un control estricto sobre la estructura de datos mediante IDs jerárquicos.

---

## ✨ Características Principales

### 🧠 Núcleo Inteligente
* **Arquitectura "Screaming":** El código está desacoplado del framework. La lógica de negocio vive en `src/FantasyWorld` y no sabe que Django existe.
* **IDs Jerárquicos (ECLAI v4.0):** Sistema de identificación único que define la posición espacial de cada entidad (ej. `01` Caos -> `0101` Abismo -> `010101` Región).
* **Metadatos Flexibles:** Almacenamiento de fichas técnicas (stats, biología, clima) en formato JSONB no relacional para máxima adaptabilidad.

### ⚖️ Gobierno de Datos (Workflow)
* **Sistema de Aprobación Estricto:** Los cambios nunca afectan al entorno "Live" directamente.
    * `Draft` (Borrador) -> `Proposal` (Propuesta vX) -> `Approval` (Aprobado) -> `Live` (Publicado).
* **Histórico Inmutable:** Cada cambio genera una versión. Al publicar, las versiones obsoletas se archivan automáticamente.
* **Auditoría:** Registro de autor, fecha y razón del cambio para cada modificación.

### 🎨 Motor de Generación IA (Local-First)
* **Pipeline de Arte Automatizado:**
    * Traducción automática de prompts (Español -> Inglés) usando Llama 3.
    * Inyección de estilos y *Negative Prompts* profesionales.
    * Gestión de Modelos en caliente (*Hot-Swap*): Carga modelos de criaturas o mapas según necesidad.
* **Narrativa Asistida:** Generación de descripciones y lore bajo demanda.

---

## 🛠️ Requisitos del Sistema

Este proyecto está diseñado para correr en local aprovechando hardware de gama alta (ej. RTX 4080 Super) para inferencia de IA.

* **Python:** 3.11.7 (Estrictamente recomendado).
* **Base de Datos:** SQLite (Default) / PostgreSQL (Compatible).
* **Servidores de IA (Externos):**
    * **Texto:** [Oobabooga Text-Generation-WebUI](https://github.com/oobabooga/text-generation-webui) con API activada.
    * **Imagen:** [Stable Diffusion WebUI (Automatic1111)](https://github.com/AUTOMATIC1111/stable-diffusion-webui) con API activada.

---

## ⚙️ Instalación y Puesta en Marcha

### 1. Configuración de IAs
Antes de iniciar el CMS, los motores de IA deben estar escuchando.

* **Llama 3 (Texto):**
    * Ejecutar en puerto **5000**.
    * Modelo recomendado: `Meta-Llama-3.1-8B-Instruct`.
* **Stable Diffusion (Imagen):**
    * Ejecutar en puerto **7861**.
    * Argumentos obligatorios en `webui-user.bat`:
        ```bat
        set COMMANDLINE_ARGS=--api --xformers --port 7861
        ```

### 2. Configuración del Proyecto
```powershell
# 1. Clonar el repositorio
git clone [https://github.com/Alonevs/FantasyWorld_ScreamingArch.git](https://github.com/Alonevs/FantasyWorld_ScreamingArch.git)
cd FantasyWorld_ScreamingArch

# 2. Crear y activar entorno virtual (Python 3.11)
py -3.11 -m venv venv
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar Base de Datos (Migraciones y Semilla)
python src/Infrastructure/DjangoFramework/manage.py migrate