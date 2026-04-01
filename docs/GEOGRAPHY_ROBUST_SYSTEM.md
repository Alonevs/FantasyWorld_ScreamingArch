# 🗺️ Roadmap: Sistema de Geografía Robustez 10K (ECLAI v0.1)

Este documento define la arquitectura conceptual para la gestión de espacio y tiempo en FantasyWorld, diseñada para ser escalable, evitar colisiones y permitir un crecimiento modular desde un mundo vacío.

## 1. El Sistema de Coordenadas Maestro
Utilizaremos un sistema de **Unidades de Caos (UAC)** en una rejilla bidimensional:
- **Escala:** 0 a 10,000 para X e Y.
- **Centro (Ecuador/Meridiano):** (5,000, 5,000).
- **Escalabilidad:** Cada unidad de 1x1 puede dividirse en sub-rejillas de 1,000x1,000 en el futuro si se requiere un nivel de detalle "microscópico" (ej: planos de edificios) sin romper las coordenadas globales.

## 2. División en 4 Cuadrantes (Jerarquía Nivel 7)
El globo se divide en 4 grandes zonas administrativas para la IA:
1. **Boreal Oeste (NW):** [0-5000, 0-5000]
2. **Boreal Este (NE):** [5001-10000, 0-5000]
3. **Austral Oeste (SW):** [0-5000, 5001-10000]
4. **Austral Este (SE):** [5001-10000, 5001-10000]

## 3. Lógica de Ocupación (Bounding Boxes)
Para evitar el "caos geográfico", cada entidad de nivel superior (Continentes, Regiones) debe declarar su **Caja de Influencia**:
- **Metadata:** `{ "geo_bounds": { "minX": 4000, "minY": 7000, "maxX": 6000, "maxY": 9000 } }`
- **Tolerancia:** El sistema bloqueará la creación de entidades que solapen sustancialmente con estas cajas en la misma Época.
- **Excepción Temporal:** El bloqueo es relativo al `CaosEpochORM`. La ocupación puede cambiar entre eras (un continente que se hunde libera su espacio).

## 4. Clasificación de Sustrato (Tierra vs Agua)
Se añade un flag visual y lógico para determinar la naturaleza del terreno:
- **Tierra Firme:** Permite asentamientos, biomas terrestres y orografía.
- **Masa de Agua (Océanos/Mares):** Permite rutas navales, biomas marinos y abismos.
- **Vacío/Desconocido:** El estado por defecto (ahorro de recursos).

## 5. Visualización (El Atlas de Control)
Se implementará una vista de **Atlas Estratégico** que renderizará estas cajas y puntos sobre un lienzo SVG, permitiendo al administrador (tú) ver los "huecos libres" del mundo de forma intuitiva.

---
*Este documento sirve como base para la implementación técnica en la versión v0.2.*
