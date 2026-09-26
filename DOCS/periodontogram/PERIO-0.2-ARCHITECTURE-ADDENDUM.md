# PERIO-0.2 — Adenda de arquitectura del Periodontograma

**Estado:** adenda clínica cerrada por PERIO-0.3; lista para PERIO-1

**Fecha de cierre clínico:** 2026-09-22

## 1. Precedencia

Esta adenda actualiza `PERIO-0-FUNCTIONAL-ARCHITECTURE.md` con las decisiones consolidadas en PERIO-0.2. No modifica código, modelos, migraciones, APIs, permisos ni datos.

Ante contradicción documental, el orden es:

1. `PERIO-0.3-CLINICAL-CLOSURE.md`;
2. `PERIO-0.2-FUNCTIONAL-CONTRACT.md` actualizado por PERIO-0.3;
3. esta adenda actualizada;
4. documentos históricos PERIO-0, PERIO-0.1 y la confirmación PERIO-0.2 superseded.

## 2. Cambios de contrato

### `APPROVED_BY_CLINICIAN`

- MVP limitado a dentición permanente e inclusión de terceros molares presentes.
- Seis sitios por diente natural o implante elegible.
- PD y GM enteros en milímetros; nulo significa no medido y no equivale a cero.
- GM negativo hacia raíz/apical, GM positivo hacia corona y `CAL = PD - GM`.
- Movilidad 0–3, con grado 0 explícito y sin movilidad en implantes.
- Implantes con seis sitios, PD, GM, BOP, placa y supuración.
- BOP y placa booleanos por sitio e indicadores agregados sobre sitios evaluados.
- Estados `DRAFT` y `FINALIZED`; finalizar no equivale a firmar una evolución.
- Gráfico periodontal obligatorio en el MVP.
- Resalte visual de todo sitio con `PD >= 4 mm`, sin diagnóstico automático.
- Furcación en molares como presencia/ausencia y ubicación mesial, distal o ambas; sin grados.
- Finalización parcial permitida con cobertura y advertencia no bloqueante.
- Corrección con UX simple y nueva versión interna; original inmutable.
- Historial MVP limitado a fecha, profesional, estado y `Ver`.
- Ninguna copia de mediciones clínicas desde el examen anterior.
- Periodontograma independiente, vínculo opcional con evolución y sin evolución automática.
- Diagnóstico periodontal solo por registro explícito del profesional.
- PDF, voz y funciones avanzadas fuera del MVP.

### `PROPOSED_BY_DENTIA`

- Entrada rápida mediante secuencia fija, teclado, buffer local y batch save.
- Modelo híbrido: filas normalizadas editables en draft y snapshot/hash al finalizar.
- Workspace de ancho completo en desktop/tablet y edición focal en móvil.

### Confirmaciones cerradas por PERIO-0.3

- convención GM y fórmula CAL;
- furcación limitada a M/D;
- umbral visual de bolsa `PD >= 4 mm`;
- corrección mediante nueva versión enlazada;
- histórico simple sin comparación en el MVP.

No queda ningún `PENDING_CONFIRMATION` clínico para iniciar PERIO-1. La comparación de dos exámenes se conserva como capacidad arquitectónica post-MVP de prioridad alta.

## 3. Deltas del modelo de dominio

### Se mantienen

- `PeriodontalExam` como aggregate root;
- snapshot dental por pieza desde el odontograma vigente;
- seis mediciones por pieza elegible;
- estado dental histórico natural/implante/ausente;
- optimistic locking durante draft;
- snapshot canónico, hash y versiones de reglas al finalizar;
- autorización tenant, sede, paciente y profesional.

### Se ajustan

- `PeriodontalSiteMeasurement` incluye supuración nullable además de PD, GM, CAL, BOP y placa.
- Furcación deja de requerir `grade_code` en el MVP; usa presencia y banderas mesial/distal únicamente.
- Los indicadores MVP obligatorios se reducen a `% BOP` y `% placa` con cobertura real.
- El gráfico pasa de fase opcional previa al piloto a entregable obligatorio del MVP.
- Una comparación futura usará dos snapshots finalizados y no el odontograma vigente.

### Se eliminan del MVP

- `copied_from_exam_id` y provenance destinados a copiar mediciones clínicas;
- endpoint `copy` y UI `Crear desde examen anterior`;
- copia de PD, GM, BOP, placa, movilidad, furcación o notas;
- tabla histórica cargada de PD media, CAL medio y rangos;
- grados de furcación;
- dentición temporal/mixta.

Materializar la estructura dental vigente al crear un examen no se considera copia clínica: proviene del odontograma actual y debe guardar su fingerprint.

## 4. Lifecycle e inmutabilidad

```text
DRAFT ── finalize ──> FINALIZED
```

- `DRAFT` acepta captura parcial y guardados batch.
- `FINALIZED` es de solo lectura y conserva actor, timestamp, snapshot, hash y auditoría.
- No existe transición inversa.
- `Corregir` crea otro `DRAFT` con vínculo al finalizado; no se edita ni recalcula el original.
- La UI presenta editar y guardar/finalizar sin exponer la complejidad del versionado.
- La corrección conserva actor, fecha y motivo cuando el patrón clínico aplicable lo requiera.
- Una comparación futura o el vínculo con una evolución nunca modifica el snapshot.

## 5. Cálculos versionados

La convención definitiva y versionada es:

```text
GM negativo = desplazamiento hacia raíz/apical
GM positivo = desplazamiento hacia corona
GM 0 = punto de referencia medido
CAL = PD - GM
```

Ejemplos canónicos:

```text
PD 4, GM -2 → CAL 6
PD 4, GM +2 → CAL 2
```

PD y GM son enteros en milímetros; CAL es derivado. `0` es un valor medido y `null` representa ausencia de medición. Los porcentajes quedan definidos:

```text
% BOP = true / sitios con BOP evaluado
% placa = true / sitios con placa evaluada
```

Los denominadores excluyen nulos, piezas ausentes y sitios no elegibles. Todo resultado parcial incluye numerador, denominador y cobertura.

## 6. Contrato de captura

Orden FDI:

```text
Maxilar:   18 → 28
Mandíbula: 48 → 38
```

En cada cara:

- lado derecho: distal → medio → mesial;
- lado izquierdo: mesial → medio → distal.

La máquina de navegación conserva cursor por pieza, cara, sitio y métrica. Es una función pura, versionada y probada. El avance automático nunca confunde cero, falso y nulo.

## 7. Contrato del gráfico

El gráfico MVP recibe una proyección de las mediciones y nunca se convierte en segunda fuente editable. Debe representar natural/implante/ausente, PD, GM, CAL, BOP, placa, furcación M/D y bolsas `PD >= 4 mm`, con alternativa textual y sin depender solo del color.

El resalte de bolsas usa la regla versionada `PD >= 4 mm`. Resaltar no crea diagnóstico.

## 8. API conceptual ajustada

Se mantienen como conceptos:

- listar historial;
- crear examen desde estado dental vigente;
- consultar examen;
- guardar cambios draft por lote y `row_version`;
- sincronizar explícitamente estado dental solo en draft;
- finalizar idempotentemente;
- verificar integridad.

Se elimina del contrato MVP el endpoint de copia de examen anterior.

La comparación de dos snapshots se agrega en post-MVP con prioridad alta y autorización equivalente a consulta histórica; no reconstruye datos desde tablas clínicas vivas. El endpoint o acción `Comparar` no forma parte del MVP.

## 9. Roadmap reemplazado

1. `PERIO-1`: foundation, lifecycle, seguridad autorizada, tenant/scope, auditoría y concurrencia.
2. `PERIO-2`: estado dental, seis sitios, variables y cálculos confirmados.
3. `PERIO-3`: captura rápida desktop/tablet, batch save y responsive focal.
4. `PERIO-4`: gráfico obligatorio, cobertura, `% BOP` y `% placa`.
5. `PERIO-5`: histórico simple y corrección versionada.
6. `PERIO-6`: hardening, ergonomía y piloto controlado.
7. `POST-MVP HIGH`: comparación de dos controles finalizados.
8. `PERIO-7+`: PDF, voz, múltiples tendencias, índices y dentición adicional.

## 10. Gate de implementación

Esta adenda no autoriza código ni RBAC. PERIO-1 requiere:

1. mantener las decisiones cerradas en `PERIO-0.3-CLINICAL-CLOSURE.md`;
2. autorizar explícitamente la matriz de permisos y cualquier migración;
3. mantener fuera del primer cambio la UI clínica completa.

Las decisiones clínicas ya no bloquean PERIO-1. Esta adenda no autoriza código, RBAC ni migraciones.
