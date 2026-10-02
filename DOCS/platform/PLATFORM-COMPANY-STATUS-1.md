# PLATFORM-COMPANY-STATUS-1 — Estado reversible de clínicas

## Causa raíz

La aplicación ya tenía los endpoints explícitos `deactivate` y `reactivate`, y el
permiso global `platform.companies.manage` ya estaba asignado exclusivamente a
`PLATFORM_ADMIN`. El problema combinaba tres factores:

1. La auto-desactivación estaba bloqueada deliberadamente en backend, porque el
   modelo de autenticación exige que la empresa del usuario esté activa incluso
   cuando este tiene `PLATFORM_ADMIN`.
2. La UI ejecutaba el cambio en un clic, sin confirmación, estado de carga ni una
   explicación visible de esa protección.
3. La revocación de sesiones usaba por error `AuthSession.revoked_reason`; el
   atributo persistido real es `AuthSession.revoke_reason`. Por ello, intentar
   desactivar otra clínica podía terminar en error interno antes del commit.

No faltaban endpoints ni permisos y no fue necesario modificar el esquema.

## Semántica

- Desactivar cambia únicamente `Company.status` de `Activa` a `Inactiva` y
  `Company.is_active` de `true` a `false`.
- Las sesiones activas de esa empresa se revocan con motivo técnico
  `COMPANY_DEACTIVATED` para que el bloqueo sea inmediato.
- No se modifican estados de usuarios u odontólogos ni datos clínicos,
  administrativos, archivos, historiales o configuraciones de módulos.
- Reactivar restablece el estado de la empresa. Los usuarios que ya eran activos
  pueden iniciar una sesión nueva; las sesiones revocadas no se restauran.
- Repetir una transición ya aplicada es un no-op exitoso y no duplica auditoría.
- La fila de empresa se bloquea durante la transición para serializar solicitudes
  concurrentes.

## Protección contra auto-bloqueo

La autenticación, el refresh y la construcción del contexto rechazan cualquier
sesión cuya empresa esté inactiva. `PLATFORM_ADMIN` no es una excepción y sus
cookies/tokens son host-only, no identidades globales separadas del tenant.

Por esa razón un administrador de plataforma no puede desactivar la empresa de
su propia sesión. La UI deshabilita únicamente esa acción y explica:

> No puedes desactivar esta clínica porque hacerlo bloquearía tu acceso actual de administración de plataforma.

Otro `PLATFORM_ADMIN` activo, perteneciente a una empresa distinta, sí puede
desactivar y reactivar la clínica. Esto conserva una ruta segura de recuperación
sin ampliar acceso clínico global ni cambiar la arquitectura de autenticación.

## RBAC y aislamiento

- Operación autorizada: `platform.companies.manage` (`PLATFORM_ADMIN`).
- Denegada por rol tenant: `ADMINISTRATOR`, `DENTIST_ADMIN`, `DENTIST` y
  `SECRETARY`.
- El permiso permite administrar el estado de empresas, pero no concede acceso a
  pacientes, historias, evoluciones u otros recursos clínicos de esos tenants.
- Las rutas usan un identificador de empresa explícito y la dependencia de
  permiso se evalúa antes de ejecutar el servicio.

## Auditoría

Cada transición efectiva genera uno de estos eventos:

- `COMPANY_DEACTIVATED`
- `COMPANY_REACTIVATED`

El evento conserva `company_id`, actor, sesión y timestamp en las columnas de
auditoría. El detalle contiene estado e indicador activo anteriores/nuevos y,
cuando se envía, un motivo opcional de máximo 300 caracteres. Nunca incluye
contenido clínico.

## UX

Una clínica activa muestra **Desactivar clínica**. Antes de ejecutar, un modal
presenta el nombre, número de usuarios activos, odontólogos activos y advierte que
el acceso se bloqueará sin eliminar información. Una clínica inactiva muestra
**Reactivar clínica**. Errores y confirmaciones se presentan en la página, y el
control queda bloqueado durante la solicitud para evitar dobles envíos.

## Preservación de módulos

Los entitlements y assignments de Ortodoncia, así como el gate y las
autorizaciones piloto de Periodontograma, permanecen sin cambios. Mientras la
empresa está inactiva, el gate general de autenticación impide operar. Después de
reactivar, las configuraciones anteriores vuelven a aplicar.

## Cobertura

Las pruebas DB-backed verifican desactivación/reactivación, bloqueo y recuperación
de login, revocación de sesiones, idempotencia, auditoría, los cuatro roles tenant,
auto-bloqueo, segundo administrador de plataforma, visibilidad de empresas
inactivas, aislamiento clínico y preservación de datos/ORT/PERIO. La prueba
frontend fija el contrato del modal, los contadores, la acción explícita y el
mensaje de auto-bloqueo.
