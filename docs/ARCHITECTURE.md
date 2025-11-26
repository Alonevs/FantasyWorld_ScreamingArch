# 🏗️ Arquitectura del Sistema v4.5

Este proyecto sigue los principios de **Screaming Architecture** (Arquitectura que "Grita") y **Domain-Driven Design (DDD)**.

El objetivo es que la estructura del proyecto comunique claramente su propósito (*Gestión de Mundos de Fantasía*) en lugar de la herramienta que utiliza (*Django*).

## 📐 1. Principios de Diseño

La arquitectura invierte la dependencia tradicional: **El Framework (Django) es un detalle de implementación**, no el núcleo de la aplicación.

### Las Capas (Layers)

1.  **Domain (Dominio)** 🧠
    * **Ubicación:** `src/FantasyWorld/*/Domain/`
    * **Responsabilidad:** Contiene las reglas de negocio puras, entidades y lógica del universo (ej. reglas de ECLAI, Value Objects).
    * **Dependencias:** Cero. No conoce ni la base de datos ni la web.

2.  **Application (Aplicación)** ⚙️
    * **Ubicación:** `src/FantasyWorld/*/Application/`
    * **Responsabilidad:** Orquesta los **Casos de Uso**. Es el "director de orquesta" que recibe una orden (ej. "Crear Mundo", "Proponer Cambio") y llama a las piezas necesarias.
    * **Ejemplos:** `CreateWorldUseCase`, `ProposeChangeUseCase`, `PublishToLiveVersionUseCase`.

3.  **Infrastructure (Infraestructura)** 🔌
    * **Ubicación:** `src/Infrastructure/` y `src/*/Infrastructure/`
    * **Responsabilidad:** Implementaciones concretas de herramientas externas.
    * **Componentes:**
        * **DjangoFramework:** Se usa solo como motor web, ORM (Base de datos) y gestión de usuarios.
        * **Servicios IA:** Adaptadores (`sd_service.py`, `llama_service.py`) que hablan con las APIs locales.

---

## 💾 2. Diseño de Datos (Schema & Versioning)

El sistema implementa un patrón de **Gobierno de Datos** estricto para proteger la integridad del universo.

### A. Entidad "Mundo" (`CaosWorldORM`) - La Verdad Única
Representa el objeto en su estado **LIVE** (Público/Oficial). Es lo que ven los usuarios finales.
* **ID Estructural:** J-ID (`01`, `0101`) inmutable.
* **Metadata (JSON):** Campo flexible para almacenar datos técnicos (stats, biología, clima) sin alterar la tabla.
* **Punteros:** `id_lore` (Narrativa externa), `current_author`.

### B. Entidad "Versión" (`CaosVersionORM`) - El Historial
Representa la auditoría y el flujo de trabajo. Ningún cambio va directo al Live.
* **Estados:**
    * `PENDING`: Borrador o propuesta esperando revisión.
    * `APPROVED`: Revisado y listo, pero no publicado.
    * `LIVE`: La versión vigente actual.
    * `REJECTED`: Propuestas descartadas.
    * `ARCHIVED`: Versiones antiguas superadas por una nueva.

---

## 🤖 3. Pipeline de Inteligencia Artificial (v4.5)

El sistema utiliza un flujo avanzado de **IA Multimodal** en local.

### Generación de Arte (Stable Diffusion)
1.  **Input:** Descripción en Español + Nombre del Mundo.
2.  **Traducción & Prompting (Llama 3):** El sistema intercepta el texto, lo envía a Llama 3 para traducirlo al inglés y enriquecerlo con términos técnicos de arte.
3.  **Selección de Modelo (Hot-Swap):** El código decide qué modelo `.safetensors` cargar (ej. `revAnimated` para criaturas, `RPG_Maps` para terrenos) y ordena a la API cambiarlo en caliente.
4.  **Renderizado:** Se genera la imagen con *Negative Prompts* de calidad inyectados.
5.  **Almacenamiento:** Se guarda en `img/{ID}/{Nombre}_v{X}.png` para mantener un histórico limpio.

### Generación de Texto (Llama 3)
* **Modo Narrativo:** Escribe Lore basado en el nombre.
* **Modo Estructurado:** Genera JSONs válidos para rellenar la `metadata` de criaturas (Peligro, Dieta, Tamaño).

---

## 📂 4. Mapa del Código (`src/`)

```text
src/
├── FantasyWorld/               # Contexto Principal
│   ├── WorldManagement/        # Módulo: Gestión de Mundos
│   │   ├── Caos/               # Agregado Principal
│   │   │   ├── Application/    # Casos de Uso (Verbos: Create, Propose, Publish...)
│   │   │   ├── Domain/         # Entidades (Sustantivos)
│   │   │   └── Infrastructure/ # Adaptadores (DjangoRepository)
│   │   └── ...
│   └── AI_Generation/          # Módulo: Generación Procedural
│       ├── Domain/             # Interfaces (LoreGenerator, ImageGenerator)
│       └── Infrastructure/     # Implementaciones Reales (LlamaService, SDService)
│
├── Shared/                     # Núcleo Compartido (Kernel)
│   ├── Domain/
│   │   └── eclai_core.py       # Motor matemático de IDs Jerárquicos v3.0
│
└── Infrastructure/             # Infraestructura Global
    └── DjangoFramework/        # El Framework Web (aislado aquí)
        ├── config/             # settings.py, urls.py
        └── persistence/        # App de Django (Models, Views, Templates)