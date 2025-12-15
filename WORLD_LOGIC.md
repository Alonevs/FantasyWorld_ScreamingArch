# Arquitectura del Sistema: Auto-Noos Worldbuilder

## 1. Lógica del Identificador Jerárquico (J-ID)

El sistema utiliza un **Identificador Jerárquico (J-ID)** basado en strings numéricos para modelar la posición de una entidad dentro del universo.

*   **Estructura:** Pares de dígitos (00-99) concatenados.
*   **Fórmula de Nivel:** `Nivel = len(J-ID) // 2`.
*   **Ejemplo:** `010103` (Longitud 6) -> Nivel 3.

### Estrategia de Relleno (Padding)
Para permitir que una entidad de nivel superior contenga directamente a una de nivel muy inferior (ej: Un Dios creando un Planeta, saltando Galaxia/Sistema), usamos **Zero Padding**.

*   **Regla:** Se rellenan los niveles intermedios con `00`.
*   **Ejemplo:** Nivel 3 (Universo) crea hijo en Nivel 6 (Planeta).
    *   Padre: `010101`
    *   Salto: Niveles 4 y 5 vacíos.
    *   Hijo: `010101` + `00` (Nivel 4) + `00` (Nivel 5) + `01` (Nivel 6).
    *   J-ID Final: `010101000001`.

## 2. Tabla de Niveles

La jerarquía define 14 niveles estándar (extendidos a 16 para Entidades/Personajes).

| Nivel | J-ID Len | Nombre (Física) | Nombre (Dimensional) | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| **01** | 2 | **CAOS PRIME** | CAOS PRIME | La raíz de todo. |
| **02** | 4 | ABISMO / GESTACIÓN | ABISMO | El caldo de cultivo previo a la existencia. |
| **03** | 6 | UNIVERSO | PLANO MAYOR | Contenedor principal de la realidad. |
| **04** | 8 | GALAXIA | DOMINIO | Agrupación masiva de sistemas/estructuras. |
| **05** | 10 | SISTEMA | ESTRUCTURA | Sistema solar o estructura dimensional compleja. |
| **06** | 12 | **PLANETA** | CAPA / CÍRCULO | Unidad principal de habitación. |
| **07** | 14 | CONTINENTE | SECTOR DIM. | Gran división geográfica/espacial. |
| **08** | 16 | PAÍS | ÁREA | División política o regional mayor. |
| **09** | 18 | CIUDAD | ASENTAMIENTO | Núcleo poblacional o base. |
| **10** | 20 | DISTRITO | - | División urbana. |
| **11** | 22 | LUGAR | - | Localización específica (Edificio, Parque). |
| **13** | 26 | RAZA/ESPECIE | ESPECIE ASTRAL | Definición biológica o metafísica. |
| **13***| 26 | **OBJETO** | ARTEFACTO | *Si el par es 90-99 (ej: ...90).* |
| **16** | 30 | **PERSONAJE** | ENTIDAD | Individuo concreto. (Salto de longitud 4 chars). |

**Nota sobre Nivel 16:** A diferencia de los demás, el último salto para personajes individualizados añade 4 dígitos para permitir mayor cardinalidad (0000-9999).

## 3. Flujo de Borrado (Soft Delete)

Para garantizar la integridad referencial y la trazabilidad, **NO se destruyen registros** de entidades vivas.

1.  **Acción:** Usuario solicita borrar Mundo/Narrativa.
2.  **Estado:** Se marca `is_active = False` y se fecha `deleted_at`.
3.  **Visibilidad:** Desaparece de las vistas normales y del árbol.
4.  **Papelera:** Aparece en la vista "Papelera de Reciclaje".
5.  **Restauración:**
    *   Se crea una **Propuesta de Restauración** (Versión `RESTORE`).
    *   Un administrador debe aprobarla en el Dashboard.
    *   Al aprobarse, se marca `is_active = True`.

*Excepción:* Las "Propuestas" (Versiones en borrador) sí pueden eliminarse definitivamente.

## 4. Estructura de Metadatos V3

El campo `metadata` (JSON) es el núcleo flexible del sistema.

### Esquema V3 (Actual)
```json
{
  "properties": [
    {"key": "Gravedad", "value": "1.5g"},
    {"key": "Bioma", "value": "Tundra Tóxica"}
  ],
  "gallery_log": { ... },
  "cover_image": "filename.webp"
}
```

### Schema Objeto vs Criatura
En el Nivel 13, diferenciamos por rango de ID:
*   **Criatura (00-89):** Define biología, sociedad, psicología.
*   **Objeto (90-99):** Define mecánica, materiales, uso, encantamientos. Usado para Items, Vehículos, Reliquias.
