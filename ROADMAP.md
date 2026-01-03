# Hoja de Ruta (Roadmap)

## 📌 Estado Actual (v0.1)
*   **Core**: Estable. Arquitectura Screaming completa sobre Django.
*   **UI**: Renovada con Tailwind, Alpine.js y animaciones "Zen".
*   **Datos**: PostgreSQL + Sistema de Propuestas Estricto.
*   **Social**: Sistema de Avatares Unificado y Lightbox Interactivo.
*   **Refactoring**: ✅ Completado (Type hints, código limpio, modularización).

## 🚀 Próximos Pasos (Prioridad Actual)

### Fase 1: Contenido Base (En Progreso)
**Objetivo:** Completar todos los niveles de geografía y entidades antes de añadir features avanzadas.

- [ ] **Completar Jerarquía de Mundos**: Definir y poblar todos los niveles geográficos necesarios.
- [ ] **Definir Tipos de Entidades**: Establecer la taxonomía completa de entidades (Razas, Facciones, Personajes, etc.).
- [ ] **Crear Contenido Base**: Poblar el universo con mundos, narrativas y entidades fundamentales.

### Fase 2: Experiencia de Usuario
- [ ] **Mapa Interactivo**: Visualización gráfica (Canvas/D3.js) del árbol J-ID.
- [ ] **Exportación**: Generar PDF o EPUB de una rama narrativa completa.
- [x] **Header Responsivo**: Implementado panel lateral y navegación optimizada.
- [ ] **Escritura Móvil**: Optimizar la experiencia de edición de narrativa en pantallas táctiles.

## 🔮 Fase Final: Inteligencia y Automatización (Pospuesto)

> **NOTA IMPORTANTE:** Estas features se implementarán SOLO cuando la jerarquía de mundos, 
> geografía y entidades estén completamente definidas y pobladas. No tiene sentido crear 
> un sistema de herencia inteligente sin tener primero el contenido base establecido.

### Features de Inteligencia (Para más adelante)
- [ ] **Visor de Contexto**: UI para ver visualmente qué hereda un hijo de su padre.
- [ ] **Wizard Inteligente**: Al crear un hijo, sugerir valores basados en el padre (ej: si Padre es "Desierto", sugerir "Raza: Nómadas").

**Razón del aplazamiento:** Primero necesitamos tener una base sólida de contenido para que 
el sistema de herencia y sugerencias tenga sentido y sea útil.
