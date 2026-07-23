# ADR-003 — Trazabilidad clínica-comercial odontograma → tratamiento → presupuesto → evolución

## Estado

Aceptado para diseño. Pendiente de implementación por fases C017E.1–C017E.4.

## Contexto

Dentia ya cuenta con módulos funcionales para historia clínica, evoluciones, odontograma histórico por eventos, tratamientos, procedimientos, presupuestos, pagos, cartera, reportes y Dental Inspector.

La auditoría posterior a C017D.4 identificó que las piezas principales existen, pero todavía hay transiciones manuales entre:

```text
Diagnóstico odontográfico
→ Procedimiento planificado
→ Tratamiento
→ Presupuesto
→ Aprobación
→ Atención clínica
→ Evolución
→ Procedimiento realizado
→ Actualización del odontograma
```

Sin un contrato explícito, existe riesgo de:

- doble digitación;
- procedimientos duplicados;
- eventos odontográficos duplicados;
- modificación indebida de presupuestos aprobados;
- divergencia entre evolución, procedimiento y odontograma;
- mezcla entre ventas, producción clínica e ingresos;
- pérdida de trazabilidad y auditoría.

## Decisión

Dentia utilizará una trazabilidad clínica-comercial explícita, auditable e idempotente.

La conversión de un diagnóstico o hallazgo odontográfico a procedimiento planificado no será automática ni silenciosa. Debe existir una acción explícita:

```text
Agregar al plan de tratamiento
```

El sistema podrá precargar paciente, pieza FDI, superficies, diagnóstico origen, sede, profesional y observación, pero el odontólogo deberá confirmar el procedimiento, tratamiento destino, cantidad, precio, prioridad y observaciones.

## Fuentes oficiales

| Dato | Fuente oficial |
|---|---|
| Estado clínico dental | `OdontogramEvent` confirmado |
| Procedimiento planificado/realizado | `TreatmentProcedure` |
| Venta aprobada | `Budget` aprobado |
| Snapshot económico y dental vendido | `BudgetDetail` |
| Producción clínica | `TreatmentProcedure` en estado `Realizado` |
| Ingreso/caja | `TreatmentPayment` válido |
| Evolución clínica firmada | `ClinicalEvolution` firmada |

El odontograma no calculará ingresos.  
Los pagos no definirán producción clínica.  
Los presupuestos aprobados no modificarán el estado clínico dental.

## Consecuencias positivas

- Reduce doble digitación sin crear automatismos clínicos peligrosos.
- Permite que un diagnóstico origine varios procedimientos.
- Mantiene presupuesto aprobado como snapshot inmutable.
- Mantiene odontograma, tratamiento, evolución y finanzas con fuentes separadas.
- Permite auditoría clara de cada transición.
- Evita que reintentos de red o doble clic creen duplicados.

## Consecuencias negativas

- Requiere nuevas relaciones de trazabilidad.
- Requiere diseño transaccional cuidadoso.
- Aumenta la complejidad de pruebas.
- Obliga a definir cuándo una operación es automática, semiautomática o manual.
- Requiere versionamiento o derivación para modificar presupuestos aprobados.

## Alternativas descartadas

### Crear procedimientos automáticamente desde todo diagnóstico

Descartado porque un diagnóstico puede no requerir tratamiento inmediato, puede requerir varios procedimientos o puede requerir criterio clínico antes de presupuestar.

### Confirmar automáticamente eventos odontográficos al marcar procedimiento realizado

Descartado porque el estado clínico dental debe ser revisado por el odontólogo. El procedimiento realizado puede generar un evento odontográfico en borrador o pendiente de confirmación, pero no confirmado silenciosamente.

### Usar pagos como fuente de producción

Descartado porque ingresos recibidos no equivalen a producción clínica.

### Modificar presupuesto aprobado directamente

Descartado porque el presupuesto aprobado representa una venta aceptada y debe conservar su snapshot económico y dental.

## Referencias de implementación actual

- `backend/app/models/odontogram.py`
- `backend/app/models/treatment.py`
- `backend/app/models/clinical_record.py`
- `backend/app/models/agenda.py`
- `backend/app/services/odontogram_service.py`
- `backend/app/services/treatment_service.py`
- `backend/app/services/clinical_record_service.py`
- `backend/app/services/agenda_service.py`
- `docs/integration/C017E-Clinical-Commercial-Integration-Contract.md`
- `docs/integration/C017E-Entity-Relationship-Proposal.md`
- `docs/integration/C017E-State-Transitions.md`
- `docs/integration/C017E-Test-Plan.md`
