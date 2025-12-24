# ⚖️ REGLAS DEL PROYECTO (THE CAOS WAY)

Este documento oficializa las reglas, filosofías y protocolos técnicos de **FantasyWorld / Caos**. Es de cumplimiento obligatorio para cualquier desarrollador humano o IA (Pyrefly).

---

## 1. 🧬 Los Pilares de la Existencia (Esencia)

### 1.1 Autoría y Soberanía
- **Propiedad**: El creador de una entidad tiene control total sobre ella.
- **Colaboración (Boss/Minion)**: El sistema permite relaciones de colaboración donde un "Boss" (Admin/Superadmin) puede autorizar a "Minions" (Subadmins) para editar o proponer cambios. 
    - **Regla Estricta**: Un Subadmin SOLO puede trabajar en entidades propiedad de sus "Jefes" vinculados. Un Subadmin puede estar vinculado a múltiples "Jefes".
- **Democracia de Rango**: Los Admins pueden proponer cambios en mundos del Superadmin, pero el Superadmin siempre tiene la última palabra.
- **Supervisión Global**: El Superadmin tiene la capacidad de auditar y gestionar los buzones de propuestas de todos los usuarios para garantizar la coherencia global.

### 1.2 Identidad (J-ID vs NanoID)
- **J-ID (Internal ID)**: Identificador jerárquico determinista. 
    - **Regla**: `Nivel = Longitud / 2`.
    - Determina la posición exacta en el árbol genealógico del mundo.
- **NanoID (Public ID)**: 10 caracteres alfanuméricos (`0-9a-zA-Z_-`). Es la identidad pública y agnóstico para URLs y referencias externas.

### 1.3 Saltos de Jerarquía (Hierarchy Leaps)
- **Definición**: Se permite crear una entidad en un nivel muy inferior al de su padre directo (ej. saltar del Nivel 3 al Nivel 10) para evitar burocracia creativa.
- **Regla de Identificadores (J-ID)**: Los niveles omitidos se rellenan con un par de ceros (`00`) por cada nivel saltado en el J-ID.
- **Prohibición de Entidades Fantasma**: NO se deben crear registros en la base de datos para los niveles intermedios saltados. El salto debe ser puramente lógico en el ID.
- **Señal Visual (Borde Amarillo)**: En la interfaz (Cards/Listas), las entidades que provienen de un salto jerárquico se distinguen por un **borde amarillo discontinuo/difuminado** para indicar su naturaleza especial.

### 1.4 Independencia de Rama por Nivel
- **Lógica de Nivel Absoluto**: El tipo de entidad (Planeta, Ciudad, etc.) está determinado exclusivamente por su **Nivel (Longitud/2)**, independientemente de la rama de origen (`0101` - Física, `0105` - Dimensional, etc.).
- **Agrupación Global**: En las vistas de índice o resúmenes, las entidades del mismo nivel deben aparecer agrupadas juntas si así lo requiere la vista, sin importar su linaje o rama padre.

---

## 2. 🏛️ Arquitectura y Código

### 2.1 Stack Técnico y Arquitectura
- **Núcleo**: Python + Django Framework.
- **Screaming Architecture & DDD**: La estructura de carpetas (`src/WorldManagement`, `src/Infrastructure`) debe gritar qué hace la aplicación, no qué framework usa.
- **Separación de Capas**: División estricta entre **Domain** (Lógica pura), **Application** (Casos de uso) e **Infrastructure** (Django/DB/Externo).

### 2.2 Frontend y Estilo (Tailwind CSS)
- **Framework**: Uso mandatorio de **Tailwind CSS** para todo el estilado.
- **Consistencia Visual**: Queda prohibido el uso de estilos ad-hoc fuera del sistema de diseño. Se deben reutilizar los tokens de color (`dark`, `card`, `accent`) definidos en la configuración de Tailwind.
- **Responsive**: Todas las vistas deben ser Mobile-First y Totalmente Responsivas.

### 2.3 Idioma y Documentación de Código
- **Idioma de Comentarios**: Todos los comentarios, docstrings y explicaciones dentro del código deben estar en **Español**.
- **Documentación Obligatoria**: Cada clase, función y bloque lógico importante debe estar documentado explicando qué hace, por qué lo hace y qué resultados espera. Se busca un código "auto-explicativo" asistido por comentarios claros.

### 2.4 Herencia Estricta
- **Regla**: Padre -> Hijo -> Nieto.
- Las propiedades (magia, clima, tecnología, etc.) se heredan de los ancestros.
- La propiedad más cercana (específica) sobrescribe a la más lejana (general).

---

## 3. 📜 Sistemas de Información

### 3.1 Control de Versiones (Proposals)
- **Nada se edita en vivo**: Todo cambio sin excepción genera una propuesta (`CaosVersionORM`).
- **Capacidad de Propuesta**: Los usuarios sin autoría o rol de edición sobre una entidad NO pueden modificarla directamente, pero SIEMPRE pueden elevar una propuesta para revisión.
- **Ciclo de Vida**: `PENDING` -> `APPROVED` -> `LIVE`. 
- **Promoción al Live**: Al aprobarse una versión, la versión `LIVE` anterior pasa automáticamente al historial (archivada) y la nueva toma el relevo (`es_version_activa=True`). Solo puede existir una versión activa por entidad.

### 3.2 Gestión de Imágenes (Fotos)
- **Sistema de Propuestas**: Al igual que el texto, la subida o borrado de imágenes genera una propuesta (`CaosImageProposalORM`).
- **Validación**: Las imágenes deben ser aprobadas por un Admin antes de ser visibles en el "Live" de una entidad.

### 3.3 Borrado Lógico (Soft Delete)
- **Prohibición**: No existe el `DELETE` físico para entidades maestras o narrativas.
- **Mecánica**: Se utiliza `is_active=False` y `deleted_at`.
- **Restauración**: Mover algo de la papelera al "mundo vivo" requiere una propuesta de restauración y aprobación admin.

### 3.4 Dependencia Existencial (Narrativas)
- El **Lore** (historias, leyendas, crónicas) no tiene vida independiente.
- Si una entidad (Mundo/Nivel) se borra o desactiva, su Lore asociado desaparece con ella (Cascada lógica).

---

## 4. 🎨 Estética y UX (Premium Standard)

- **UI Pattern**: Uso obligatorio del global `CaosModal` para confirmaciones y alertas. Queda prohibido el uso de `alert()` o `confirm()` nativos.
- **Mensajes de Sistema**: Quedan prohibidos los mensajes genéricos o "grises". Todo mensaje de sistema (alertas, errores, avisos) debe tener un diseño personalizado, vibrante y acorde a la estética del proyecto.
- **Estados de Página**: 
    - **Páginas Borradas/Vacías**: Deben mostrar un mensaje claro de vacío o inexistencia.
    - **En Construcción/Acceso Denegado**: Se deben utilizar las plantillas de error o "work in progress" establecidas para redirigir al usuario de forma amigable.
- **Aesthetics**: Glassmorphism, gradientes vibrantes y micro-animaciones en cada interacción.
- **Consistencia**: Si un componente no se siente "Premium", no está terminado.

---

## 5. 🔮 Sistema de Sabiduría (ECLAI / AI)

### 5.1 Dualidad Generativa
- **Texto (LLM)**: Utilizado para la expansión de narrativa, mejora de escritura, generación de lore y títulos. Debe operar bajo el sistema de prompts contextuales (SYSTEM + CONTEXT + INSTRUCTION).
- **Imágenes**: Sistema dedicado para la creación visual de mundos, entidades y atmósferas.
- **Auto-Noos (Extracción)**: Módulo especializado en transformar narrativas de texto plano en datos estructurados (JSON) para alimentar los metadatos de las entidades.

### 5.2 Evolución y Futuro
- **Expansión**: La IA debe enfocarse en profundizar la coherencia del mundo, no solo en rellenar texto.
- **Sistema de Capítulos**: (Roadmap) Se planea implementar una lógica de procesamiento de archivos externos (PDF, Word) para segmentar y categorizar contenido en capítulos de forma inteligente.

---

## 6. ⚡ Protocolo de Eficiencia Pyrefly (Ahorro de Tokens)

Para que la IA no desperdicie recursos:
1.  **Lectura Inteligente**: Obligatorio usar `view_file_outline` antes de leer un archivo completo.
2.  **Conciencia Previa**: Consultar siempre `MANUAL_TECNICO.md`, `MANUAL_IA.md` y este `readme_rules.md` antes de pedir aclaraciones arquitectónicas.
3.  **No Redundancia**: Prohibido crear funciones que ya existan en `utils.py`, `hierarchy_utils.py` o `rbac.py`.
4.  **Flujo de Trabajo**: Registro constante en `task.md` y uso de planes de implementación para cambios de más de 1 archivo.

---

> [!NOTE]
> Estas reglas son la "Línea de la Verdad". Si hay conflicto entre el código y este documento, el documento prevalece hasta que se actualice oficialmente.
