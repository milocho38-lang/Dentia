# C019A.1 — Implementación del motor de plantillas

## Decisiones derivadas del contrato C019A.0

La fuente de verdad es la versión persistida, no una vista previa ni un futuro PDF. Se mantuvo íntegramente la máquina `DRAFT → PUBLISHED → SUPERSEDED | RETIRED` y `DRAFT → VOIDED`.

## Modelo

- `consentimiento_plantillas`: identidad estable tenant, código único, tipo, país e idioma.
- `consentimiento_plantilla_versiones`: contenido, alcance, estado, hash, snapshot de variables y trazabilidad.
- `consentimiento_plantilla_version_sedes`: FK versionada a sede.
- `consentimiento_plantilla_version_procedimientos`: FK versionada al catálogo de procedimientos.
- `consentimiento_plantilla_version_especialidades`: asociación explícita código/nombre porque Dentia no posee un catálogo relacional de especialidades.

No se añadió `current_published_version_id`: el índice parcial único sobre `template_id WHERE status='PUBLISHED'` evita una segunda fuente de verdad y garantiza como máximo una publicación vigente.

## Migración

La revisión `20260801_0023` depende de `20260724_0022`. Crea constraints de estado, secuencia, prioridad, unicidad e índices de consulta. Las FK usan `RESTRICT` o `SET NULL`; no existe cascada que elimine el historial de plantillas.

Los siete permisos se insertan idempotentemente y se asignan a roles tenant. El downgrade conserva permisos y asociaciones rol-permiso porque el bootstrap pudo haberlos creado antes y eliminarlos sería destructivo.

## Formato de contenido

Se eligió `RESTRICTED_MARKDOWN_V1` sobre HTML porque cubre títulos, subtítulos, párrafos, listas, énfasis y separadores sin requerir sanitizar DOM arbitrario. El renderer frontend crea nodos React, nunca utiliza `dangerouslySetInnerHTML`.

Se rechazan:

- etiquetas HTML;
- enlaces e imágenes Markdown en este MVP;
- URI `javascript`, `vbscript` y `data:text/html`;
- delimitadores incompletos;
- expresiones Jinja, filtros y acceso dinámico.

## Publicación y hash

La publicación bloquea la plantilla y versión con `FOR UPDATE`. Si existe una publicación, primero se actualiza y vacía como `SUPERSEDED`; después la nueva versión entra al índice parcial como `PUBLISHED`, todo en una transacción.

El SHA-256 usa JSON canónico con:

- identidad: código, tipo, país e idioma;
- versión, título, contenido y formato;
- variables usadas;
- ámbito, prioridad, sedes, procedimientos y especialidades.

El snapshot de variables guarda únicamente definiciones permitidas usadas en esa publicación.

## Servicios y API

El router expone catálogo, CRUD administrativo sin eliminación física, historial, validación, preview, publicación, retiro, anulación, duplicación a borrador y auditoría. El tenant siempre procede de `AuthContext`; ningún payload acepta `empresa_id`.

Los errores son:

- `403`: permiso o asociación cross-tenant;
- `404`: recurso tenant no visible;
- `409`: transición, inmutabilidad, versión optimista, código o publicación concurrente;
- `422`: contenido, variable, país, idioma o asociación inválida.

## Integración C019A.2

`find_applicable_published_templates` recibe empresa, país, idioma y criterios opcionales de sede, procedimientos y especialidades. Solo devuelve `PUBLISHED` de plantillas activas, ordenadas por especificidad y prioridad. Si existen varios candidatos, el profesional deberá elegir; C019A.1 no resuelve ambigüedad clínica.

## Seguridad

- tenant derivado de sesión y aplicado en cada lectura/mutación;
- validación separada de FK para sedes y procedimientos;
- `PLATFORM_ADMIN` sin permisos tenant;
- control optimista `row_version` en borradores;
- límites Pydantic y DB constraints;
- auditoría sin contenido completo ni datos de paciente;
- rutas críticas registradas como DB-backed.

## Diferencias del repositorio real

- el rol conceptual `COMPANY_ADMIN` se llama `ADMINISTRATOR`;
- especialidad es texto en empresa/tratamiento, no catálogo; por eso se versiona como código y nombre explícitos;
- los servicios acceden directamente a SQLAlchemy; no existe repositorio de dominio general para replicar;
- la UI no tiene framework de pruebas de componentes, por lo que se añadió prueba ejecutable de helpers puros más caracterización del contrato visual.
