# C017E — Contrato de integración clínica-comercial

## Propósito

Definir el contrato funcional y técnico para integrar:

```text
Odontograma histórico
→ Tratamientos
→ Procedimientos
→ Presupuestos
→ Evoluciones
→ Pagos
→ Reportes
```

Este documento no implementa el puente. Establece las reglas que deberán respetar C017E.1–C017E.4.

## Alcance actual inspeccionado

Código inspeccionado:

- `backend/app/models/odontogram.py`
- `backend/app/models/treatment.py`
- `backend/app/models/clinical_record.py`
- `backend/app/models/agenda.py`
- `backend/app/services/odontogram_service.py`
- `backend/app/services/treatment_service.py`
- `backend/app/services/clinical_record_service.py`
- `backend/app/services/agenda_service.py`
- `backend/app/routers/odontogram_router.py`
- `backend/app/routers/treatment_router.py`
- `backend/app/routers/clinical_record_router.py`
- `backend/app/routers/agenda_router.py`
- `frontend/components/patients/OdontogramPage.tsx`
- `frontend/components/odontogram/inspector/`
- `frontend/components/treatments/`
- `frontend/components/patients/ClinicalRecordPage.tsx`
- `backend/migrations/versions/`

Documentación inspeccionada:

- `docs/D002 - REGLAS DE NEGOCIO.md`
- `docs/D003A - MODELO DATOS.md`
- `docs/D003B - MODELO DATOS.md`
- `docs/D003C - MODELO DATOS.md`
- `docs/HISTORIAL_DECISIONES.md`

## Principios obligatorios

### Conversión explícita

Un diagnóstico o hallazgo odontográfico nunca crea silenciosamente un procedimiento.

Debe existir una acción explícita:

```text
Agregar al plan de tratamiento
```

El formulario podrá precargar:

- paciente;
- pieza FDI;
- superficies;
- diagnóstico o hallazgo origen;
- observación;
- sede;
- profesional.

El odontólogo debe confirmar:

- procedimiento;
- tratamiento destino;
- cantidad;
- precio;
- prioridad;
- observaciones.

### Un origen puede producir varios destinos

Un evento odontográfico puede originar varios procedimientos.

Ejemplo:

```text
Diagnóstico: pérdida extensa de estructura dental
→ Endodoncia
→ Reconstrucción
→ Corona
```

Cada procedimiento debe tener trazabilidad propia hacia el evento origen.

### Idempotencia

Repetir una acción no debe crear accidentalmente el mismo procedimiento.

La deduplicación no puede basarse únicamente en nombre. Debe considerar:

- empresa;
- paciente;
- evento odontográfico origen;
- tratamiento destino;
- catálogo/procedimiento seleccionado;
- alcance dental;
- pieza;
- superficies;
- estado no cancelado;
- clave idempotente de intento cuando aplique.

### Presupuesto aprobado como snapshot

Un presupuesto aprobado no debe modificarse directamente en:

- pieza;
- superficies;
- procedimiento;
- cantidad;
- precio;
- descuento;
- subtotal;
- total.

Los cambios requieren nueva versión o presupuesto derivado.

### Realización clínica

Marcar un procedimiento como realizado no debe crear silenciosamente un evento odontográfico confirmado.

Debe generar, cuando corresponda, un evento odontográfico vinculado en estado `DRAFT` o pendiente de confirmación clínica.

### Firma de evolución

Firmar una evolución puede confirmar únicamente:

- procedimientos asociados explícitamente a esa evolución;
- eventos odontográficos generados desde esos procedimientos;
- elementos revisados explícitamente antes de firmar.

No debe confirmar todos los borradores del paciente ni todos los borradores de la pieza.

## Fuentes oficiales

| Métrica o dato | Fuente oficial | Exclusiones |
|---|---|---|
| Presupuesto enviado | `Budget` con estado de envío | No pagos |
| Venta aprobada | `Budget` aprobado | No procedimientos realizados |
| Producción clínica | `TreatmentProcedure` realizado | No pagos |
| Ingreso | `TreatmentPayment` válido | No presupuesto aprobado |
| Cartera | Saldo financiero entre presupuesto aprobado y pagos válidos | No odontograma |
| Estado odontográfico | `OdontogramEvent` confirmado | No pagos ni presupuestos |
| Evolución legal clínica | `ClinicalEvolution` firmada | No evento odontográfico sin firma si la política exige firma |

## Mapa de entidades actuales

| Entidad | Identificador | Empresa | Sede | Paciente | Profesional | Estado | Pieza/superficies | Relaciones actuales | Inmutabilidad | Auditoría |
|---|---|---|---|---|---|---|---|---|---|---|
| Evento odontográfico | `OdontogramEvent.id` | `company_id` | `site_id` | `patient_id` | `dentist_id` | `DRAFT`, `CONFIRMED`, `VOIDED_BY_COMPENSATING_EVENT` | En `OdontogramEventDetail` | Puede vincular `evolution_id`, `appointment_id`, `treatment_id`, `procedure_id` | Confirmado no se edita; corrección compensa | `ODONTOGRAM_EVENT_*` |
| Detalle odontográfico | `OdontogramEventDetail.id` | `company_id` | No directa | Por evento | Por evento | Capa | `scope_type`, `tooth_code`, `surfaces` | `event_id`, `catalog_item_id` | Depende del evento | Por evento padre |
| Tratamiento | `Treatment.id` | `company_id` | `main_site_id` | `patient_id` | `responsible_dentist_id` | `Borrador`, `Presupuestado`, `Aprobado`, `En ejecución`, `Pausado`, `Finalizado`, `Cancelado` | No directa | Procedimientos, presupuestos, pagos | Final/cancelado restringe cambios | `TREATMENT_*` |
| Procedimiento | `TreatmentProcedure.id` | `company_id` | `site_id` | `patient_id` | `dentist_id` | `Pendiente`, `Agendado`, `En proceso`, `Realizado`, `Cancelado` | `scope_type`, `tooth`, `surfaces` | `treatment_id`, `appointment_id`, catálogo | Realizado no se edita sin corrección | `PROCEDURE_*` |
| Presupuesto | `Budget.id` | `company_id` | Por tratamiento | `patient_id` | Por tratamiento | `Borrador`, `Pendiente de aprobación`, `Aprobado`, `Rechazado`, `En ejecución`, `Finalizado` | Por detalles | `treatment_id` | Aprobado/rechazado no permite edición económica directa | `BUDGET_*` |
| Detalle presupuesto | `BudgetDetail.id` | `company_id` | No directa | Por presupuesto | Por procedimiento | Snapshot | `scope_type`, `tooth`, `surfaces` | `budget_id`, `procedure_id` | Snapshot del presupuesto | Por presupuesto |
| Evolución | `ClinicalEvolution.id` | `company_id` | `site_id` | `patient_id` | `dentist_id` | `DRAFT`, `SIGNED`, `VOIDED_BY_COMPENSATING_RECORD` | Por links a procedimientos | `appointment_id`, `treatment_id`, `followup_id` | Firmada no se edita; adenda | `CLINICAL_EVOLUTION_*` |
| Procedimiento de evolución | `ClinicalEvolutionProcedure.id` | `company_id` | Por evolución | Por evolución | Por evolución | Acción `PLANNED`, `PERFORMED`, `REVIEWED`, `SUSPENDED` | Por procedimiento | `evolution_id`, `treatment_id`, `procedure_id` | Depende de evolución | Por evolución |
| Cita | `Appointment.id` | `company_id` | `site_id` | `patient_id` | `dentist_id` | `Programada`, `Confirmada`, `Atendida`, etc. | Por procedimiento vinculado | `treatment_id`, `treatment_procedure_id` | Historial separado | `AppointmentHistory`, auditoría |
| Pago | `TreatmentPayment.id` | `company_id` | `site_id` | `patient_id` | `dentist_id` | `valido`, reversado según servicio | No clínica | `treatment_id`, `budget_id`; tabla con procedimientos pagados | Reversa, no edición directa | `PAYMENT_*` |
| Auditoría | `AuditEvent.id` | `company_id` | Según metadata | Según entidad | `user_id` | Resultado | No aplica | Entidad/acción/detalle | Inmutable | Es la auditoría |

## Relaciones actuales relevantes

Ya existen:

- `OdontogramEvent.evolution_id`
- `OdontogramEvent.appointment_id`
- `OdontogramEvent.treatment_id`
- `OdontogramEvent.procedure_id`
- `TreatmentProcedure.appointment_id`
- `Appointment.treatment_id`
- `Appointment.treatment_procedure_id`
- `BudgetDetail.procedure_id`
- `ClinicalEvolution.treatment_id`
- `ClinicalEvolution.appointment_id`
- `ClinicalEvolutionProcedure.procedure_id`
- `TreatmentPayment.budget_id`
- `TreatmentPaymentProcedure.procedure_id`

Relaciones ausentes:

- `TreatmentProcedure.source_odontogram_event_id`
- relación explícita uno-a-muchos entre evento odontográfico origen y procedimientos generados;
- relación entre `BudgetDetail` y evento odontográfico origen preservada como snapshot;
- relación entre procedimiento realizado y evento odontográfico generado;
- relación explícita entre firma de evolución y eventos odontográficos confirmados por esa firma;
- tabla de idempotencia/intentos para acciones clínicas-comerciales.

## Flujo objetivo

| Paso | Acción | Tipo | Resultado |
|---|---|---|---|
| 1 | Odontólogo registra diagnóstico odontográfico | MANUAL | `OdontogramEvent` `DRAFT` o `CONFIRMED` |
| 2 | Selecciona “Agregar al plan de tratamiento” | MANUAL | Abre formulario precargado |
| 3 | Confirma procedimiento y tratamiento destino | MANUAL | Datos validados |
| 4 | Se crea procedimiento planificado vinculado al evento origen | SEMIAUTOMÁTICO | `TreatmentProcedure` `Pendiente` |
| 5 | Procedimiento entra a presupuesto | SEMIAUTOMÁTICO | `BudgetDetail` snapshot |
| 6 | Presupuesto se aprueba | MANUAL | `Budget` `Aprobado`, tratamiento `Aprobado` |
| 7 | Procedimiento se agenda o vincula a cita | SEMIAUTOMÁTICO | `Appointment.treatment_procedure_id` |
| 8 | Durante atención se vincula a evolución | SEMIAUTOMÁTICO | `ClinicalEvolutionProcedure` |
| 9 | Procedimiento se marca realizado | MANUAL | `TreatmentProcedure` `Realizado` |
| 10 | Se genera evento odontográfico realizado en borrador | SEMIAUTOMÁTICO | `OdontogramEvent` `DRAFT` vinculado |
| 11 | Odontólogo revisa antes de firmar | MANUAL | Confirmación explícita |
| 12 | Firma de evolución confirma eventos revisados | SEMIAUTOMÁTICO | Evolución `SIGNED`, evento odontográfico `CONFIRMED` |
| 13 | Reportes actualizan producción | AUTOMÁTICO | Producción por procedimientos realizados |
| 14 | Pagos afectan cartera/caja | MANUAL/SEMIAUTOMÁTICO | Ingreso válido, sin alterar estado clínico |

## Contrato de idempotencia

### Crear procedimiento desde odontograma

Entrada conceptual:

- `source_odontogram_event_id`
- `target_treatment_id`
- `procedure_catalog_id` o procedimiento libre
- `scope_type`
- `tooth`
- `surfaces`
- `quantity`
- `unit_value`
- `idempotency_key`

Regla:

- Si existe un procedimiento no cancelado con la misma clave de origen y equivalencia clínica/económica, devolver el existente.
- Si el usuario confirma explícitamente “crear otro procedimiento desde el mismo diagnóstico”, debe registrarse un motivo o diferenciador clínico.
- No deduplicar solo por nombre.

### Generar evento odontográfico desde procedimiento realizado

Entrada conceptual:

- `source_treatment_procedure_id`
- `source_clinical_evolution_id`
- `appointment_id`
- `tooth`
- `surfaces`
- `catalog_item_id` equivalente realizado
- `idempotency_key`

Regla:

- Si ya existe evento odontográfico `DRAFT` o `CONFIRMED` generado para ese procedimiento y evolución, devolverlo.
- Si existe evento confirmado, no crear otro salvo corrección/retratamiento explícito.

## Atomicidad

### Crear procedimiento desde odontograma

Debe ser una sola transacción:

```text
validar evento origen
validar tratamiento destino
validar alcance dental
validar presupuesto editable si aplica
crear procedimiento
crear vínculo origen→procedimiento
auditar
commit
```

Si falla cualquier paso, no debe quedar procedimiento sin vínculo ni vínculo sin procedimiento.

### Firmar evolución con eventos odontográficos vinculados

Debe evitar:

- evolución firmada con procedimiento sin actualizar;
- procedimiento realizado sin evento odontográfico generado cuando el usuario lo confirmó;
- evento confirmado sin evolución firmada;
- confirmación parcial silenciosa.

Si falla la confirmación odontográfica, la firma debe abortarse o devolver fallo parcial explícito según política aprobada. Para datos clínicos inmutables se recomienda abortar la transacción completa en la firma, salvo que el usuario haya elegido un flujo parcial documentado.

## Casos especiales

| Caso | Regla |
|---|---|
| Un diagnóstico con varios procedimientos | Permitir varios procedimientos con mismo `source_odontogram_event_id`, diferenciados por catálogo/alcance/motivo. |
| Varios diagnósticos para un procedimiento | Usar tabla intermedia futura procedimiento↔evento origen. |
| Procedimiento sin pieza | `scope_type = GENERAL`; no pintar superficie ni diente. |
| Procedimiento de pieza completa | `scope_type = TOOTH`; pieza requerida, superficies nulas. |
| Procedimiento con varias superficies | `scope_type = TOOTH_SURFACE`; superficies snapshot ordenadas/canonizadas. |
| Tratamiento realizado parcialmente | Solo procedimientos marcados `Realizado` cuentan como producción. |
| Cambio de pieza antes de aprobar presupuesto | Permitido si presupuesto editable; recalcular snapshot. |
| Cambio de superficie después de aprobar presupuesto | Requiere nueva versión o presupuesto derivado. |
| Presupuesto rechazado | No genera venta; puede duplicarse/derivarse. |
| Presupuesto vencido | No aprobar sin confirmación o renovación según política futura. |
| Procedimiento cancelado | No cuenta en presupuesto editable ni producción. |
| Procedimiento repetido en otra fecha | Permitido con nuevo procedimiento o retratamiento explícito. |
| Retratamiento | Crear procedimiento nuevo, referenciar antecedente si aplica. |
| Procedimiento realizado sin presupuesto | Permitido solo si política actual lo permite; pagos ya exigen presupuesto o tratamiento aprobado. |
| Evento odontográfico manual posterior | Permitido; no inferir vínculo comercial si no existe. |
| Reversión clínica | Evento compensatorio, no borrado. |
| Adenda de evolución | No reabre evolución; puede documentar aclaración. |
| Doble clic/reintento | Idempotencia obligatoria. |
| Dos usuarios simultáneos | Bloqueo transaccional + restricción única o clave idempotente. |

## Permisos actuales y necesidades

| Acción | Permisos actuales candidatos | ¿Suficiente? | Nota |
|---|---|---|---|
| Ver diagnóstico | `odontogram.view`, `clinical_records.view_sensitive` según contexto | PARCIAL | Odontograma ya protege vista; cuidado con sensibilidad clínica. |
| Convertir diagnóstico en procedimiento | `odontogram.view` + `treatments.update` o `treatments.create` | PARCIAL | Puede requerir permiso nuevo futuro si se quiere granularidad. |
| Editar procedimiento planificado | `treatments.update` | SÍ para MVP | Respetar presupuesto aprobado. |
| Crear presupuesto | `budgets.create` | SÍ | Ya existe. |
| Aprobar presupuesto | `budgets.update` | PARCIAL | Tal vez separar `budgets.approve` en futuro. |
| Marcar procedimiento realizado | `treatments.update` | SÍ para MVP | Ya existe. |
| Firmar evolución | `clinical_evolutions.sign` | SÍ | Ya existe. |
| Confirmar evento odontográfico | `odontogram.confirm` | SÍ | Ya existe. |
| Revertir/corregir operación | `odontogram.correct`, `payments.reverse`, `treatments.cancel` | PARCIAL | Operación compuesta requerirá política. |

No se crean permisos nuevos en C017E.0.

## Auditoría futura mínima

| Evento | Mínimo a guardar |
|---|---|
| `ODONTOGRAM_EVENT_LINKED_TO_PROCEDURE` | empresa, sede, usuario, paciente, evento origen, procedimiento destino, pieza, superficies |
| `PROCEDURE_CREATED_FROM_ODONTOGRAM` | empresa, tratamiento, procedimiento, evento origen, idempotency key |
| `PROCEDURE_ADDED_TO_BUDGET` | presupuesto, detalle, procedimiento, snapshot dental |
| `BUDGET_APPROVED` | presupuesto, versión, valor final, usuario |
| `PROCEDURE_MARKED_COMPLETED` | procedimiento, estado anterior/posterior, cita/evolución si aplica |
| `ODONTOGRAM_DRAFT_GENERATED` | procedimiento origen, evento generado, evolución/cita |
| `EVOLUTION_SIGNED` | evolución, versión, hash |
| `ODONTOGRAM_EVENT_CONFIRMED_FROM_EVOLUTION` | evolución, evento, procedimiento |

No guardar contenido clínico completo en auditoría.

## Reportes actuales a vigilar

| Reporte/métrica | Riesgo |
|---|---|
| Producción clínica | Debe usar procedimientos realizados, no pagos. |
| Venta aprobada | Debe usar presupuestos aprobados, no pagos. |
| Ingreso | Debe usar pagos válidos, excluyendo reversados. |
| Estado odontográfico | Debe usar eventos odontográficos confirmados, no procedimientos. |
| Cartera | Debe usar saldo financiero, no odontograma. |

No se corrigen reportes en C017E.0.

## Plan de implementación futuro

Ver detalle en `docs/integration/C017E-Test-Plan.md`.
