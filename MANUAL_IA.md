# Manual de Inteligencia Artificial (ECLAI)

Especificaciones para el "Cerebro" del sistema, encargado de la generación de contenido y coherencia.

## 1. Filosofía de Coherencia
El sistema utiliza un **Modelo de Herencia Estricta**.
*   **Regla**: Un hijo hereda las propiedades de su padre, abuelo, y ancestros, a menos que se especifique lo contrario explícitamente.
*   **Resolución**: La propiedad más específica (más cercana al hijo) gana.
    *   *Ejemplo*: Si Universo es `Magia: Alta` pero Planeta es `Magia: Nula`, el Personaje en ese planeta tendrá `Magia: Nula`.

## 2. Auto-Noos (Extracción de Metadatos)
El módulo "Auto-Noos" analiza narrativas de texto plano y extrae atributos estructurados (JSON).

*   **Input**: Texto descriptivo o historia.
*   **Proceso**: LLM (Llama 3) analiza el texto buscando datos clave (Clima, Gobierno, Raza).
*   **Output**: JSON estandarizado.

### Atributos Clave (Schema V3)
El sistema busca rellenar claves como:
*   `Bioma`: Entorno físico.
*   `Tech_Level`: Nivel tecnológico.
*   `Magic_System`: Reglas mágicas.
*   `Culture_Tags`: Valores sociales.

## 3. Prompts (Plantillas Llama 3)
Los prompts se construyen dinámicamente inyectando el contexto heredado.

**Estructura del Prompt:**
1.  **SYSTEM**: Rol ("Eres un Arquitecto de Mundos Expertos"). Instrucción de formato JSON.
2.  **CONTEXT**: Lista de propiedades heredadas de los ancestros (para mantener coherencia).
3.  **INSTRUCTION**: La solicitud específica ("Genera un Herrero para esta Ciudad").

```json
// Ejemplo de Salida Esperada
{
  "nombre": "Garral",
  "descripcion": "Herrero orco especializado en aleaciones de cristal.",
  "atributos": {
    "Fuerza": "Alta",
    "Oficio": "Herrería Mágica"
  }
}
```
