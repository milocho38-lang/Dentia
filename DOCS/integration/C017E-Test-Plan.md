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
- `sign_clinical_evolution` firma evolución y desde C017E.3 confirma únicamente eventos odontográficos vinculados/revisados.
- `create_event` permite vincular evento odontográfico con tratamiento/procedimiento.
- Desde C017E.1, `TreatmentProcedure` conserva `source_odontogram_event_id` y clave de idempotencia para el puente explícito.

## Pruebas C017E.1

### Diagnóstico odontográfico → procedimiento planificado

Debe probar:

- Crear procedimiento desde evento confirmado.
- Rechazar evento en borrador.
- Precargar pieza y superficies.
- Un diagnóstico genera varios procedimientos.
- Doble clic devuelve existente o conflicto controlado.
- Reintento con misma `idempotency_key`.
- Dos usuarios simultáneos.
- Permisos insuficientes.
- Evento de otra empresa rechazado.
- Tratamiento de otro paciente rechazado.
- Tratamiento nuevo aparece inmediatamente en `Tratamientos del paciente`.
- La tarjeta del Dental Inspector separa tratamiento, procedimiento, ambos estados, alcance y valor.
- `Ver tratamiento` abre el detalle real del tratamiento.
- `Volver al paciente` retorna a la pestaña Tratamientos.
- Marcar procedimiento `Realizado` no cambia el odontograma en C017E.1.

## Pruebas C017E.2

### Procedimientos → presupuesto versionado

Debe probar:

- Presupuesto captura snapshot dental.
- Presupuesto captura snapshot económico.
- El usuario puede seleccionar explícitamente qué procedimientos entran al presupuesto.
- Doble clic o reintento con `budget_idempotency_key` no crea duplicados.
- Cambio antes de aprobar recalcula presupuesto editable respetando sus procedimientos incluidos.
- Presupuesto aprobado o rechazado no se edita directamente.
- Cambio después de aprobar exige nueva versión.
- Nueva versión copia `BudgetDetail` snapshot del presupuesto origen.
- Guardar cambios de una versión en borrador usa `PATCH` y no crea una versión adicional.
- Guardar una V2 tres veces mantiene la serie con V1 y V2; no aparece V3.
- Una serie con V2 en edición reutiliza ese borrador si se pulsa otra vez “Crear nueva versión”.
- El historial permite abrir cada versión y muestra su total propio.
- Una versión borrador se etiqueta como `En edición`, no como `Histórica`.
- Aprobar nueva versión sustituye la vigente anterior de la misma serie.
- Aprobar una versión nueva bloquea la serie y retira la vigencia anterior antes de marcar la nueva como vigente.
- Una falla durante aprobación hace rollback completo.
- El frontend captura errores de aprobación y mantiene la versión seleccionada sin overlay de Next.js.
- Presupuesto rechazado no queda como versión vigente ni cuenta como venta aprobada.
- Procedimiento cancelado sale de presupuesto editable cuando el presupuesto todavía no está bloqueado.
- Procedimiento originado en odontograma conserva trazabilidad vía `TreatmentProcedure.source_odontogram_event_id`.
- PDF muestra número y versión.

## Pruebas C017E.3

### Procedimiento realizado → evolución → odontograma

Debe probar:

- Registrar realización clínica genera evento odontográfico `DRAFT`.
- Evento generado conserva tratamiento, procedimiento, cita y evolución.
- No se crea evento duplicado por reintento.
- Firma de evolución confirma solo eventos vinculados revisados.
- Firma no confirma borradores ajenos.
- Fallo al generar evento o resolver diagnóstico aborta la transacción.
- Evento manual posterior no se vincula automáticamente.
- Adenda no modifica evento confirmado.
- Selector muestra `Restauración en resina realizada` para `DONE_RESIN`.
- Modal muestra diagnóstico origen leído por `TreatmentProcedure.source_odontogram_event_id`.
- `RESOLVE_ON_SIGN` conserva el diagnóstico en historial y lo excluye del estado vigente.
- `KEEP_ACTIVE` conserva diagnóstico y resultado realizado como condiciones vigentes.
- Procedimiento sin diagnóstico origen permite registrar resultado y no ofrece resolver.
- Vista anatómica y mapa de cinco caras usan el mismo estado vigente.
- Dental Inspector separa eventos históricos de condiciones vigentes.
- No se modifican pagos.
- No se modifican presupuestos.

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
