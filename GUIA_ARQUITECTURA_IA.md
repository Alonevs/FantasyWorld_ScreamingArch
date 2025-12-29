# 🗺️ Mapa del Sistema (Guía para IAs)

Esta guía sirve para que cualquier IA asistente entienda la arquitectura del proyecto y no duplique datos, cambie nombres o pierda el contexto de las asociaciones actuales.

## 🏗️ Estructura de Directorios Principal

-   `src/Infrastructure/DjangoFramework/persistence/`: **Núcleo del Backend**.
    -   `models.py`: Definición de modelos ORM (Base de Datos).
    -   `views/`: Lógica de controladores, dividida por funciones (`world_views.py`, `media_views.py`, `narrative_views.py`, `period_api.py`).
    -   `templates/`: HTML (Frontend). `ficha_mundo.html` es el centro de mando.
    -   `static/persistence/img/`: Almacén físico de imágenes organizado por `jid` (ID de entidad).
-   `src/WorldManagement/Caos/`: **Lógica de Dominio y Aplicación**.
    -   `Application/`: Casos de uso (ej: `GetWorldDetailsUseCase`).
    -   `Infrastructure/django_repository.py`: Adaptador que conecta la lógica con la base de datos.
-   `src/Shared/Services/`: Servicios compartidos, como `TimelinePeriodService`.

## 💾 Modelos Críticos (ORM)

1.  **`CaosWorldORM`**: La entidad principal (Mundo, Ciudad, etc.).
2.  **`TimelinePeriod`**: Representa una era histórica de un mundo. Tiene un `slug`.
3.  **`CaosNarrativeORM`**: Documentos de lore. Tienen un `timeline_period` (FK).
4.  **`CaosImageProposalORM`**: Propuestas de imágenes. Tienen un `timeline_period` (FK).
5.  **`CaosVersionORM`**: Versiones del mundo (Live, Timeline, etc.).

## 🎞️ El Nuevo Sistema de Periodos (Timeline)

-   **Contexto**: El sistema ya no usa años numéricos fijos, sino nombres de periodos (ej: "Era de los Mitos").
-   **Navegación**: Se controla mediante el parámetro `?period=[slug]` en la URL.
-   **Almacenamiento de Fotos**: Las fotos físicas están en disco, pero sus metadatos (autor, título, periodo) están en `world.metadata['gallery_log']`.
-   **Filtrado de Contenido**: El helper `get_world_images` y los casos de uso de narrativa filtran automáticamente según el periodo activo.

## ⚠️ Reglas de Oro para IAs

-   **No Duplicar**: Antes de crear un campo nuevo, revisa `models.py`. Casi todo el dinamismo se maneja con `metadata` (JSONB) o FKs de periodo.
-   **Nombres de Archivos**: Al guardar imágenes, usa `repo.save_manual_file`. No manipules el sistema de archivos directamente si puedes evitarlo.
-   **Contexto de Periodo**: Si vas a modificar una vista, asegúrate de pasar o recibir el `current_period_slug` para no perder la coherencia temporal.
-   **Permisos**: Usa siempre `check_ownership` de `permissions.py` antes de permitir ediciones.

## 🔗 Vinculaciones Importantes

-   `CaosNarrativeORM` -> `world` (FK) + `timeline_period` (FK).
-   `CaosImageProposalORM` -> `world` (FK) + `timeline_period` (FK).
-   `TimelinePeriod` -> `world` (FK).
