# 🗺️ ESPECIFICACIÓN TÉCNICA: NIVEL 7 (HEMISFERIOS) v1.0

> **Estado:** Pendiente de Implementación (Backend & Frontend).
> **Objetivo:** Dividir Planetas (Nivel 6) en contenedores climáticos lógicos para herencia de datos.

---

## 1. Arquitectura de División (Opción 1: Geográfica)

Se establece que todo Planeta (Nivel 6) se dividirá en **2 entidades hijas fijas** (Nivel 7):

| Entidad | Sufijo J-ID | Concepto Físico | Regla Estacional |
| :--- | :---: | :--- | :--- |
| **Hemisferio Norte** | `...01` | Latitud 0° a 90° | Verano en Junio / Invierno en Diciembre |
| **Hemisferio Sur** | `...02` | Latitud -90° a 0° | Invierno en Junio / Verano en Diciembre |

> **Nota:** Los ID son fijos. No se generan secuencialmente (03, 04...), son espacios reservados.

---

## 2. Sistema de "Franjas Climáticas" (Slots)

Para evitar coordenadas GPS complejas, los Hemisferios actúan como contenedores de **3 Franjas (Slots)**.
Al crear un hijo (Continente/Región), se le asignará una de estas etiquetas en su metadata para heredar el clima automáticamente.

### Las 3 Franjas de Herencia:

1.  **`EQUATORIAL` (Ecuador):**
    * **Clima Base:** Cálido, Húmedo/Seco extremo.
    * **Estaciones:** Débiles o inexistentes (Eterna primavera/verano).
    * **Biomas probables:** Selva, Sabana, Desierto.

2.  **`TEMPERATE` (Zona Templada):**
    * **Clima Base:** Moderado.
    * **Estaciones:** 4 estaciones marcadas (Ciclo completo).
    * **Biomas probables:** Bosque, Pradera, Montaña habitable.

3.  **`POLAR` (Zona Polar):**
    * **Clima Base:** Gélido.
    * **Estaciones:** Días/Noches extremos (Sol de medianoche).
    * **Biomas probables:** Tundra, Glaciar, Taiga.

---

## 3. Estructura de Datos (JSONB Metadata)

Cuando implementemos el código, el Hemisferio debe guardarse con esta estructura en la BD:

```json
{
  "tipo_entidad": "HEMISFERIO",
  "geo_config": {
    "posicion": "NORTE", // o "SUR"
    "rango_latitud": [0, 90],
    "polo_magnetico": true
  },
  "reglas_clima": {
    "invertir_estaciones": false, // true para el Sur
    "gradiente_temperatura": "NORMAL" // Calor en Ecuador -> Frío en Polo
  }
}