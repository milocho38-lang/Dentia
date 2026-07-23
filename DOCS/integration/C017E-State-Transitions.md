# C017E — Estados y transiciones clínicas-comerciales

## Evento odontográfico

Estados reales actuales en código:

- `DRAFT`
- `CONFIRMED`
- `VOIDED_BY_COMPENSATING_EVENT`

| Desde | Hacia | Acción | Permiso | Precondición | Efectos secundarios | Auditoría | Reversión | Idempotencia |
|---|---|---|---|---|---|---|---|---|
| No existe | `DRAFT` | Crear evento | `odontogram.update_draft` | Historia y odontograma existen | Detalles creados | `ODONTOGRAM_EVENT_CREATED` | Eliminar solo si política futura; hoy se edita borrador | Payload/idempotency futura |
| No existe | `CONFIRMED` | Crear confirmado | `odontogram.update_draft` + `odontogram.confirm` | Detalles válidos | Hash de contenido | `ODONTOGRAM_EVENT_CREATED` | Corrección | Evitar duplicados por origen futuro |
| `DRAFT` | `DRAFT` | Editar borrador | `odontogram.update_draft` | Autor o `DENTIST_ADMIN`, versión coincide | Reemplaza detalles, incrementa versión | `ODONTOGRAM_EVENT_UPDATED_DRAFT` | N/A | Control optimista por `version` |
| `DRAFT` | `CONFIRMED` | Confirmar | `odontogram.confirm` | Autor o `DENTIST_ADMIN`, versión coincide | `confirmed_at`, `confirmed_by`, hash | `ODONTOGRAM_EVENT_CONFIRMED` | Corrección | No confirmar dos veces |
| `CONFIRMED` | `VOIDED_BY_COMPENSATING_EVENT` | Corregir | `odontogram.correct` | Motivo requerido | Crea compensación/reemplazo si aplica | `ODONTOGRAM_EVENT_CORRECTED` | No editar original | Una corrección por intención futura |

## Procedimiento de tratamiento

Estados reales actuales:

- `Pendiente`
- `Agendado`
- `En proceso`
- `Realizado`
- `Cancelado`

Estados conceptuales del contrato:

- Planificado ≈ `Pendiente`
- Agendado ≈ `Agendado`
- En ejecución ≈ `En proceso`
- Realizado ≈ `Realizado`
- Cancelado ≈ `Cancelado`

| Desde | Hacia | Acción | Permiso | Precondición | Efectos secundarios | Auditoría | Reversión | Idempotencia |
|---|---|---|---|---|---|---|---|---|
| No existe | `Pendiente` | Crear procedimiento | `treatments.update` | Tratamiento no final/cancelado | Recalcula presupuestos editables | `PROCEDURE_CREATED` | Editar/cancelar si permitido | Futura clave origen odontograma |
| `Pendiente` | `Agendado` | Vincular cita | `treatments.update` / `appointments.update` | Cita del mismo paciente | Cita queda vinculada | `APPOINTMENT_LINKED_TREATMENT_PROCEDURE` | Desvinculación futura | Procedimiento+cita único |
| `Pendiente`/`Agendado`/`En proceso` | `Realizado` | Marcar realizado | `treatments.update` | No cancelado | `performed_at`, tratamiento puede pasar a `En ejecución` | `PROCEDURE_MARKED_DONE` | Corrección futura | No repetir si ya realizado |
| No realizado | `Cancelado` | Cancelar | `treatments.update` | Motivo, presupuesto aprobado exige nueva versión | Recalcula presupuestos editables | `PROCEDURE_CANCELLED` | Nuevo procedimiento | No repetir |

## Tratamiento

Estados reales actuales:

- `Borrador`
- `Presupuestado`
- `Aprobado`
- `En ejecución`
- `Pausado`
- `Finalizado`
- `Cancelado`

| Desde | Hacia | Acción | Permiso | Precondición | Efectos secundarios | Auditoría | Reversión | Idempotencia |
|---|---|---|---|---|---|---|---|---|
| No existe | `Borrador` | Crear tratamiento | `treatments.create` | Paciente accesible | Tratamiento base | `TREATMENT_CREATED` | Cancelar | N/A |
| `Borrador` | `Presupuestado` | Crear presupuesto | `budgets.create` | Procedimientos activos | Presupuesto borrador | `BUDGET_CREATED` | Rechazar/cancelar | Versión por tratamiento |
| `Borrador`/`Presupuestado` | `Aprobado` | Aprobar presupuesto | `budgets.update` | Presupuesto válido | Tratamiento aprobado | `BUDGET_APPROVED` | Nueva versión/cancelar | No aprobar dos veces |
| `Aprobado` | `En ejecución` | Pago o procedimiento realizado | `payments.create` / `treatments.update` | Pago válido o procedimiento realizado | Inicio operativo | `PAYMENT_REGISTERED` / `PROCEDURE_MARKED_DONE` | Reversa/corrección | Idempotencia por pago/procedimiento |
| Activo | `Finalizado` | Cerrar tratamiento | `treatments.close` | Sin procedimientos pendientes | `end_date` | `TREATMENT_CLOSED` | Reapertura no definida | No repetir |
| No finalizado | `Cancelado` | Cancelar | `treatments.cancel` | Motivo | Cierre operativo | `TREATMENT_CANCELLED` | No definido | No repetir |

## Presupuesto

Estados reales actuales:

- `Borrador`
- `Pendiente de aprobación`
- `Aprobado`
- `Rechazado`
- `En ejecución`
- `Finalizado`

El contrato menciona `Vencido` y `Sustituido`; no existen como estados reales actuales.

| Desde | Hacia | Acción | Permiso | Precondición | Efectos secundarios | Auditoría | Reversión | Idempotencia |
|---|---|---|---|---|---|---|---|---|
| No existe | `Borrador` | Crear presupuesto | `budgets.create` | Hay procedimientos no cancelados | Snapshot `BudgetDetail` | `BUDGET_CREATED` | Eliminar no definido | Versión única por tratamiento |
| `Borrador` | `Pendiente de aprobación` | Enviar | `budgets.update` | Datos completos | Estado enviado | `BUDGET_SUBMITTED` | Volver no definido | No repetir |
| `Borrador`/`Pendiente de aprobación` | `Aprobado` | Aprobar | `budgets.update` | Valor final >= 0 | `approved_at`, tratamiento aprobado | `BUDGET_APPROVED` | Nueva versión | No aprobar dos veces |
| `Borrador`/`Pendiente de aprobación` | `Rechazado` | Rechazar | `budgets.update` | Usuario autorizado | `rejected_at` | `BUDGET_REJECTED` | Duplicar versión | No repetir |
| Aprobado | Nueva versión | Duplicar/derivar | `budgets.create` | Cambio requerido | Nuevo presupuesto | `BUDGET_CREATED` | Rechazar versión | Versión incremental |

## Evolución clínica

Estados reales actuales:

- `DRAFT`
- `SIGNED`
- `VOIDED_BY_COMPENSATING_RECORD`

“Con adenda” no es estado; se representa por `ClinicalEvolutionAddendum`.

| Desde | Hacia | Acción | Permiso | Precondición | Efectos secundarios | Auditoría | Reversión | Idempotencia |
|---|---|---|---|---|---|---|---|---|
| No existe | `DRAFT` | Crear evolución | `clinical_evolutions.create` | Historia activa, cita única si aplica | Timeline | `CLINICAL_EVOLUTION_CREATED` | Editar borrador | Una principal por cita |
| `DRAFT` | `DRAFT` | Editar | `clinical_evolutions.update_draft` | Versión coincide | Reemplaza links a procedimientos | `CLINICAL_EVOLUTION_DRAFT_UPDATED` | N/A | Control optimista |
| `DRAFT` | `SIGNED` | Firmar | `clinical_evolutions.sign` | Confirmación completa, versión coincide | Hash, timeline | `CLINICAL_EVOLUTION_SIGNED` | Adenda | No firmar dos veces |
| `SIGNED` | `SIGNED` + adenda | Agregar adenda | `clinical_evolutions.add_addendum` | Evolución firmada | Nueva adenda | `CLINICAL_EVOLUTION_ADDENDUM_CREATED` | Nueva adenda | No editar firma |

## Transiciones compuestas futuras

| Transición | Tipo recomendado | Atomicidad |
|---|---|---|
| Diagnóstico → procedimiento planificado | SEMIAUTOMÁTICA | Una transacción |
| Procedimiento → presupuesto editable | SEMIAUTOMÁTICA | Recalcular solo presupuestos editables |
| Presupuesto aprobado → tratamiento aprobado | AUTOMÁTICA | Misma transacción de aprobación |
| Procedimiento realizado → evento odontográfico borrador | SEMIAUTOMÁTICA | Misma transacción o fallo explícito |
| Firma evolución → confirmar eventos vinculados | SEMIAUTOMÁTICA | Misma transacción preferida |
