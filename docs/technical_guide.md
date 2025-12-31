# Guía Técnica: FantasyWorld (Screaming Architecture)

Este documento es la referencia definitiva para entender la arquitectura, lógica y flujos de trabajo de **FantasyWorld**.

---

## 1. Arquitectura del Sistema

### Screaming Architecture
El proyecto sigue el principio de que la estructura de carpetas debe "gritar" de qué trata la aplicación.

*   **`src/WorldManagement` (Dominio)**: Contiene la lógica pura del negocio (Entidades, Casos de Uso, Repositorios). No depende de Django.
*   **`src/Infrastructure/DjangoFramework` (Infraestructura)**: Implementación de la web y persistencia mediante Django.

### Flujo de Datos
1. **Vista (Django)** recibe la petición.
2. Llama a un **Caso de Uso (Application Layer)**.
3. El Caso de Uso usa un **Repositorio** para obtener/guardar **Entidades de Dominio**.
4. Se devuelve el resultado a la vista para renderizar.

---

## 2. Identidad y Jerarquía (Sistema J-ID)

Usamos **Identificadores Jerárquicos (J-ID)** para modelar la relación padre-hijo (Universo > Galaxia > Planeta).

*   **Formato**: Pares de dígitos. Ejemplo: `01` (Raíz) -> `0105` (Hijo) -> `010502` (Nieto).
*   **Nivel**: Profundidad = (Longitud ID / 2).
*   **Gap Filling**: Si se salta un nivel, se rellena con `00`.
*   **Personajes**: Nivel 16 (Detección especial con 4 dígitos finales).

### Tabla de Niveles
| Nivel | Nombre | Ejemplo |
| :--- | :--- | :--- |
| **01** | CAOS PRIME | Raíz del sistema. |
| **03** | UNIVERSO | Contenedor principal. |
| **06** | PLANETA | Unidad habitable. |
| **16** | PERSONAJE | Entidad individual. |

---

## 3. Flujos de Trabajo (Paso a Paso)

### Gestión de Mundos
1. **Propuesta**: Al crear o editar un mundo, se genera una **Propuesta** (vX o ImageProposal).
2. **Revisión**: Los cambios NO son inmediatos. Aparecen en el **Dashboard** en estado `PENDING`.
3. **Aprobación**: Un Admin o Superuser aprueba la propuesta para que pase a estado `LIVE`.

### Línea Temporal (Timeline)
*   **Periodos**: El sistema usa periodos nombrados (e.j. "Era de los Mitos").
*   **Navegación**: Se activa mediante el parámetro `?period=[slug]`.
*   **Contenido Histórico**: Cada periodo tiene su propia descripción y galería de imágenes.

### Sistema de Silos (Privacidad)
*   **Superadmin**: Ve y gestiona todo.
*   **Admin**: Gestiona sus propios mundos y las propuestas de sus colaboradores asignados. No ve el trabajo de otros equipos ajenos.

---

## 4. Instalación y Desarrollo

1. **Entorno**: Python 3.10+ y PostgreSQL.
2. **Setup**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python src/Infrastructure/DjangoFramework/manage.py migrate
   python server_run.py
   ```
3. **Variables**: Configurar `.env` con las credenciales de la base de datos y la SECRET_KEY.
