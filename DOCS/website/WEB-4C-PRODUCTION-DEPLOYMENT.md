# WEB-4C — Publicación y validación productiva de solicitudes de demo

**Fecha:** 2026-09-21

**Commit anterior / rollback de código:** `013d77470592d8fff741acfff36f171a7eebb523`

**Commit desplegado:** `c64161f7cab65ae0b359046a9d89b1628ff44dac`

**Migración:** `20260921_0040_demo_requests.py`, con parent `20260914_0039`

## Alcance publicado

WEB-4C publicó el flujo WEB-4B previamente aprobado:

- formulario público de solicitudes de demo;
- persistencia, consentimiento, deduplicación y controles anti-spam;
- notificación interna por correo;
- listado y detalle exclusivos para Administrador de plataforma;
- asignación de responsable, agenda con zona horaria, transiciones de estado y notas internas append-only;
- auditoría sin datos personales del prospecto.

No se modificaron RIPS, Ortodoncia, Periodontograma, datos tenant, DNS, TLS, NPM ni AdminPH.

## Commit, CI y backup

El commit WEB-4C fue creado como hijo directo de `013d77470592d8fff741acfff36f171a7eebb523` y publicado por fast-forward en `origin/master`.

GitHub Actions validó el SHA exacto mediante la ejecución `35655033520` del workflow **Dentia Security Tests**, con resultado `completed/success`.

Antes del despliegue, el procedimiento oficial creó y validó el backup:

```text
/opt/backups/dentia/dentia_20260921_211802
```

Registro del backup:

- commit: `013d77470592d8fff741acfff36f171a7eebb523`;
- Alembic: `20260914_0039`;
- PostgreSQL: `17.10 (Debian 17.10-1.pgdg13+1)`;
- SHA-256 PostgreSQL: `9ebc6082a9e7290583449d8fe92aba62a7a4de405e3e27bdb762f74a5c65eedd`;
- SHA-256 storage: `015c2b492ad28069e07108d679593c6a18c40beb770629c5e8c56c4e0c99f3f0`;
- resultado: `BACKUP_VALID`.

La configuración SMTP de WEB-4C quedó validada sin imprimir destinatarios, credenciales ni secretos. El despliegue oficial finalizó correctamente y dejó Alembic en `20260921_0040 (head)`; `alembic check` reportó `No new upgrade operations detected`.

## Smoke público

La prueba pública se ejecutó mediante el endpoint same-origin de la website con un prospecto completamente sintético:

- creación: HTTP 201 con respuesta genérica y sin ID interno;
- reenvío idéntico: HTTP 201 sin crear un segundo registro;
- honeypot: respuesta genérica sin persistencia;
- fuente persistida: `WEBSITE`;
- consentimiento y versión conservados;
- notificación interna: `SENT`;
- auditoría y logs sin email, teléfono, mensaje completo ni IP en claro.

## Validación manual informada

Camilo informó haber realizado desde Platform Admin el siguiente recorrido sobre el lead sintético **Ana Demo**, país Chile:

1. asignar responsable;
2. marcar como Contactado;
3. agendar una demo futura en `America/Santiago`;
4. añadir la nota `Prueba sintética WEB-4C`;
5. marcar la demo como realizada;
6. finalizar como No continúa con el motivo `Lead sintético de validación WEB-4C`.

La interfaz completó el recorrido sin errores visibles para el operador.

## Verificación persistida en modo solo lectura

La comprobación posterior se realizó exclusivamente con consultas PostgreSQL `READ ONLY`, revisión de auditoría y logs. No se ejecutó ninguna escritura, reparación ni repetición de acciones.

| Verificación | Resultado | Evidencia persistida |
|---|---|---|
| `DemoRequest` existe | PASS | Existe exactamente un lead sintético coincidente. |
| Estado final | PASS | `NOT_CONTINUING`. |
| Responsable | PASS | Usuario responsable persistido, activo y con membresía `PLATFORM_ADMIN` activa. |
| `contacted_at` | **FAIL** | El valor permanece `NULL`. |
| Agenda | PASS | `scheduled_at` está presente y es posterior a la creación. |
| Zona horaria | PASS | `America/Santiago`. |
| Coherencia de agenda | PASS | Fecha y zona horaria del evento auditado coinciden con la fila vigente. |
| Nota `Prueba sintética WEB-4C` | **FAIL** | No existe una nota separada con ese contenido. |
| Notas append-only | PASS parcial | Existe una nota append-only con autor y timestamps, correspondiente al motivo de cierre. |
| Transición `DEMO_COMPLETED` | PASS | Auditoría `DEMO_REQUEST_STATUS_CHANGED`: `DEMO_SCHEDULED` → `DEMO_COMPLETED`. |
| Transición `NOT_CONTINUING` | PASS | Auditoría `DEMO_REQUEST_CLOSED`: `DEMO_COMPLETED` → `NOT_CONTINUING`. |
| Motivo final | PASS semántico | Persistido como `Lead sintético de validación WEB-4C.`; contiene un punto final adicional respecto del texto informado. |
| Consentimiento | PASS | Timestamp y versión permanecen intactos. |
| Fuente | PASS | `WEBSITE`. |
| Auditoría sin PII | PASS | Seis eventos, sin email, teléfono, mensaje completo ni IP pública. |
| Duplicados | PASS | Sigue existiendo un único lead. |
| Datos tenant | PASS | Los eventos WEB-4C conservan `company_id = NULL`; no se observan mutaciones tenant asociadas al recorrido. |
| ORT/PERIO/RIPS | PASS | Cero eventos relacionados en la ventana y actor del recorrido. |

La secuencia auditada real fue:

```text
DEMO_REQUEST_CREATED
DEMO_REQUEST_NOTIFICATION_SENT
DEMO_REQUEST_ASSIGNED
DEMO_REQUEST_SCHEDULED        NEW → DEMO_SCHEDULED
DEMO_REQUEST_STATUS_CHANGED   DEMO_SCHEDULED → DEMO_COMPLETED
DEMO_REQUEST_CLOSED           DEMO_COMPLETED → NOT_CONTINUING
```

Los logs HTTP corroboran las mutaciones de asignación, agenda, demo realizada y cierre. No registran una solicitud de transición a `CONTACTED` ni una solicitud `POST` para crear la nota `Prueba sintética WEB-4C`. La versión de fila final también es coherente con las cuatro mutaciones de plataforma persistidas: asignación, agenda, demo realizada y cierre.

Por lo anterior, el flujo principal y el cierre son funcionales, pero la evidencia persistida no permite aprobar todavía el recorrido manual completo tal como fue informado. No se corrige el registro productivo dentro de esta validación.

## WEB-4C.1 discrepancy remediation

La investigación local reprodujo el flujo completo a través de las mismas rutas HTTP usadas por Platform Admin:

```text
NEW
→ ASSIGNED
→ CONTACTED
→ DEMO_SCHEDULED
→ INTERNAL NOTE
→ DEMO_COMPLETED
→ NOT_CONTINUING
```

El backend persistió correctamente `CONTACTED`, estableció `contacted_at` una sola vez, conservó ese timestamp durante los estados posteriores, creó la nota independiente, mantuvo separado el motivo de cierre y registró todas las transiciones en auditoría. Por tanto, la causa no se encuentra en el modelo, schema, router, servicio, transacción ni migración `0040`.

La evidencia productiva muestra que las acciones faltantes nunca llegaron al backend: no existe request de cambio a `CONTACTED` ni `POST /notes`. La UI permitía avanzar de `NEW` directamente a agenda —una transición válida— sin una confirmación persistida explícita de la acción de contacto. Además, el helper de mutaciones absorbía cualquier error y resolvía igualmente la promesa; los callbacks posteriores podían limpiar la nota o el motivo aunque el backend hubiera rechazado la escritura. La pantalla tampoco diferenciaba con suficiente precisión la nota interna, la nota de agenda y el motivo de transición.

WEB-4C.1 corrige exclusivamente esa capa cliente:

- una mutación solo se considera exitosa si la escritura termina y un `GET` posterior confirma el estado persistido;
- los campos se limpian únicamente después de esa confirmación;
- los errores permanecen visibles y no producen mensaje de éxito;
- `CONTACTED` muestra confirmación explícita después del refetch;
- la nota interna se etiqueta como registro independiente;
- la nota de agenda y el motivo del cambio de estado quedan diferenciados;
- todos los botones declaran explícitamente su tipo para evitar submits implícitos.

Se añadió una regresión DB-backed con el recorrido exacto WEB-4C.1 y aserciones sobre estado final, `contacted_at`, responsable, zona horaria, notas, motivo de cierre y las cuatro transiciones históricas. El contrato frontend prueba que `CONTACTED` y notas usan sus endpoints correctos, que siempre existe refetch después de una escritura y que un rechazo no puede convertirse en éxito aparente.

Validación local de la remediación:

- WEB-4B/WEB-4C.1 focal: 7 pruebas aprobadas;
- DB-backed completa: 258 pruebas aprobadas;
- seguridad: 299 rutas caracterizadas, 0 pendientes;
- frontend Platform Admin: contrato WEB-4C.1 aprobado;
- concurrencia de autenticación y pilot hardening: aprobados;
- fechas clínicas: 14 pruebas aprobadas;
- frontend privado: lint y build aprobados;
- website: tests, lint, typecheck y build aprobados;
- backend: compileall y `pip check` aprobados;
- Alembic: `20260921_0040 (head)` y `No new upgrade operations detected`.

Esta remediación permanece únicamente en local. No modifica el lead productivo existente, no fabrica auditoría retroactiva y no afirma que producción esté corregida antes de un despliegue posterior autorizado.

## Salud posterior

Después del despliegue se verificó:

- `https://dentiapro.com`: HTTP 200;
- `https://app.dentiapro.com`: HTTP 200;
- backend y PostgreSQL saludables;
- AdminPH saludable;
- NPM en ejecución;
- cero OOM y cero reinicios inesperados;
- repositorio productivo limpio;
- Alembic `20260921_0040 (head)` y check limpio.

## Rollback

El rollback de código disponible es:

```text
013d77470592d8fff741acfff36f171a7eebb523
```

Como la migración `0040` ya contiene información productiva de solicitudes de demo, un rollback funcional debe conservar las tablas y sus datos. No debe ejecutarse downgrade destructivo sin una decisión explícita de retención/exportación.

## Gate de cierre

Pasan los gates de listado, detalle, agenda, zona horaria, RBAC, seguridad, notificación y salud de servicios. No pasan aún los gates completos de workflow e internal notes debido a la ausencia persistida de `CONTACTED` y de la nota interna esperada.

Resultado:

```text
WEB_4C_PRODUCTION_VERIFICATION_MISMATCH
WEB_4C_REVIEW_REQUIRED
READ_ONLY_VALIDATION_ONLY
NO_FURTHER_MUTATIONS
```
