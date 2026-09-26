# PERIO-0 — Diseño funcional y arquitectura del módulo Periodontograma

**Estado:** propuesta para revisión clínica y técnica; sin implementación

**Fecha:** 2026-09-17

**Ámbito:** módulo clínico general del paciente, independiente de Ortodoncia

**Siguiente fase permitida:** PERIO-1, únicamente después de validar las decisiones clínicas bloqueantes identificadas en `PERIO-0-CLINICAL-QUESTIONS.md`

## 1. Objetivo

Definir el contrato funcional, clínico y técnico de un periodontograma propio de Dentia. El módulo debe permitir registrar exámenes periodontales completos, conservar su evolución longitudinal y operar con alta velocidad de captura sin crear una segunda fuente de verdad del paciente, del odontograma ni de la historia clínica.

La unidad clínica central es `PeriodontalExam`: una observación del estado periodontal de un paciente, realizada en una sede, por un profesional y en una fecha clínica determinada. Cada examen es independiente de los anteriores; nunca se actualiza un examen finalizado para representar un control posterior.

PERIO-0 es solo diseño. Este documento no crea modelos, migraciones, endpoints, permisos, componentes, flags ni datos.

## 2. Scope

El diseño cubre:

- entrada `Paciente → Periodontograma`, como pestaña clínica par de Historia clínica, Odontograma y Ortodoncia;
- múltiples exámenes por paciente con estados `DRAFT` y `FINALIZED`;
- dentición permanente FDI y una estrategia explícita para evaluar dentición temporal/mixta;
- seis sitios de sondaje por pieza elegible;
- profundidad de sondaje, margen gingival, nivel de inserción, sangrado y placa;
- estado dental, implantes, movilidad, furcación y nota clínica;
- copia selectiva de un examen anterior hacia un nuevo borrador;
- historial y resumen de indicadores con cobertura explícita;
- captura rápida por teclado y guardado por lotes;
- inmutabilidad, hash, auditoría, concurrencia y aislamiento multiempresa;
- integración con odontograma, expediente, sedes, odontólogos y timeline clínico;
- arquitectura preparada para comparación longitudinal, impresión y evolución futura.

El módulo no se limita por especialidad. Un odontólogo general o especialista puede usarlo si cumple permiso, identidad profesional activa y scope clínico.

## 3. No-scope

PERIO-0 y el MVP propuesto no incluyen:

- implementación funcional, migraciones ni asignación real de permisos;
- diagnóstico o clasificación automática de periodontitis;
- recomendaciones terapéuticas automáticas;
- IA, reconocimiento de voz o dictado clínico;
- microbiología periodontal;
- índices avanzados GI, mGI, mPI, Miller, Cairo o personalizados;
- periodontograma radiográfico ni carga de radiografías;
- integración RIPS, facturación, presupuestos o automatización comercial;
- configuración por clínica de secuencias o convenciones de signo en el MVP;
- edición de odontograma desde el periodontograma;
- sincronización retroactiva de exámenes finalizados cuando cambie el odontograma;
- impresión/PDF o comparación avanzada hasta validar su prioridad clínica;
- dentición temporal/mixta hasta resolver su contrato clínico;
- cambios al módulo de Ortodoncia.

## 4. Personas y roles

### 4.1 Personas funcionales

| Persona | Necesidad | Restricción principal |
|---|---|---|
| Odontólogo general | Registrar, consultar y finalizar exámenes de sus pacientes autorizados | permiso clínico, identidad odontológica activa y scope vigente |
| Periodoncista | Captura completa, rápida y longitudinal | mismas reglas de tenant/sede; la especialidad no reemplaza RBAC |
| Odontólogo administrador | Operación clínica y consulta histórica según sus permisos | su capacidad administrativa no concede acceso clínico por sí sola |
| Administrador de clínica | Configuración futura y consulta administrativa mínima | no debe poder alterar ni finalizar contenido clínico sin permiso clínico e identidad profesional |
| Secretaria | Ningún acceso clínico por defecto | no registra ni consulta mediciones periodontales por su rol operativo |
| Administrador de plataforma | Soporte de plataforma sin contenido clínico tenant | no hereda acceso clínico global |

### 4.2 Permisos conceptuales

Se recomiendan permisos específicos porque el examen periodontal es un artefacto clínico distinto y de alta sensibilidad:

- `periodontogram.view`
- `periodontogram.create`
- `periodontogram.update_draft`
- `periodontogram.finalize`
- `periodontogram.history`

Crear desde un examen previo puede reutilizar `periodontogram.create`; no necesita un permiso redundante si el servicio audita la procedencia. Una futura corrección o anulación exigiría un permiso separado cuando se defina el mecanismo.

PERIO-0 no asigna estos permisos a roles. La matriz definitiva requiere autorización posterior. La autorización efectiva debe ser la intersección de permiso, tenant, sede, paciente, identidad profesional y estado del examen.

## 5. Flujo clínico

```text
Paciente
  ↓
Pestaña Periodontograma
  ├── Historial de exámenes
  ├── Abrir examen FINALIZED (solo lectura)
  └── Crear examen DRAFT
          ├── desde estado dental vigente
          └── opcionalmente copiar categorías de un examen anterior
                    ↓
        Registrar mediciones por recorrido clínico
                    ↓
        Guardar borrador por lotes
                    ↓
        Revisar cobertura, alertas e indicadores parciales
                    ↓
        Finalizar con confirmación explícita
                    ↓
        Snapshot canónico + hash + auditoría + timeline
```

Principios del flujo:

1. Crear un examen toma un snapshot inicial del estado dental vigente; no clona automáticamente mediciones anteriores.
2. Copiar un examen es una acción explícita y selectiva que siempre produce un nuevo `DRAFT`.
3. Un borrador puede estar incompleto y guardarse repetidas veces.
4. Finalizar requiere una revisión visible de datos faltantes, warnings y cobertura.
5. Un examen finalizado es de solo lectura y no se resincroniza con el odontograma.

## 6. Modelo de dominio

```text
Company
  └── Site
       └── Patient ── Odontogram
              │             │
              │             └── estado dental vigente
              │
              └── PeriodontalExam
                    ├── PeriodontalExamTooth (snapshot por FDI)
                    │      ├── PeriodontalSiteMeasurement × 6
                    │      └── PeriodontalFurcation × 0..n
                    ├── indicadores derivados
                    ├── snapshot canónico final
                    ├── provenance / copied_from
                    └── entrada de timeline clínico
```

### 6.1 `PeriodontalExam`

Aggregate root responsable de lifecycle, autorización, fecha clínica, procedencia, integridad y concurrencia. Pertenece a una empresa y un paciente; se asocia a sede y odontólogo.

### 6.2 `PeriodontalExamTooth`

Representa la pieza FDI dentro de ese examen, no la pieza viva del odontograma. Conserva el estado observado/sincronizado al crear el examen: diente natural, implante, ausente u otro estado soportado por el adaptador. Contiene datos por pieza como movilidad y nota.

### 6.3 `PeriodontalSiteMeasurement`

Representa un sitio anatómico estable y sus mediciones nullable. Una ausencia de valor significa “no medido”; nunca equivale a cero.

### 6.4 `PeriodontalFurcation`

Entidad separada porque un diente multirradicular puede tener más de una entrada de furcación y la ubicación no coincide necesariamente con un único sitio de sondaje. Conserva ubicación y grado mediante códigos clínicos validados.

### 6.5 Indicadores derivados

Son proyecciones calculadas a partir de mediciones elegibles. No son campos editables. En borrador pueden recalcularse; al finalizar se incluyen en el snapshot canónico con numerador, denominador y cobertura.

## 7. Lifecycle

### 7.1 Estados iniciales

| Estado | Escritura | Uso |
|---|---|---|
| `DRAFT` | permitida con permiso, scope y `row_version` válidos | captura parcial, corrección y revisión antes de firmar clínicamente |
| `FINALIZED` | prohibida | registro clínico congelado, verificable y disponible en historial |

Transición permitida en MVP:

```text
DRAFT ── finalize ──> FINALIZED
```

No se permite volver de `FINALIZED` a `DRAFT`.

### 7.2 Finalización

La finalización ocurre en una transacción que:

1. bloquea el examen y valida `row_version`;
2. revalida empresa, paciente, sede, odontólogo, permiso y estado;
3. aplica las reglas de completitud aprobadas;
4. calcula CAL e indicadores con la versión de reglas vigente;
5. construye el snapshot canónico determinista;
6. calcula SHA-256;
7. guarda profesional, fecha clínica, zona horaria, fecha de finalización y versión de esquema;
8. cambia el estado a `FINALIZED`;
9. registra auditoría y timeline dentro de la misma unidad transaccional.

### 7.3 Correcciones posteriores

PERIO-0 no fija todavía addenda, anulación compensatoria ni examen correctivo. La arquitectura reserva referencias como `supersedes_exam_id`/`correction_of_exam_id`, pero no deben implementarse hasta decidir si se reutiliza el patrón de `ClinicalEvolution` o se crea una corrección propia del artefacto. Nunca se editará en sitio un examen finalizado.

## 8. Modelo dental

### 8.1 Numeración y dentición

FDI es el sistema canónico. Para dentición permanente se usan las 32 posiciones existentes en Dentia:

```text
18 17 16 15 14 13 12 11 | 21 22 23 24 25 26 27 28
48 47 46 45 44 43 42 41 | 31 32 33 34 35 36 37 38
```

La UI puede mostrar esa distribución, mientras el orden de captura se define de forma separada. No debe deducirse el orden de teclado a partir del orden visual del array.

Dentia ya soporta dentición permanente, temporal y mixta en el odontograma. El MVP periodontal se recomienda inicialmente para dentición permanente, pero esta es una decisión clínica pendiente. El modelo debe reservar `dentition_type` para evitar una migración destructiva si luego se habilita dentición temporal/mixta.

### 8.2 Relación con el odontograma

Se recomienda una combinación versionada:

- el odontograma sigue siendo fuente vigente del estado dental general;
- al crear un examen, el servicio transforma ese estado mediante un adaptador explícito y lo copia a `PeriodontalExamTooth`;
- el examen conserva `source_odontogram_id`, versión/fingerprint y timestamp de sincronización;
- el profesional puede revisar el snapshot antes de medir;
- una acción explícita de “Actualizar estado dental” puede volver a sincronizar un `DRAFT`, mostrando el diff y limpiando solo mediciones que resulten incompatibles mediante confirmación;
- un `FINALIZED` nunca cambia cuando cambia el odontograma.

El periodontograma no escribe eventos en el odontograma. Si durante el examen se detecta una ausencia o implante no registrado, la corrección debe hacerse en el odontograma y luego sincronizarse al borrador.

### 8.3 Ausencias e implantes

- `ABSENT`: no admite PD, GM, CAL, BOP ni placa periodontal normal.
- `IMPLANT`: admite observaciones periimplantarias en los seis sitios, pero debe identificarse explícitamente como implante y aplicar reglas propias validadas.
- `NATURAL_TOOTH`: admite el conjunto periodontal aprobado.

El examen guarda el estado como snapshot histórico y también el código fuente utilizado; así puede probar qué se conocía al finalizar sin duplicar la fuente vigente.

La inclusión de terceros molares, piezas no erupcionadas y dientes parcialmente presentes queda pendiente de validación clínica. El denominador nunca debe asumir automáticamente 168 o 192 sitios.

## 9. Sitios periodontales

### 9.1 Códigos internos

Se recomiendan códigos anatómicos independientes del idioma y de la arcada:

| Código | Label superior | Label inferior | Abreviatura UI |
|---|---|---|---|
| `DISTAL_FACIAL` | Distovestibular | Distovestibular | DV |
| `MID_FACIAL` | Vestibular | Vestibular | V |
| `MESIAL_FACIAL` | Mesiovestibular | Mesiovestibular | MV |
| `DISTAL_ORAL` | Distopalatino | Distolingual | DP/DL |
| `MID_ORAL` | Palatino | Lingual | P/L |
| `MESIAL_ORAL` | Mesiopalatino | Mesiolingual | MP/ML |

`ORAL` evita guardar “palatino” o “lingual” como anatomías distintas cuando la diferencia es de label según maxilar/mandíbula. Los códigos se congelan en el snapshot final.

### 9.2 Orden y orientación

La visualización debe respetar la orientación FDI existente en Dentia. La navegación clínica usa una lista de posiciones explícita generada por una función pura y versionada; no por índices visuales implícitos.

Como candidato de MVP se propone un recorrido fijo por arcada y superficie, posterior a anterior y con retorno por la cara oral. La ruta exacta —incluido el sentido por cuadrante y si se alternan GM/PD por sitio o por vuelta completa— queda bloqueada hasta validación clínica. La UI debe mostrar siempre el próximo sitio y permitir cambiar manualmente de pieza sin corromper la secuencia.

### 9.3 Elegibilidad

Las seis filas pueden materializarse al crear el examen para cada pieza elegible. Las piezas ausentes conservan su fila dental pero no necesitan mediciones activas. Furcación se modela aparte con reglas anatómicas por pieza, no como séptimo sitio.

## 10. Variables clínicas

### 10.1 Por sitio

| Variable | Tipo lógico | Null | Fuente | Observación |
|---|---|---:|---|---|
| `probing_depth_mm` (PD) | entero en mm | sí | medido | cero y no medido son estados diferentes |
| `gingival_margin_mm` (GM) | entero con signo | sí | medido | requiere convención de signo aprobada |
| `clinical_attachment_level_mm` (CAL/AL) | entero derivado | sí | calculado | solo si PD y GM existen y la regla está versionada |
| `bleeding_on_probing` (BOP) | booleano triestado | sí | observado | `false` = evaluado sin sangrado; `null` = no evaluado |
| `plaque_present` | booleano triestado | sí | observado | misma semántica triestado |

### 10.2 Por diente

| Variable | Tipo lógico | Nota |
|---|---|---|
| `tooth_state` | código snapshot | derivado del odontograma y confirmado en el examen |
| `mobility_grade` | código nullable | escala pendiente de aprobación |
| `is_implant` | derivado de `tooth_state` | no debe divergir como segundo booleano editable |
| `clinical_note` | texto breve saneado | opcional; contenido clínico, no log técnico |

### 10.3 Furcación

Cada registro contiene `entrance_code`, `grade_code` y, si se aprueba, notas. Tanto el catálogo de grados como las entradas válidas por FDI se resolverán en revisión clínica. No se inventa una escala en PERIO-0.

### 10.4 Reglas de validación

Tres niveles:

1. **Técnico:** tipo, signo, entero, payload, longitud y ausencia de valores no finitos. Siempre bloqueante.
2. **Anatómico:** no medir pieza ausente, no registrar furcación imposible, no mezclar estado natural/implante. Bloqueante cuando la regla esté clínicamente confirmada.
3. **Clínico:** valor inusual pero posible. Produce warning visible y confirmación; no debe bloquear por un rango arbitrariamente estrecho.

Los rangos exactos de PD, GM, CAL, movilidad y furcación son preguntas clínicas. El esquema debe permitir ampliar límites de warning sin reescribir exámenes finalizados.

## 11. Cálculos

### 11.1 Convención de GM y CAL

Se documentan dos convenciones equivalentes, pero no se selecciona una por inferencia:

| Convención | GM | Fórmula CAL | Ejemplo de recesión |
|---|---|---|---|
| A, candidata alineada con las fuentes revisadas | distancia firmada margen→CEJ; positiva si el margen está coronal a CEJ y negativa si está apical | `CAL = PD - GM` | PD 4, GM -2 → CAL 6 |
| B, recesión positiva | recesión positiva y agrandamiento/coronal negativo | `CAL = PD + GM` | PD 4, GM +2 → CAL 6 |

Ejemplos bajo la convención A: PD 2 y GM 2 producen CAL 0; PD 7 y GM 2 producen CAL 5. Antes de PERIO-2 un periodoncista debe aprobar la convención, nomenclatura y ejemplos. El sistema tendrá una sola convención canónica versionada; no se recomienda permitir inversión libre por usuario o por examen porque complica comparaciones e integridad.

### 11.2 Promedios

- `mean_pd = sum(PD no nulos) / count(PD no nulos)`.
- `mean_cal = sum(CAL calculables) / count(CAL calculables)`.
- Debe mostrarse también `measured_count / eligible_count`.
- Un promedio parcial se etiqueta como `Parcial`; no aparenta representar toda la boca.

### 11.3 BOP y placa

- `% BOP = sitios con BOP=true / sitios con BOP evaluado`.
- `% placa = sitios con plaque=true / sitios con placa evaluada`.
- `false` participa en el denominador; `null` no participa.
- Piezas ausentes y sitios no elegibles no participan.
- La UI presenta numerador, denominador, porcentaje y cobertura.

### 11.4 Progreso

El progreso no usa un denominador fijo. Se calcula con sitios elegibles según dentición, estado dental, terceros molares y variables requeridas. Puede mostrarse por métrica, por ejemplo `120/168 sitios con PD`, solo cuando 168 sea realmente el denominador del examen.

Todos los algoritmos quedan identificados por `calculation_version` y deben tener pruebas de frontera y fixtures clínicos aprobados.

## 12. Historial

La pestaña inicia con un historial paginado:

| Fecha clínica | Profesional | Sede | Estado | PD media | CAL media | BOP | Placa | Cobertura | Acciones |
|---|---|---|---|---:|---:|---:|---:|---:|---|

Reglas:

- más reciente primero;
- borradores visibles solo a usuarios con scope y permiso correspondientes;
- indicadores parciales llevan etiqueta visible;
- exámenes finalizados se abren en modo de solo lectura y permiten verificar integridad;
- el detalle muestra fuente dental, esquema, regla de cálculo y procedencia de copia;
- no se reemplazan exámenes anteriores por el más reciente.

La comparación entre dos exámenes usa sus snapshots finalizados, nunca el estado actual del odontograma.

## 13. Copia de examen anterior

La acción `Crear desde examen anterior` crea un nuevo `DRAFT` y permite elegir categorías:

- estado dental e implantes;
- movilidad;
- furcaciones;
- PD;
- GM;
- BOP;
- placa;
- notas, solo si se aprueba clínicamente.

Decisiones de seguridad:

1. Ninguna categoría se copia silenciosamente por defecto hasta aprobación clínica.
2. La pantalla identifica fecha, profesional y estado del examen fuente.
3. Solo un examen accesible del mismo paciente y tenant puede ser fuente.
4. Se guarda `copied_from_exam_id`, categorías copiadas, actor y timestamp.
5. El examen fuente nunca cambia.
6. Los valores copiados son un punto de partida clínico; la UI los diferencia hasta que el profesional revise/guarde el nuevo examen.
7. Si el estado dental vigente contradice el examen fuente, el servicio muestra conflicto y prioriza una decisión explícita; no crea mediciones en una pieza ausente.

La auditoría registra IDs y categorías, no el contenido clínico completo.

## 14. UX

### 14.1 Workspace

El periodontograma requiere un workspace de ancho completo dentro del expediente, no una tabla administrativa estrecha. Estructura propuesta:

```text
Encabezado: paciente · fecha · profesional · sede · estado · guardado
Barra: Historial | Examen | Indicadores | Finalizar
Controles: métrica activa · cara activa · navegación · progreso
┌──────────────── arcada superior ────────────────┐
│ valores vestibulares · dientes · valores orales │
└──────────────────────────────────────────────────┘
┌──────────────── arcada inferior ────────────────┐
│ valores orales · dientes · valores vestibulares │
└──────────────────────────────────────────────────┘
Panel auxiliar: pieza actual · movilidad · furcación · nota
```

En desktop/laptop se prioriza captura completa. En tablet horizontal se mantienen cuadrícula y teclado. En móvil, el MVP debe priorizar consulta y edición focal de una pieza; no fingir que una cuadrícula de hasta 192 sitios cabe cómodamente.

### 14.2 Estados visibles

- guardado, guardando, cambios sin guardar y conflicto de versión;
- examen parcial/finalizado;
- sitio no medido frente a valor cero;
- pieza ausente, implante y natural sin depender solo del color;
- warnings clínicos con texto y foco navegable;
- modo de solo lectura claramente distinto del borrador.

### 14.3 Accesibilidad

La cuadrícula debe usar semántica de tabla/grid accesible, labels que incluyan FDI, sitio y métrica, foco visible, atajos documentados y una alternativa textual a cualquier gráfico. Color nunca es el único portador de BOP, placa, ausencia o warning.

## 15. Navegación rápida

La captura se implementa como una máquina de navegación determinista:

- `cursor = {tooth_fdi, site_code, metric_code}`;
- una función pura calcula anterior/siguiente según `probing_sequence_version`;
- entrada numérica válida confirma el valor y avanza;
- `Tab` y `Shift+Tab` recorren siguiente/anterior;
- flechas cambian de celda sin modificar el valor;
- `Enter` confirma;
- `Escape` revierte el buffer no confirmado;
- teclado numérico funciona sin clics;
- BOP y placa tienen atajos binarios explícitos que no confunden `false` con vacío.

El buffer de entrada es local; no se envía una petición por tecla. Valores negativos requieren un token completo y no deben avanzar al escribir solo `-`.

La ruta clínica exacta es una decisión pendiente. La primera versión debe ofrecer una sola secuencia fija, visible y probada, sin configuración avanzada. Cambiar manualmente de pieza no altera datos y, al volver a “Continuar”, retoma la próxima posición incompleta de la secuencia activa.

## 16. Visualización clínica

### 16.1 Representación principal

Se propone HTML/CSS para inputs y estructura, con SVG para líneas y áreas clínicas. Ventajas frente a Canvas:

- accesibilidad y foco de inputs;
- hit testing y tooltips simples;
- pruebas de DOM;
- escalado responsive;
- estilos y capas mantenibles;
- exportación futura sin convertir toda la interacción en píxeles opacos.

El SVG no es fuente de verdad: recibe una proyección de las mediciones.

### 16.2 Gráfico periodontal

El gráfico puede representar por cara:

- línea de referencia/CEJ;
- margen gingival;
- fondo de sondaje;
- CAL o área de bolsa según la convención validada;
- marcadores de BOP y placa;
- implantes y ausencias con símbolos propios.

Las coordenadas usan una escala vertical en milímetros con clipping visual, sin alterar el valor real. Los puntos siguen el orden anatómico de los sitios. Maxilar y mandíbula usan transformaciones explícitas, no inversión accidental de signos.

Para reducir riesgo, la captura tabular, el resumen y la inmutabilidad son MVP obligatorio; el gráfico clínico entra en PERIO-4 antes del piloto si el odontólogo lo confirma indispensable. No bloquea el foundation de datos.

### 16.3 Identidad visual

Se mantiene el lenguaje Dentia “Clínica Moderna”, verde `#16A34A`, fondo claro y componentes existentes. Rojo para BOP o alertas no debe confundirse con selección. La densidad clínica y la legibilidad tienen prioridad sobre decoración.

## 17. Modelo de datos recomendado

### 17.1 Alternativas

| Estrategia | Ventajas | Riesgos |
|---|---|---|
| Relacional | constraints, queries por sitio, índices y comparación eficientes | snapshot/hash y evolución de esquema más complejos |
| JSONB puro | escritura simple y snapshot natural | constraints débiles, consultas/índices complejos, diffs y validación más frágiles |
| Híbrido | operación relacional y snapshot inmutable determinista | exige disciplina para evitar dos fuentes editables |

### 17.2 Recomendación: híbrido

Durante `DRAFT`, las tablas normalizadas son la fuente editable. Al finalizar, se genera un snapshot JSONB canónico y su hash; ese snapshot es el artefacto de integridad. Las filas normalizadas del examen finalizado quedan bloqueadas y permiten consultas/comparaciones. No hay dos fuentes editables.

#### `periodontal_exams`

- `id`, `company_id`, `patient_id`, `site_id`, `dentist_id`;
- `status`, `clinical_date`, `clinical_timezone`;
- `dentition_type`, `schema_version`, `calculation_version`, `sign_convention_version`;
- `source_odontogram_id`, `source_odontogram_fingerprint`, `dental_snapshot_at`;
- `copied_from_exam_id`, provenance de copia;
- `row_version`;
- `canonical_snapshot`, `content_hash`;
- `finalized_at`, `finalized_by_user_id`;
- timestamps y metadatos de creación/actualización.

#### `periodontal_exam_teeth`

- `id`, `exam_id`, `tooth_fdi`;
- `tooth_state`, `source_state_code`;
- `mobility_grade_code`, `clinical_note`;
- constraints de unicidad `(exam_id, tooth_fdi)`.

#### `periodontal_site_measurements`

- `id`, `exam_tooth_id`, `site_code`;
- `probing_depth_mm`, `gingival_margin_mm`;
- `clinical_attachment_level_mm` derivado/materializado al finalizar;
- `bleeding_on_probing`, `plaque_present` como booleanos nullable;
- unicidad `(exam_tooth_id, site_code)`.

#### `periodontal_furcations`

- `id`, `exam_tooth_id`, `entrance_code`, `grade_code`;
- snapshot de labels/versiones de catálogo si aplica;
- unicidad compatible con la regla clínica aprobada.

### 17.3 Constraints e índices

- FK y tenant consistente desde examen hacia paciente, sede y profesional validados en servicio;
- checks de FDI/dentición y códigos de sitio;
- índice por `(company_id, patient_id, clinical_date desc)`;
- índice por `(exam_id, status)` y por claves de comparación necesarias;
- el estado `FINALIZED` bloquea writes en servicio; se evalúa defensa adicional de DB en PERIO-1;
- soft deletion no debe ocultar ni borrar un examen finalizado; futuras anulaciones son estados compensatorios.

## 18. API propuesta

Endpoints conceptuales, sujetos a las convenciones reales del router:

| Método | Ruta conceptual | Uso |
|---|---|---|
| `GET` | `/api/patients/{patient_id}/periodontal-exams` | historial paginado |
| `POST` | `/api/patients/{patient_id}/periodontal-exams` | crear borrador desde odontograma vigente |
| `GET` | `/api/periodontal-exams/{exam_id}` | detalle autorizado |
| `PATCH` | `/api/periodontal-exams/{exam_id}/draft` | batch de cambios con `row_version` |
| `POST` | `/api/periodontal-exams/{exam_id}/copy` | nuevo borrador con categorías seleccionadas |
| `POST` | `/api/periodontal-exams/{exam_id}/sync-dental-status` | diff y sincronización explícita del borrador |
| `POST` | `/api/periodontal-exams/{exam_id}/finalize` | finalización idempotente |
| `GET` | `/api/periodontal-exams/{exam_id}/integrity` | verificación autorizada del snapshot |

El `PATCH` transporta cambios agrupados por diente/sitio y devuelve el examen consolidado, indicadores, warnings y nueva versión. No existe endpoint por celda.

Todos los endpoints clínicos usan `Cache-Control: no-store`, validan UUID dentro del tenant y no revelan si un recurso ajeno existe. Crear/copiar/finalizar aceptan una clave de idempotencia o equivalente según el patrón del proyecto.

La comparación longitudinal y exportación se agregan en fases posteriores; no deben inflar el contrato inicial.

## 19. Integración frontend

### 19.1 Entrada en el expediente

`PatientDetail` incorpora `Periodontograma` como pestaña independiente de Ortodoncia. La visibilidad y las acciones se derivan de permisos; la ausencia de permiso no se resuelve solo ocultando la pestaña, pues backend sigue siendo autoridad.

Estructura conceptual:

```text
frontend/components/periodontogram/
  PeriodontalWorkspace
  PeriodontalHistory
  PeriodontalExamEditor
  PeriodontalArch
  PeriodontalToothColumn
  PeriodontalSiteInput
  PeriodontalToothPanel
  PeriodontalIndicators
  PeriodontalChart
  periodontalNavigation
  periodontalCalculations
  types
```

### 19.2 Estado cliente

- query cache para historial/detalle remoto;
- reducer local normalizado por `tooth_fdi/site_code` durante edición;
- componentes memoizados por pieza y métrica;
- dirty state y confirmación al cambiar pestaña/paciente;
- guardado explícito como base del MVP;
- autosave debounced solo si puede mostrar estado, gestionar conflicto y no finalizar implícitamente;
- invalidación focal del historial al guardar/finalizar, sin recargar el expediente completo.

### 19.3 Integración clínica

La finalización publica una entrada en el timeline clínico con ID, fecha, profesional, sede y resumen no sensible. El detalle y las mediciones permanecen en el bounded context periodontal. No se crea automáticamente una `ClinicalEvolution` para evitar duplicar firma y narrativa; se deja abierta una relación opcional con una evolución existente tras revisión clínica.

## 20. Seguridad

Controles acumulativos en cada operación:

1. usuario autenticado y activo;
2. permiso exacto;
3. empresa activa y coincidente;
4. paciente perteneciente a la empresa;
5. sede permitida al usuario/profesional;
6. identidad odontológica activa para escritura/finalización;
7. scope clínico vigente;
8. estado del examen compatible;
9. relación de IDs internos validada en backend.

Reglas:

- `PLATFORM_ADMIN` no recibe contenido periodontal por herencia global;
- IDs del frontend nunca determinan tenant o profesional sin validación;
- cross-tenant e IDOR se prueban explícitamente;
- mensajes de error no filtran existencia de pacientes/exámenes ajenos;
- no incluir mediciones en logs, trazas o auditoría salvo necesidad legal explícita;
- exportaciones futuras exigen autorización y storage tenant-scoped;
- valores de texto se sanean para renderizado y PDFs futuros.

Un eventual entitlement comercial sería un control adicional, separado de RBAC. PERIO-0 no decide si Periodontograma será add-on.

## 21. Auditoría

Eventos conceptuales mínimos:

- `PERIODONTAL_EXAM_CREATED`
- `PERIODONTAL_EXAM_DRAFT_UPDATED`
- `PERIODONTAL_EXAM_COPIED`
- `PERIODONTAL_EXAM_DENTAL_STATUS_SYNCED`
- `PERIODONTAL_EXAM_FINALIZED`
- `PERIODONTAL_EXAM_INTEGRITY_CHECKED`
- futuros eventos compensatorios, solo cuando se diseñen.

Cada evento incluye actor, empresa, paciente/examen como entidad, sede, resultado, timestamp, versiones anterior/nueva y categorías afectadas. En una copia registra examen fuente y categorías; en sincronización, conteos de piezas cambiadas; en finalización, versión/hash. No registra matrices de PD/GM, notas ni datos clínicos completos.

La auditoría se escribe en la misma transacción de la mutación. Un fallo de auditoría aborta la operación clínica cuando así lo exige el patrón vigente.

## 22. Integridad

El snapshot final usa JSON canónico determinista:

- claves ordenadas y serialización estable;
- arrays en orden FDI/sitio definido por contrato, no por orden de inserción;
- fechas ISO-8601 y zona horaria explícita;
- enteros en mm, booleanos y null sin strings ambiguos;
- inclusión de schema, cálculo, convención de signo, procedencia dental y copia;
- snapshot de profesional/sede requerido para lectura histórica;
- SHA-256 sobre bytes canónicos.

La verificación reconstruye el payload desde las filas congeladas o compara el snapshot guardado según un contrato único. Cualquier divergencia se reporta y audita; no se “repara” automáticamente.

Finalizar no altera exámenes anteriores ni registros del odontograma. Un cambio futuro de fórmula no recalcula históricos: se conserva `calculation_version` y los valores derivados finalizados.

## 23. Concurrencia

`row_version` implementa locking optimista para edición. El cliente envía la versión leída; el backend actualiza con condición `id + row_version + DRAFT`. Si no coincide, responde conflicto con versión actual y obliga a revisar.

Operaciones críticas:

- crear/copiar: idempotencia para evitar dobles borradores por retry;
- guardar batch: transacción única por payload;
- sincronizar estado dental: lock del examen y verificación de fingerprint;
- finalizar: `SELECT FOR UPDATE`, doble chequeo de estado y hash;
- ninguna estrategia “last write wins” silenciosa;
- no mezclar automáticamente dos ediciones clínicas concurrentes por celda.

La UI conserva el buffer local ante conflicto y ofrece recargar/comparar; nunca sobrescribe la versión remota sin una acción consciente.

## 24. Performance

Un examen permanente puede tener hasta 192 sitios si incluye 32 piezas; excluir terceros molares produce 168. El diseño debe ser eficiente para ambos sin fijar uno como regla clínica.

Estrategia:

- una carga consolidada del examen con dientes, sitios, furcaciones e indicadores;
- estado local normalizado y actualización de una sola celda/pieza en React;
- guardados batch con solo filas cambiadas y `row_version`;
- bulk upsert del servicio, no queries una a una;
- precarga de un examen, no de toda la historia detallada;
- historial paginado con métricas materializadas del snapshot;
- SVG memoizado y desacoplado del buffer de cada tecla;
- índices compuestos por tenant/paciente/examen;
- límites de payload y número de filas coherentes con la dentición.

El MVP usa guardado explícito y puede sugerir guardado tras un intervalo; un autosave completo solo se habilita si las pruebas demuestran que no genera tormenta de requests ni conflictos invisibles.

## 25. MVP

MVP clínico propuesto:

- pestaña Periodontograma en paciente;
- historial y creación de múltiples exámenes;
- estados `DRAFT`/`FINALIZED`;
- dentición permanente FDI, con decisión explícita sobre terceros molares;
- snapshot del estado dental desde odontograma;
- natural/implante/ausente;
- seis sitios por pieza elegible;
- PD, GM, CAL, BOP y placa binaria;
- movilidad, furcación y nota cuando sus catálogos sean aprobados;
- captura de alta velocidad con teclado y secuencia fija;
- guardado batch, dirty state y conflicto de versión;
- indicadores básicos con cobertura;
- copia selectiva desde examen anterior;
- finalización, snapshot, hash, auditoría y timeline;
- consulta responsive y edición focal en móvil;
- seguridad tenant/sede/paciente/profesional y pruebas de IDOR.

El gráfico periodontal se incluye en PERIO-4 antes del piloto si la revisión clínica lo considera requisito de seguridad/uso; el modelo y la captura no dependen de él.

## 26. POST-MVP

- comparación visual de dos o más exámenes y tendencias por sitio;
- secuencias de sondaje configurables por clínica/profesional;
- voz y entrenamiento de comandos;
- impresión y PDF institucional;
- exportación estructurada;
- dentición temporal/mixta, si se aprueba;
- índices GI, mGI, mPI y otros índices clínicamente seleccionados;
- recesión Miller/Cairo, fenotipo, ancho de encía y línea mucogingival;
- microbiología y riesgo periodontal, si existe contrato clínico;
- gráficos longitudinales y filtros por profundidad;
- corrección/addendum/anulación compensatoria;
- integración explícita con una evolución clínica;
- entitlement comercial, si producto lo decide;
- captura offline o recuperación local avanzada.

## 27. Preguntas pendientes y riesgos

Las preguntas que requieren odontólogo/periodoncista están aisladas en [PERIO-0-CLINICAL-QUESTIONS.md](./PERIO-0-CLINICAL-QUESTIONS.md). Son bloqueantes para cerrar el contrato de PERIO-2/3 cuando afectan fórmula, escala, anatomía o completitud.

Riesgos principales:

| Riesgo | Consecuencia | Mitigación de arquitectura |
|---|---|---|
| Signo GM ambiguo | CAL incorrecto e históricos incomparables | convención única, versionada y aprobada antes de implementar |
| Estado dental duplicado | contradicción odontograma/periodontograma | fuente vigente + snapshot por examen + sincronización explícita solo en DRAFT |
| Nulos tratados como cero | indicadores falsos | tipos nullable y denominadores basados en sitios evaluados |
| Captura lenta | abandono o registros incompletos | secuencia fija, teclado, batch y renders focales |
| Rangos demasiado estrictos | bloqueo de casos clínicos reales | hard validation técnica y warnings clínicos configurables/versionados |
| Edición concurrente | pérdida silenciosa | `row_version`, lock final y conflictos visibles |
| Cambio de fórmula | alteración histórica | `calculation_version`, snapshot y no recálculo retroactivo |
| Acceso por UUID ajeno | fuga clínica | autorización tenant/paciente/sede en cada servicio y pruebas IDOR |
| Copia automática | arrastre de datos no reevaluados | copia selectiva, provenance y revisión explícita |
| UI móvil sobredensa | errores de captura | consulta y editor focal, no cuadrícula comprimida |

## 28. Roadmap propuesto PERIO-1+

### PERIO-1 — Foundation, seguridad y lifecycle

- contratos, permisos autorizados, aggregate root, DRAFT/FINALIZED;
- integración paciente/sede/profesional/timeline;
- auditoría, tenant scope, locking e idempotencia;
- migración inicial sin UI clínica completa.

### PERIO-2 — Modelo dental y mediciones clínicas

- adaptador de estado odontográfico y snapshot;
- dientes, seis sitios, furcaciones y variables aprobadas;
- convención GM/CAL versionada;
- validaciones anatómicas y clínicas.

### PERIO-3 — Captura de alta velocidad

- workspace, arcadas, teclado y secuencia aprobada;
- batch save, dirty state, warnings y responsive focal;
- pruebas de ergonomía con odontólogo.

### PERIO-4 — Indicadores y visualización

- cálculos con cobertura y fixtures clínicos;
- SVG periodontal accesible;
- resumen, progreso y verificación de consistencia.

### PERIO-5 — Historial, copia e integridad

- historial paginado;
- copia selectiva con provenance;
- finalización, snapshot canónico, hash y verificador;
- impresión básica solo si queda aprobada para MVP.

### PERIO-6 — Hardening y piloto clínico

- concurrencia, performance, seguridad e IDOR;
- revisión de rangos y fixtures por periodoncista;
- prueba de flujo real en desktop/tablet;
- recuperación/rollback y rollout controlado.

### PERIO-7+ — Evolución posterior

- comparación longitudinal;
- correcciones compensatorias;
- índices avanzados, voz, exportación y configuración;
- dentición temporal/mixta y otras extensiones aprobadas.

## Apéndice A — Decisiones de arquitectura consolidadas

| Tema | Recomendación PERIO-0 |
|---|---|
| Fuente vigente del estado dental | Odontograma |
| Verdad histórica del examen | Snapshot dental y periodontal congelado en `PeriodontalExam` |
| Persistencia | Híbrida: tablas normalizadas + snapshot JSONB/hash al finalizar |
| Edición | Solo `DRAFT`; batch y optimistic locking |
| Finalización | Transaccional, inmutable y versionada |
| Sitios | Seis códigos anatómicos estables por pieza elegible |
| Nulos | “No medido”; nunca cero implícito |
| Furcación | Entidad por entrada/ubicación, no scalar único por diente |
| Timeline | Artefacto periodontal independiente enlazado al expediente |
| Evolución clínica | No creación automática en MVP; vínculo futuro por decidir |
| UI | Workspace clínico, teclado y SVG; móvil focal |
| Add-on | Posible control futuro, separado de RBAC; no decidido |

## Apéndice B — Fuentes y referencias revisadas

### Arquitectura Dentia

- `backend/app/models/clinical_record.py`
- `backend/app/services/clinical_record_service.py`
- `backend/app/models/odontogram.py`
- `backend/app/services/site_access_service.py`
- `backend/app/models/orthodontics.py`
- `backend/app/services/orthodontic_record_service.py`
- `backend/app/core/security_catalog.py`
- `frontend/components/patients/PatientDetail.tsx`
- `frontend/components/odontogram/classic/dualOdontogramLayout.ts`

### Referencia funcional

- [Periodontograma Online, Universidad de Berna / perio-tools.com](https://www.periodontalchart-online.com/?lang=es), consultado el 2026-09-17. Se revisaron flujo, seis sitios, copia selectiva, secuencia, indicadores, visualización y voz. Se usa únicamente como referencia conceptual; no se copian código, diseño ni assets.

### Fuentes clínicas y de medición

- [CDC/NCHS — NHANES Oral Health Examiners Manual](https://wwwn.cdc.gov/nchs/data/nhanes/public/2013/manuals/Oral_Health_Examiners.pdf), consultado el 2026-09-17. Documenta seis sitios, orden de examen y relación entre margen, profundidad y pérdida de inserción en su protocolo epidemiológico.
- [CDC/NCHS — NHANES Examination Variable List](https://wwwn.cdc.gov/nchs/nhanes/search/variablelist.aspx?Component=Examination), consultado el 2026-09-17. Confirma variables periodontales y fórmula del protocolo NHANES.
- [CDC — MMWR, Periodontal Disease Surveillance](https://www.cdc.gov/MMWr/preview/mmwrhtml/su6203a21.htm), consultado el 2026-09-17. Describe examen de seis sitios y mediciones de pérdida de inserción en contexto de vigilancia.
- [WHO — Oral Health Surveys: Basic Methods, 5th edition](https://www.who.int/publications/b/31326), consultado el 2026-09-17. Referencia epidemiológica; no se adopta como contrato completo de charting individual.
- [American Academy of Periodontology — Diagnosis and Examination](https://www.perio.org/research-science/periodontal-literature-review/diagnosis-and-examination/), consultado el 2026-09-17.

Estas fuentes informan el diseño, pero no sustituyen la validación del odontólogo/periodoncista ni constituyen asesoría clínica o regulatoria.
