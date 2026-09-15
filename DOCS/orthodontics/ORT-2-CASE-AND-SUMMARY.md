# ORT-2 — Caso de Ortodoncia y resumen clínico

## Alcance

ORT-2 incorpora la raíz clínica de Ortodoncia por paciente sin implementar todavía evoluciones especializadas ni la ficha ortodóncica extensa. El módulo reutiliza el entitlement, los cupos y el resolver de acceso de ORT-1, además de la historia clínica y la agenda existentes.

La estructura del resumen se verificó contra la fuente clínica `dentia ortodoncia.docx`: plan de tratamiento, aparatología, última visita/evolución, actividad realizada, próxima cita e indicaciones para la siguiente sesión.

## Modelo

`OrthodonticCase` es tenant-scoped y patient-scoped. Relaciona el caso con la historia clínica general, la sede de apertura y el odontólogo responsable. Persiste solamente:

- lifecycle y fechas de apertura/cierre;
- responsable clínico;
- plan general de tratamiento;
- resumen de aparatología actual;
- motivo de cierre, actores y `row_version`.

Un índice parcial único impide más de un caso abierto (`DRAFT`, `ACTIVE` o `SUSPENDED`) por paciente y empresa. Los casos cerrados permanecen inmutables y no existe eliminación física.

## Lifecycle

El contrato ORT-0 se conserva:

```text
DRAFT → ACTIVE ⇄ SUSPENDED
           └────→ COMPLETED
                  ↘ cierre interrumpido
```

Una interrupción se persiste como cierre `COMPLETED` con `closure_reason_code=DISCONTINUED`; la API la expone con `display_status=DISCONTINUED`. Esto preserva la nomenclatura de ORT-0 y permite diferenciar el resultado clínico sin reabrir casos históricos. El motivo es obligatorio para la interrupción.

Después de un cierre puede abrirse un caso nuevo. Nunca se reactiva silenciosamente uno histórico.

## Acceso y responsable

No se agregaron permisos nuevos. Cada endpoint exige `clinical.view` o `clinical.update` y, además, el resolver central de ORT-1 valida:

- entitlement efectivo de la empresa;
- usuario y perfil odontológico activos;
- assignment activo de Ortodoncia;
- mismo tenant;
- sede activa dentro del scope odontológico.

El responsable debe pertenecer al tenant, estar operativo, tener assignment activo y estar habilitado en la sede del caso. El cambio de responsable solo admite otro odontólogo elegible y deja auditoría del identificador anterior y nuevo.

La lectura mantiene el aislamiento fuerte definido por ORT-0: retirar el assignment o desactivar el entitlement bloquea el acceso clínico de Ortodoncia, aunque los casos y su historia permanecen intactos en la base de datos.

`ADMINISTRATOR`, `SECRETARY` y `PLATFORM_ADMIN` no obtienen acceso clínico por sus facultades administrativas. Un administrador solo podría operar clínicamente si también fuera un odontólogo activo, assigned y con los permisos clínicos requeridos.

## Resumen derivado

El DTO de resumen combina los datos persistidos del caso con datos derivados:

- responsable, estado, fecha de inicio, plan y aparatología: desde el caso;
- próxima cita agendada: primera cita futura activa del paciente, excluyendo canceladas y atendidas;
- última visita, qué se hizo, indicaciones, próximo control clínico y alertas: `null` o lista vacía hasta ORT-3.

No se crean textos clínicos ficticios ni una evolución artificial. La próxima cita administrativa se presenta separada del próximo control clínico recomendado.

## Historia clínica y auditoría

Crear, activar y cerrar un caso agrega un evento resumido al timeline clínico general. No se crea una segunda historia ni una `ClinicalEvolution` falsa.

Se auditan:

- `ORTHODONTIC_CASE_CREATED`;
- `ORTHODONTIC_CASE_ACTIVATED`;
- `ORTHODONTIC_CASE_SUSPENDED`;
- `ORTHODONTIC_CASE_RESUMED`;
- `ORTHODONTIC_CASE_RESPONSIBLE_CHANGED`;
- `ORTHODONTIC_CASE_PLAN_UPDATED`;
- `ORTHODONTIC_CASE_APPLIANCE_UPDATED`;
- `ORTHODONTIC_CASE_COMPLETED`;
- `ORTHODONTIC_CASE_DISCONTINUED`.

La auditoría de ediciones registra nombres de campos, no el texto clínico completo.

## API

```text
GET   /api/patients/{patient_id}/orthodontics
POST  /api/patients/{patient_id}/orthodontics/cases
GET   /api/orthodontics/cases/{case_id}
PATCH /api/orthodontics/cases/{case_id}
POST  /api/orthodontics/cases/{case_id}/activate
POST  /api/orthodontics/cases/{case_id}/complete
POST  /api/orthodontics/cases/{case_id}/suspend
POST  /api/orthodontics/cases/{case_id}/resume
POST  /api/orthodontics/cases/{case_id}/discontinue
POST  /api/orthodontics/cases/{case_id}/change-responsible
```

Las mutaciones usan control optimista por `row_version`. La creación combina bloqueo de paciente e índice único para que solicitudes repetidas o concurrentes produzcan un solo caso abierto.

## UI

`Paciente → Ortodoncia` solo aparece tras un preflight exitoso del resolver. La navegación interna ofrece:

- Resumen: funcional en ORT-2;
- Evolución: placeholder controlado;
- Historia clínica de Ortodoncia (Colombia) o Ficha clínica de Ortodoncia (Chile): placeholder controlado.

El resumen muestra estado, responsable, inicio, plan, aparatología, próxima cita, estados vacíos explícitos e historial de casos. La edición es una acción expresa con feedback; no hay autosave clínico. Los casos cerrados son de solo lectura.

## Integración futura

El texto `treatment_plan` es un resumen clínico del caso y no duplica presupuestos. ORT-3 podrá derivar visitas, indicaciones, control y alertas desde evoluciones ortodóncicas firmadas. Una fase posterior podrá enlazar el caso con tratamientos comerciales existentes sin convertir ORT-2 en una segunda fuente financiera.

## Pruebas

La cobertura incluye acceso, tenant isolation, responsable elegible, unicidad e idempotencia concurrente, lifecycle, cierre inmutable, historial, resumen derivado, próxima cita, auditoría sin texto clínico, revocación de assignment y etiquetas por país. La caracterización de seguridad registra las ocho rutas como privadas y DB-backed.

## Fuera de ORT-2

No se implementan evoluciones especializadas, cefalometría, ATM, periodoncia, hábitos, catálogos de aparatología, firma ortodóncica especializada, pricing ni billing. Esos elementos permanecen para ORT-3 y fases posteriores.
