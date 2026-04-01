# 🗺️ Roadmap: Sistema de Geografía Robustez 10K (ECLAI v0.1)

Este documento define la arquitectura conceptual para la gestión de espacio y tiempo en FantasyWorld, diseñada para ser escalable, evitar colisiones y permitir un crecimiento modular desde un mundo vacío.

## 1. El Sistema de Coordenadas Maestro (Aislado por Planeta)
Utilizaremos un sistema de **Unidades de Caos (UAC)** en una rejilla bidimensional:
- **Escala:** 0 a 10,000 para X e Y.
- **Ámbito (Scope):** Las coordenadas son relativas a una **Entidad de Nivel 6 (Planeta)**. Cada planeta tiene su propio "lienzo" y su propia "semilla" (seed) de generación.
- **Escalabilidad:** Cada unidad de 1x1 puede dividirse en sub-rejillas de 1,000x1,000 en el futuro si se requiere un nivel de detalle "microscópico" (ej: planos de edificios) sin romper las coordenadas globales.

## 2. Dimensiones Especiales (Inframundo y Bendecidos)
Para dimensiones que no son planetas esféricos tradicionales:
- **Inframundo:** Estructura por **Capas (Layers)**. Cada capa tiene su propia semilla de generación y su propio mapa de 10K.
- **Los Bendecidos:** Estructura por **Plataformas (Platforms)** suspendidas. Cada plataforma es una entidad independiente con su propia semilla.
- **Representación Visual:** Aunque el espacio de datos es plano/cuadrado (0-10,000), el Atlas permitirá una **Visualización Circular (Proyección Polar)** para representar estas dimensiones de forma concéntrica.

## 3. Capas Temporales (Mapas por Época)
Cada **Época (CaosEpochORM)** mantiene su propio estado del mapa para permitir la evolución histórica:
- **Herencia Progresiva:** Al crear una nueva Época, el sistema puede "heredar" el mapa de la era anterior como base.
- **Evolución Visual:** Un usuario puede pintar cambios en la Era 2 (ej: un volcán que nace) sin alterar el mapa de la Era 1.
- **Validación de Ocupación:** El servicio de colisiones solo chequeará entidades que coexistan en la **misma Época** y el mismo **Planeta/Dimensión**.

## 4. Lógica de Ocupación (Bounding Boxes)
Para evitar el "caos geográfico", cada entidad de nivel superior (Continentes, Regiones) debe declarar su **Caja de Influencia**:
- **Metadata:** `{ "geo_bounds": { "minX": 4000, "minY": 7000, "maxX": 6000, "maxY": 9000 } }`
- **Bloqueo Histórico:** El bloqueo es relativo a la Época activa. Si una ciudad es destruida en el Año 100, la zona queda libre para el Año 150.

## 5. Clasificación de Sustrato y Orografía
Se añade un flag visual y lógico para determinar la naturaleza del terreno:
- **Tierra Firme:** Permite asentamientos, biomas terrestres y orografía.
- **Masa de Agua:** Permite rutas navales, biomas marinos y abismos.
- **Accidentes:** Capa de iconos (Montañas, Ríos, Lagos) que definen las "limitaciones del terreno".

## 6. Visualización (El Atlas de Control)
Se implementará una vista de **Atlas Estratégico** que renderizará estas capas temporales sobre un lienzo SVG, permitiendo ver la evolución del mundo al cambiar de época.

---
*Este documento sirve como base para la implementación técnica en la versión v0.2.*
