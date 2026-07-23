# Dentia Documentation

Este directorio es la fuente oficial de documentación de Dentia.

A partir de DOC-001, toda funcionalidad importante debe seguir el flujo:

Idea → Documento de diseño → Aprobación funcional → Implementación → Pruebas → Producción.

## Índice

- [Arquitectura](architecture/)
- [Módulos](modules/)
- [Design System](design-system/)
- [UX](ux/)
- [Architecture Decision Records](adr/)
- [Roadmap](roadmap/)
- [Integraciones](integration/)

## Design System

- [DDS-001 — Tooth Component](design-system/DDS-001-Tooth-Component.md)
- [DDS-002 — Dental Inspector](design-system/DDS-002-Dental-Inspector.md)
- [DDS-003 — Odontogram Workspace](design-system/DDS-003-Odontogram-Workspace.md)
- [DDS-004 — Tooth Visual States](design-system/DDS-004-Tooth-Visual-States.md)
- [DDS-004A — Tooth Illustration Guide](design-system/DDS-004A-Tooth-Illustration-Guide.md)
- [DDS-004B — Clinical Representation Rules](design-system/DDS-004B-Clinical-Representation-Rules.md)
- [DDS-004C — Classic Odontogram Representation Rules](design-system/DDS-004C-Classic-Odontogram-Representation-Rules.md)
- [DDS-005 — Classic Odontogram Component](design-system/DDS-005-Classic-Odontogram-Component.md)
- [DDS-005A — Dual Clinical Tooth Representation](design-system/DDS-005A-Dual-Clinical-Tooth-Representation.md)

## Architecture Decision Records

- [ADR-001 — Decisión de representación clínica del odontograma](architecture/ADR-001-Classic-Odontogram-Decision.md)
- [ADR-002 — Representación dual y sincronizada del diente](architecture/ADR-002-Dual-Synchronized-Tooth-Representation.md)
- [ADR-003 — Trazabilidad clínica-comercial odontograma → tratamiento → presupuesto → evolución](architecture/ADR-003-Clinical-Commercial-Traceability.md)

## Integraciones

- [C017E — Contrato de integración clínica-comercial](integration/C017E-Clinical-Commercial-Integration-Contract.md)
- [C017E — Propuesta de relaciones entidad-relación](integration/C017E-Entity-Relationship-Proposal.md)
- [C017E — Estados y transiciones](integration/C017E-State-Transitions.md)
- [C017E — Plan de pruebas](integration/C017E-Test-Plan.md)

## Convención documental

- Architecture: `A-001`, `A-002`, ...
- Modules: `M-001`, `M-002`, ...
- Design System: `DDS-001`, `DDS-002`, ...
- Architecture Decision Records: `ADR-001`, `ADR-002`, ...
- UX: `UX-001`, `UX-002`, ...
- Roadmap: `RM-001`, `RM-002`, ...

## Regla de versionado documental

Los documentos aprobados no deben sobrescribirse de forma que se pierda el historial de decisiones.

Cuando exista un cambio importante, se debe crear una nueva revisión o versión del documento, por ejemplo:

- `DDS-001-Tooth-Component-v1.md`
- `DDS-001-Tooth-Component-v2.md`
