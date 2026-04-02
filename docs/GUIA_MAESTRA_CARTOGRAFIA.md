# Guía Maestra de Cartografía y Geolocalización

Este documento sirve como el plano arquitectónico y teórico para el desarrollo del **Sistema GIS de FantasyWorld**. No escribiremos código de producción hasta que todas y cada una de las mecánicas descritas aquí estén 100% aprobadas y pulidas. 

El modelo geográfico de la aplicación abandona la "creación ciega a través de formularios" y adopta un modelo visual georreferenciado estilo *Google Maps*, escalando de Planeta a Habitación.

---

## 1. El Pilar: El Modelo Poligonal (Vectorial)
Toda ubicación física es obligatoriamente un **Polígono** o **Vector**.
*   **Procedimiento:** A través de un lienzo interactivo, el usuario hace clics conformando "puntos" (`[X, Y]`). Al unir el primer punto con el último, se "cierra el área".
*   **Escalabilidad:** Al ser cálculos matemáticos y no matrices de píxeles, permitirán hacer un *zoom-in* infinito cuando proyectemos en un motor 3D (Globo) o en motores de dibujo 2D, manteniendo bordes perfectos.

## 2. Paradigma "Atlas-First" (Jerarquía Inviolable)
Para evitar paradojas temporales o de ubicación (Ej: *Un país solitario flotando en la nada*), la creación de entidades físicas está supeditada al mapa.

1.  **Imposibilidad Huérfana:** Estará prohíbo bajar a un Nivel (ej. `País`) para generar geografía si el `Continente` por encima de él no existe y no está delimitado físicamente.
2.  **Candado de Profundidad (Bloqueo Descendente):** Una vez que bajas un nivel jerárquico (de `Continente` a `País`), las herramientas de trazado adaptan su escala.

---

## 3. Jerarquía Maestra de Niveles (J-ID)

El sistema utiliza una arquitectura de **16 niveles de profundidad**. Esta estructura permite que el "sentido común" del mundo se herede de arriba hacia abajo.

| Nivel | Nombre del Nivel | Función Narrativa / Cartográfica | Estado |
| :--- | :--- | :--- | :--- |
| **01** | **CAOS** | Raíz absoluta del motor. | Activo |
| **02** | **ABISMO** | Gestación de conceptos universales. | Activo |
| **03** | **UNIVERSO** | Nivel astronómico superior. | Reserva |
| **04** | **GALAXIA** | Agrupación de sistemas estelares. | Reserva |
| **05** | **SISTEMA** | Sistema solar (Sol y planetas). | Reserva |
| **06** | **PLANETA** | **Pilar Geofísico:** Astronomía, clima base, lunas. | **Fase 1** |
| **07** | **CONTINENTE** | **Pilar Geográfico:** Masas de tierra y fallas tectónicas. | **Fase 2** |
| **08** | **PAÍS / REINO** | **Pilar Político:** Esferas de autoridad y cultura. | **Fase 3** |
| **09** | **REGIÓN NATURAL** | **Pilar Ecológico:** Biomas (Bosques, Pantanos). | **Fase 4** |
| **10** | **ASENTAMIENTO** | **Pilar Urbano:** Ciudades, Castillos, Aldeas. | **Fase 4** |
| **11** | **LOCALIZACIÓN** | **Capa Adaptativa:** Distritos o Hitos (Cuevas). | **Fase 4** |
| **12** | **CAT. BIOLÓGICA** | Transición hacia la taxonomía de vida. | Reserva |
| **13** | **RAZA / ESPECIE** | Biología, rasgos raciales, adaptaciones. | Reserva |
| **14** | **CLASES / ROLES** | Arquetipos de magia y combate (Edad Media). | Reserva |
| **15** | **ESTADO INDIV.** | Perfiles técnicos de personajes. | Reserva |
| **16** | **PERSONAJE** | El individuo único (Héroe, Villano, Rey). | Reserva |

### 3.1. Racional de los Niveles 09-11 (Inheritance Flow)
*   **Naturaleza antes que Civ (9 > 10):** Un bosque existía antes que la ciudad. Al ser el Bioma (9) padre del Asentamiento (10), la ciudad hereda automáticamente el clima, humedad y peligros del entorno.
*   **Capa Adaptativa (11):** Es el zoom final. Si el padre es ciudad, el 11 son barrios. Si el padre es montaña, el 11 son cuevas. Simplifica la base de datos eliminando niveles redundantes.

---

## 4. Lógica del "Espacio Negativo" y Velo Elemental
Evitaremos forzar al usuario a dibujar el 100% del globo.
1.  **El Velo Base:** El espacio no dibujado hereda el "Elemento Dominante" del Planeta (ej: Agua).
2.  **Inferencia Térmica:** El Eje Y (Latitud) actúa como multiplicador sobre la temperatura base del planeta (Ecuador = Calor / Polos = Frío).

---

## 5. PROTOCOLO DE CREACIÓN: Paso a Paso por Niveles

A continuación se detalla el flujo de trabajo exacto para construir geografía coherente:

### FASE 1: El Planeta (Nivel 6) - "La Semilla"
1.  **Wizard de Creación:** Un formulario de dos pasos:
    *   *Paso 1 (Narrativa):* Nombre, mitos, breve descripción.
    *   *Paso 2 (Físicas):* Temperatura (Helado/Templado/Volcánico), Inclinación Axial, Lunas (cantidad y nombres), Elemento del Velo (Agua/Lava/Vacío).
2.  **Persistencia:** Guardado en `metadata.planet_laws` (Django JSONB). Se autogenera la **Era 0 (Génesis)**.

### FASE 2: Los Continentes (Nivel 7) - "Las Placas"
1.  **Sincronización entre Hermanos:** Los continentes no pueden solaparse (Bloqueo de colisión).
2.  **Snapping Tectónico:** La herramienta de dibujo permite imantar bordes entre continentes adyacentes para crear fallas, istmos o cordilleras de colisión.
3.  **Coherencia Térmica:** Dos continentes en la misma latitud compartirán el mismo clima base por defecto.

### FASE 3: Esferas de Autoridad y Reinos (Nivel 8) - "El Poder"
1.  **Territorios Contextuales:** Capacidad de delimitar zonas sin fronteras estrictas (ej: "Llanuras del Este: Hogar Ancestral de Humanos").
2.  **Semillas de Soberanía:** Marcar áreas que en eras futuras se convertirán en imperios.
3.  **Fricción Política:** Al solapar una esfera de autoridad con otra, el sistema inyecta metadatos de "Zona de Conflicto" automáticamente.

### FASE 4: Micro-Cartografía (Niveles 9-11) - "El Detalle"
1.  **Biomas y Áreas Naturales (9):** Dibujo de Bosques, Pantanos, Desiertos. Definen el ecosistema.
2.  **Asentamientos y POIs (10):** Colocación de Ciudades, Castillos, Monasterios o Aldeas medievales.
3.  **Localizaciones Adaptativas (11):**
    *   En Ciudades: Distritos, Armerías, Plazas, Mercados.
    *   En Naturaleza: Cuevas, Ruinas, Minas, Hitos mágicos.
4.  **Atributos de Estado:** `[Próspero | Ruinas | Bajo Asedio]`. La IA usará esto para el lore.

---

## 6. SISTEMAS TRANSVERSALES (Tiempo y Evolución)

### A. El Mapamundi por Eras (Timeline Atlas)
La cartografía es un registro histórico vivo.
1.  **Deltas de Cambio:** Cada Era permite modificar la geografía existente (ej: un bosque que desaparece por un incendio).
2.  **Registro de Sucesos:** Cada edición genera un log (ej: "Capital destruida en Era 5"). La IA usará esto para narrar la historia del mundo.
3.  **Filtrado Temporal:** Cada elemento tiene un rango `valid_from` / `valid_to`. Al mover el slider de eras, los elementos nacen o mueren visualmente.

### B. Memoria del Lugar (Narrative Overlays)
En cualquier nivel se pueden anclar "Susurros" (Post-its invisibles) con hechos históricos que la IA usará para generar misiones.

---

## 7. EL MOTOR CLIMÁTICO HEREDITARIO (Inferencia para IA)

Para que la IA cree criaturas coherentes, el clima se calcula por agregación:
1.  **Capa 1 (Planeta):** Temperatura base inamovible (Ej: Planeta Térmico).
2.  **Capa 2 (Latitud):** El sistema suma/resta calor según la posición Y en el Atlas.
3.  **Capa 3 (Región):** El usuario añade "Etiquetas de Sensación": `[Gélido | Seco | Empapado | Niebla | Azufre]`.

**Resultado:** La IA recibe un prompt consolidado: *"Esta criatura vive en un bosque empapado, de temperatura fresca, bajo la luz de 3 lunas en un planeta volcánico"*.

---

## 8. RECURSOS Y STACK TECNOLÓGICO

1.  **Dibujo:** SVG (Vectores matemáticos para zoom infinito).
2.  **Datos:** GeoJSON (Estándar mundial, fácil de leer para IA).
3.  **Cálculos:** `Turf.js` (Validación de colisiones y "punto en polígono").
4.  **Backend:** Django (Gestión de J-ID y lógica de herencia en campos JSONB).

---

## 13. GUÍA DE IMPLEMENTACIÓN Y PRUEBAS POR NIVELES

Este protocolo define el orden de ejecución técnica y las pruebas necesarias antes de certificar cada fase como "Completada".

### FASE 1: El Despertar del Mundo (Nivel 6 - Planeta)
**Pasos Técnicos:**
1.  **ORM:** Extender el uso del campo `metadata` en `CaosWorldORM` para validar el esquema `planet_laws`.
2.  **Frontend:** Crear el `PlanetCreationWizard` (Modal en 2 pasos).
3.  **Lógica:** Implementar el "Generador de Era 0" automático tras el éxito del Wizard.
**Pruebas de Nivel:**
*   [ ] **Manual:** Crear un planeta con 3 lunas y temperatura "Helada". Verificar que el fondo del Atlas sea azul/blanco (según el velo).
*   [ ] **Inferencia:** Verificar que al consultar la API, el campo `visible_in_atlas` sea True.

### FASE 2: La Danza Tectónica (Nivel 7 - Continente)
**Pasos Técnicos:**
1.  **SVG Canvas:** Inicializar la herramienta de trazado poligonal sobre el Velo del Planeta.
2.  **Turf.js:** Implementar el validador de `booleanDisjoint` para evitar solapamientos entre continentes hermanos.
3.  **Snapping:** Activar imantación de vértices en el trazado de bordes.
**Pruebas de Nivel:**
*   [ ] **Topológica:** Intentar dibujar un continente sobre otro. El sistema debe denegar el guardado.
*   [ ] **Climática:** Dibujar un continente en el polo sur. La IA debe recibir automáticamente el tag `temp_feel: "Gélida"`.

### FASE 3: El Velo de la Historia (Nivel 8 - Autoridad/Reinos)
**Pasos Técnicos:**
1.  **Capa Contextual:** Implementar el toggle de "Soberanía Narrativa" (áreas sin fronteras).
2.  **Motor de Fricción:** Lógica de detección de solapamiento entre esferas de autoridad distintas.
**Pruebas de Nivel:**
*   [ ] **Sucesión:** Crear una Era 2 y heredar los países de la Era 1. Modificar una frontera y verificar que la Era 1 se mantiene intacta.
*   [ ] **Lore:** Poner un reino humano sobre un hogar ancestral elfo. Verificar que el prompt de la IA incluye: "Zona de fricción histórica".

### FASE 4: La Vida en el Detalle (Niveles 9-11 - Micro)
**Pasos Técnicos:**
1.  **Asignación Hereditaria:** Función `inherit_parent_metadata()` que inyecta el clima del Bioma (9) en el Asentamiento (10).
2.  **Nivel 11 Adaptativo:** Switch lógico en el formulario de creación: `if parent.level == 10: show_district_fields() else: show_location_fields()`.
**Pruebas de Nivel:**
*   [ ] **Inferencia:** Crear un "Pantano" (9) y una "Ciudad" (10) dentro. Verificar que la IA describe la ciudad como "Húmeda y rodeada de aguas estancadas".
*   [ ] **Lógica Detalle:** Crear una "Cueva" dentro de una "Montaña" (Nivel 9 -> 11). Verificar que el J-ID es válido.

---

## 14. ROADMAP Y FUTURO
1.  **Cálculo de Recursos:** Inferencia de % de recursos según biomas dibujados.
2.  **Meteorología Dinámica:** Cambios visuales en el Atlas según la era (inviernos que cubren de blanco los países).
3.  **Visor 3D:** Proyección de los vectores GeoJSON sobre el globo `Globe.gl`.
