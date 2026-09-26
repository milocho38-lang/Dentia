# PERIO-1 — Foundation clínica del Periodontograma

**Estado:** `IMPLEMENTED_PENDING_VALIDATION`

**Fecha:** 2026-09-22

## 1. Alcance

PERIO-1 implementa la base clínica y de seguridad necesaria para que un paciente tenga múltiples controles periodontales independientes. Cada control tiene versiones trazables y conserva de forma inmutable todo contenido finalizado.

Esta fase incluye:

- permisos clínicos específicos;
- aislamiento por empresa y sede;
- identidad odontológica activa para escrituras;
- lifecycle `DRAFT → FINALIZED`;
- corrección mediante una versión nueva;
- historial mínimo por paciente;
- snapshot JSONB canónico y SHA-256 determinista;
- auditoría sin contenido clínico;
- UI mínima dentro del expediente del paciente.

No incluye captura clínica de seis sitios, gráfico, navegación por teclado, métricas, comparación ni PDF. Esas capacidades pertenecen a fases posteriores.

## 2. Decisión de dominio

Un `PeriodontalExam` representa un control periodontal independiente. Un paciente puede tener varios exámenes, incluso en la misma fecha si el profesional crea controles distintos.

Una `PeriodontalExamVersion` representa una versión del mismo control. Una corrección no crea otro control ni sobrescribe el original: crea una nueva versión enlazada mediante `supersedes_version_id`.

La versión vigente está identificada por `current_version_id`. Solo puede existir un borrador por examen.

## 3. Lifecycle e inmutabilidad

```text
Nuevo control → V1 DRAFT → V1 FINALIZED
                         ↓ Corregir con motivo
                      V2 DRAFT → V2 FINALIZED
```

- `FINALIZED` exige snapshot, hash, actor y fecha de finalización.
- Una versión finalizada no admite `UPDATE` ni `DELETE`; esta regla está reforzada mediante trigger de PostgreSQL.
- Corregir conserva V1 y crea V2.
- `row_version` protege finalización y corrección frente a clientes obsoletos.
- La restricción parcial `uq_periodontal_exam_single_draft` evita dos borradores simultáneos del mismo examen.
- No existe endpoint de eliminación destructiva.

## 4. Snapshot e integridad

La versión de contrato es `PERIODONTAL_EXAM_V1`. Al finalizar se congela un payload canónico con:

- identificadores de empresa, paciente, examen, sede y odontólogo responsable;
- fecha clínica;
- versión de esquema;
- contrato clínico aprobado por PERIO-0.3;
- `clinical_data`, vacío en PERIO-1 y reservado para la captura estructurada posterior.

El hash se calcula con JSON UTF-8, claves ordenadas y separadores canónicos. La lectura informa `PASS`, `FAIL` o `NOT_APPLICABLE` sin modificar el artefacto.

El contrato clínico congelado declara:

- dentición permanente;
- seis sitios por pieza;
- GM apical negativo y coronal positivo;
- `CAL = PD - GM`;
- umbral visual de bolsa desde 4 mm.

Declarar estas reglas no implementa todavía campos de medición ni diagnóstico automático.

## 5. RBAC

Permisos persistidos:

- `periodontogram.view`
- `periodontogram.create`
- `periodontogram.update_draft`
- `periodontogram.finalize`
- `periodontogram.correct`

Matriz:

| Rol | view | create | update_draft | finalize | correct |
|---|---:|---:|---:|---:|---:|
| DENTIST | Sí | Sí | Sí | Sí | Sí |
| DENTIST_ADMIN | Sí | Sí | Sí | Sí | Sí |
| ADMINISTRATOR | No | No | No | No | No |
| SECRETARY | No | No | No | No | No |
| PLATFORM_ADMIN | No | No | No | No | No |

Los permisos de escritura no bastan por sí solos: también se exige usuario activo, perfil `Dentist` activo, pertenencia al tenant, sede autorizada y asignación activa del odontólogo a esa sede. Platform Admin no hereda acceso clínico cross-tenant.

## 6. API

| Método | Ruta | Permiso | Propósito |
|---|---|---|---|
| GET | `/api/patients/{patient_id}/periodontograms` | `periodontogram.view` | Historial mínimo |
| POST | `/api/patients/{patient_id}/periodontograms` | `periodontogram.create` | Crear control V1 borrador |
| GET | `/api/periodontograms/{exam_id}` | `periodontogram.view` | Consultar detalle y versiones |
| POST | `/api/periodontograms/{exam_id}/finalize` | `periodontogram.finalize` | Congelar versión vigente |
| POST | `/api/periodontograms/{exam_id}/correct` | `periodontogram.correct` | Crear versión correctiva |

Los endpoints devuelven 404 para recursos de otra empresa o de una sede fuera del scope, evitando revelar su existencia.

## 7. Auditoría

Eventos:

- `PERIODONTAL_EXAM_CREATED`
- `PERIODONTAL_EXAM_FINALIZED`
- `PERIODONTAL_EXAM_CORRECTION_STARTED`
- `PERIODONTAL_EXAM_VERSION_FINALIZED`

El detalle contiene únicamente IDs y número de versión. No almacena mediciones, snapshots ni texto clínico.

## 8. UI mínima

El expediente del paciente incorpora el tab `Periodontograma`, visible solo con `periodontogram.view`. Presenta:

- estado vacío;
- nuevo control con fecha clínica;
- historial con fecha, profesional, sede, estado y acción `Ver`;
- finalización del borrador;
- creación de corrección con motivo;
- estado de integridad.

No se presentan controles clínicos que todavía no forman parte de esta fase.

## 9. Migración

`20260922_0042_periodontogram_foundation.py` sucede a `20260921_0041` y crea exclusivamente:

- `periodontal_exams`;
- `periodontal_exam_versions`;
- constraints, índices y trigger de inmutabilidad;
- cinco permisos y asignaciones a `DENTIST`/`DENTIST_ADMIN`.

No habilita acceso a roles administrativos no clínicos ni migra contenido histórico.

## 10. Pruebas

La suite DB-backed cubre:

- creación de controles independientes e historial;
- matriz RBAC y requisito de identidad odontológica;
- tenant y sede;
- snapshot/hash verificable;
- finalización e inmutabilidad en base de datos;
- corrección V1 → V2 sin reescribir V1;
- `current_version_id` apuntando a V2 después de finalizarla;
- `row_version` obsoleto;
- finalización y corrección concurrentes con un solo ganador;
- un único borrador por examen;
- ausencia de endpoint destructivo;
- auditoría sin contenido clínico.

La caracterización registra las cinco rutas como críticas y DB-backed, con cero rutas pendientes. La prueba frontend verifica el tab, permisos, estado vacío y acciones básicas, además de impedir que PERIO-1 adelante campos clínicos de PERIO-2.

## 11. Pendientes de PERIO-2

- modelo estructurado por pieza y seis sitios;
- PD, GM, CAL derivado, BOP, placa, supuración, movilidad, furcación e implantes;
- edición de borrador y navegación clínica eficiente;
- validación de examen parcial/completitud;
- gráfico periodontal derivado;
- indicadores `% BOP` y `% placa`.

Comparación y PDF continúan fuera de PERIO-2 salvo decisión expresa de una fase posterior.
