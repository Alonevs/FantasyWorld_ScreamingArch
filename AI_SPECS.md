# Especificaciones de IA y Prompting (Llama 3)

## 🧠 Filosofía del "Cerebro" (Context Rules)
El sistema utiliza un modelo de herencia estricta para generar coherencia narrativa. 

### 1. Estrategia de Herencia
*   **Regla de Oro:** "Un hijo hereda propiedades del padre a menos que las sobrescriba explícitamente".
*   **Resolución de Conflictos:** 
    *   Si Nivel 3 (Universo) dice `Magia: Alta` y Nivel 6 (Planeta) dice `Magia: Nula`, la entidad final (Personaje) tendrá `Magia: Nula` (Especificidad gana).
    *   Si Nivel 6 no define Magia, hereda `Magia: Alta` del Universo.

### 2. Propiedades Heredables (Lista Viva)
Estas son las claves principales que el `ContextAggregationService` debe rastrear:

| Clave | Descripción | Ejemplo |
| :--- | :--- | :--- |
| **Bioma** | Entorno físico/climático. | Tundra, Desierto de Cristal. |
| **Tech_Level** | Nivel tecnológico disponible. | Neolítico, Cyberpunk, Estelar. |
| **Magic_System** | Reglas de la magia ambiental. | Vanciana, Salvaje, Nula, Psiónica. |
| **Gravity** | Condiciones físicas. | 0.5g, 2.0g, Microgravedad. |
| **Culture_Tags** | Valores sociales predominantes. | Honor, Comercio, Guerra, Secreto. |
| **Language** | Idioma raíz. | Común, Élfico Antiguo, Binario. |

---

## 🤖 Estructura del Prompt (Llama 3 Template)

El `Llama3PromptBuilder` debe construir el prompt en 3 bloques: `SYSTEM`, `CONTEXT`, `INSTRUCTION`.

### Esqueleto JSON Esperado
El LLM debe responder SIEMPRE en formato JSON estricto para facilitar el parsing.

```json
{
  "nombre": "Nombre Generado",
  "descripcion_breve": "Resumen de 1 linea",
  "descripcion_detallada": "Texto narrativo completo...",
  "biografia": "Historia del personaje/entidad...",
  "atributos": {
    "Fuerza": "Alta",
    "Inteligencia": "Media"
  },
  "tags": ["Tag1", "Tag2"]
}
```

### Ejemplo de Prompt del Sistema

```text
[SYSTEM]
Eres un Arquitecto de Mundos de Fantasía experto (nivel Tolkien/Sanderson).
Tu tarea es generar una entidad coherente que encaje perfectamente en su entorno.
RESPUESTA: Solo JSON válido. Sin markdown, sin preámbulos.

[CONTEXTO HEREDADO del Padré/Abuelo]
- Universo: Caos Primordial (Magia Infinita).
- Planeta: Xylos (Gravedad Alta, Tribus Guerreras).
- Ciudad: Fortaleza de Hierro (Tecnología de Vapor).

[INSTRUCCIÓN]
Genera un PERSONAJE (Nivel 16) que viva en esta Ciudad.
Rol: Herrero Mágico.
Tono: Sombrío pero esperanzador.
```
