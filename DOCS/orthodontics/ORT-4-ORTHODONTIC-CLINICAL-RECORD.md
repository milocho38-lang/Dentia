# ORT-4 — Historia clínica de Ortodoncia versionada

## Objetivo

ORT-4 incorpora una ficha clínica especializada vinculada al caso de Ortodoncia. En Colombia se presenta como **Historia clínica de Ortodoncia** y en Chile como **Ficha clínica de Ortodoncia**. No reemplaza la historia clínica general, las evoluciones ni el resumen derivado del caso.

La estructura se contrastó con el documento fuente `dentia ortodoncia.docx`. Los campos se mantienen opcionales: el indicador de avance informa el estado de captura, pero no convierte campos en requisitos clínicos inventados.

## Modelo

- `OrthodonticClinicalRecord`: raíz única por `OrthodonticCase`.
- `OrthodonticClinicalRecordVersion`: versiones numeradas y tenant-scoped.
- `DRAFT`: editable con control optimista mediante `row_version`.
- `FINALIZED`: inmutable, con fecha clínica, zona horaria, actor, snapshot del schema, snapshot humano del contenido y SHA-256 canónico.
- Solo puede existir un borrador simultáneo por ficha.
- Una modificación posterior a la finalización crea una nueva versión clonada; nunca reabre ni altera la anterior.

El contenido clínico usa JSONB únicamente bajo `ORTHODONTIC_RECORD_V1`. El backend rechaza claves, tipos, opciones o duplicados no registrados. El snapshot final conserva códigos y etiquetas utilizados, de modo que cambios futuros del formulario no reinterpreten versiones históricas.

## Secciones clínicas

| Orden | Sección |
|---:|---|
| 1 | Generales / Anamnesis |
| 2 | Características faciales |
| 3 | Análisis oclusal y dentario |
| 4 | Dentoalveolar |
| 5 | Montaje de articulador |
| 6 | Análisis periodontal |
| 7 | ATM y muscular |
| 8 | Radiografías / estudios |
| 9 | Vía aérea |
| 10 | Análisis cefalométrico |
| 11 | Otros factores |

Los estudios se documentan como hallazgos o diagnósticos. ORT-4 no duplica almacenamiento de imágenes. Los campos cuya semántica, unidad u opción múltiple aún requiere homologación clínica conservan una bandera explícita `clinical_pending_flag`; no se presentan como definiciones regulatorias o clínicas cerradas.

### Matriz del schema V1

| Sección | Campos derivados de la fuente | Implementación V1 |
|---|---|---|
| Generales | Motivo de consulta, hábitos, radiografía de mano | Texto, multiselección y selección única |
| Facial | Asimetría, desviación mandibular, exposición gingival, cierre labial, clase facial, tercio inferior, labios y mentón | Selecciones estables y texto manual |
| Oclusal | Dentición, líneas medias, clases molares/caninas, overjet, Spee, overbite, plano oclusal, transversal, Wilson y formas de arco | Selecciones estables de la fuente |
| Dentoalveolar | Discrepancias, Bolton, supernumerarios/agenesias, ausentes/retenidos, molares, trauma, facetas y panorámica | Texto manual, booleano y selecciones estables |
| Articulador | RC/OC, contacto prematuro, rotación, torque y CPI | Selección RC/OC y texto manual |
| Periodontal | Higiene, biotipo, recesiones, hiperplasia, eminencia, frenillos y otros | Selecciones estables y texto manual |
| ATM y muscular | Manipulación, ATM bilateral, palpación y patrón de apertura | Selección y multiselección según convención de la fuente |
| Estudios | Dx CBCT, otro estudio y Dx RNM | Texto clínico; integración documental futura |
| Vía aérea | Respiración, sueño y otros | Texto manual |
| Cefalometría | Ricketts, Jarabak, inclinaciones, ANB, WITS, clase esqueletal, vertical y transversal | Selecciones de fuente y texto sin inventar unidades |
| Otros | Factores determinantes | Texto manual |

### Registro de decisiones clínicas pendientes

| Campo | Fuente | Implementación MVP | Pendiente clínico |
|---|---|---|---|
| Discrepancia dental superior/inferior | Línea manual | Texto | Definición y unidades |
| Índice de Bolton | Línea manual | Texto | Formato/unidad |
| CPI derecho/izquierdo/transversal | Línea manual | Texto | Tipo y unidad |
| ATM derecha/izquierda | Lista sin modo inequívoco | Multiselección conservadora | Confirmar single/multi |
| Palpación muscular | Guiones | Multiselección | La fuente no define lado, dolor ni intensidad |
| Patrón de apertura | Guiones | Multiselección | Confirmar exclusiones clínicas |
| Tipo de respiración, sueño y otros | Líneas manuales | Texto | Catálogo clínico futuro |
| Jarabak tipo | Checklist | Multiselección | Confirmar exclusividad |
| Jarabak porcentaje | Línea manual | Texto | Unidad/formato |
| Inclinaciones incisivas, ANB y WITS | Líneas manuales | Texto | Unidades/formato |
| Clase esqueletal | Guiones | Multiselección | Confirmar exclusividad |
| Mediciones verticales, Penn | Líneas manuales | Texto | Unidades/formato |

Las correcciones de presentación inequívocas —por ejemplo, “Presenica” a “Presencia”— no alteran abreviaturas ni términos clínicos (`Pp2`, `Mp3`, `CPI`, `WITS`).

## Lifecycle y acceso

- Crear, guardar y generar una nueva versión exige caso `ACTIVE`, tenant correcto, identidad odontológica activa, entitlement activo, assignment activo, sede válida y `clinical.update`.
- Finalizar exige además `clinical_evolutions.sign`; no se creó un permiso redundante.
- Casos `SUSPENDED` o `COMPLETED` son de solo lectura.
- La desactivación del entitlement o la revocación del assignment conserva la lectura histórica al odontólogo activo dentro de su tenant y sede, pero bloquea toda escritura.
- `ADMINISTRATOR`, `SECRETARY` y `PLATFORM_ADMIN` no obtienen acceso clínico por sus roles administrativos o globales.
- Todo acceso usa IDs asociados al tenant; un ID de otra empresa se responde como no encontrado.

## Auditoría y timeline

Se auditan la creación de la ficha, actualización del borrador, finalización y creación de nueva versión. La finalización agrega un evento real al timeline clínico general, enlazado con la versión finalizada. No se crea una evolución clínica ficticia ni se duplica la fuente de verdad.

## API

- `GET /api/orthodontics/cases/{case_id}/record`: ficha, schema y versiones; acepta `version_id` para lectura histórica.
- `POST /api/orthodontics/cases/{case_id}/record`: crea la raíz y V1 en borrador.
- `PATCH /api/orthodontics/cases/{case_id}/record/versions/{version_id}`: guarda un borrador con `row_version`.
- `POST /api/orthodontics/cases/{case_id}/record/versions/{version_id}/finalize`: finaliza e inmoviliza.
- `POST /api/orthodontics/cases/{case_id}/record/versions`: clona una versión finalizada en un nuevo borrador.

No se exponen endpoints de eliminación ni mutación de versiones finalizadas.

## UI

La pestaña especializada permite:

- navegar por las once secciones mediante sidebar o selector responsive;
- consultar avance informativo por sección;
- guardar explícitamente el borrador;
- advertir cambios sin guardar al abandonar la página;
- finalizar con confirmación;
- consultar cualquier versión histórica;
- crear una nueva versión desde una versión finalizada;
- consultar casos históricos cuando no existe un caso abierto.

## Migración

`20260914_0039_orthodontic_clinical_record.py` crea las dos tablas, constraints de integridad, unicidad raíz/caso, unicidad de numeración y el índice parcial que impide más de un borrador. No agrega ni asigna permisos.

## Pruebas

La cobertura DB-backed verifica lifecycle, opcionalidad, schema, snapshot, hash, auditoría, timeline, inmutabilidad, clonación, concurrencia, estados suspendido/cerrado, conservación histórica sin entitlement, RBAC, aislamiento tenant y etiqueta por país. El test frontend verifica integración de pestaña, navegación, guardado, finalización, cambio de versión y advertencia de cambios sin guardar.

## Fuera de alcance

ORT-4 no implementa adjuntos diagnósticos, exportación documental, plantillas genéricas, nuevas reglas clínicas, ORT-5 ni cambios en RIPS o website.
