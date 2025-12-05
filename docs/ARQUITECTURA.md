# Guía de Arquitectura: Screaming Architecture + Django

## 🏗️ Filosofía
Este proyecto sigue el principio de **Screaming Architecture** (Arquitectura que "Grita"). La idea central es que la estructura de directorios debe comunicar claramente qué *hace* la aplicación (el dominio), en lugar de qué framework utiliza.

En nuestro caso, el dominio es **Gestión de Mundos (WorldManagement)**, y el detalle de implementación es **Django**.

## 📂 Estructura de Directorios

### `src/WorldManagement` (El Núcleo / Dominio)
Contiene la lógica de negocio pura. Debe ser agnóstico del framework (en la medida de lo posible).
-   **Domain/**: Entidades puras (`World`, `Narrative`) y Objetos de Valor. Reglas de negocio.
-   **Application/**: Casos de Uso (`CreateWorld`, `ProposeChange`). Orquestan el flujo de datos.
-   **Infrastructure/**: Implementaciones de contratos definidos en Domain (ej. Repositorios que usan Django ORM).

### `src/Infrastructure/DjangoFramework` (El Detalle)
Contiene todo lo específico de Django.
-   **config/**: `settings.py`, `urls.py`.
-   **persistence/**: Modelos ORM (`CaosWorldORM`), Vistas, Templates. Actúa como la capa de persistencia y presentación.

## 🔄 Flujo de Datos
1.  **Vista (View)**: Recibe la petición HTTP.
2.  **Caso de Uso (Use Case)**: La vista invoca un Caso de Uso (ej. `CreateWorldUseCase`).
3.  **Repositorio**: El Caso de Uso interactúa con una interfaz de repositorio.
4.  **ORM**: La implementación del repositorio usa Django ORM para guardar/leer SQL.
5.  **Entidad**: Los datos regresan convertidos en Entidades de Dominio, no modelos de Django.

## 🧩 Patrones Clave
-   **Repositorio**: Desacopla el dominio de la base de datos.
-   **Aprobación Estricta**: Usamos `CaosVersionORM`. Ningún cambio va a "LIVE" directamente. Todo pasa por `Propuesta -> Aprobación`.
-   **Dual-Write**: Al aprobar, los datos se copian de la Versión a la Entidad Live.
