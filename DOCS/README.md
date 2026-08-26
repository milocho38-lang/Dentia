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
- [Clínica](clinical/)
- [Cumplimiento](compliance/)
- [Preparación para piloto](readiness/)
- [Operaciones](operations/)
- [Seguridad](security/)
- [Pruebas](testing/)
- [Producto](product/)

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
- [C019A.0 — Arquitectura de consentimientos](architecture/C019A0-Consent-Architecture.md)
- [C019A.1 — Implementación del motor de plantillas](architecture/C019A1-Consent-Template-Implementation.md)
- [C019A.2 — Implementación de instancias](architecture/C019A2-Consent-Instance-Implementation.md)
- [C019A.3 — Seguridad de acceso, portal y OTP](architecture/C019A3-Consent-Access-Security.md)
- [C019A.4 — Evidencia y PDF final](architecture/C019A4-Consent-Evidence-and-PDF-Architecture.md)

## Integraciones

- [C017E — Contrato de integración clínica-comercial](integration/C017E-Clinical-Commercial-Integration-Contract.md)
- [C017E — Propuesta de relaciones entidad-relación](integration/C017E-Entity-Relationship-Proposal.md)
- [C017E — Estados y transiciones](integration/C017E-State-Transitions.md)
- [C017E — Plan de pruebas](integration/C017E-Test-Plan.md)
- [C017E.1 — Diagnóstico odontográfico → procedimiento planificado](integration/C017E1-Odontogram-Diagnosis-to-Planned-Procedure.md)
- [C017E.2 — Procedimientos → presupuesto versionado e inmutable](integration/C017E2-Procedures-to-Versioned-Budget.md)
- [C017E.3 — Procedimiento realizado → evolución clínica → odontograma confirmado](integration/C017E3-Completed-Procedure-to-Evolution-Odontogram.md)

## Clínica

- [C017F.1 — Evolución clínica simplificada](clinical/C017F1-Simplified-Clinical-Evolution.md)
- [C017F.2 — Tratamiento como punto de entrada al odontograma](clinical/C017F2-Treatment-First-Odontogram.md)
- [C017G.1 — Informes clínicos, remisiones y cartas](clinical/C017G1-Clinical-Reports-Referrals-Letters.md)
- [C017G.2 — Recetario odontológico](clinical/C017G2-Odontological-Prescriptions.md)
- [C019A.0 — Contrato de consentimientos informados y aceptación electrónica](clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md)

## Cumplimiento

- [C019A.0 — Matriz normativa de consentimientos Colombia/Chile](compliance/C019A0-Consent-Colombia-Chile.md)

## UX

- [C019A.0 — Flujos de revisión, decisión y firma](ux/C019A0-Consent-Signing-Flows.md)

## Preparación para piloto

- [C018R.1 — Auditoría de preparación para piloto real](readiness/C018R1-Pilot-Readiness-Audit.md)
- [C018R.1 — Checklist operativo del piloto](readiness/C018R1-Pilot-Checklist.md)
- [C018R.1 — Bloqueantes y riesgos](readiness/C018R1-Blocking-Issues.md)
- [C018R.1 — Plan de despliegue y preparación](readiness/C018R1-Deployment-Plan.md)
- [C018R.2 — Hardening integral previo al piloto controlado](readiness/C018R2-Pilot-Hardening.md)
- [C018R.3 — Backup completo PostgreSQL + storage clínico](readiness/C018R3-Complete-Backup-and-Restore.md)
- [C018R.4 — Pruebas automáticas de aislamiento multiempresa, roles y permisos](readiness/C018R4-Multitenancy-and-Permissions.md)
- [C019A.0 — Registro de decisiones y preparación para C019A.1](readiness/C019A0-Consent-Decision-Log.md)
- [C019A.1 — Decisiones y compuerta para C019A.2](readiness/C019A1-Consent-Template-Decision-Update.md)
- [C019A.2 — Decisiones y compuerta para C019A.3](readiness/C019A2-Consent-Instance-Decision-Update.md)
- [C019A.3 — Decisiones y compuerta para C019A.4](readiness/C019A3-Consent-Access-Decision-Update.md)
- [C019A.4 — Decisiones y compuerta de producción](readiness/C019A4-Consent-Acceptance-Decision-Update.md)
- [C019 — Preparación productiva y responsabilidades](product/C019-Consent-Production-Readiness.md)

## Producto

- [C019A.1 — Plantillas y versiones de consentimientos](product/C019A1-Consent-Templates-and-Versioning.md)
- [C019A.2 — Instancias y flujo clínico previo a firma](product/C019A2-Consent-Instances-and-Clinical-Flow.md)
- [C019A.3 — Acceso, portal y OTP](product/C019A3-Consent-Access-Portal-and-OTP.md)
- [C019A.4 — Aceptación, firma capturada y documento final](product/C019A4-Consent-Acceptance-Signature-and-Final-Document.md)

## Operaciones

- [Validación local de aceptación de consentimientos](operations/Dentia-Consent-Local-Acceptance-Validation.md)

- [Runbook — Backup y restauración Dentia](operations/Dentia-Backup-Restore-Runbook.md)
- [Runbook — Storage persistente Dentia](operations/Dentia-Persistent-Storage-Runbook.md)
- [Runbook — Despliegue seguro Dentia](operations/Dentia-Safe-Deployment-Runbook.md)
- [Configuración — Correo de consentimientos](operations/Dentia-Consent-Email-Configuration.md)
- [Recuperación — Documento final de consentimiento](operations/Dentia-Consent-Final-Document-Recovery.md)

## Seguridad

- [Runbook — Secretos de producción Dentia](security/Dentia-Production-Secrets-Runbook.md)
- [Matriz — Seguridad multiempresa, roles y permisos](security/Dentia-Multitenancy-Security-Matrix.md)
- [C019A.3-FIX1 — Triage de dependencias frontend](security/C019A3-Npm-Audit-Triage.md)

## Pruebas

- [Runbook — Pruebas de seguridad C018R.4](testing/Dentia-Security-Test-Runbook.md)
- [C019A.0 — Estrategia de pruebas de consentimientos](testing/C019A0-Consent-Test-Strategy.md)
- [C019A.1 — Reporte de pruebas del motor de plantillas](testing/C019A1-Consent-Template-Test-Report.md)
- [C019A.2 — Reporte de pruebas de instancias](testing/C019A2-Consent-Instance-Test-Report.md)
- [C019A.3 — Reporte de acceso, portal y OTP](testing/C019A3-Consent-Access-Test-Report.md)
- [C019A.4 — Reporte de aceptación, evidencia y PDF](testing/C019A4-Consent-Acceptance-Test-Report.md)

## Roadmap

- [Roadmap oficial de desarrollo](D005%20-%20ROADMAP%20DESARROLLO.md)

Comando operativo complementario de hardening previo al piloto:

```bash
./scripts/local/test_dentia_security.sh --hardening
```

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

- C019A4-LIB1 documenta la biblioteca oficial Dentia de documentos odontológicos, su importación, procedencia y pruebas.
