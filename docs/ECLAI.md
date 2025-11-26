# 🆔 ECLAI v4.0 Specification

> **Enhanced Code for Logical and Architectural Identification**
> *Versión 4.0 - Paradigma Espacial Puro*

ECLAI es el sistema de identificación central del proyecto. A diferencia de los IDs autoincrementales tradicionales (1, 2, 3...), ECLAI utiliza **IDs semánticos y jerárquicos** que permiten conocer la ubicación exacta de una entidad en el multiverso solo mirando su código.

---

## 1. Filosofía v4.0: Separación Espacio-Tiempo

En versiones anteriores (v3.0), el tiempo (Épocas) era parte de la jerarquía. En la v4.0 se ha desacoplado para permitir la persistencia de entidades a través del tiempo.

* **J-ID (Espacial):** Define **QUÉ** es y **DÓNDE** está. Es inmutable. (Ej: El Planeta Tierra siempre es el mismo objeto físico).
* **Epoch (Temporal):** Define **CUÁNDO** existe. Es un metadato relacional.

---

## 2. J-ID (Jerarquía Espacial)

El J-ID es un string numérico de longitud variable. Cada nivel añade **2 dígitos** al ID de su padre.

### Algoritmo de Generación
`ID_HIJO = ID_PADRE + DIGITOS_HIJO`

### Tabla de Niveles (Revisión Espacial)

| Nivel | Longitud | Nombre | Ejemplo | Significado |
| :--- | :---: | :--- | :--- | :--- |
| **1** | 2 | **Caos Prime** | `01` | La raíz de todo. |
| **2** | 4 | **Abismo** | `0101` | Divisiones primordiales. |
| **3** | 6 | **Realidad** | `010102` | Planos de existencia. |
| **4** | 8 | **Galaxia** | `01010205` | Cúmulos estelares (*Antes era Época*). |
| **5** | 10 | **Sistema** | `...01` | Sistema Solar/Estelar. |
| **6** | 12 | **Planeta** | `...03` | Cuerpo celeste. |
| **7** | 14 | **Hemisferio** | `...01` | División geográfica grande. |
| **8** | 16 | **Continente** | `...04` | Masa de tierra. |
| **9** | 18 | **Territorio** | `...02` | Reino / País. |
| **...** | ... | ... | ... | ... |
| **16** | 34 | **Entidad** | `...99` | Objeto/Ser específico (Nivel Atómico). |

---

## 3. N-ID (Narrative ID)

El **N-ID** conecta una entidad espacial (J-ID) con su contenido narrativo (Lore). Permite tener múltiples textos asociados a un mismo lugar.

### Formato
`[J-ID] + [TIPO] + [NUMERO] + [CAPITULO?]`

### Tipos de Contenido
| Código | Tipo | Descripción |
| :---: | :--- | :--- |
| **L** | Lore | Historia general, descripción, mitología. |
| **H** | Historia | Narrativa secuencial (Novela/Cuento). Admite Capítulos (`C01`). |
| **R** | Regla | Leyes físicas, mágicas o sistemas de juego. |
| **E** | Evento | Sucesos históricos (Guerras, Cataclismos). |
| **N** | NPC | Personajes no jugadores vinculados al lugar. |

### Ejemplo
* **Lugar:** `0101` (Abismo de Fuego).
* **Lore:** `0101L01` (Descripción del Abismo).
* **Evento:** `0101E05` (La Batalla de la Llama Eterna).

---

## 4. Codificación (Base62)

Para uso en URLs o referencias cortas, el sistema utiliza una codificación Base62 personalizada.

* **Alfabeto:** `AEIOUaeiouBCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz0123456789`
* **Objetivo:** Comprimir IDs largos en códigos legibles y cortos.

### Conversión
* **J-ID:** `01` -> **Code:** `OD9`
* **J-ID:** `010103` -> **Code:** `2qX` (Ejemplo)

---

## 5. Gestión Temporal (Épocas)

El tiempo ya no está en el ID. Se gestiona mediante relaciones en la Base de Datos.

* **Campo `born_in_epoch`:** Indica en qué Era se creó la entidad.
* **Campo `died_in_epoch`:** (Opcional) Indica cuándo dejó de existir.

**Ejemplo de Lógica:**
Si estamos visualizando la **Época 5**, el sistema mostrará:
1.  Entidades creadas en la Época 5.
2.  Entidades creadas en Épocas 1-4 que **NO** hayan muerto antes de la 5.