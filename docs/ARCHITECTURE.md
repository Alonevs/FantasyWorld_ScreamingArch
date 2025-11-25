# Arquitectura del Proyecto

Este proyecto sigue los principios de **Screaming Architecture** (Arquitectura que "Grita") y **Domain-Driven Design (DDD)**. El objetivo es que la estructura del proyecto comunique claramente su propósito (gestión de mundos de fantasía) en lugar del framework que utiliza (Django).

## 🏗️ Visión General

La arquitectura invierte la dependencia tradicional: **El Framework (Django) es un detalle de implementación**, no el núcleo de la aplicación.

### Capas Principales

1.  **Domain (Dominio)**: El corazón del software. Contiene las reglas de negocio, entidades y lógica pura. No depende de nada externo (ni base de datos, ni web, ni frameworks).
2.  **Application (Aplicación)**: Orquesta los casos de uso. Conecta el mundo exterior con el dominio.
3.  **Infrastructure (Infraestructura)**: Implementaciones concretas. Aquí vive Django, los repositorios SQL, las llamadas a APIs de IA, etc.

## 📂 Estructura de Carpetas

```text
d:\FantasyWorld_ScreamingArch\
├── src\
│   ├── FantasyWorld\           # Contexto Principal (Bounded Context)
│   │   ├── WorldManagement\    # Módulo de Gestión de Mundos
│   │   │   ├── Caos\           # Agregado 'Caos' (Mundos Nivel 1)
│   │   │   │   ├── Application\ # Casos de Uso (CreateWorld, etc.)
│   │   │   │   ├── Domain\      # Entidades (CaosWorld) y Repositorios (Interfaces)
│   │   │   │   └── Infrastructure\ # Implementación Django (Models, Repositories)
│   │   │   └── ...
│   │   └── AI_Generation\      # Módulo de Generación con IA
│   ├── Shared\                 # Kernel Compartido (Value Objects, IDs ECLAI)
│   │   ├── Domain\
│   │   └── Infrastructure\
│   └── Infrastructure\         # Infraestructura Global
│       └── DjangoFramework\    # Proyecto Django (settings, manage.py)
├── docs\                       # Documentación
├── main.py                     # Entry point para modo consola
└── requirements.txt            # Dependencias
```

## 🔄 Flujo de Datos

Un flujo típico de creación de un mundo (Caso de Uso: `CreateWorld`) funciona así:

1.  **Entrada**: El usuario (vía Web o Consola) invoca el caso de uso.
2.  **Application**: `CreateWorldUseCase` recibe la petición.
    *   Llama a `eclai_core` (Shared Domain) para generar un ID único.
    *   Crea una entidad `CaosWorld` (Domain).
3.  **Domain**: La entidad valida sus propias reglas.
4.  **Infrastructure**: El caso de uso llama al `CaosRepository` (Interfaz definida en Domain, implementada en Infrastructure).
    *   `DjangoCaosRepository` traduce la entidad a un modelo de Django (`CaosModel`) y lo guarda en SQLite.

## 🔑 Conceptos Clave

### ECLAI IDs (v3.0)
Sistema de identificación jerárquico personalizado.
- **J-ID (Jerárquico)**: Define la estructura (ej. `01` -> Caos).
- **N-ID (Narrativo)**: Define el contenido (ej. `01L01` -> Lore del Caos 1).

### Inyección de Dependencias
Los casos de uso no instancian sus dependencias directamente; las reciben en el constructor (ej. el repositorio). Esto facilita el testing y el cambio de implementaciones.
