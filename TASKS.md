# Lista de Tareas (TASKS)

## 📌 Estado Actual
- **Sistema Base:** Funcional (Django + SQLite/Postgres).
- **Jerarquía:** Implementada con Padding (J-ID).
- **Generación:** Llama 3 integrado para descripciones simples.
- **Workflow:** Propuestas y Aprobaciones (Dashboard) activo.

## 🚀 Fase 1: Refactorización y Limpieza (COMPLETADO)
- [x] Limpieza de funciones de ID obsoletas.
- [x] Unificación de creación bajo `EntityService`.
- [x] Implementación estricta de Soft Delete en Narrativas y Mundos.

## 🧠 Fase 2: Inteligencia y Herencia (EN PROGRESO)

### Módulo de Inteligencia
* [ ] **Implementar `ContextAggregationService`:**
    *   Servicio que recorra ancestros (Entity -> Parent -> Root).
    *   Merge inteligente de propiedades (Hijo sobrescribe a Padre).
    *   Soporte para "Traits" heredados (ej: Magia Alta en el Universo afecta a todas las criaturas).

* [ ] **Implementar `Llama3PromptBuilder`:**
    *   Constructor de prompts narrativos que inyecte el Contexto Agregado.
    *   Templates para "Crear Criatura", "Generar Evento", "Describir Lugar".

* [ ] **Integración API LLM Avanzada:**
    *   Mejorar el conector para soportar JSON Mode nativo (si disponible) o parsing robusto.
    *   Manejo de errores y retries.

## 🔮 Fase 3: Interfaz y Experiencia (FUTURO)
- [ ] **Visor de Contexto:** UI para ver qué rasgos hereda una entidad.
- [ ] **Wizard de Creación Inteligente:** Formulario que sugiere valores basados en el padre.
