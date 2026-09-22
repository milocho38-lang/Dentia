# USAGE-0 — Diseño de métricas de adopción de usuarios piloto

**Estado:** diseño funcional y técnico para revisión; sin implementación

**Fecha:** 2026-09-21

**Alcance:** actividad funcional agregada de usuarios piloto en Dentia

**Siguiente fase propuesta:** USAGE-1, únicamente después de aprobar este contrato

## 1. Objetivo

Definir cómo medir si los odontólogos piloto incorporan Dentia a su trabajo diario sin leer, copiar ni exponer contenido clínico. Las métricas deben responder cuánto se usan los módulos, con qué continuidad y sobre cuántos pacientes, pero no evaluar la calidad clínica, la productividad ni el desempeño profesional.

USAGE-0 es exclusivamente una fase de análisis y diseño. No crea tablas, eventos, endpoints, permisos, componentes, migraciones ni procesos de analítica.

Decisiones principales:

1. La unidad primaria es la **acción atribuible al usuario**, no el objeto asignado al odontólogo.
2. `user_id` y `dentist_id` se conservan como dimensiones diferentes.
3. Los conteos históricos parten de las tablas transaccionales; la auditoría se usa solamente cuando aporta actor o transición que la fila actual ya no conserva.
4. El dashboard entrega agregados. No devuelve nombres, identificadores ni listas de pacientes.
5. El MVP muestra métricas directas y tendencias; no crea un score de adopción.
6. Pagos se consideran adopción operativa de la clínica, no adopción clínica del odontólogo, salvo que el propio odontólogo haya registrado la acción.

## 2. Scope

El diseño cubre:

- actividad por `company_id`, `user_id`, `dentist_id` y, cuando la fuente lo soporta, `site_id`;
- último acceso, primera y última actividad funcional y días activos;
- Agenda, Pacientes, Historia Clínica, Evoluciones, Tratamientos, Presupuestos, Consentimientos, Pagos y Ortodoncia;
- periodos de 7 días, 30 días, desde el inicio del piloto y rango personalizado;
- tendencias semanales;
- dashboard agregado para Platform Admin;
- inventario de fuentes existentes, brechas y eventos no recomendados;
- arquitectura de consulta, backfill, privacidad y evolución.

El análisis se realizó sobre el snapshot productivo actual del repositorio y, principalmente, sobre:

- `backend/app/models/auth_session.py`, `user.py` y `audit_event.py`;
- `backend/app/models/agenda.py`, `clinical_record.py`, `treatment.py`, `consent_template.py`, `consent_acceptance.py` y `orthodontics.py`;
- los servicios de autenticación, pacientes, agenda, historia clínica, tratamientos, consentimientos y Ortodoncia;
- `backend/app/services/report_service.py`, como referencia para periodos, zona horaria y filtros existentes;
- `backend/app/core/security_catalog.py`, para confirmar que aún no existe un permiso de adopción de plataforma.

## 3. No-scope

USAGE-0 no diseña ni autoriza:

- lectura o análisis semántico de evoluciones, diagnósticos, notas, consentimientos o documentos;
- medición de calidad, efectividad, complejidad o resultado clínico;
- ranking o comparación competitiva de profesionales;
- metas comerciales, comisiones o decisiones laborales;
- grabación de clicks, teclas, navegación detallada o session replay;
- tracking de IP, user-agent, dispositivo o ubicación como indicador de adopción;
- analítica de pacientes identificables;
- un score único de adopción;
- alertas automáticas en el MVP;
- exportación de datos de uso a terceros;
- instrumentación, código o migraciones.

Los términos aceptados son **uso**, **adopción**, **actividad** y **cobertura de módulos**. Deben evitarse **rendimiento**, **efectividad**, **calidad** y **productividad profesional**.

## 4. Modelo de atribución

### 4.1 Dimensiones

| Dimensión | Definición | Regla |
|---|---|---|
| `company_id` | Tenant dueño de la actividad | Obligatorio en toda métrica |
| `user_id` | Persona autenticada que ejecutó la acción | Dimensión primaria de adopción |
| `dentist_id` | Perfil profesional relacionado | Se resuelve por `odontologos.usuario_id`; nunca sustituye al actor |
| `site_id` | Sede clínica u operativa de la acción | Solo se usa cuando la entidad/evento la conserva de forma histórica |
| periodo | Ventana temporal del evento | Intervalo semiabierto `[inicio, fin)` en UTC, derivado de la zona horaria de la empresa |

### 4.2 Actor y profesional no son equivalentes

Dentia conserva citas, tratamientos y otros objetos asignados a un odontólogo que pueden ser creados o gestionados por secretaría o administración. Por eso deben existir dos conceptos:

- `actor_user_id`: quien realmente ejecutó la acción en Dentia;
- `clinical_dentist_id`: profesional asignado o responsable del objeto clínico.

El dashboard de adopción de un odontólogo cuenta por defecto acciones cuyo `actor_user_id` corresponde a su usuario. Una cita asignada al odontólogo pero creada por secretaría no incrementa **citas creadas por el odontólogo**. Puede mostrarse separadamente como **citas asignadas/atendidas**, etiquetada como contexto asistencial y no como acción del usuario.

### 4.3 Reglas de atribución

1. Nunca inferir actor a partir de `responsible_dentist_id`, `dentist_id` o `professional_user_id`.
2. Preferir columnas explícitas: `created_by`, `signed_by`, `approved_by`, `registered_by`, `finalized_by_user_id` o `AppointmentHistory.user_id`.
3. Para transiciones, usar el evento auditado exitoso cuando la fila actual no conserva todos los cambios históricos.
4. No atribuir una aceptación pública de consentimiento al odontólogo. Puede medirse como resultado de una instancia iniciada por él.
5. Si no hay actor verificable, clasificar la métrica como no atribuible; no completar el dato por heurística.
6. No inferir sede histórica desde la sede activa actual de la sesión.
7. Cuando una acción carece de sede, devolver `site_id = null`/`NOT_APPLICABLE`; no excluirla del total de empresa o usuario.
8. Toda consulta debe aplicar simultáneamente tenant, usuario, periodo y, si corresponde, sede.

### 4.4 Zonas horarias y semanas

- El contrato inicial reutiliza la zona horaria de la empresa, como hace `report_service.py`.
- Los límites locales se convierten a UTC antes de consultar.
- Los días activos se agrupan por fecha local de la empresa.
- La semana inicia el lunes y termina el domingo.
- Un filtro por sede no cambia la zona horaria del reporte en el MVP; la respuesta informa explícitamente la zona usada.
- Las marcas clínicas (`attended_at`, `clinical_date`) y las marcas de acción (`created_at`, `occurred_at`) no deben intercambiarse. Adopción usa la fecha de la acción, salvo que la métrica diga expresamente “atenciones clínicas del periodo”.

## 5. Fuentes existentes y confiabilidad

### 5.1 Niveles

| Nivel | Significado |
|---|---|
| Alta | La tabla canónica conserva actor, tenant, fecha y entidad suficientes |
| Media | Requiere auditoría allowlisted, join estable o tiene limitación histórica conocida |
| Baja | Solo puede inferirse de estado actual o de un campo mutable; no entra al MVP |

### 5.2 Inventario por dominio

| Dominio | Fuente existente | Evidencia útil | Confiabilidad | Observación |
|---|---|---|---|---|
| Login | `usuarios`, `auth_sessions`, `auth_attempts`, `auditoria_eventos` | `last_login_at`, sesión, `LOGIN_SUCCESS`, `last_seen_at` | Alta para último login; media para días activos | `last_seen_at` se sobrescribe y no reconstruye días históricos |
| Agenda | `citas`, `cita_historial`, auditoría | `created_by`, sede, paciente, odontólogo, transición, `user_id` | Alta | Permite separar actor de odontólogo asignado |
| Pacientes | `pacientes`, auditoría | `created_by`, `updated_by`, `PATIENT_CREATED`, `PATIENT_QUICK_CREATED` | Alta para creación; baja para consulta | No existe un evento fiable de apertura del paciente |
| Historia clínica | `historias_clinicas`, timeline y auditoría | apertura, actualización y `CLINICAL_RECORD_*` | Alta para creación; media para actividad | `CLINICAL_RECORD_VIEWED` existe, pero no es métrica primaria |
| Evoluciones | `evoluciones_clinicas`, `evoluciones_adendas`, timeline y auditoría | `created_by`, `signed_by`, estado, firma, addenda | Alta | No requiere leer texto clínico |
| Tratamientos | `tratamientos`, `tratamiento_procedimientos`, `tratamiento_eventos`, auditoría | creación, estados, procedimientos, realización | Alta | La fila actual no reemplaza el historial de transiciones |
| Presupuestos | `presupuestos`, auditoría | creador, versión, aprobación/rechazo y actor | Alta | Versiones deben deduplicarse según definición de cada métrica |
| Consentimientos | instancias, sesiones de acceso, aceptación, papel y auditoría | creador, profesional, sede, emisión, firma, canal | Alta | Resultado público y acción profesional son conceptos distintos |
| Pagos | `pagos_tratamiento`, auditoría | `registered_by`, sede, registro y reverso | Alta | Predominantemente adopción administrativa |
| Ortodoncia | casos, ficha versionada, extensión de evolución y auditoría | creador, responsable, sede, firma/finalización | Alta | Evolución ortodóntica reutiliza `ClinicalEvolution` |
| Auditoría | `auditoria_eventos` | tenant, usuario, sesión, entidad, acción, resultado y fecha | Media como fuente analítica | Incluye ruido, eventos de lectura, IP/UA y detalles que no deben exponerse |

### 5.3 Capacidades actuales importantes

- `AuditEvent` ya está indexado por empresa/fecha y usuario/fecha.
- `AuthSession` conserva creación, expiración y última actividad de sesión.
- `AppointmentHistory` conserva transiciones y actor.
- `ClinicalEvolution` conserva creación, firma, profesional, sede, paciente y timestamps.
- `TreatmentEvent` y auditoría conservan transiciones, pero sus descripciones/metadata no deben salir al dashboard.
- Consentimientos conservan estado, canal, creador, profesional, sede, firma y eventos detallados.
- Ortodoncia conserva caso, evolución vinculada, versiones de ficha y actores de finalización.
- No existe actualmente una tabla o API específica de product analytics/adopción.
- No existe todavía `platform.usage.view`; cualquier implementación futura debe agregar un permiso específico y no reutilizar permisos clínicos.

## 6. Métricas por módulo

Todas las métricas siguientes retornan conteos o fechas, nunca contenido.

### 6.1 Login y actividad general

| Métrica | Definición | Fuente | Estado |
|---|---|---|---|
| Último acceso | Último login exitoso del usuario | `User.last_login_at` | YA MEDIBLE |
| Logins exitosos | `LOGIN_SUCCESS` del usuario en el periodo | auditoría/auth attempts | YA MEDIBLE |
| Sesiones iniciadas | sesiones creadas en el periodo | `AuthSession.created_at` | YA MEDIBLE |
| Primera actividad funcional | mínimo evento exitoso del allowlist funcional | auditoría | YA MEDIBLE |
| Última actividad funcional | máximo evento exitoso del allowlist funcional | auditoría | YA MEDIBLE |
| Días activos | fechas locales distintas con al menos una acción funcional allowlisted | auditoría | YA MEDIBLE con contrato de allowlist |
| Duración de sesión | diferencia entre creación y última actividad | `AuthSession` | NO RECOMENDADO |

`TOKEN_REFRESHED`, refresh en segundo plano, lectura de healthchecks y apertura de pantalla no cuentan como actividad funcional. Login sirve como contexto, no como indicador principal de adopción.

### 6.2 Agenda

| Métrica | Definición atribuible | Fuente |
|---|---|---|
| Citas creadas | citas con `created_by = user_id` y `created_at` en el periodo | `Appointment` |
| Citas confirmadas | transición `APPOINTMENT_CONFIRMED` ejecutada por el usuario | auditoría o `AppointmentHistory` |
| Citas reprogramadas | `APPOINTMENT_RESCHEDULED` ejecutada por el usuario | auditoría |
| Citas completadas | `APPOINTMENT_COMPLETED` ejecutada por el usuario | auditoría/`AppointmentHistory` |
| Citas canceladas | `APPOINTMENT_CANCELLED` ejecutada por el usuario | auditoría |
| Días con actividad de agenda | días distintos de las acciones anteriores | eventos allowlisted |
| Pacientes únicos con cita gestionada | `COUNT(DISTINCT appointment.patient_id)` sobre acciones del usuario | join evento-cita |
| Citas asignadas al odontólogo | citas cuyo `dentist_id` coincide, independientemente del actor | `Appointment` |

La última métrica es contexto asistencial y debe presentarse separada de las acciones del usuario. Una cita no se cuenta dos veces si una operación compuesta genera eventos auxiliares.

### 6.3 Pacientes

| Métrica | Definición | Estado |
|---|---|---|
| Pacientes creados | pacientes con `created_by = user_id` | YA MEDIBLE |
| Pacientes únicos con actividad clínica | pacientes distintos vinculados a evoluciones, tratamientos, consentimientos u Ortodoncia accionados por el usuario | YA MEDIBLE mediante unión deduplicada |
| Pacientes únicos atendidos | pacientes con evolución firmada por el usuario o cita completada por el usuario | YA MEDIBLE |
| Pacientes consultados | aperturas de ficha por el usuario | NO FIABLE actualmente |

`CLINICAL_RECORD_VIEWED` no sustituye un evento general de paciente consultado y no debe usarse para inflar adopción. Tampoco se recomienda instrumentar cada apertura de pantalla en el MVP.

### 6.4 Historia clínica y evoluciones

| Métrica | Definición | Fuente |
|---|---|---|
| Historias abiertas | historias con `created_by = user_id` | `ClinicalRecord` |
| Historias con actividad | historias/pacientes con acciones de creación, actualización, evolución o addendum del usuario | tablas canónicas + auditoría allowlisted |
| Evoluciones creadas | `ClinicalEvolution.created_by = user_id` | `ClinicalEvolution` |
| Evoluciones firmadas | `signed_by = user_id`, estado `SIGNED`, firma dentro del periodo | `ClinicalEvolution` |
| Pacientes con evolución | pacientes distintos de evoluciones creadas o firmadas por el usuario | `ClinicalEvolution` |
| Addenda creadas | `ClinicalEvolutionAddendum.created_by = user_id` | addenda |
| Borradores vigentes | evoluciones `DRAFT` creadas por el usuario | `ClinicalEvolution` |

No se seleccionan `evolution_text`, motivo, hallazgos, diagnósticos, indicaciones ni contenido de addenda.

### 6.5 Tratamientos, procedimientos y presupuestos

| Métrica | Definición | Fuente |
|---|---|---|
| Tratamientos creados | `Treatment.created_by = user_id` | `Treatment` |
| Tratamientos cerrados | evento `TREATMENT_CLOSED` exitoso por el usuario | auditoría |
| Procedimientos registrados | procedimientos creados por el usuario | `TreatmentProcedure.created_by` |
| Procedimientos realizados | `PROCEDURE_MARKED_DONE` o finalización clínica atribuible al usuario | auditoría + procedimiento |
| Presupuestos creados | versiones iniciales creadas por el usuario | `Budget.created_by` |
| Versiones de presupuesto creadas | todas las versiones creadas por el usuario | `Budget.created_by`, `version` |
| Presupuestos aprobados | `BUDGET_APPROVED` por el usuario | auditoría/`approved_by` |
| Pacientes con tratamiento | pacientes distintos de tratamientos/procedimientos accionados por el usuario | tablas canónicas |

“Presupuestos creados” debe contar series, no todas las versiones. “Versiones creadas” es una métrica separada para evitar duplicación engañosa.

### 6.6 Consentimientos

| Métrica | Definición | Fuente |
|---|---|---|
| Consentimientos generados | instancias con `created_by = user_id` | `ConsentInstance` |
| Consentimientos preparados | instancias confirmadas por el profesional (`professional_confirmed_by`) | instancia |
| Consentimientos enviados/compartidos | emisión de sesión de acceso ejecutada por el usuario | `CONSENT_ACCESS_SESSION_ISSUED/REISSUED` |
| Consentimientos firmados | instancias iniciadas por el usuario que alcanzaron `SIGNED` en el periodo | instancia + `signed_at` |
| Consentimientos pendientes | cohorte creada por el usuario y actualmente en estado no terminal | instancia |
| Consentimientos en papel finalizados | finalización de paquete papel por el usuario | auditoría/paquete papel |

La aceptación electrónica la realiza el paciente o adulto responsable. Por tanto, **firmado** es un resultado del flujo iniciado, no una acción atribuida al odontólogo. El dashboard no expone firmante, declaraciones, documento, OTP, enlace ni contenido.

### 6.7 Pagos

| Métrica | Definición | Uso recomendado |
|---|---|---|
| Pagos registrados | `registered_by = user_id` | Vista operativa secundaria |
| Pagos reversados | evento/`reversed_by = user_id` | Vista operativa secundaria |
| Comprobantes generados | `PAYMENT_RECEIPT_GENERATED` | Opcional, no indicador clínico |

Los montos no son necesarios para adopción y deben omitirse. En el dashboard de odontólogo piloto, Pagos no entra al resumen principal. Puede mostrarse en una sección “Actividad administrativa” si el usuario ejecutó esas acciones.

### 6.8 Ortodoncia

| Métrica | Definición | Fuente |
|---|---|---|
| Casos creados | `created_by_user_id = user_id` | `OrthodonticCase` |
| Casos activos | casos actuales `ACTIVE` cuyo responsable es el odontólogo | `OrthodonticCase` |
| Evoluciones ortodónticas creadas | extensiones ortodónticas cuya evolución padre fue creada por el usuario | `OrthodonticEvolution` + `ClinicalEvolution` |
| Evoluciones ortodónticas firmadas | evolución padre firmada por el usuario | `ClinicalEvolution` |
| Fichas finalizadas | versión `FINALIZED` por `finalized_by_user_id` | `OrthodonticClinicalRecordVersion` |
| Pacientes con actividad ortodóntica | pacientes distintos de casos/evoluciones/fichas accionados por el usuario | joins canónicos |

Un caso asignado al odontólogo pero creado por otro usuario no cuenta como creación propia. “Casos activos” es inventario clínico contextual, no volumen de interacción.

## 7. Pacientes únicos y deduplicación

La métrica `unique_patients_with_activity` usa una unión de identificadores internos de paciente provenientes de acciones atribuibles al usuario:

```text
evoluciones creadas o firmadas
UNION tratamientos/procedimientos creados o completados
UNION consentimientos creados/preparados
UNION casos/evoluciones/fichas de Ortodoncia
UNION citas completadas por el usuario
```

Después se aplica `COUNT(DISTINCT patient_id)`. El `patient_id` se usa dentro de la consulta, pero no se serializa en la respuesta. La creación administrativa de un paciente, por sí sola, no significa que el odontólogo lo atendió.

## 8. Inventario de disponibilidad

### 8.1 YA MEDIBLE

- último login y logins exitosos;
- sesiones iniciadas;
- citas creadas, confirmadas, reprogramadas, completadas y canceladas por actor;
- pacientes creados por actor;
- historias clínicas abiertas;
- evoluciones creadas, firmadas y addenda;
- tratamientos y procedimientos creados;
- procedimientos marcados como realizados;
- tratamientos cerrados;
- presupuestos/versiones creados y aprobados;
- pagos registrados y reversados;
- consentimientos creados, confirmados, compartidos, firmados y finalizados en papel;
- casos, evoluciones y fichas finalizadas de Ortodoncia;
- pacientes únicos por actividad funcional;
- primera/última actividad funcional y días activos, una vez congelado el allowlist.

### 8.2 REQUIERE NUEVO EVENTO O PROYECCIÓN

| Necesidad | Motivo |
|---|---|
| Historial robusto de “paciente consultado” | No existe un evento general y consistente de apertura de ficha |
| Agregados diarios estables | Actualmente deben calcularse desde varias tablas/auditoría |
| Historial de disponibilidad de módulos | El entitlement actual no siempre expresa disponibilidad histórica completa para todos los módulos |
| Atribución de sede para acciones sin `site_id` | No debe inferirse desde la sesión actual |
| Versión del catálogo de métricas | Necesaria para reproducibilidad cuando cambie el allowlist |
| Backfill materializado | Necesario solo si rendimiento/retención justifica persistencia agregada |

“Nuevo evento” no significa capturar contenido. Debe ser un evento funcional mínimo con identificadores internos, actor, tenant, sede opcional, tipo y timestamp.

### 8.3 NO RECOMENDADO

- texto clínico leído o escrito;
- términos buscados, diagnósticos o medicamentos;
- contenido del consentimiento o firma;
- clicks, movimiento del mouse, teclas o tiempo por pantalla;
- session replay;
- URLs que incluyan IDs de pacientes;
- IP, user-agent o dispositivo como métrica de adopción;
- duración de sesión calculada desde `last_seen_at`;
- pantalla abierta como sustituto de atención;
- monto cobrado como indicador de adopción;
- score o ranking de odontólogos.

## 9. Periodos y tendencias

### 9.1 Vistas de periodo

| Vista | Contrato |
|---|---|
| Últimos 7 días | Hoy local y seis días anteriores |
| Últimos 30 días | Hoy local y 29 días anteriores |
| Desde inicio del piloto | `pilot_started_at` futuro o fecha configurada explícitamente; no inferir del primer dato sin mostrarlo |
| Personalizado | Fechas inclusivas en UI, convertidas a intervalo UTC semiabierto |

Mientras no exista `pilot_started_at`, la UI debe solicitar una fecha de inicio o usar la primera actividad funcional con la etiqueta “Desde la primera actividad registrada”, no “Desde el inicio del piloto”.

### 9.2 Tendencia semanal

El endpoint debe devolver una serie por semana y módulo, incluso para semanas con cero:

```json
{
  "week_start": "2026-09-07",
  "agenda_actions": 12,
  "unique_patients": 7,
  "clinical_evolutions_signed": 3,
  "treatments_created": 2,
  "consents_created": 1,
  "orthodontic_evolutions_signed": 1
}
```

La tendencia muestra conteos absolutos. No muestra porcentajes de mejora ni interpreta una subida o bajada como positiva o negativa.

## 10. Estado por módulo

Para el MVP se recomienda **mostrar métricas directas sin etiquetas evaluativas**. Los umbrales `SIN USO / USO OCASIONAL / USO RECURRENTE` serían arbitrarios entre módulos con frecuencias naturales muy diferentes.

Sí pueden mostrarse estados descriptivos sin scoring:

| Estado | Regla transparente |
|---|---|
| Sin actividad registrada | todas las métricas primarias del módulo son cero en el periodo |
| Con actividad registrada | al menos una métrica primaria es mayor que cero |
| No disponible | el módulo no estaba habilitado o el usuario no era elegible según los datos disponibles |
| Datos incompletos | no existe atribución suficiente para el periodo |

Una clasificación de frecuencia puede evaluarse en USAGE-3 usando baseline real de pilotos y umbrales visibles, versionados y específicos por módulo. No debe producir un ranking global.

## 11. Privacidad y seguridad

### 11.1 Contrato de salida

El dashboard puede recibir:

- nombre visible del usuario/odontólogo seleccionado;
- empresa, sede seleccionada y periodo;
- conteos, fechas de primera/última actividad y series temporales;
- flags de disponibilidad y calidad del dato.

No puede recibir:

- `patient_id`, nombre, documento, teléfono o correo de pacientes;
- IDs de citas, historias, evoluciones, tratamientos o consentimientos;
- textos, diagnósticos, notas, motivos o documentos;
- montos financieros;
- IP, user-agent, token, sesión, OTP o evidencia de firma;
- detalle crudo de auditoría.

### 11.2 Acceso

La implementación futura debe crear un permiso específico, conceptualmente `platform.usage.view`, asignado solo a Platform Admin autorizado. Este permiso:

- permite consultar agregados de adopción;
- no concede permisos clínicos tenant;
- no habilita endpoints de pacientes o historias;
- no permite drill-down a una persona atendida;
- exige `company_id` y valida que `user_id`/`dentist_id` pertenezcan a esa empresa;
- registra `USAGE_DASHBOARD_VIEWED` sin copiar filtros sensibles más allá de IDs internos necesarios.

La API debe aplicar límites de rango, paginación del selector y `Cache-Control: no-store`.

### 11.3 Minimización

- Consultar únicamente columnas necesarias para agrupar.
- Agregar en backend antes de serializar.
- No enviar eventos al frontend para que este los cuente.
- No registrar resultados completos del dashboard en logs o auditoría.
- Definir retención separada para agregados de adopción y auditoría.
- Los datos agregados siguen siendo información empresarial y requieren control de acceso.

## 12. Auditoría versus adopción

| Auditoría | Adopción |
|---|---|
| Quién hizo qué y cuándo | Cuánto se usó un módulo en un periodo |
| Evidencia detallada e investigable | Agregado mínimo para acompañamiento |
| Puede incluir resultado, IP/UA y metadata | Excluye IP/UA, contenido y detalle por paciente |
| Se consulta por evento | Se consulta por métrica y serie |
| Optimizada para trazabilidad | Optimizada para conteos reproducibles |

La auditoría no debe convertirse directamente en el dashboard. Se permite usar un allowlist de acciones como fuente interna cuando es la única evidencia fiable del actor/transición, pero el query layer debe proyectarlas a hechos mínimos y agregarlas antes de responder.

El catálogo de métricas debe versionar:

- nombre de métrica;
- acciones incluidas/excluidas;
- fuente canónica;
- campo temporal;
- regla de actor;
- regla de deduplicación;
- disponibilidad de sede;
- versión de definición.

## 13. Arquitectura recomendada

### 13.1 Comparación

| Alternativa | Ventajas | Riesgos | Evaluación |
|---|---|---|---|
| A. Tiempo real desde tablas existentes | Sin duplicar datos; backfill inmediato; precisión canónica | Queries complejas, acoplamiento y costo creciente | Adecuada para USAGE-1/MVP con rangos limitados |
| B. Event stream de product analytics | Consultas rápidas; taxonomía uniforme | Instrumentación nueva, duplicación, gobernanza/retención y backfill difícil | Excesiva para el MVP |
| C. Híbrida | Fuente canónica + hechos mínimos/rollups reproducibles | Requiere catálogo y reconciliación | Recomendada |

### 13.2 Diseño híbrido

```text
Tablas transaccionales + auditoría allowlisted
                    │
                    ▼
        Usage Metric Query Layer
        - tenant guard
        - actor resolver
        - metric catalog
        - deduplicación
        - privacy projection
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
Consultas directas MVP   Rollups diarios futuros
          │                   │
          └─────────┬─────────┘
                    ▼
        API agregada Platform Admin
                    ▼
          Dashboard sin drill-down
```

Fase inicial:

- consultas directas parametrizadas sobre fuentes canónicas;
- allowlist explícito para eventos auditados;
- rango máximo inicial de 12 meses, consistente con reportes existentes;
- cache corta y privada solo si se demuestra necesaria;
- pruebas de atribución y cross-tenant por cada métrica.

Evolución:

- hechos diarios mínimos o rollups por empresa/usuario/odontólogo/sede/métrica/fecha;
- sin `patient_id` ni contenido en la tabla agregada;
- backfill idempotente desde fuentes canónicas;
- watermark y versión del catálogo;
- reconciliación entre rollup y consulta directa;
- recomputación ante correcciones autorizadas.

No se recomienda copiar todo `AuditEvent` a una segunda tabla. Si se materializan datos, deben ser agregados diarios o hechos estrictamente allowlisted y minimizados.

## 14. Dashboard Platform Admin propuesto

### 14.1 Navegación

```text
Platform Admin
└── Uso y adopción
    ├── Empresa
    ├── Odontólogo / usuario
    ├── Sede (opcional)
    └── Periodo
```

### 14.2 Wireframe

```text
┌──────────────────────────────────────────────────────────────┐
│ Uso y adopción                                               │
│ Empresa [Clínica X]  Usuario [Dra. Y]  Sede [Todas]         │
│ Periodo [Últimos 30 días]   Zona horaria: America/Bogota    │
├──────────────────────────────────────────────────────────────┤
│ Último acceso │ Días activos │ Primera actividad │ Última    │
├──────────────────────────────────────────────────────────────┤
│ Citas gestionadas       18 │ Pacientes únicos             11 │
│ Evoluciones creadas      8 │ Evoluciones firmadas          7 │
│ Tratamientos creados     3 │ Consentimientos generados     4 │
│ Casos Ortodoncia         1 │ Evoluciones Ortodoncia        3 │
├──────────────────────────────────────────────────────────────┤
│ Tendencia semanal                                             │
│ Agenda              4 → 12 → 18 → 24                         │
│ Evoluciones         0 →  3 →  8 → 15                         │
│ Pacientes únicos    2 →  7 → 11 → 14                         │
├──────────────────────────────────────────────────────────────┤
│ Actividad por módulo                                          │
│ Agenda            [conteos y días, sin detalle de pacientes] │
│ Historia clínica  [creadas, firmadas, addenda]               │
│ Tratamientos      [tratamientos, procedimientos, cierres]    │
│ Consentimientos   [generados, compartidos, firmados]         │
│ Ortodoncia        [casos, evoluciones, fichas]               │
│ Administración    [pagos, opcional y separado]               │
└──────────────────────────────────────────────────────────────┘
```

### 14.3 Estados de pantalla

- Sin selección: solicitar empresa y usuario.
- Usuario sin perfil odontológico: mostrar actividad operativa atribuible, sin inventar `dentist_id`.
- Módulo no habilitado: “No disponible en el periodo/datos actuales”.
- Métrica cero: mostrar `0`, no ocultarla.
- Fuente incompleta: mostrar aviso de calidad del dato.
- Nunca ofrecer “Ver pacientes”, “Ver evolución” o “Ver consentimiento”.

## 15. MVP propuesto

### 15.1 Métricas principales

El mínimo dashboard útil incluye:

1. último acceso;
2. días activos funcionales;
3. citas gestionadas por el usuario y días de agenda;
4. pacientes únicos con actividad atribuible;
5. evoluciones creadas y firmadas;
6. tratamientos y procedimientos creados;
7. consentimientos generados, compartidos y firmados como resultado;
8. casos/evoluciones/fichas de Ortodoncia cuando el módulo aplica;
9. tendencia semanal de agenda, pacientes únicos y evoluciones;
10. módulos sin actividad registrada, sin scoring.

### 15.2 Exclusiones del MVP

- pagos en el encabezado principal;
- pacientes consultados;
- duración de sesión;
- etiquetas ocasional/recurrente;
- alertas automáticas;
- comparación entre odontólogos;
- exportación masiva;
- tracking frontend genérico;
- métricas financieras o de calidad clínica.

### 15.3 Definition of done futura

- cada métrica tiene definición versionada y prueba de atribución;
- un actor de otra empresa nunca entra al agregado;
- una acción de secretaría no se atribuye al odontólogo asignado;
- conteos directos y tendencia semanal reconcilian;
- cero contenido o identificador de paciente en API, logs y UI;
- consultas de 30 días cumplen el presupuesto de rendimiento acordado;
- backfill produce el mismo resultado al repetirse;
- Platform Admin no adquiere acceso clínico.

## 16. POST-MVP

Evaluar después de obtener baseline real:

- rollups diarios y recomputación incremental;
- historial explícito de habilitación por módulo;
- etiquetas de frecuencia con umbrales públicos por módulo;
- comparación del mismo usuario contra sus semanas previas, nunca contra otros profesionales;
- hitos: primer tratamiento, primer consentimiento, primer caso de Ortodoncia;
- alertas de acompañamiento:
  - sin actividad funcional durante siete días;
  - usa Agenda pero aún no registra Historia Clínica;
  - primer tratamiento creado;
  - primer caso de Ortodoncia;
- digest interno para acompañamiento del piloto;
- consentimiento/aviso contractual específico si el uso de métricas cambia de finalidad;
- exportación agregada con controles y auditoría.

Las alertas deben ser descriptivas y configurables. No deben etiquetar al profesional como inactivo, deficiente o improductivo.

## 17. Riesgos y controles

| Riesgo | Control propuesto |
|---|---|
| Atribuir a odontólogo una acción de secretaría | Separar actor de profesional asignado |
| Doble conteo por eventos compuestos | Clave de deduplicación por métrica, entidad y transición |
| Inflar uso con refresh o vistas | Allowlist funcional; excluir refresh y lecturas de baja señal |
| Exponer información clínica | Agregar en backend y prohibir drill-down |
| Cross-tenant | Validación de pertenencia en cada dimensión y prueba negativa |
| Cambiar definiciones sin trazabilidad | Catálogo versionado de métricas |
| Diferencias por zona horaria | Límites UTC derivados de zona de empresa y respuesta explícita |
| Estado actual interpretado como evento histórico | Usar timestamps/eventos históricos; marcar stocks por separado |
| Consultas costosas | Rango limitado, índices existentes, plan de rollups |
| Retención de auditoría insuficiente | Política documentada y rollups mínimos antes de purgar |
| Módulo no habilitado interpretado como no adopción | Estado “No disponible” separado de cero actividad |
| Uso punitivo de métricas | Nombres neutrales, sin ranking/score y finalidad contractual explícita |

## 18. Roadmap USAGE-1+

### USAGE-1 — Foundation y query layer

- congelar catálogo de métricas y allowlist;
- definir permiso Platform Admin específico;
- implementar resolutor actor/odontólogo/sede;
- consultas directas y contrato API agregado;
- filtros 7/30 días, piloto y personalizado;
- pruebas de deduplicación, zona horaria, RBAC y cross-tenant;
- evaluar índices con `EXPLAIN`, sin crear rollups prematuramente.

### USAGE-2 — Dashboard Platform Admin

- selectores de empresa, usuario/odontólogo, sede y periodo;
- tarjetas del MVP y actividad por módulo;
- estados cero/no disponible/datos incompletos;
- no-store, accesibilidad y auditoría de consulta;
- sin drill-down clínico.

### USAGE-3 — Tendencias y madurez de adopción

- series semanales completas;
- comparación del usuario consigo mismo;
- rollups diarios si el volumen lo requiere;
- baseline de pilotos y evaluación de etiquetas transparentes;
- hitos de primera adopción.

### USAGE-4 — Pilot hardening

- validación con clientes fundadores;
- pruebas de rendimiento y reconciliación;
- retención, minimización y revisión de privacidad;
- monitoreo de consultas y errores;
- documentación operativa y runbook;
- decisión explícita sobre alertas POST-MVP.

La separación puede ajustarse tras revisar USAGE-0, pero no se debe empezar por instrumentación frontend masiva ni por un score.

## 19. Uso con clientes fundadores

Ejemplo de lectura correcta:

```text
Odontólogo piloto — Chile
Periodo: últimos 30 días

Último acceso: 20-sep-2026
Días con actividad funcional: 9
Citas gestionadas por el usuario: 24
Pacientes únicos con actividad: 14
Evoluciones firmadas: 8
Tratamientos creados: 3
Consentimientos generados: 4
Casos de Ortodoncia creados: 1
Módulos sin actividad registrada: Presupuestos
```

Interpretación permitida: “Conviene acompañar al piloto en el flujo de Presupuestos”.

Interpretaciones no permitidas: “El odontólogo atiende poco”, “es menos productivo” o “su calidad clínica es baja”. Los datos solo muestran actividad registrada en Dentia.

## 20. Decisiones pendientes para USAGE-1

Antes de implementar deben aprobarse:

1. nombre definitivo del permiso Platform Admin;
2. allowlist exacto de acciones funcionales para `active_days`;
3. fecha de inicio del piloto o regla visible de fallback;
4. rango máximo y presupuesto de rendimiento;
5. política de retención de agregados;
6. si Pagos aparece únicamente en detalle administrativo;
7. si las citas asignadas se muestran como contexto separado;
8. si se implementan consultas directas primero o rollups desde el inicio tras medir volumen.

## 21. Gates de diseño

```text
USAGE_0_REPOSITORY_ANALYZED
USAGE_0_EXISTING_EVENTS_MAPPED
USAGE_0_ADOPTION_METRICS_DEFINED
USAGE_0_PRIVACY_MODEL_READY
USAGE_0_ARCHITECTURE_RECOMMENDED
USAGE_0_DASHBOARD_WIREFRAME_READY
USAGE_0_MVP_SCOPE_READY
USAGE_0_ROADMAP_READY

READY_FOR_USAGE_REVIEW

NO_CODE
NO_MIGRATION
NO_PUSH
NO_DEPLOY
```
