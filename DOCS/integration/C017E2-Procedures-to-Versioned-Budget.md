# C017E.2 — Procedimientos → presupuesto versionado e inmutable

## Estado

Implementado como integración clínica-comercial explícita.

## Objetivo

Convertir procedimientos planificados de un tratamiento en presupuestos versionados, preservando una fotografía comercial inmutable cuando el presupuesto deja de ser editable.

Este flujo separa estrictamente:

- procedimiento clínico/comercial planificado;
- presupuesto como propuesta económica;
- venta aprobada;
- pagos;
- producción clínica;
- estado odontográfico.

## Fuente de verdad

| Dato | Fuente oficial |
|---|---|
| Procedimiento planificado | `TreatmentProcedure` |
| Alcance dental del procedimiento | `TreatmentProcedure.scope_type`, `tooth`, `surfaces`, `zone` |
| Presupuesto | `Budget` |
| Línea congelada del presupuesto | `BudgetDetail` |
| Versión vigente aprobada | `Budget.es_version_vigente = true` |
| Ingreso | Pagos válidos, no presupuestos |
| Producción clínica | Procedimientos realizados, no presupuestos |
| Estado odontográfico | Eventos odontográficos confirmados, no presupuestos |

## Modelo implementado

### `Budget`

Campos agregados:

- `budget_series_id`
- `previous_budget_id`
- `superseded_by_id`
- `es_version_vigente`
- `motivo_version`
- `budget_idempotency_key`

Reglas:

- La primera versión de una serie usa `budget_series_id = id`.
- Las versiones siguientes conservan la misma serie.
- `version` incrementa dentro de la serie.
- Solo una versión aprobada puede estar vigente por empresa y serie.
- Crear una versión nueva copia snapshots del presupuesto origen, no lee de nuevo los procedimientos vivos.

### `BudgetDetail`

Cada detalle conserva snapshot de:

- procedimiento origen;
- nombre;
- categoría;
- cantidad;
- valor unitario;
- valor total;
- alcance;
- zona;
- pieza;
- superficies.

El detalle no depende de cambios posteriores del procedimiento para explicar qué se presupuestó.

## Reglas funcionales

### Crear presupuesto

El usuario selecciona explícitamente uno o varios procedimientos elegibles del tratamiento.

Si no se envía selección, el backend conserva compatibilidad y utiliza los procedimientos activos elegibles.

El presupuesto se crea como `Borrador`, versión `1`, con una serie propia.

### Editar presupuesto editable

Solo se permite modificar presupuestos en:

- `Borrador`;
- `Pendiente de aprobación`.

Los presupuestos editables recalculan sus líneas respetando la selección enviada para esa versión.

Desde C017E.2-FIX1, una versión en `Borrador` puede actualizar su selección de procedimientos mediante `PATCH /api/budgets/{budget_id}`. Esta operación reemplaza los `BudgetDetail` de esa versión, recalcula subtotal/descuento/total y no toca versiones aprobadas anteriores.

### Aprobar presupuesto

Al aprobar:

- se valida que existan líneas;
- se valida que la versión esté en `Borrador` o `Pendiente de aprobación`;
- se bloquea la serie completa del presupuesto;
- se retira primero la vigencia de la versión aprobada anterior;
- se ejecuta `flush` explícito para que PostgreSQL vea la serie sin vigente temporal;
- se marca `approved_at`;
- se marca la versión como vigente;
- se sustituye la versión vigente anterior de la misma serie, si existe;
- el tratamiento pasa a `Aprobado` cuando corresponde.

La máquina real de C017E.2 permite aprobación directa desde `Borrador` para usuarios con permiso de actualización de presupuestos. `Enviar aprobación` permanece como paso operativo opcional hacia `Pendiente de aprobación`.

Si la aprobación falla, la transacción hace rollback completo: la versión anterior conserva su vigencia, la versión nueva conserva su estado previo y no se registran pagos, procedimientos realizados ni eventos odontográficos.

### Crear nueva versión

La nueva versión requiere motivo.

Puede originarse desde:

- `Aprobado`;
- `Rechazado`;
- `Pendiente de aprobación`.

La versión nueva:

- queda en `Borrador`;
- copia líneas snapshot del presupuesto origen;
- conserva la serie;
- referencia `previous_budget_id`;
- no altera la versión aprobada anterior hasta que sea aprobada.

Regla C017E.2-FIX1:

- `Crear nueva versión` crea una sola versión editable.
- Si ya existe una versión `Borrador` dentro de la misma serie, el backend devuelve ese borrador en vez de crear V3 accidentalmente.
- `Guardar cambios` sobre una versión en edición usa `PATCH /api/budgets/{budget_id}`.
- Guardar cambios no incrementa `version`.
- Guardar cambios no crea una nueva serie.
- Guardar cambios sustituye las líneas del borrador seleccionado de forma transaccional.
- La versión activa en frontend se conserva mediante el `budget_id` retornado por el backend.

Regla C017E.2-FIX2:

- La aprobación se ejecuta sobre la versión seleccionada.
- El frontend captura errores de negocio y los muestra inline.
- Un `ApiError` de aprobación no debe romper la página ni activar el overlay de Next.js.
- La confirmación previa informa qué versión se aprueba y qué versión vigente anterior quedará sustituida.

### Inmutabilidad

Un presupuesto aprobado o rechazado no se edita directamente.

Los cambios económicos o de alcance deben realizarse creando una nueva versión.

## Idempotencia

La creación de presupuestos y versiones acepta `budget_idempotency_key`.

Restricción:

- clave única parcial por `empresa_id + budget_idempotency_key`.

Si se repite una solicitud con la misma clave válida, se devuelve el presupuesto existente y no se crea duplicado.

## Endpoint principal

Se mantiene la arquitectura existente.

Endpoints relevantes:

- `POST /api/treatments/{treatment_id}/budgets`
- `POST /api/budgets/{budget_id}/duplicate-version`
- `PATCH /api/budgets/{budget_id}`
- `POST /api/budgets/{budget_id}/submit`
- `POST /api/budgets/{budget_id}/approve`
- `POST /api/budgets/{budget_id}/reject`
- `GET /api/budgets/{budget_id}/pdf`

No se agregaron endpoints para pagos ni odontograma realizado.

## PDF

El PDF conserva el motor documental existente y muestra la versión del presupuesto.

El archivo generado incluye la versión en el nombre.

## Auditoría

Eventos relevantes:

- `BUDGET_CREATED`
- `BUDGET_CREATED_FROM_TREATMENT_PROCEDURES`
- `BUDGET_VERSION_CREATED`
- `BUDGET_VERSION_DRAFT_REUSED`
- `BUDGET_DRAFT_UPDATED`
- `BUDGET_VERSION_SUPERSEDED`
- `BUDGET_APPROVED`
- `BUDGET_REJECTED`

La auditoría no guarda contenido clínico completo; guarda identificadores, serie, versión, procedimientos incluidos, totales y resultado.

## Restricciones explícitas

Este desarrollo no implementa:

- pagos;
- reversas;
- cartera nueva;
- reasignación automática de pagos entre versiones;
- procedimiento realizado → evento odontográfico;
- modificación del odontograma;
- cambios de producción clínica;
- nuevos permisos;
- cambios de endpoints clínicos.

## Riesgos pendientes

- El consecutivo visible del presupuesto se calcula bajo bloqueo transaccional por empresa. Una secuencia dedicada podría ser deseable en una fase futura si el volumen crece.
- `BudgetDetail` aún no guarda snapshot directo del evento odontográfico origen; la trazabilidad actual se conserva por `procedure_id → TreatmentProcedure.source_odontogram_event_id`.
- Si una versión anterior tiene pagos, C017E.2 no reasigna pagos automáticamente a una versión nueva.
- No se implementó política de vencimiento automático.
