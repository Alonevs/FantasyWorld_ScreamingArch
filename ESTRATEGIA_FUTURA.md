# Estrategia de Evolución: Hacia React y APIs Modulares
*Documento de Planificación Teórica - Enero 2026*

Este documento describe la hoja de ruta para evolucionar *Fantasy World Screaming Arch* desde una aplicación monolítica Django (Server-Side Rendering) hacia una arquitectura moderna desacoplada (Backend API + Frontend React/Node).

---

## 1. Arquitectura Desacoplada: "Backoffice" vs "Public Frontend"
Tu visión es clara: **No reemplazar, sino expandir**.

### A. El Backoffice (Lo que tenemos ahora)
- **Tecnología**: Django (Monolito con HTML Server-Side).
- **Función**: Panel de Administración, Gestión de Mundos, Edición de Narrativas.
- **Usuario**: EL CREADOR / EL ADMIN.
- **Estrategia**: Mantenerlo tal cual. Es robusto, seguro y ya funciona perfecto para gestionar.

### B. El Public Frontend (Lo que construiremos)
- **Tecnología**: React / Next.js / Node.js.
- **Función**: La "Cara Pública" para que el mundo navegue, lea historias y explore mapas.
- **Usuario**: EL LECTOR / JUGADOR / INTERNET.
- **Estrategia**: Construir una **API REST (o GraphQL)** en Django que sirva datos a este frontend.

---

## 2. El Plan "Headless CMS"
Django se convertirá en un **CMS descabezado** (Headless CMS) para el público, mientras sigue siendo un CMS completo para ti.

### Nuevos Módulos de API (Solo Lectura Pública)
No necesitamos migrar las vistas actuales. Necesitamos crear **Nuevos Endpoints de Solo Lectura** para el frontend público.

```text
src/Infrastructure/DjangoFramework/persistence/api/public/
    ├── v1/
    │   ├── public_world.py   # GET /api/public/world/{slug} (JSON)
    │   ├── public_feed.py    # GET /api/public/feed (Últimas novedades)
    │   └── read_story.py     # GET /api/public/narrative/{id}
```
*Nota: El Backoffice seguirá usando las vistas `views.py` normales.*

---

## 2. Sistema de Plantillas (Blueprints)
Mencionaste evitar "word util etc" y rellenar datos automáticamente para niveles inferiores (Geografía, Entidades...).

**La Solución: "Blueprints" (Arquetipos)**
En lugar de crear tablas para cada cosa (Tabla `Montaña`, Tabla `Río`), crea un sistema de **Esquemas JSON**.

### ¿Cómo funciona?
1.  **Defines el Blueprint** (JSON Schema):
    *Ejemplo: "Geografía Volcánica"*
    ```json
    {
      "fields": [
        {"name": "activity_level", "type": "select", "options": ["Dormido", "Activo"]},
        {"name": "last_eruption", "type": "date"},
        {"name": "danger_zone_radius", "type": "number"}
      ]
    }
    ```
2.  **El Frontend (React) lee este JSON** y genera el formulario automáticamente.
3.  **El Backend guarda los datos** en un campo `metadata` (JSONField) en el modelo `CaosEntityORM`.

**Ventaja**: Puedes inventar nuevos tipos de entidades ("Hechizos", "Naves Espaciales", "Clanes") sin tocar la base de datos ni el código Python.

---

## 3. Preparando el Terreno (Action Plan)

Para que el cambio a React sea suave, empieza a aplicar estos cambios en el backend **HOY**, aunque sigas usando HTML:

### A. Aísla la Lógica de Negocio (Use Cases)
Ya lo hacemos, pero seamos estrictos.
- **MAL**: La lógica de "calcular daño" está dentro de `views.py`.
- **BIEN**: La lógica está en `CalculateDamageUseCase`.
- **POR QUÉ**: Así, tanto la vista vieja HTML como la nueva API React llamarán al MISMO caso de uso. Sin duplicar código.

### B. Estandariza las Respuestas JSON
Define un formato estándar para todas tus respuestas futuras.
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "version": "1.0" }
}
```

### C. Autenticación: JWT vs Session
Django usa Cookies/Session. Las Apps modernas (React/Mobile) prefieren **Tokens (JWT)**.
- **Paso Preparatorio**: Instala `django-cors-headers` (para permitir que React hable con Django) y ve investigando `SimpleJWT`.

---

## 4. ¿Backend Node.js o Django?
Mencionaste "quizás Node.js".
- **Si te quedas con Django**: Tienes el ORM, la seguridad y el Admin panel GRATIS. Solo tienes que exponer la API. **(Recomendado por ahora)**.
- **Si cambias a Node.js**: Tendrás que reescribir TODOS los modelos, migraciones y lógica de negocio. Es mucho trabajo.

**Mi consejo**: Mantén Django como el "Cerebro" (Backend/API) potente y usa React/Next.js como la "Cara" (Frontend) bonita y rápida. Es la combinación ganadora de la industria (stack conocido como T3 o similar, pero con Django).

---

## Resumen del Mapa de Ruta

1.  **Fase 1 (Actual)**: Limpieza Modular (Terminado ✅).
2.  **Fase 2 (Inmediata)**: Implementar **Sistema de Blueprints** en el Backend (Modelos JSON).
3.  **Fase 3 (Híbrida)**: Crear endpoints API para funciones nuevas (ej. el creador de personajes) mientras el resto sigue en HTML.
4.  **Fase 4 (Migración)**: Crear la App React que consume esas APIs.
