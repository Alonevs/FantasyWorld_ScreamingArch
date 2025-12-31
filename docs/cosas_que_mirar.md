# Cosas que Mirar (Backlog de Arquitectura)

Este documento sirve como recordatorio para mejoras estructurales y refactorizaciones futuras de **FantasyWorld**.

---

## 1. Unificación del Sistema de Propuestas (TEÓRICO)
Actualmente, las propuestas están fragmentadas en tres modelos (`CaosVersionORM`, `CaosNarrativeVersionORM`, `CaosImageProposalORM`). 

**Filosofía**: *"Si funciona, no lo toques"*. No se unificará nada que sea crítico o que funcione correctamente (como el sistema de periodos paralelo).

**Objetivo Teórico**: Evaluar en el futuro si compensa crear un sistema universal.
- **Concepto**: Una sola tabla `UniversalProposal` con un `proposed_payload` en JSONB.
- **Casos Especiales**: El sistema de **Periodos** dentro de una ficha y ciertos campos **JSONB** se mantendrán como excepciones si su complejidad actual lo requiere.
- **Beneficio**: Centralizar lógica solo cuando aporte estabilidad, no solo por "estética" de código.

## 2. Sistema de Excepciones de Autorización
- **Idea**: Crear un sistema donde ciertos roles puedan saltarse la aprobación estándar para acciones críticas o automatizadas, pero manteniendo la auditoría.

## 3. Optimización de Roles
- Revisar si el sistema de "Silos" de Admins puede simplificarse aún más mediante decoradores de vista más potentes que utilicen la "API de permisos" interna.
