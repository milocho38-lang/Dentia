# WEB-0.9 — Causa raíz de persistencia de sesión

**Fecha:** 2026-09-03 (COT)

**Base productiva analizada:** `568e0df94d1e488387735ff487adcd9108c44496`

**Estado:** corrección local completada; despliegue y validación manual productiva pendientes.

Este documento no contiene tokens, cookies, hashes, credenciales, IP, PII ni información clínica.

## 1. Evidencia manual

Después de WEB-0.8 se comprobó que dos pestañas podían funcionar y recargarse durante un intervalo corto, pero:

- una pestaña nueva podía solicitar autenticación otra vez;
- cerrar y reabrir inmediatamente podía restaurar la sesión;
- una reapertura aproximadamente un minuto después podía solicitar autenticación;
- el logout explícito revocaba correctamente la sesión y protegía las rutas privadas.

La política esperada continuaba siendo: access token de 15 minutos, refresh persistente de hasta 8 horas e idle timeout de 60 minutos.

## 2. Evidencia productiva anonimizada

Se consultaron exclusivamente acciones técnicas de autenticación posteriores al despliegue. Las sesiones se reemplazaron por etiquetas efímeras `S1` a `S6`; no se extrajeron usuarios, correos, IP, user agents, tokens ni hashes.

En las seis sesiones observadas apareció el mismo patrón:

1. uno o más `TOKEN_REFRESHED` avanzaron la generación;
2. solicitudes de otra pestaña presentaron la generación inmediatamente anterior;
3. durante dos segundos recibieron `TOKEN_REFRESH_RACE_ACCEPTED`;
4. los cuatro reintentos continuaron presentando la generación anterior;
5. al terminar la ventana fija, el backend registró `REFRESH_TOKEN_REUSE` y `SESSION_REVOKED`.

En una secuencia representativa, la generación vigente llegó a 8. Dos solicitudes de generación 7 recibieron tratamiento de carrera y, 2,858 segundos después de la última rotación, la misma generación produjo la revocación. La sesión tenía expiración absoluta ocho horas después de su creación y su última actividad era reciente.

No se observó `IDLE_TIMEOUT`, expiración absoluta, cierre por background cleanup ni ausencia inicial de cookie como causa. Solicitudes posteriores continuaron llegando asociadas a la sesión ya revocada y fueron rechazadas como `SESSION_EXPIRED`; el router eliminó entonces la cookie inválida.

## 3. Causa raíz exacta

WEB-0.8 resolvió la carrera en el backend cuando dos requests presentan el mismo token: una rota y la otra recibe HTTP 409 sin revocación. Sin embargo, el frontend solo deduplicaba refreshes dentro de un contexto JavaScript mediante `refreshPromise`.

Las pestañas seguían pudiendo enviar refreshes independientes en paralelo. La respuesta ganadora rotaba la cookie, pero solicitudes ya despachadas por otros contextos conservaban la generación anterior. En la evidencia productiva, esos contextos no observaron la nueva cookie antes de agotar sus reintentos. Al superar la ventana de dos segundos, el backend aplicó correctamente la protección de replay y revocó la familia.

La aparente pérdida “al minuto” no era un temporizador de un minuto: era la sesión que había sido revocada durante una carrera anterior y se descubría al intentar restaurarla. Una de las secuencias observadas llegó a la carrera aproximadamente 109 segundos después del login, pero la revocación ocurrió segundos después del refresh concurrente, no por inactividad.

## 4. Cookie y expiraciones

El contrato efectivo quedó confirmado en código, configuración productiva y pruebas HTTP:

| Propiedad | Valor |
|---|---|
| Nombre | `dentia_refresh` |
| Persistencia inicial | `Max-Age=28800` (8 horas) |
| Renovación | conserva la expiración absoluta original; su `Max-Age` disminuye |
| `Secure` | `true` en producción |
| `HttpOnly` | `true` |
| `SameSite` | `Lax` |
| `Path` | `/api/auth` |
| `Domain` | ausente; cookie host-only |
| Idle timeout | 60 minutos |
| Access token | 15 minutos |

`Path=/api/auth` es suficiente: el navegador solo necesita enviar el refresh cookie a `/api/auth/refresh` y `/api/auth/logout`. El frontend no intenta leer la cookie HttpOnly ni usarla fuera de ese path.

La cookie seguía existiendo y era enviada durante la falla: los eventos estaban asociados a una sesión y contenían generaciones válidas anteriores. No fue una expiración o eliminación autónoma del navegador. Después de la revocación, un 401 definitivo sí ejecutó la limpieza prevista.

## 5. Actividad y procesos de fondo

`last_seen_at` se establece durante login y se actualiza en:

- refresh válido;
- requests autenticados con access token.

Los 60 minutos se calculan con `timedelta(minutes=...)`. No existe conversión a segundos, timer frontend de autenticación a 60 segundos, listener de `visibilitychange`, `beforeunload` o `pagehide`, ni tarea periódica que elimine una sesión válida al minuto.

## 6. Corrección

Cada refresh del frontend se ejecuta ahora dentro de un Web Lock exclusivo y same-origin llamado `dentia-auth-refresh-v1`. El lock cubre la operación completa, incluidos los reintentos 409 de WEB-0.8.

Con dos pestañas:

1. la primera adquiere el lock y completa request, recepción de `Set-Cookie` y actualización de estado;
2. la segunda espera;
3. al adquirir el lock, envía la cookie vigente del jar compartido;
4. no existen dos rotaciones de la misma sesión en vuelo desde el frontend Dentia.

El lock no almacena ni comunica access tokens, refresh tokens, cookies ni datos de usuario. Si Web Locks no está disponible, se mantiene el comportamiento acotado de WEB-0.8; no se debilita el backend ni se abre un bypass.

No se añadió `BroadcastChannel`: el lock del navegador proporciona exclusión mutua real entre contextos del mismo origen. Un canal de mensajes sería únicamente una señal y no garantizaría por sí mismo exclusión ni orden de requests.

## 7. Protección de replay

El backend no cambia:

- current válido rota;
- N−1 dentro de dos segundos recibe 409 y no revoca;
- N−1 fuera de grace revoca;
- N−2 revoca inmediatamente;
- logout, cambio de contraseña, cuenta/sede inactiva e idle/absolute expiration conservan sus fronteras;
- una firma manipulada no revoca una sesión válida.

La corrección reduce carreras legítimas antes de llegar al backend. No amplía grace, no acepta tokens antiguos y no convierte un replay en refresh válido.

## 8. Pruebas

La validación automatizada incluye:

- dos contextos frontend con cookie jar compartido y un lock exclusivo;
- comprobación de que solo existe un refresh en vuelo y ambos contextos terminan autenticados;
- fallback acotado cuando Web Locks no está disponible;
- recuperación 409 de WEB-0.8;
- N−1 fuera de grace y N−2 con revocación;
- logout;
- expiración idle de 60 minutos y absoluta de 8 horas;
- sesión válida después de 75 segundos de inactividad;
- atributos y persistencia de la cookie.

Además de la prueba rápida que retrocede `last_seen_at` 75 segundos para proteger las unidades en cada CI, se ejecutó una vez un smoke HTTP real con cookie jar persistente y espera efectiva de 75 segundos. El segundo refresh respondió correctamente y la sesión permaneció activa.

El navegador integrado no estuvo disponible durante la implementación. No se instaló Playwright ni otro framework pesado solo para esta tarea. La prueba manual productiva en dos pestañas continúa siendo obligatoria después del despliegue autorizado.

## 9. Cambios y operación

No hay migración, cambio de esquema ni variable productiva nueva. No se modifican DNS, TLS, Nginx Proxy Manager, dominios ni WEB-1A.

Rollback: volver a `568e0df94d1e488387735ff487adcd9108c44496` mediante el procedimiento productivo existente. La corrección es frontend y no requiere transformar sesiones ni datos.

## 10. Gate local

Una vez completadas todas las suites:

- **CROSS_TAB:** `CROSS_TAB_FIXED`;
- **PERSISTENCE:** `SESSION_PERSISTENCE_FIXED`;
- **REPLAY:** `REPLAY_PROTECTION_PRESERVED`;
- **DEPLOY:** `READY_FOR_CONTROLLED_DEPLOY`.

Estos gates son locales. Requieren autorización explícita antes de push/deploy y una nueva prueba manual productiva. WEB-1A continúa sin autorización.
