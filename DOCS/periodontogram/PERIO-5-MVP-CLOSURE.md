# PERIO-5 — Cierre del MVP de Periodontograma

## Alcance final

PERIO-5 cierra el MVP clínico construido en PERIO-0 a PERIO-4.3. El módulo conserva el periodontograma como un registro clínico independiente, con 32 piezas permanentes, seis sitios por pieza, captura rápida, gráfico periodontal, lifecycle `DRAFT`/`FINALIZED`, correcciones versionadas, snapshots deterministas e historial inmutable.

El cierre añade el historial operativo definitivo y una integración opcional, explícita y auditable con una evolución clínica existente. No genera evoluciones, diagnósticos ni contenido clínico automáticamente.

## Exámenes e historial

La lista principal representa controles periodontales independientes y se ordena por fecha clínica y creación, del más reciente al más antiguo. Cada fila muestra:

- fecha clínica;
- profesional responsable;
- sede;
- estado humano (`Borrador` o `Finalizado`);
- versión actual;
- acción contextual.

Un borrador ofrece `Continuar`. Un examen finalizado ofrece `Ver` y, con el permiso correspondiente, `Corregir`. El historial de exámenes no se mezcla con el historial de versiones.

## Versiones y correcciones

Las versiones pertenecen a un único examen. La versión actual aparece primero y las anteriores se identifican como históricas. Una versión histórica se carga desde su snapshot, permanece en solo lectura y no muestra acciones de guardar, finalizar o corregir.

El flujo de corrección permanece:

1. examen finalizado;
2. inicio explícito de corrección con motivo;
3. nueva versión `DRAFT`;
4. edición y finalización;
5. versión anterior intacta y nuevo hash para la versión corregida.

La concurrencia se controla mediante bloqueo de fila y `row_version`: una finalización o corrección concurrente obtiene un único ganador; una solicitud obsoleta recibe conflicto y nunca sobrescribe silenciosamente.

## Integración opcional con evolución clínica

La integración elegida para el MVP vincula un `PeriodontalExam` finalizado a una `ClinicalEvolution` existente mediante `periodontal_exams.evolucion_id`.

Reglas:

- el vínculo es nullable y cada examen puede apuntar como máximo a una evolución;
- repetir exactamente el mismo vínculo es un no-op idempotente;
- reemplazarlo por otra evolución es un conflicto;
- no existe desvinculación en el MVP;
- la evolución debe pertenecer a la misma empresa, paciente y sede;
- el actor debe tener acceso clínico vigente a ambos registros y scope de sede válido;
- el snapshot vigente debe superar la verificación de integridad;
- los IDs se validan en backend; la UI no define el scope de seguridad.

La FK usa `ON DELETE RESTRICT`, por lo que una evolución vinculada no puede eliminarse silenciosamente. El vínculo no copia PD, margen gingival, CAL, sangrado, placa, supuración, notas ni diagnósticos. La UI muestra únicamente una referencia resumida con fecha, profesional, sede y estado.

## Migración 0044

`20260923_0044_periodontogram_evolution_link.py` agrega:

- columna nullable `periodontal_exams.evolucion_id`;
- FK a `evoluciones_clinicas.id` con borrado restringido;
- índice `ix_periodontal_exams_evolution_link` sobre empresa, paciente y evolución.

La migración no actualiza datos, no reescribe snapshots ni toca versiones finalizadas. El downgrade elimina solamente índice, FK y columna, siguiendo el patrón Alembic del repositorio.

## Fechas clínicas y zona horaria

`clinical_date` representa la fecha del control. `created_at` registra la creación técnica y `finalized_at` la finalización. Son conceptos distintos.

La creación desde UI obtiene la fecha de calendario en la zona horaria de la sede activa. Fechas y horas de versiones y evoluciones se presentan con la zona horaria persistida; no se expone UTC crudo como hora clínica.

## Auditoría y privacidad

Se conservan los eventos de creación, actualización de borrador, finalización e inicio de corrección. El vínculo agrega:

`PERIODONTAL_EXAM_EVOLUTION_LINKED`

Su registro contiene únicamente identificadores técnicos del examen, evolución, actor, empresa y sede, además del timestamp estándar. No contiene nombre del paciente, mediciones, notas, diagnósticos ni snapshots.

Consultar historial o versiones no produce escrituras de auditoría.

## Seguridad

Todas las rutas mantienen:

- aislamiento por empresa;
- scope de sede;
- permisos clínicos PERIO existentes;
- validación de paciente, examen, versión y evolución en backend;
- ausencia de acceso clínico implícito para `ADMINISTRATOR`, `SECRETARY` y `PLATFORM_ADMIN`;
- respuestas controladas ante IDOR y referencias incompatibles.

El endpoint de vínculo reutiliza permisos clínicos existentes; no introduce un permiso redundante. Vincular requiere finalizar periodontogramas y consultar registros/evoluciones clínicas dentro del scope actual.

## Integridad y rendimiento

- Una versión finalizada no se edita directamente.
- Los snapshots históricos se verifican con su hash persistido.
- El vínculo no cambia el snapshot ni su hash.
- Cada examen mantiene exactamente una referencia a versión actual.
- La carga de historial resuelve examen, versión actual, profesional y sede en una consulta compuesta.
- Una versión histórica se presenta desde el snapshot persistido, sin reconstruirla desde las filas clínicas actuales.
- La matriz y el gráfico conservan las optimizaciones y el scroll local aprobados en PERIO-4.3.

## UX y responsive

El encabezado diferencia explícitamente historial de exámenes e historial de versiones. Las acciones, estados y errores se presentan en lenguaje clínico. La protección contra cambios sin guardar cubre cierre, cambio de examen, consulta de versión histórica y creación de un nuevo examen.

Desktop conserva matriz, gráfico y acciones en anchos de 1280, 1440 y 1920 px. Tablet usa scroll horizontal local sincronizado. Mobile prioriza consulta, historial, gráfico y edición básica sin alterar el modelo clínico.

## Escenario sintético de piloto

El entorno local de revisión usa exclusivamente datos sintéticos y contempla:

- tenant, sede, odontólogo y paciente de prueba;
- V1 finalizada;
- corrección V2 finalizada;
- V3 en borrador o un examen independiente en borrador;
- pieza ausente e implante;
- movilidad y furcación;
- sangrado, placa y supuración;
- márgenes gingivales positivos y negativos;
- profundidades de 3, 4, 5 y 6 mm;
- una evolución compatible del mismo paciente y sede para probar el vínculo opcional.

Recorrido manual: iniciar sesión, abrir paciente y Periodontograma, revisar historial, continuar borrador, guardar, finalizar, corregir, consultar versiones, vincular opcionalmente a una evolución y volver a consultar el snapshot histórico.

## Fuera del MVP

Permanecen fuera de alcance:

- comparación longitudinal entre exámenes;
- diff visual entre versiones;
- PDF;
- dictado por voz;
- secuencias de captura configurables;
- índices periodontales adicionales;
- variables mucogingivales avanzadas;
- diagnóstico o clasificación periodontal automáticos;
- IA.

## Criterio de cierre

El MVP queda listo para piloto cuando migración, pruebas focales y DB-backed, caracterización de seguridad, fechas clínicas, hardening, concurrencia de autenticación, suites frontend, lint, typecheck, build, compileall, `pip check`, Alembic y `git diff --check` estén limpios, seguidos de revisión manual del escenario sintético. Este documento no autoriza push ni deploy.
