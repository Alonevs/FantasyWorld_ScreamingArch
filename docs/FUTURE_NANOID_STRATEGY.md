# 🔐 ESTRATEGIA DE IDENTIDAD PÚBLICA (NANOID) v1.0

> **Estado:** Planificado (Futuro).
> **Objetivo:** Desacoplar la identidad lógica (J-ID Jerárquico) de la identidad pública (URL) para ocultar la estructura del mundo y acortar enlaces.

---

## 1. El Problema Actual
* **J-ID (Internal):** `01010105030101...` (Contiene lógica, es largo, revela padres/hijos).
* **URL Actual:** `/mundo/0101010503...`
* **Riesgo:** Un usuario puede deducir qué planetas existen cambiando los números finales.

## 2. La Solución: "Doble Identidad"

El sistema mantendrá dos IDs por cada entidad:

1.  **`id` (PK):** El J-ID ECLAI actual. Se usa para relaciones, herencia de clima y ordenamiento en backend.
2.  **`public_id` (Unique Index):** Un código aleatorio corto (NanoID). Se usa **solo** para URLs y búsquedas web.

---

## 3. Especificación Técnica

### A. Librería Recomendada
Usar `nanoid` o `shortuuid` para Python.
* **Alfabeto:** `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-`
* **Longitud:** 10 caracteres (suficiente para evitar colisiones en millones de mundos).

### B. Cambios en Base de Datos (`CaosWorldORM`)
Añadir columna:
```python
public_id = models.CharField(
    max_length=12, 
    unique=True, 
    db_index=True, 
    editable=False
)