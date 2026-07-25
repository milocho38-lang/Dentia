# C017F.2 — Tratamiento como punto de entrada al odontograma

## Propósito

Permitir que un procedimiento creado desde un tratamiento registre, cuando el odontólogo lo confirme explícitamente, el diagnóstico u hallazgo odontográfico que justifica ese procedimiento.

Este flujo complementa el camino existente:

```text
Odontograma → Diagnóstico/Hallazgo → Procedimiento planificado
```

con el nuevo camino:

```text
Tratamiento → Procedimiento planificado → Diagnóstico/Hallazgo confirmado en odontograma
```

Ambos caminos mantienen una sola fuente de verdad clínica: los eventos odontográficos confirmados.

## Regla principal

Dentia nunca infiere un diagnóstico por el nombre del procedimiento.

Un procedimiento como “Endodoncia”, “Resina” o “Corona” no crea por sí mismo pulpitis, caries, fractura ni ningún otro diagnóstico.

El diagnóstico se registra únicamente cuando:

- el catálogo del procedimiento lo permite o lo exige;
- el usuario selecciona explícitamente el diagnóstico/hallazgo;
- el usuario confirma la acción;
- el backend valida permisos, paciente, empresa, alcance y catálogo.

## Configuración del catálogo de procedimientos

Cada procedimiento de catálogo puede definir:

- `UNCONFIGURED`: sin contrato odontográfico definido.
- `NO_CHANGE`: no modifica odontograma.
- `OPTIONAL_DIAGNOSIS`: puede registrar diagnóstico/hallazgo si el usuario lo confirma.
- `REQUIRES_DIAGNOSIS`: exige registrar o reutilizar un diagnóstico/hallazgo compatible.

También puede definir:

- alcance odontográfico esperado;
- diagnósticos/hallazgos permitidos;
- resultado odontográfico realizado sugerido para fases posteriores.

## Creación desde tratamiento

Cuando el usuario crea un procedimiento con diagnóstico:

1. Se crea el procedimiento planificado.
2. Se crea un evento odontográfico confirmado o se reutiliza uno existente compatible.
3. El procedimiento queda enlazado mediante `source_odontogram_event_id`.
4. La operación es transaccional.
5. La operación es idempotente mediante `idempotency_key`.

## Reutilización de diagnósticos existentes

Dentia puede reutilizar un diagnóstico confirmado existente solo si coincide en:

- empresa;
- paciente;
- catálogo odontográfico;
- alcance;
- diente;
- superficies.

Una condición similar con otra superficie no es equivalente.

## Qué no hace este flujo

Este flujo no crea:

- presupuestos;
- pagos;
- evoluciones clínicas;
- procedimientos realizados;
- eventos de realización clínica.

Tampoco cambia reglas económicas existentes.

## Auditoría

Eventos auditados:

- `TREATMENT_PROCEDURE_CREATED`
- `ODONTOGRAM_DIAGNOSIS_CREATED_FROM_TREATMENT`
- `ODONTOGRAM_EXISTING_DIAGNOSIS_LINKED_TO_PROCEDURE`
- `PROCEDURE_LINKED_TO_ODONTOGRAM_DIAGNOSIS`

La auditoría conserva identificadores y contexto, no contenido clínico extenso.

## Permisos

El flujo requiere:

- `treatments.update`
- `odontogram.view`
- `odontogram.update_draft`
- `odontogram.confirm`

Los procedimientos sin cambios odontográficos continúan usando el flujo normal de tratamientos.

## Riesgos controlados

- Diagnóstico duplicado: se detecta coincidencia exacta y se ofrece reutilizar.
- Diagnóstico inventado: prohibido por contrato; siempre debe elegirse desde catálogo.
- Diagnóstico sin historia clínica: se rechaza si el paciente no tiene historia clínica.
- Procedimientos generales: pueden permanecer sin cambio odontográfico.
