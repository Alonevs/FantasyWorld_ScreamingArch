# ⚡ ESPECIFICACIÓN: "GENESIS WIZARD" (ATAJO DE CREACIÓN)

> **Problema:** La navegación jerárquica (Drill-down) es demasiado lenta para crear entidades profundas como Planetas (Nivel 6).
> **Solución:** Implementar un formulario de creación directa con selectores contextuales.

---

## 1. Concepto de "Contexto Predeterminado"

Como las capas 1, 2 y 3 (Caos, Abismo, Realidad) son estructurales y raramente cambian, el sistema debe tener una configuración de **"Contexto Activo"**.

* **Default Root:** `010101` (Caos Prime -> Abismo Prime -> Realidad Base).
* *El usuario no debería tener que seleccionar esto cada vez.*

---

## 2. Flujo de UI (Frontend)

Se requiere un nuevo formulario en el Dashboard (`index.html`) o una vista dedicada `create_wizard`:

### Selector 1: Galaxia (Nivel 4)
* **Fuente:** Buscar todos los hijos de `Default Root` con longitud de Nivel 4.
* **Opción Extra:** "➕ Crear Nueva Galaxia".

### Selector 2: Sistema (Nivel 5)
* **Comportamiento:** Se carga dinámicamente al seleccionar una Galaxia.
* **Fuente:** Buscar hijos de la Galaxia seleccionada.
* **Opción Extra:** "➕ Crear Nuevo Sistema".

### Input Final: Planeta (Nivel 6)
* Nombre, Descripción, Metadata base.

---

## 3. Requerimientos Técnicos

1.  **Endpoint API Interna:** Una vista ligera de Django que devuelva JSON con la estructura del árbol para llenar los `select` sin recargar la página (AJAX/Fetch).
    * `GET /api/structure?parent=010101` -> Devuelve lista de Galaxias.
2.  **Lógica de Creación en Cadena:**
    * Si el usuario elige "Nueva Galaxia" + "Nuevo Sistema" + "Nuevo Planeta", el backend debe crear los 3 padres/hijos en una sola transacción atómica.

---

## 4. Prioridad
Implementar esto **después** de la lógica de Hemisferios para facilitar el poblado rápido del universo.