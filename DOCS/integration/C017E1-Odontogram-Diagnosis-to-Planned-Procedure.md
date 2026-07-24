# C017E.1 — Diagnóstico odontográfico → procedimiento planificado

## Propósito

Permitir que un diagnóstico o hallazgo odontográfico confirmado origine explícitamente un procedimiento planificado dentro de un tratamiento, sin modificar el estado clínico del odontograma.

## Regla principal

Un evento odontográfico confirmado puede crear uno o varios procedimientos planificados, siempre mediante una acción explícita del usuario:

```text
Evento odontográfico confirmado
↓
Agregar al plan de tratamiento
↓
Tratamiento existente o nuevo
↓
Procedimiento planificado
↓
Trazabilidad directa al evento origen
```

## Fuente de verdad

- El odontograma conserva la fuente de verdad clínica.
- Tratamientos conserva la fuente de verdad comercial-operativa.
- La relación se almacena en el procedimiento mediante `source_odontogram_event_id`.
- La idempotencia se protege mediante `odontogram_idempotency_key` por empresa.

## No automatizaciones

Este flujo no crea automáticamente:

- presupuestos;
- pagos;
- evoluciones;
- eventos odontográficos;
- procedimientos realizados.

Tampoco cambia el estado del evento odontográfico origen.

## Endpoint

```http
POST /api/odontogram/events/{event_id}/planned-procedures
```

El endpoint:

- valida empresa desde sesión;
- exige evento confirmado;
- acepta tratamiento existente o creación de tratamiento nuevo;
- crea procedimiento en estado `Pendiente`;
- detecta duplicados probables;
- permite duplicado solo con `allow_similar_duplicate`;
- audita la creación y el vínculo.

Consulta de vínculos por paciente/pieza:

```http
GET /api/patients/{patient_id}/odontogram/planned-procedure-links?tooth_code=36
```

## Auditoría

Eventos mínimos:

- `PROCEDURE_CREATED_FROM_ODONTOGRAM`
- `ODONTOGRAM_EVENT_LINKED_TO_PROCEDURE`

No se guarda contenido clínico completo en auditoría.

## Restricción

La creación normal de procedimientos no acepta `source_odontogram_event_id`.
La trazabilidad clínica-comercial debe pasar por el endpoint explícito del puente.

## C017E.1-FIX1 — Sincronización y navegación contextual

Después de crear un procedimiento desde el Dental Inspector:

- el Patient Center debe refrescar los tratamientos del paciente sin recarga completa del navegador;
- el Dental Inspector debe refrescar los procedimientos derivados de la pieza seleccionada;
- el drawer debe permanecer abierto y la pieza seleccionada debe conservarse;
- si el refetch falla después de crear correctamente, no debe repetirse la creación; se debe ofrecer una acción `Actualizar`.

La sección `Plan de tratamiento` del Dental Inspector muestra los procedimientos derivados como tarjetas funcionales, separando:

- procedimiento;
- tratamiento;
- estado del tratamiento;
- estado del procedimiento;
- alcance dental;
- valor planificado.

Cada procedimiento derivado ofrece la acción:

```text
Ver tratamiento
```

La navegación contextual esperada es:

```text
Dental Inspector
→ Ver tratamiento
→ Detalle del tratamiento
→ Volver al paciente
→ Pestaña Tratamientos
```

Los procedimientos derivados no forman parte del historial odontográfico. El historial del diente sigue mostrando únicamente eventos odontográficos.

## Pendiente C017E.3

Marcar un procedimiento como `Realizado` todavía no actualiza el odontograma, no pinta el diente en azul y no crea eventos odontográficos. Esa integración pertenece a C017E.3.
