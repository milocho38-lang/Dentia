# PERIO-0.2 — Contrato funcional del MVP de Periodontograma

**Estado:** contrato clínico cerrado por PERIO-0.3; listo para iniciar PERIO-1

**Fecha de cierre clínico:** 2026-09-22

**Precedencia:** este documento concreta PERIO-0 a partir de la revisión clínica de PERIO-0.1 e incorpora el cierre PERIO-0.3. Ante cualquier contradicción, prevalece `PERIO-0.3-CLINICAL-CLOSURE.md`, luego este contrato actualizado, después la adenda PERIO-0.2 actualizada y finalmente los documentos históricos PERIO-0/0.1.

## 1. Objetivo

Definir el comportamiento clínico y funcional mínimo que debe implementar PERIO-1+ sin volver a abrir el cuestionario original. Dentia no diagnostica automáticamente, no copia mediciones entre controles y no modifica exámenes finalizados.

Estados de decisión usados:

- `APPROVED_BY_CLINICIAN`: respuesta clínica suficientemente cerrada para el MVP.
- `PROPOSED_BY_DENTIA`: solución concreta de producto derivada de las respuestas.
- `APPROVED_USER_EXPERIENCE`: interacción confirmada por el profesional.
- `DENTIA_INTERNAL_TRACEABILITY_REQUIRED`: salvaguarda interna obligatoria aunque no se exponga como complejidad técnica en la UI.

## 2. Decisiones consolidadas

| Tema | Decisión | Estado |
|---|---|---|
| Flujo | Nuevo examen, captura, revisión, finalización, histórico y nuevo control independiente | `APPROVED_BY_CLINICIAN` |
| Dentición | Solo permanente; incluye terceros molares presentes | `APPROVED_BY_CLINICIAN` |
| Sitios | Seis sitios por pieza elegible | `APPROVED_BY_CLINICIAN` |
| PD | Milímetros enteros; nullable; cero es un valor medido | `APPROVED_BY_CLINICIAN` |
| Margen/CAL | GM negativo hacia raíz/apical, GM positivo hacia corona y `CAL = PD - GM` | `APPROVED_BY_CLINICIAN` |
| Completitud | Puede finalizarse un examen parcial con advertencia y cobertura visible | `APPROVED_BY_CLINICIAN` |
| Movilidad | Grados 0–3 por diente natural; no aplica a implantes | `APPROVED_BY_CLINICIAN` |
| Furcación | Presencia/ausencia solo en molares; puede marcar mesial, distal o ambas; sin grados | `APPROVED_BY_CLINICIAN` |
| Implantes | Seis sitios, PD, GM, BOP, placa y supuración; sin movilidad | `APPROVED_BY_CLINICIAN` |
| Indicadores | Porcentaje BOP y porcentaje de placa sobre sitios evaluados | `APPROVED_BY_CLINICIAN` |
| Bolsa destacada | Resalte visual en todo sitio con `PD >= 4 mm`, sin diagnóstico automático | `APPROVED_BY_CLINICIAN` |
| Lifecycle | `DRAFT` y `FINALIZED`; finalización sin firma equivalente a evolución | `APPROVED_BY_CLINICIAN` |
| Corrección | UI simple `Corregir` y guardar/finalizar; versión anterior preservada internamente | `APPROVED_USER_EXPERIENCE` + `DENTIA_INTERNAL_TRACEABILITY_REQUIRED` |
| Dispositivo | Desktop y tablet; captura individual o por dictado | `APPROVED_BY_CLINICIAN` |
| Entrada rápida | Teclado numérico, avance automático y corrección directa | `PROPOSED_BY_DENTIA` |
| Control anterior | No copiar mediciones ni hallazgos clínicos previos | `APPROVED_BY_CLINICIAN` |
| Comparación | Fuera del MVP; comparación de dos controles en post-MVP de prioridad alta | `APPROVED_BY_CLINICIAN` |
| Gráfico | Representación periodontal clara obligatoria en el MVP | `APPROVED_BY_CLINICIAN` |
| Historial | Lista simple por fecha, profesional, estado y acción `Ver`; sin `Comparar` en MVP | `APPROVED_BY_CLINICIAN` |
| Evolución | Registro independiente; vínculo opcional, sin crear evolución automática | `APPROVED_BY_CLINICIAN` |
| Diagnóstico | Solo lo registra expresamente el profesional | `APPROVED_BY_CLINICIAN` |
| PDF | Fuera del MVP | `APPROVED_BY_CLINICIAN` |

## 3. Flujo funcional

```text
Paciente
  → Periodontograma
  → Nuevo examen
  → Confirmar dientes presentes, ausentes e implantes
  → Registrar mediciones
  → Revisar gráfico, cobertura e indicadores
  → Finalizar
  → Histórico
  → Nuevo control independiente
```

Reglas:

1. El nuevo examen parte del estado dental vigente, no de mediciones periodontales anteriores.
2. Un `DRAFT` puede guardarse incompleto.
3. `FINALIZED` congela el examen y lo agrega al histórico.
4. El histórico MVP permite abrir cada examen con `Ver`; no ofrece comparación.
5. Una comparación futura leerá snapshots finalizados sin modificar ninguno.

## 4. Dentición, recorrido y sitios

El MVP cubre dentición permanente FDI. Incluye cada tercer molar presente y excluye dentición temporal o mixta.

Cada diente natural o implante elegible tiene seis sitios:

| Cara | Sitios |
|---|---|
| Vestibular | distal, medio, mesial |
| Palatina/lingual | distal, medio, mesial |

Recorrido canónico:

```text
Maxilar:   18 → 17 → … → 27 → 28
Mandíbula: 48 → 47 → … → 37 → 38
```

Dentro de cada cara de la pieza:

- lado derecho: distal → medio → mesial;
- lado izquierdo: mesial → medio → distal.

La UI usa labels clínicos completos y puede acompañarlos con abreviaturas: DV/V/MV y DP-P-MP o DL-L-ML según arcada. El orden de navegación debe estar definido por una función pura; no se deduce de la posición visual del DOM.

## 5. Mediciones por sitio

| Variable | Tipo funcional | Nulo | Regla |
|---|---|---:|---|
| PD | entero en mm | sí | cero es distinto de no medido |
| GM | entero con signo en mm | sí | negativo hacia raíz/apical; positivo hacia corona; cero es referencia medida |
| CAL | entero derivado en mm | sí | solo se calcula si existen PD y GM |
| BOP | booleano triestado | sí | `false` es evaluado sin sangrado; `null` no evaluado |
| Placa | booleano triestado | sí | misma semántica que BOP |
| Supuración | booleano triestado | sí | aplica también alrededor de implantes |

Dentia valida tipos, enteros, payload y consistencia anatómica. No bloquea un valor solo por ser clínicamente inusual ni convierte un rango en diagnóstico. Los límites puramente técnicos de integridad se documentarán en PERIO-1 y deberán ser amplios, versionados y probados.

## 6. Margen gingival y CAL

Convención clínica definitiva:

- GM negativo: encía desplazada hacia la raíz/apical;
- GM positivo: encía desplazada hacia la corona;
- GM cero: punto de referencia medido;
- `CAL = PD - GM`.

Ejemplos:

```text
PD 4 mm, GM -2 mm → CAL 6 mm
PD 4 mm, GM +2 mm → CAL 2 mm
```

La convención queda cerrada como `APPROVED_BY_CLINICIAN`. PD y GM son milímetros enteros; CAL lo calcula Dentia solo cuando existen ambos valores. Cero es una medición explícita y nunca representa “no medido”; la ausencia de medición se expresa con `null`. El examen finalizado conservará `calculation_version` y `sign_convention_version`; una versión futura nunca recalcula históricos.

## 7. Completitud

`PARTIAL_EXAM_ALLOWED = true`.

- El borrador puede contener cualquier nivel de avance.
- Finalizar no exige el 100 % de sitios.
- Antes de finalizar se muestra `X de Y sitios evaluados` y una advertencia si la cobertura es parcial.
- El profesional puede continuar y finalizar después de reconocer la advertencia.
- No se inventan valores negativos ni ceros para completar sitios faltantes.

Los indicadores parciales deben mostrar su denominador real y quedar identificados como parciales.

## 8. Movilidad

Se registra un único grado explícito por diente natural:

| Grado | Descripción clínica |
|---:|---|
| 0 | Movilidad fisiológica |
| 1 | Movimiento horizontal leve, hasta aproximadamente 1 mm |
| 2 | Movimiento horizontal mayor de 1 mm |
| 3 | Movilidad severa horizontal y vertical |

No se crean campos separados horizontal/vertical. El grado 0 se guarda explícitamente. Movilidad no se muestra ni se admite en implantes.

## 9. Furcaciones

El MVP solo muestra furcación en molares elegibles y no usa grados.

Modelo definitivo del MVP:

- `furcation_present`: sí/no;
- si es sí, ubicaciones permitidas: mesial, distal o ambas;
- no existe un estado especial para “no evaluada”; ausencia de dato permanece nula;
- no se muestran controles de furcación en piezas no elegibles.

No se incluyen vestibular, palatina/lingual ni grados I/II/III en el MVP. La representación gráfica permite rellenar o marcar M y D de forma independiente.

## 10. Implantes

Un implante:

- conserva los mismos seis sitios;
- admite PD, GM, BOP, placa y supuración;
- usa la misma referencia clínica del margen;
- participa en los indicadores agregados de BOP y placa;
- no admite movilidad;
- se distingue con una representación visual de implante, no solo por color.

El estado de implante proviene del snapshot dental del examen. No se mantiene un segundo booleano clínico editable que pueda contradecirlo.

## 11. Sangrado, placa e indicadores

BOP y placa se registran por sitio. BOP se captura inmediatamente durante el examen.

```text
% BOP = sitios evaluados con BOP / sitios con BOP evaluado × 100
% placa = sitios evaluados con placa / sitios con placa evaluada × 100
```

- `false` participa en el denominador;
- `null` no participa;
- piezas ausentes y sitios no elegibles no participan;
- dientes naturales e implantes comparten el indicador del MVP.

Los únicos KPI clínicos obligatorios del MVP son `% BOP` y `% placa`. PD media, CAL medio y conteos por rango pueden aparecer como información secundaria durante prototipo, pero no son requisito de aceptación.

## 12. Gráfico y hallazgos visuales

El gráfico periodontal es obligatorio en el MVP. Debe distinguir:

- diente natural, implante y ausencia;
- PD, GM y CAL;
- BOP y placa;
- furcación M/D cuando aplique;
- sitios con bolsa visual `PD >= 4 mm`.

El gráfico es una proyección de los datos, no una fuente editable independiente. Debe incluir alternativa textual/accesible y priorizar claridad clínica sobre fidelidad estética a herramientas externas.

Dentia resalta visualmente todo sitio con `PD >= 4 mm`. Es una ayuda visual derivada de la medición, no un diagnóstico ni una recomendación terapéutica. El umbral se conserva como regla versionada para mantener trazabilidad.

## 13. Finalización, integridad y corrección

Lifecycle:

```text
DRAFT → FINALIZED
```

`FINALIZED` no necesita firma clínica equivalente a una evolución, pero sí confirmación explícita, actor, timestamp y auditoría. La finalización genera snapshot canónico y hash sin alterar exámenes anteriores.

Flujo de corrección aprobado:

1. El profesional abre un examen finalizado.
2. Selecciona `Corregir periodontograma`.
3. Edita y selecciona guardar/finalizar mediante la misma experiencia simple del examen.
4. Dentia crea internamente una nueva versión `DRAFT` vinculada al examen corregido.
5. El original permanece inmutable y visible en la trazabilidad.
6. Dentia registra actor, fecha y motivo cuando el patrón clínico aplicable lo requiera.
7. Al finalizar, la nueva versión pasa a ser la vigente y conserva el vínculo con la anterior.

La UI no obliga al profesional a comprender el versionado técnico. Internamente nunca se sobrescribe silenciosamente el original.

## 14. Entrada rápida y dispositivos

El MVP prioriza desktop y tablet horizontal, tanto para un profesional que registra como para un equipo donde una persona dicta y otra captura. El objetivo operativo aproximado para un examen completo es 20 minutos.

La captura debe incluir:

- teclado numérico;
- autofocus y avance automático al siguiente sitio;
- `Tab`/`Shift+Tab` y navegación anterior/siguiente;
- clic directo para corregir una celda;
- buffer local y guardado por lotes, nunca una petición por tecla;
- secuencia fija, visible y no configurable en el MVP;
- estado claro de guardando, guardado, cambios pendientes y conflicto.

En móvil se prioriza consulta y edición focal; no se comprime artificialmente la cuadrícula completa.

## 15. Histórico y comparación

Historial MVP aprobado:

```text
Fecha        Profesional   Estado       Acciones
17/09/2026  Dra. X        Finalizado   Ver
15/12/2026  Dra. X        Finalizado   Ver
```

La lista responde únicamente cuándo, quién, estado y abrir. No se carga de promedios ni indicadores y no incluye la acción `Comparar` en el MVP.

La comparación de dos periodontogramas se mueve a post-MVP con prioridad alta. Cuando se implemente, se limitará a snapshots finalizados, se ejecutará solo a solicitud del profesional y mostrará diferencias por sitio sin convertir cambios en diagnóstico.

No bloquea PERIO-1. La arquitectura del gráfico y del snapshot debe permitirla en el futuro sin reconstruir datos desde el odontograma vigente.

## 16. Integración clínica

- El periodontograma es un registro clínico independiente dentro del paciente.
- Puede vincularse opcionalmente a una evolución existente.
- Finalizar no crea una evolución automática.
- El vínculo muestra una referencia al examen; no duplica mediciones.
- Una enfermedad periodontal solo aparece como diagnóstico cuando el profesional la registra expresamente.

Dentia puede calcular, representar, destacar y advertir. No diagnostica ni recomienda tratamiento automáticamente.

## 17. Impacto en el modelo de datos

| Área | Impacto requerido |
|---|---|
| Examen | Aggregate root con `DRAFT`/`FINALIZED`, fecha, profesional, sede, cobertura, versiones y auditoría |
| Estado dental | Snapshot por FDI de natural/implante/ausente; odontograma sigue como fuente vigente |
| Sitios | Seis filas estables por pieza elegible con valores nullable |
| Mediciones | PD, GM, CAL derivado, BOP, placa y supuración |
| Pieza | Movilidad nullable y nota clínica; movilidad prohibida en implante |
| Furcación | Presencia y banderas mesial/distal; sin otras caras ni `grade_code` en MVP |
| Integridad | Snapshot JSON canónico, SHA-256 y versiones de esquema/cálculo/signo |
| Corrección | Referencia de versión/supersesión obligatoria; original finalizado inmutable |
| Comparación | Capacidad futura de leer dos snapshots finalizados; fuera del MVP |

Se elimina del MVP cualquier campo o endpoint destinado a copiar PD, GM, BOP, placa, movilidad o furcación de un examen anterior. La estructura dental inicial puede materializarse desde el odontograma vigente porque no representa una medición periodontal previa.

## 18. Impacto UX

- workspace clínico de ancho completo;
- estado dental confirmado antes de medir;
- cursor de captura y sitio siguiente siempre visibles;
- diferencia inequívoca entre cero, falso y no medido;
- cobertura parcial visible antes de finalizar;
- gráfico sincronizado con la matriz de captura;
- implantes y ausencias identificables sin depender del color;
- historial simple con acción `Ver`;
- finalizado en solo lectura;
- corrección versionada expuesta como una acción sencilla.

## 19. Scope MVP

Incluye:

- dentición permanente y terceros molares presentes;
- natural, implante y ausente;
- seis sitios por pieza;
- PD, GM, CAL, BOP, placa y supuración;
- movilidad 0–3 y furcación M/D sin grados;
- captura rápida con secuencia fija;
- borrador parcial, cobertura y finalización;
- `% BOP` y `% placa`;
- gráfico periodontal accesible;
- resalte visual de bolsas con `PD >= 4 mm`;
- histórico simple;
- corrección sencilla con trazabilidad y preservación de versiones;
- snapshot, hash, auditoría, concurrencia y aislamiento tenant/sede/paciente;
- vínculo opcional con evolución;
- arquitectura preparada para comparar dos exámenes en una fase posterior.

## 20. Prioridad post-MVP alta

- comparación visual del examen actual con el anterior;
- diferencias por sitio sobre snapshots finalizados;
- no forma parte de la aceptación del MVP ni se expone como acción en el historial inicial.

## 21. Scope post-MVP

- dentición temporal o mixta;
- PDF institucional;
- comparación de más de dos controles y tendencias;
- voz;
- secuencias configurables;
- índices adicionales;
- variables mucogingivales avanzadas;
- automatizaciones diagnósticas o terapéuticas, que requerirían un contrato clínico separado.

## 22. Cierre de confirmaciones

No quedan preguntas clínicas que bloqueen PERIO-1. Las cinco confirmaciones de PERIO-0.2 fueron cerradas por PERIO-0.3. `PERIO-0.2-CLINICAL-CONFIRMATION.md` se conserva únicamente como registro histórico y no tiene vigencia normativa.

## 23. Roadmap actualizado

### PERIO-1 — Foundation y lifecycle

- aggregate root, estados, tenant/sede/paciente/profesional;
- snapshot de estado dental, locking, idempotencia y auditoría;
- seguridad y permisos solo después de autorización explícita;
- sin UI clínica completa.

### PERIO-2 — Mediciones y reglas clínicas

- seis sitios, PD, GM, CAL, BOP, placa, supuración y movilidad;
- implantes y furcación M/D conforme al cierre PERIO-0.3;
- cálculo versionado e indicadores con cobertura.

### PERIO-3 — Captura rápida

- workspace desktop/tablet;
- secuencia fija, teclado, buffer y batch save;
- draft parcial, warnings y responsive focal.

### PERIO-4 — Gráfico obligatorio e indicadores

- representación accesible de PD, GM, CAL, BOP, placa, implantes, ausencias y furcación;
- `% BOP`, `% placa` y regla visual de bolsa confirmada.

### PERIO-5 — Histórico y corrección

- historial simple;
- corrección versionada con experiencia simple;
- preservación de originales finalizados y trazabilidad.

### PERIO-6 — Hardening y piloto

- concurrencia, integridad, performance, IDOR y cross-tenant;
- validación ergonómica del objetivo aproximado de 20 minutos;
- piloto controlado y rollback.

### Post-MVP prioritario — Comparación

- comparación de dos periodontogramas finalizados;
- diferencias por sitio sin diagnóstico automático;
- lectura exclusiva de snapshots históricos inmutables.

## 24. Gate

El contrato clínico está cerrado y PERIO-1 puede comenzar. La matriz RBAC y cualquier migración continúan requiriendo autorización explícita separada; este cierre documental no las autoriza.
