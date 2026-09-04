# WEB-0.8 — Concurrencia segura del refresh token

**Fecha:** 2026-09-03 (COT)

**Estado:** implementación y pruebas locales completadas; despliegue y validación manual productiva pendientes.

Este documento no contiene tokens, cookies, hashes, credenciales, PII ni información clínica.

## 1. Causa raíz

Dentia rota el refresh token en cada llamada a `POST /api/auth/refresh`. La fila de `auth_sessions` conserva únicamente el hash del token vigente. Antes de WEB-0.8, dos solicitudes que salían casi simultáneamente con el mismo token producían esta secuencia:

1. la primera solicitud bloqueaba la sesión, validaba el token y lo rotaba;
2. la segunda esperaba el bloqueo y luego encontraba que su token ya no coincidía con el hash vigente;
3. el backend interpretaba la diferencia como reutilización maliciosa, revocaba la sesión y el router eliminaba la cookie;
4. el usuario perdía una sesión válida.

La evidencia productiva de WEB-0.7B mostró una diferencia aproximada de 104 ms entre `TOKEN_REFRESHED` y `REFRESH_TOKEN_REUSE`. El `refreshPromise` del frontend solo coordinaba solicitudes dentro de un contexto JavaScript; no protegía pestañas o contextos distintos.

## 2. Lifecycle resultante

La política de sesión no cambia:

- access token en memoria: 15 minutos;
- refresh token en cookie host-only, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/api/auth`;
- expiración absoluta: 8 horas;
- inactividad máxima: 60 minutos;
- rotación en cada refresh válido;
- almacenamiento persistente: únicamente SHA-256 del refresh token vigente.

Los refresh tokens nuevos tienen este formato firmado:

```text
v1.<session_id>.<generation>.<random_secret>.<hmac>
```

El HMAC usa el secreto JWT con separación de dominio exclusiva para refresh tokens. La firma permite comprobar que la generación declarada pertenece a un token emitido por Dentia; el secreto aleatorio mantiene la entropía del token. Ni el token ni su secreto se almacenan en claro.

La columna existente `auth_sessions.rotation_counter` es la generación vigente. No se añade estado en memoria ni se requiere una migración.

## 3. Estrategia elegida

Se combinan generación firmada, bloqueo transaccional y una ventana de carrera fija:

- el token cuyo hash y generación coinciden con la sesión rota normalmente;
- solamente la generación inmediatamente anterior puede recibir tratamiento de carrera;
- ese tratamiento está limitado por `REFRESH_TOKEN_RACE_GRACE_SECONDS`, con valor por defecto de 2 segundos y rango permitido de 1 a 5 segundos;
- la ventana comienza en la rotación exitosa y no se extiende cuando llega el token anterior;
- el backend responde HTTP 409 con código `REFRESH_RACE_RETRY`, no revoca la sesión y no elimina la cookie;
- el frontend reintenta con pausas de 100, 200, 400 y 800 ms;
- el reintento usa la cookie vigente instalada por la respuesta ganadora;
- al agotarse los cuatro reintentos, el frontend falla de forma cerrada y no entra en un ciclo infinito.

El backend usa `SELECT ... FOR UPDATE` sobre `auth_sessions`, por lo que la corrección funciona entre workers y procesos que comparten PostgreSQL. No depende de memoria de un proceso.

No se implementó `BroadcastChannel`: reduciría solicitudes duplicadas, pero no resolvería por sí solo las carreras de red, arranque o contextos sin canal. El backend es la fuente de corrección y el retry frontend es una recuperación acotada.

## 4. Contrato HTTP de carrera

Una solicitud que presenta la generación inmediatamente anterior dentro de la ventana recibe:

```json
{
  "detail": {
    "code": "REFRESH_RACE_RETRY",
    "message": "La sesión se está actualizando en otra pestaña. Reintenta."
  }
}
```

con HTTP 409. Esta respuesta no contiene refresh token, no reconstruye material secreto almacenado como hash y no emite `Set-Cookie` para borrar la cookie.

Una generación N-2, una generación anterior fuera de la ventana, o una generación/hash incoherentes continúan siendo replay y revocan la sesión.

## 5. Propiedades de seguridad

| Propiedad | Garantía |
|---|---|
| Token vigente | Es el único token normalmente válido. |
| Token anterior | Solo N-1 recibe tratamiento especial y únicamente dentro de la ventana fija. |
| Renovación de grace | La respuesta de carrera no actualiza `last_seen_at`; la ventana no se renueva. |
| Tokens N-2 o anteriores | Se consideran replay inmediato. |
| Replay tardío | N-1 fuera de grace revoca la sesión. |
| Logout | Revoca la sesión; current y previous dejan de funcionar. |
| Sesión revocada | Se valida antes de cualquier tratamiento de carrera y no puede revivir. |
| Idle/expiración absoluta | Se validan antes de la carrera y no se extienden. |
| Cuenta o empresa inactiva | Se rechaza y revoca antes de la carrera. |
| Sede no autorizada | Se rechaza y revoca antes de la carrera. |
| Firma manipulada | Se rechaza sin permitir que un atacante revoque una sesión válida. |
| Cambio de contraseña | Bloquea la sesión y salta una generación; el token previo no entra en grace. |
| Fijación de sesión | Login crea un UUID de sesión, familia y secreto aleatorio nuevos. |
| Aislamiento tenant | No se modifica la construcción ni validación del contexto de empresa/sede. |

## 6. Compatibilidad de sesiones existentes

Los tokens anteriores al formato `v1` no contienen una generación autenticada. Aceptarlos dentro de una ventana sería ambiguo y permitiría debilitar la detección de replay.

Por ello, una sesión legacy cuyo hash aún coincide se revoca una sola vez con razón:

```text
REFRESH_TOKEN_FORMAT_UPGRADE
```

Después del despliegue, los usuarios con una sesión abierta deberán iniciar sesión una vez. El siguiente login emite el formato firmado. No se crea un backfill inseguro ni se almacenan tokens de reemplazo en claro.

## 7. Observabilidad

- `TOKEN_REFRESHED`: rotación normal, con contador de generación.
- `TOKEN_REFRESH_RACE_ACCEPTED`: N-1 recibido dentro de grace; evento legítimo y medible.
- `ACCESS_DENIED` con `REFRESH_TOKEN_REUSE`: reutilización fuera del contrato.
- `SESSION_REVOKED`: revocación por replay u otra frontera de seguridad.
- `SESSION_REVOKED` con `REFRESH_TOKEN_FORMAT_UPGRADE`: cierre único de una sesión legacy.

Los eventos no registran tokens, secretos ni hashes completos.

## 8. Pruebas

La suite DB-backed cubre:

1. token firmado y detección de manipulación;
2. rotación normal T0 → T1 sin cambiar expiración absoluta;
3. dos solicitudes HTTP concurrentes reales con resultado 200/409 y sesión activa;
4. N-1 inmediato sin revocación;
5. N-1 fuera de grace con revocación;
6. N-2 con revocación inmediata;
7. logout con current y previous rechazados;
8. idle timeout y expiración absoluta sin reactivación;
9. firma inválida sin revocar la sesión válida;
10. transición segura de formato legacy;
11. cambio de contraseña fuera de la ventana de carrera;
12. validación de configuración 1–5 segundos.

La suite frontend cubre:

- clasificación exclusiva de `REFRESH_RACE_RETRY`;
- recuperación acotada;
- dos contextos simulados que comparten la cookie del navegador;
- propagación inmediata de replay real;
- ausencia de bucle infinito.

El script oficial `test_dentia_security.sh --hardening` ejecuta esta suite frontend además de los guardrails existentes.

## 9. Impacto operativo y rollback

No hay migración ni cambio de esquema. El despliegue requiere configurar opcionalmente:

```text
REFRESH_TOKEN_RACE_GRACE_SECONDS=2
```

Si no se declara, el valor seguro por defecto es 2.

Rollback de código:

1. restaurar la imagen/commit anterior mediante el procedimiento productivo existente;
2. comprobar salud de frontend y backend;
3. solicitar nuevo login a los usuarios cuyas sesiones hayan sido emitidas con el formato `v1`, porque el código anterior no reconoce ese formato.

No se debe intentar convertir tokens ni editar `auth_sessions` manualmente.

## 10. Gate

La implementación local preserva la protección de replay, pero el gate productivo permanece sin autorizar hasta completar:

- despliegue controlado;
- prueba manual en dos pestañas;
- recarga casi simultánea;
- cierre y reapertura dentro de vigencia;
- logout y redirección posterior;
- comprobación de salud y auditoría anonimizada.

Hasta esa validación:

- **AUTH:** pendiente de validación productiva;
- **SECURITY:** `REPLAY_PROTECTION_PRESERVED` en pruebas locales;
- **WEB-1A:** `DO_NOT_AUTHORIZE_WEB_1A`.
