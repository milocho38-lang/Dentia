# ORT-3 Evoluciones estructuradas de Ortodoncia

## Resultado

ORT-3 incorpora controles ortodóncicos estructurados como extensiones uno a uno de `ClinicalEvolution`. La evolución clínica existente continúa siendo la fuente canónica de autor, paciente, sede, fecha clínica, estado, firma, hash, timeline, auditoría y addenda. La extensión ortodóncica conserva únicamente el detalle especializado y participa en el material firmado del padre.

La implementación fue contrastada con `dentia ortodoncia.docx`. No incluye la ficha clínica extensa, análisis facial, oclusión, ATM, periodoncia, cefalometría, imágenes ni cobro mensual; esos elementos permanecen fuera de ORT-3.

## Arquitectura

```text
OrthodonticCase
  └── OrthodonticEvolution
        ├── ClinicalEvolution 1:1 canónica
        ├── snapshots de material y tamaño por arcada
        ├── alineadores y elásticos manuales
        ├── 0..N OrthodonticEvolutionMiniScrew
        ├── próximo control
        └── alerta simple
```

`clinical_evolution_id` es único. El servicio verifica empresa, paciente e historia clínica contra el caso. La creación del padre y de la extensión se confirma en una sola transacción. La firma bloquea padre, extensión y caso, valida nuevamente entitlement, assignment, identidad odontológica, sede y estado del caso, calcula el hash ortodóncico y lo incorpora al payload canónico del padre antes de confirmar la transacción.

Las rutas genéricas de edición y firma rechazan padres con extensión ortodóncica. Esto evita modificar o firmar solo la narrativa y dejar los campos especializados fuera del control de versión. El endpoint especializado reutiliza el motor de firma clínico, ejecuta el preflight ortodóncico y calcula el hash compuesto en una única transacción. Las adendas continúan usando la ruta clínica existente, pero aplican además entitlement, assignment, identidad y scope de Ortodoncia.

## Ciclo clínico

- Solo un caso `ACTIVE` permite crear, editar o firmar evoluciones.
- Un caso `SUSPENDED` permite lectura, pero debe reactivarse para continuar el tratamiento.
- Los casos `DRAFT` y `COMPLETED` no aceptan controles clínicos.
- El profesional se deriva de la identidad odontológica del actor; no se escoge arbitrariamente.
- Otro ortodoncista asignado puede consultar el historial. La edición y firma conservan las reglas de ownership de `ClinicalEvolution`: un odontólogo opera sus registros y un `DENTIST_ADMIN` clínicamente habilitado puede operar borradores autorizados.
- Una evolución firmada es inmutable. Las aclaraciones narrativas usan addenda. ORT-3 no implementa mutación estructurada retrospectiva; un cambio clínico vigente debe registrarse prospectivamente en otra evolución firmada.

El contenido mínimo para firma es al menos uno de: `performed_summary`, notas narrativas o un campo ortodóncico estructurado. Cuando solo existe estructura, el padre conserva un marcador clínico neutro interno; la respuesta especializada mantiene las notas vacías.

## Campos

El formulario contiene los bloques Consulta, Arco superior, Arco inferior, Alineadores, Elásticos, Microtornillos, Próxima sesión y Alertas.

Los campos `performed_summary` y notas se proyectan respectivamente en `performed_procedure` y `evolution_text` del padre. Las indicaciones se integran con `indications`. La fecha sugerida se calcula desde la fecha clínica local de la sede, no desde la zona horaria del host, y también se expone como próximo control del padre. Guardar la evolución nunca crea una cita.

Los microtornillos son una colección. Cada fila conserva tipo, ubicación, material, medida manual y notas opcionales. La medida no presupone unidad porque la fuente clínica todavía no la define.

## Catálogos y snapshots

Las categorías extensibles iniciales son:

- `ARCH_MATERIAL`;
- `ARCH_SIZE`;
- `CONTROL_INTERVAL`.

Las opciones base Dentia se cargan en la migración `20260914_0038`, son inmutables y no pertenecen a una empresa. Las opciones personalizadas pertenecen a una sola empresa, se auditan y se retiran sin eliminación física. Una opción retirada deja de estar disponible para nuevos borradores.

Cada evolución copia `option_id`, código y etiqueta. La historia firmada no cambia si una opción se retira posteriormente. `Sin arco` y `Sin cambios` son selecciones explícitas distintas de `null`. ORT-3 registra el comando utilizado, pero no propaga automáticamente un estado de aparatología ambiguo. `current_appliance_summary` de ORT-2 continúa siendo el resumen manual del caso.

## Próximo control y resumen

Los intervalos base son una a seis semanas y dos a doce meses. Se almacenan como valor, unidad y etiqueta congelada. La fecha sugerida aplica suma calendaria sobre la fecha clínica local; no constituye una cita.

El Resumen ORT-2 consulta dinámicamente la evolución ortodóncica firmada más reciente y muestra:

- fecha y profesional de la última visita;
- qué se hizo;
- indicaciones para la siguiente sesión;
- intervalo y fecha sugerida del próximo control;
- alerta activa de esa evolución.

Los borradores no alimentan el resumen. No se guarda una copia mutable de la última visita.

## Permisos

Las acciones clínicas reutilizan `clinical_evolutions.view`, `create`, `update_draft`, `sign` y `add_addendum`, siempre junto con el resolver ORT-1.

La migración agrega únicamente:

| Rol | catalog.view | catalog.manage |
|---|---:|---:|
| ADMINISTRATOR | Sí | Sí |
| DENTIST_ADMIN | Sí | Sí |
| DENTIST | Sí | No |
| SECRETARY | No | No |
| PLATFORM_ADMIN | No | No |

Gestionar catálogos no concede acceso a pacientes, casos ni evoluciones.

## API

- `GET /api/orthodontics/catalogs/{catalog_type}`
- `POST /api/orthodontics/catalogs/{catalog_type}/options`
- `POST /api/orthodontics/catalog-options/{id}/retire`
- `GET|POST /api/orthodontics/cases/{case_id}/evolutions`
- `GET /api/orthodontics/evolutions/{id}`
- `PATCH /api/orthodontics/evolutions/{id}/draft`
- `POST /api/orthodontics/evolutions/{id}/sign`

## Auditoría

Se registran `ORTHODONTIC_EVOLUTION_CREATED`, `UPDATED`, `SIGNED`, `ORTHODONTIC_CATALOG_OPTION_CREATED` y `RETIRED`. La auditoría no copia la narrativa clínica completa.

## Decisiones clínicas pendientes

- Semántica exacta del identificador de alineador superior e inferior.
- Catálogo clínico de tipos y configuraciones de elásticos.
- Unidad y formato de la medida de microtornillos.
- Evolución futura de alertas hacia severidad, fecha objetivo y resolución.
- Propagación clínica exacta de `Sin cambios` cuando exista `OrthodonticApplianceState`.
- Operación compensatoria para correcciones estructuradas retrospectivas.

Estos puntos se conservan como texto manual o comportamiento no inferido. No bloquean la captura y firma del control ORT-3.
