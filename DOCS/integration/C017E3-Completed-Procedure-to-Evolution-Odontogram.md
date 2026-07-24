# C017E.3 — Procedimiento realizado → evolución clínica → odontograma confirmado

## Propósito

Integrar la realización de un procedimiento de tratamiento con la evolución clínica y el odontograma histórico sin crear una segunda fuente de verdad.

El flujo aprobado es:

```text
Procedimiento realizado
→ evento odontográfico en borrador
→ vínculo con evolución clínica
→ revisión explícita
→ firma de evolución
→ confirmación odontográfica
```

## Regla principal

Marcar un procedimiento como realizado no confirma el odontograma de forma silenciosa.

La realización clínica crea o reutiliza un evento odontográfico `DRAFT` vinculado a:

- tratamiento;
- procedimiento;
- evolución clínica;
- odontograma;
- diagnóstico odontográfico origen, si existe.

El evento odontográfico se confirma únicamente al firmar la evolución clínica vinculada.

## Diagnóstico odontográfico de origen

El diagnóstico origen se obtiene exclusivamente mediante:

```text
TreatmentProcedure.source_odontogram_event_id
```

No se busca por:

- nombre;
- pieza;
- superficie;
- fecha;
- coincidencia textual;
- último diagnóstico del diente.

Si no existe diagnóstico origen vinculado, el procedimiento puede registrarse como realizado, pero no se ofrece resolver un diagnóstico inexistente.

## Resolver diagnóstico

Resolver diagnóstico no significa eliminarlo.

Cuando `source_diagnosis_action = RESOLVE_ON_SIGN`:

- el diagnóstico origen permanece en el historial;
- el diagnóstico origen deja de participar en el estado vigente;
- la restauración/procedimiento realizado queda vigente;
- la evolución firmada conserva la trazabilidad de la decisión;
- la auditoría registra la resolución.

El estado usado para excluirlo de vigencia es:

```text
VOIDED_BY_COMPENSATING_EVENT
```

## Estado vigente vs historial

Historial conserva todos los hechos clínicos:

- diagnóstico inicial;
- procedimiento realizado;
- resolución del diagnóstico.

Estado vigente excluye eventos resueltos, sustituidos o compensados.

Ejemplo:

```text
Diente 46
Caries activa — Oclusal
Restauración en resina realizada — Oclusal
Acción: Resolver diagnóstico al firmar
```

Después de firmar:

- historial: muestra caries activa y restauración realizada;
- estado vigente: muestra solo restauración en resina realizada;
- odontograma dual: vista anatómica y mapa de cinco caras muestran azul;
- Dental Inspector: resumen vigente no muestra la caries resuelta.

## Acción mantener activo

Cuando `source_diagnosis_action = KEEP_ACTIVE`:

- el diagnóstico origen continúa vigente;
- el procedimiento realizado también queda vigente;
- el historial conserva ambos;
- el Inspector debe explicar la coexistencia.

## Atomicidad

La firma de evolución confirma únicamente eventos odontográficos:

- vinculados a esa evolución;
- en `DRAFT`;
- marcados como revisados para la evolución;
- correspondientes al procedimiento realizado.

Si falla la resolución del diagnóstico origen:

- no se firma la evolución;
- no se confirma el resultado;
- no cambia el estado vigente;
- toda la transacción hace rollback.

## Auditoría

Eventos relevantes:

- `PROCEDURE_MARKED_COMPLETED`
- `ODONTOGRAM_DRAFT_GENERATED`
- `ODONTOGRAM_DRAFT_LINKED_TO_EVOLUTION`
- `ODONTOGRAM_DRAFT_REVIEWED`
- `ODONTOGRAM_EVENT_CONFIRMED_FROM_EVOLUTION`
- `SOURCE_ODONTOGRAM_DIAGNOSIS_RESOLVED`

La auditoría de resolución debe incluir:

- diagnóstico origen;
- resultado realizado;
- evolución;
- procedimiento;
- pieza;
- superficies;
- usuario;
- fecha.

## Restricciones

Este flujo no modifica:

- pagos;
- presupuestos;
- cartera;
- reglas financieras;
- historia clínica firmada;
- eventos históricos confirmados en su contenido clínico.

No se crea automatización por nombre de procedimiento.
