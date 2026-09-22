# USAGE-1 — Foundation y query layer de métricas de adopción

**Estado:** implementado para validación local

**Fecha:** 2026-09-21

**Catálogo:** `USAGE_1_V1`

## 1. Objetivo y alcance

USAGE-1 implementa una consulta agregada, read-only y exclusiva de Platform Admin para medir actividad funcional atribuible a un usuario dentro de una empresa y periodo. Sigue el contrato de `USAGE-0-ADOPTION-METRICS.md` y no construye dashboard, scoring, rankings, rollups ni tracking frontend.

La consulta no evalúa productividad ni calidad clínica. Responde cuánto se usaron flujos existentes y conserva separados los indicadores clínicos de la actividad administrativa.

## 2. Arquitectura

```text
Tablas transaccionales + auditoría allowlisted
                    │
                    ▼
        usage_adoption_service.py
        - tenant/dimension guards
        - actor attribution
        - local-date boundaries
        - SQL aggregation
        - privacy projection
                    │
                    ▼
 GET /api/platform/usage/users/{user_id}
                    │
                    ▼
  Aggregate response; no clinical drill-down
```

No se creó almacenamiento analítico. Los datos se calculan desde las fuentes canónicas. La migración `20260921_0041` agrega únicamente RBAC.

## 3. API

```http
GET /api/platform/usage/users/{user_id}
```

Query parameters:

- `company_id`, obligatorio;
- `start_date` y `end_date`, fechas locales inclusivas;
- `dentist_id`, opcional y validado contra usuario/empresa;
- `site_id`, opcional y validado contra empresa;
- `preset`, opcional: `last_7_days`, `last_30_days` o `pilot_to_date`.

`pilot_to_date` exige `start_date` explícita mientras Dentia no tenga `pilot_started_at`. Un rango personalizado exige ambas fechas. El máximo es 366 días.

La respuesta usa:

```text
Cache-Control: no-store, max-age=0
Pragma: no-cache
```

No existe endpoint de detalle ni endpoint que devuelva qué pacientes originaron un conteo.

## 4. Seguridad y RBAC

Permiso nuevo:

```text
platform.usage.view
```

Asignación:

| Rol | Acceso |
|---|---|
| `PLATFORM_ADMIN` | Sí |
| `ADMINISTRATOR` | No |
| `DENTIST_ADMIN` | No |
| `DENTIST` | No |
| `SECRETARY` | No |

El permiso permite consultar agregados; no concede acceso a endpoints clínicos tenant. El endpoint exige `company_id` y rechaza usuarios, perfiles odontológicos o sedes que no pertenezcan a la empresa indicada.

La consulta no escribe auditoría adicional en USAGE-1 para conservar semántica read-only. La decisión de auditar vistas del futuro dashboard queda para USAGE-2, con evento mínimo y sin resultados ni filtros sensibles.

## 5. Periodos y zona horaria

- La zona horaria proviene de `Company.timezone`.
- Las fechas de entrada son inclusivas para la interfaz.
- Internamente se convierten a un intervalo UTC semiabierto `[start_at, end_at)`.
- Los días activos se agrupan en fecha local de la empresa.
- Las semanas empiezan el lunes.
- Un filtro por sede no cambia la zona horaria del reporte.
- Cuando una fuente no conserva sede histórica —por ejemplo, creación de paciente o auditoría general— no se inventa una sede y no se excluye silenciosamente del total de usuario/empresa.

## 6. Atribución

La dimensión primaria es el actor (`user_id`). Nunca se atribuye una acción a partir del odontólogo asignado.

| Dominio | Actor utilizado |
|---|---|
| Citas creadas | `Appointment.created_by` |
| Transiciones de cita | `AppointmentHistory.user_id` |
| Pacientes creados | `Patient.created_by` |
| Historia abierta | `ClinicalRecord.created_by` |
| Evolución creada/firmada | `created_by` / `signed_by` |
| Addendum | `ClinicalEvolutionAddendum.created_by` |
| Tratamiento/procedimiento | `created_by` |
| Tratamiento cerrado | auditoría `TREATMENT_CLOSED` exitosa |
| Presupuesto creado/aprobado | `created_by` / `approved_by` |
| Consentimiento creado/compartido | `created_by` de instancia/sesión de acceso |
| Consentimiento aceptado | resultado de una instancia iniciada por el actor |
| Caso de Ortodoncia creado | `created_by_user_id` |
| Evolución ortodóncica | actor de la `ClinicalEvolution` vinculada |
| Ficha ortodóncica finalizada | `finalized_by_user_id` |
| Pago registrado/reversado | `registered_by` / `reversed_by` |

`orthodontic_cases_active` es el único dato contextual: si el usuario tiene perfil odontológico, cuenta casos actualmente activos asignados a ese perfil. Se mantiene separado de `orthodontic_cases_created`, que sí es actor-scoped.

## 7. Métricas implementadas

### General

- último login desde `User.last_login_at`;
- primer login exitoso dentro del periodo;
- primera y última actividad funcional allowlisted;
- días locales distintos con actividad funcional.

El allowlist excluye refresh, healthchecks y vistas de baja señal. Incluye acciones exitosas de agenda, pacientes, historia/evoluciones, tratamientos, presupuestos, consentimientos, Ortodoncia y pagos.

### Agenda

- citas creadas;
- confirmadas, reprogramadas, completadas y canceladas por actor;
- días con actividad de agenda;
- pacientes únicos con actividad de agenda.

### Pacientes

- pacientes creados por actor;
- pacientes únicos con actividad atribuible en agenda, clínica, tratamientos, consentimientos u Ortodoncia.

La creación administrativa aislada de un paciente no incrementa el agregado de pacientes con actividad funcional.

### Historia clínica

- historias abiertas;
- evoluciones creadas;
- evoluciones firmadas;
- addenda creadas;
- borradores actuales creados en el periodo;
- pacientes únicos con actividad clínica.

Las consultas no seleccionan texto de evolución, diagnósticos, hallazgos, indicaciones ni addenda.

### Tratamientos y presupuestos

- tratamientos creados;
- procedimientos registrados;
- tratamientos cerrados por actor;
- presupuestos iniciales creados;
- versiones creadas;
- presupuestos aprobados por actor;
- pacientes únicos con actividad del módulo.

No se seleccionan ni serializan valores monetarios.

### Consentimientos

- instancias creadas;
- sesiones de acceso compartidas;
- instancias iniciadas por el actor y firmadas en el periodo;
- instancias pendientes creadas en el periodo;
- pacientes únicos con actividad.

No se selecciona contenido, snapshot, firma, OTP, token ni destinatario.

### Ortodoncia

- casos creados por actor;
- casos activos asignados al perfil odontológico, como contexto;
- evoluciones ortodóncicas creadas y firmadas;
- fichas finalizadas;
- pacientes únicos con actividad ortodóncica.

La consulta no abre casos ni obtiene contenido de ficha/evolución y no evita los resolvers clínicos existentes: este endpoint solo devuelve agregados a Platform Admin.

### Actividad administrativa

- pagos registrados;
- pagos reversados.

Los montos quedan excluidos. Esta sección no se mezcla con adopción clínica.

## 8. Tendencia semanal

Cada semana del rango se devuelve, incluso si todos sus conteos son cero:

- `appointments_activity`;
- `unique_patients`;
- `evolutions_signed`;
- `treatments_created`;
- `consents_created`;
- `orthodontic_activity`.

La serie se calcula con un `UNION ALL` de proyecciones mínimas (`metric`, `occurred_at`, `patient_id`) y se agrupa en PostgreSQL. Los identificadores de pacientes solo participan dentro del conteo `DISTINCT`; nunca salen del servicio.

## 9. Métricas no soportadas

La respuesta declara explícitamente:

| Código | Razón |
|---|---|
| `patients_viewed` | No existe un evento general fiable de apertura de paciente |
| `session_duration` | `last_seen_at` no representa duración real |
| `cash_closures` | No existe fuente transaccional canónica con actor para cierres |

No se fabrican aproximaciones silenciosas.

## 10. Privacidad

El schema no expone:

- `patient_id`, nombre, documento, correo o teléfono del paciente;
- IDs de citas, historias, evoluciones, tratamientos o consentimientos;
- diagnósticos, texto clínico, notas, mensajes o contenido documental;
- valores monetarios;
- IP, user-agent, sesión, token u OTP;
- detalle crudo de auditoría.

Sí devuelve los IDs administrativos mínimos de empresa, usuario, perfil odontológico y sede solicitados, junto con conteos y timestamps agregados.

## 11. Estrategia de consultas y rendimiento

- Agregaciones `COUNT`, `COUNT DISTINCT`, filtros y uniones se ejecutan en PostgreSQL.
- No se cargan colecciones ORM ni se itera por entidad, por lo que no hay N+1.
- La prueba de baseline limita una consulta completa a 32 statements; el diseño actual permanece por debajo del límite con todas las secciones.
- Se reutilizan índices actuales por empresa/fecha, usuario/fecha, sede y relaciones.
- No se agregó índice sin evidencia de un plan deficiente.
- Si volumen real lo exige, USAGE-2/3 puede introducir rollups diarios minimizados y reconciliables, no una copia de auditoría.

## 12. Pruebas

La suite DB-backed cubre:

- permiso exclusivo de Platform Admin;
- 401 anónimo y 403 para los cuatro roles tenant;
- validación cruzada de empresa/usuario;
- diez citas creadas por secretaría para un odontólogo sin atribuirlas al odontólogo;
- deduplicación de paciente único;
- evolución clínica firmada por actor;
- pago atribuido al administrador que lo registra;
- caso/evolución de Ortodoncia atribuibles;
- límites locales Colombia alrededor de medianoche;
- helpers de 7 y 30 días;
- ausencia de PII, texto clínico, montos, IP y user-agent;
- número acotado de queries.

La migración 0041 se valida con upgrade, downgrade, upgrade final, `alembic current`, `heads` y `check`. La caracterización registra 300 rutas y ninguna pendiente.

## 13. Pendientes de USAGE-2

- construir el selector y dashboard visual Platform Admin;
- definir auditoría mínima de vistas sin convertirla en tracking clínico;
- acordar una fuente explícita para `pilot_started_at`;
- medir planes reales con `EXPLAIN ANALYZE` y volumen productivo anonimizado;
- evaluar cache privada o rollups solo si el costo lo justifica;
- mantener sin scoring, ranking ni drill-down.
