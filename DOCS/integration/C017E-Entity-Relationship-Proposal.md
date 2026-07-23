# C017E — Propuesta de relaciones entidad-relación

## Estado

Propuesta de diseño. No implementada.

## Relación mínima recomendada

### Opción preferida para C017E.1

Agregar trazabilidad desde procedimiento hacia evento odontográfico origen:

```text
TreatmentProcedure.source_odontogram_event_id → OdontogramEvent.id
```

Motivo:

- El procedimiento es el objeto comercial/operativo que nace desde el diagnóstico.
- El evento odontográfico ya existe y representa el estado clínico fuente.
- Un evento puede originar muchos procedimientos.
- Cada procedimiento necesita saber de dónde nació.

Cardinalidad:

```text
OdontogramEvent 1 ── N TreatmentProcedure
```

Política:

- `ondelete=SET NULL` o `RESTRICT` según decisión clínica.
- Recomendación: `SET NULL` si se preserva snapshot textual del origen; `RESTRICT` si se exige trazabilidad completa.
- Siempre filtrar por `company_id`.

Índices:

- `(empresa_id, source_odontogram_event_id)`
- `(empresa_id, tratamiento_id, source_odontogram_event_id)`

Restricción idempotente futura:

No basta una única restricción global, porque un diagnóstico puede originar varios procedimientos. Se recomienda una tabla de vínculos o clave idempotente.

### Tabla intermedia recomendada para mayor flexibilidad

```text
clinical_commercial_links
```

Campos conceptuales:

- `id`
- `empresa_id`
- `paciente_id`
- `source_type`
- `source_id`
- `target_type`
- `target_id`
- `relationship_type`
- `idempotency_key`
- `status`
- `created_by`
- `created_at`
- `metadata`

Ventajas:

- Soporta varios diagnósticos para un procedimiento.
- Soporta procedimiento realizado → evento odontográfico generado.
- Soporta presupuesto detalle ↔ procedimiento ↔ origen clínico.
- Permite auditoría e idempotencia sin sobrecargar modelos existentes.

Desventajas:

- Más complejidad.
- Requiere validaciones fuertes para no crear vínculos inconsistentes.

## Campos conceptuales evaluados

| Campo | Entidad sugerida | ¿FK? | Cardinalidad | Recomendación |
|---|---|---:|---|---|
| `source_odontogram_event_id` | `TreatmentProcedure` | Sí | Evento 1 → N procedimientos | Implementar en C017E.1 o vía tabla intermedia |
| `source_treatment_procedure_id` | `OdontogramEvent` | Ya existe como `procedure_id` | Procedimiento 1 → N eventos | Reutilizar con política clara |
| `source_budget_detail_id` | `TreatmentProcedure` o link table | Opcional | Detalle 1 → N acciones | No necesario para C017E.1 |
| `source_clinical_evolution_id` | `OdontogramEvent` | Ya existe como `evolution_id` | Evolución 1 → N eventos | Reutilizar |
| `generated_odontogram_event_id` | Link table | Sí | Procedimiento/evolución → evento | Mejor en tabla intermedia |

## BudgetDetail como snapshot

`BudgetDetail` ya conserva:

- `procedure_id`
- `name`
- `category`
- `quantity`
- `unit_value`
- `total_value`
- `scope_type`
- `zone`
- `tooth`
- `surfaces`

Para trazabilidad futura, se recomienda snapshot adicional:

- `source_odontogram_event_id`
- `source_odontogram_event_type`
- `source_odontogram_catalog_code`
- `source_tooth`
- `source_surfaces`

Esto permite preservar la venta aunque el procedimiento o evento origen cambie después.

## Procedimiento realizado → evento odontográfico

El flujo futuro debe crear evento en borrador:

```text
TreatmentProcedure Realizado
→ OdontogramEvent DRAFT
   procedure_id = TreatmentProcedure.id
   treatment_id = Treatment.id
   evolution_id = ClinicalEvolution.id cuando exista
   appointment_id = Appointment.id cuando exista
```

No confirmar automáticamente salvo firma/revisión explícita.

## Firma de evolución → confirmación de eventos

La evolución firmada puede confirmar eventos odontográficos vinculados si:

- están en `DRAFT`;
- pertenecen al mismo paciente y empresa;
- están vinculados a esa evolución;
- están vinculados a procedimientos asociados a esa evolución;
- fueron revisados explícitamente en UI.

No confirmar:

- borradores sin `evolution_id`;
- borradores de otra cita;
- borradores de otra pieza;
- borradores del mismo paciente no incluidos en la evolución.

## Política de reversión

| Objeto | Reversión |
---|---|
| Evento odontográfico confirmado | Evento compensatorio o corrección; no edición directa |
| Procedimiento planificado | Cancelación o edición si presupuesto editable |
| Procedimiento realizado | Corrección clínica futura; no edición directa simple |
| Presupuesto aprobado | Nueva versión o derivado |
| Pago válido | Reversa |
| Evolución firmada | Adenda |

## Aislamiento multiempresa

Toda relación futura debe incluir validación:

```text
source.company_id == target.company_id == context.user.company_id
```

Los índices compuestos deben iniciar por `empresa_id` cuando participen en consultas de negocio.
