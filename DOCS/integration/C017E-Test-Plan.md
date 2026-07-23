# C017E — Plan de pruebas de integración clínica-comercial

## Objetivo

Caracterizar el comportamiento actual y definir la suite futura para implementar C017E sin romper módulos existentes.

## Pruebas de caracterización creadas en C017E.0

Archivo:

```text
frontend/scripts/clinical-commercial-characterization-tests.mjs
```

Estas pruebas son estáticas/no invasivas. Verifican contratos actuales en código fuente sin levantar base de datos ni modificar comportamiento.

Cubren:

- `OdontogramEvent` ya puede guardar `treatment_id` y `procedure_id`.
- `TreatmentProcedure` conserva alcance dental (`scope_type`, `tooth`, `surfaces`).
- `BudgetDetail` conserva snapshot dental y económico.
- `ClinicalEvolutionProcedure` vincula evolución con procedimiento.
- `Appointment` vincula tratamiento y procedimiento.
- `create_budget` usa procedimientos activos y crea snapshot.
- `update_procedure` bloquea cambios si hay presupuesto aprobado sin presupuesto editable.
- `mark_procedure_done` marca procedimiento realizado y no crea evento odontográfico.
- `sign_clinical_evolution` firma evolución y no confirma eventos odontográficos.
- `create_event` permite vincular evento odontográfico con tratamiento/procedimiento.
- No existe todavía `source_odontogram_event_id` en procedimientos.

## Pruebas futuras C017E.1

### Diagnóstico odontográfico → procedimiento planificado

Debe probar:

- Crear procedimiento desde evento confirmado.
- Crear procedimiento desde evento en borrador si la política lo permite.
- Precargar pieza y superficies.
- Un diagnóstico genera varios procedimientos.
- Doble clic devuelve existente o conflicto controlado.
- Reintento con misma `idempotency_key`.
- Dos usuarios simultáneos.
- Permisos insuficientes.
- Evento de otra empresa rechazado.
- Tratamiento de otro paciente rechazado.

## Pruebas futuras C017E.2

### Procedimientos → presupuesto versionado

Debe probar:

- Presupuesto captura snapshot dental.
- Presupuesto captura snapshot económico.
- Cambio antes de aprobar recalcula presupuesto editable.
- Cambio después de aprobar exige nueva versión.
- Presupuesto rechazado no cuenta como venta.
- Presupuesto vencido según política futura.
- Procedimiento cancelado sale de presupuesto editable.
- Procedimiento originado en odontograma conserva trazabilidad.

## Pruebas futuras C017E.3

### Procedimiento realizado → evolución → odontograma

Debe probar:

- Marcar procedimiento realizado genera evento odontográfico `DRAFT`.
- Evento generado conserva tratamiento, procedimiento, cita y evolución.
- No se crea evento duplicado por reintento.
- Firma de evolución confirma solo eventos vinculados revisados.
- Firma no confirma borradores ajenos.
- Fallo al generar evento aborta o reporta fallo según contrato.
- Evento manual posterior no se vincula automáticamente.
- Adenda no modifica evento confirmado.

## Pruebas futuras C017E.4

### Endurecimiento integral

Debe probar:

- Multiempresa.
- Multisede.
- DENTIST, DENTIST_ADMIN, ADMINISTRATOR, SECRETARY, PLATFORM_ADMIN.
- Bogotá/Santiago.
- Presupuesto/pago/reversa/cartera.
- Reportes: ventas, producción, ingresos, cartera.
- Auditoría completa.
- Carga concurrente.

## Casos especiales obligatorios

| Caso | Prueba esperada |
|---|---|
| Diagnóstico con varios procedimientos | Cada procedimiento tiene trazabilidad independiente |
| Varios diagnósticos para un procedimiento | Tabla intermedia futura o bloqueo documentado |
| Procedimiento sin pieza | No crea evento superficial falso |
| Procedimiento pieza completa | Snapshot con `TOOTH` |
| Procedimiento varias superficies | Snapshot preserva lista canonizada |
| Tratamiento parcialmente realizado | Producción solo por realizados |
| Cambio pieza antes de aprobar | Permitido en presupuesto editable |
| Cambio superficie después de aprobar | Requiere nueva versión |
| Presupuesto rechazado | No venta |
| Procedimiento repetido | Permitido con diferenciador clínico |
| Retratamiento | Nuevo procedimiento, no deduplicar indebidamente |
| Reversión clínica | Evento compensatorio |
| Doble clic | Sin duplicado |
| Dos usuarios | Lock/restricción/idempotencia |

## Comandos de validación C017E.0

```bash
node frontend/scripts/clinical-commercial-characterization-tests.mjs
node frontend/scripts/dental-inspector-tests.mjs
node frontend/scripts/classic-orientation-tests.mjs
npm --prefix frontend run lint
npm --prefix frontend run build
python3 -m compileall backend/app
git diff --check
```

## Criterios para declarar C017E completo

- El diagnóstico odontográfico puede convertirse explícitamente en uno o varios procedimientos.
- El procedimiento conserva vínculo con su origen clínico.
- El presupuesto aprobado conserva snapshot inmutable.
- Procedimiento realizado genera evento odontográfico borrador, no confirmado silenciosamente.
- Firma de evolución confirma únicamente eventos vinculados y revisados.
- Reportes no mezclan ventas, producción, ingresos ni estado clínico.
- Existen pruebas automáticas de negocio y permisos.
- Auditoría registra cada transición relevante sin contenido clínico completo.
