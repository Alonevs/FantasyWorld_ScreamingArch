# Arquitectura de Inteligencia Artificial (ECLAI)

Este documento detalla el funcionamiento del "Cerebro" de FantasyWorld y cómo interactuar con el sistema de IA.

---

## 1. Filosofía de Coherencia Narrativa

El sistema utiliza un **Modelo de Herencia Estricta** basado en la jerarquía J-ID.
*   **Herencia**: Un hijo hereda las propiedades de sus ancestros (Universo > Galaxia > Planeta).
*   **Resolución**: Las propiedades más específicas (cercanas al hijo) tienen prioridad.
    *   *Ejemplo*: Si el Universo tiene "Magia: Alta" pero el Planeta tiene "Magia: Nula", las entidades en ese planeta se tratarán con "Magia: Nula".

---

## 2. Generación de Contenido

### Auto-Noos (Extracción de Metadatos)
Módulo encargado de analizar textos narrativos y extraer atributos estructurados (JSON).
*   **Input**: Descripción en lenguaje natural.
*   **Proceso**: Un LLM analiza el texto buscando claves del Schema (Bioma, Tecnología, Cultura).
*   **Output**: Propuesta de metadatos clave/valor.

### Generación de Imágenes
*   **Servicio**: Stable Diffusion.
*   **Integración**: `StableDiffusionService` se comunica mediante API con el servidor de generación.
*   **Propuestas**: Todas las imágenes generadas se envían al Dashboard para revisión manual antes de ser publicadas (`ADD` action).

---

## 3. Guía para Desarrolladores de IA

Para mantener la coherencia del sistema, cualquier asistente IA debe seguir estas reglas:

1.  **No Duplicar Datos**: Antes de añadir campos nuevos a los modelos, verifica si se pueden guardar en `metadata` (JSONB).
2.  **Identidad J-ID**: Respeta siempre la jerarquía de IDs al crear o buscar entidades.
3.  **Contexto Temporal**: Al generar contenido, comprueba siempre el `timeline_period` activo para evitar anacronismos.
4.  **Escritura Segura**: Usa `repo.save_manual_file` para manejar assets físicos. No manipules el disco directamente.
5.  **Permisos**: Todas las acciones de edición deben validarse con `check_ownership`.

---

## 4. Requisitos de Infraestructura
*   **LLM de Texto**: Puerto 5000 (Qwen/Llama 3).
*   **Stable Diffusion**: Puerto 7861.
