# WEB-0.7 — Cierre de gates previos a dual-host Dentia

**Fecha de ejecución:** 2026-09-03 (COT)

**VPS:** `srv1776883`

**Versión Dentia observada:** `4cdde75`

**Alcance:** ciclo autenticado productivo, política SSH administrativa, persistencia del firewall y salud final de Dentia y AdminPH.

Este documento no contiene secretos, credenciales, tokens, valores de cookies, PII ni información clínica.

## 1. Resultado ejecutivo

WEB-0.7 y su verificación WEB-0.7B confirmaron que los controles aplicados por WEB-0.6 continúan efectivos:

- Dentia y AdminPH están saludables;
- la administración SSH root acepta únicamente clave pública;
- la autenticación SSH por contraseña está deshabilitada;
- las reglas IPv4 e IPv6 de `DOCKER-USER` están presentes;
- los puertos internos continúan cerrados o filtrados desde Internet;
- 80 y 443 continúan disponibles;
- todos los contenedores observados tienen cero reinicios y `OOMKilled=false`.

Camilo ejecutó posteriormente un ciclo autenticado manual con una cuenta productiva controlada, sin compartir credenciales. Login, navegación y recarga funcionaron, pero al cerrar la pestaña y volver a abrir Dentia fue necesario iniciar sesión nuevamente. La inspección técnica y de auditoría confirmó que este último resultado no corresponde a la política de sesión declarada: una carrera de rotación produjo `REFRESH_TOKEN_REUSE` y revocó la sesión.

No se reinició Docker porque no existía una ventana operativa confirmada. La configuración de persistencia está instalada, pero el comportamiento posterior a un reinicio continúa pendiente de prueba controlada.

## 2. Gate A — ciclo autenticado

### Prueba manual WEB-0.7B

Camilo verificó en `https://dentiapro.com`, sin compartir credenciales:

- login: correcto;
- dashboard: correcto;
- pacientes: correcto;
- agenda: correcto;
- recarga completa autenticada: la sesión se restauró correctamente;
- cierre de pestaña y reapertura: Dentia solicitó login;
- nuevo login y logout: una visita posterior a `/pacientes` redirigió a `/login`.

### Política implementada

`dentia_refresh` es deliberadamente una **cookie persistente**, no una session cookie del navegador:

| Propiedad | Valor efectivo |
|---|---|
| `Max-Age` inicial | 8 horas (`28800` segundos) |
| `Expires` | No se declara; `Max-Age` define persistencia |
| `Path` | `/api/auth` |
| `Secure` | `true` |
| `HttpOnly` | `true` |
| `SameSite` | `Lax` |
| `Domain` | Ausente; cookie host-only |
| Access token | 15 minutos, solo en memoria frontend |
| Expiración absoluta de sesión | 8 horas |
| Timeout por inactividad | 60 minutos |

El login crea una sesión backend y un refresh token cuyo hash queda almacenado. Cada refresh:

1. bloquea la sesión;
2. valida estado, expiración absoluta e inactividad;
3. rota el refresh token;
4. incrementa `rotation_counter`;
5. actualiza `last_seen_at`;
6. reemite la cookie con el tiempo restante hasta la expiración absoluta original.

El logout revoca la sesión backend y elimina la cookie usando el mismo nombre y `Path`.

### Restauración frontend

El access token no se guarda en `localStorage` ni `sessionStorage`; vive en memoria dentro de `apiClient.ts`. Al montar `AuthProvider`, tanto después de una recarga completa como en una pestaña nueva, el frontend ejecuta:

```text
POST /api/auth/refresh
```

con `credentials: include`. Si la cookie persiste y la sesión continúa vigente, el backend entrega un access token nuevo y reconstruye al usuario. Por ello, una pestaña normal abierta dentro de las ocho horas y antes del timeout de inactividad debería restaurar la sesión.

### Hallazgo confirmado

La auditoría productiva se consultó sin usuarios, IP, identificadores, tokens ni valores de cookie. Para una misma sesión anonimizada se observó:

```text
02:31:15.363 UTC  LOGIN_SUCCESS
02:31:50.711 UTC  TOKEN_REFRESHED
02:32:25.117 UTC  TOKEN_REFRESHED
02:32:27.716 UTC  TOKEN_REFRESHED
02:32:27.820 UTC  ACCESS_DENIED — REFRESH_TOKEN_REUSE
02:33:06.013 UTC  ACCESS_DENIED — REFRESH_TOKEN_REUSE
```

El refresh rechazado ocurrió aproximadamente 104 ms después de un refresh exitoso de la misma sesión. El backend trata cualquier token rotado anterior como replay: revoca la sesión completa. El router, además, elimina la cookie ante ese error.

La protección frontend `refreshPromise` evita duplicados dentro de un único contexto JavaScript, pero no coordina pestañas o contextos diferentes. La evidencia es compatible con dos solicitudes concurrentes que enviaron el mismo refresh token: la primera lo rotó y la segunda quedó obsoleta.

La pérdida de sesión fue causada por el manejo de concurrencia/reutilización del refresh token. No fue causada por una cookie de sesión ni por el cierre normal de la pestaña.

### Relación con WEB-0.6

WEB-0.6 cambió únicamente `REFRESH_COOKIE_SECURE` de `false` a `true` en producción y añadió guardrails. No modificó:

- `Max-Age`;
- expiración absoluta;
- timeout por inactividad;
- rotación;
- almacenamiento frontend;
- restauración al montar `AuthProvider`;
- respuesta ante reutilización.

`Secure` solo impide enviar la cookie fuera de HTTPS. El comportamiento encontrado es preexistente y no constituye una regresión introducida por WEB-0.6.

### Recomendación de producto

Mantener por ahora la política existente equivalente a la opción B:

- sesión persistente hasta ocho horas;
- access token corto de 15 minutos;
- timeout por inactividad de 60 minutos;
- refresh token rotativo, host-only, `Secure` y `HttpOnly`.

Esta política ofrece un equilibrio razonable para operación clínica. Antes de WEB-1A debe corregirse la carrera sin debilitar la detección real de replay. La solución requiere diseño y pruebas específicas, por ejemplo coordinación cross-tab y/o un tratamiento backend acotado para refresh concurrente legítimo. No debe resolverse deshabilitando la rotación o ignorando indiscriminadamente la reutilización.

### Resultado

**AUTH_CYCLE_FAIL**

Motivo: login, navegación y refresh individual funcionan, pero la carrera confirmada de rotación puede revocar una sesión válida al reconstruirla desde otro contexto. No es una política intencional de cierre de pestaña.

## 3. Gate B — política SSH administrativa

### Estado efectivo

```text
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
```

OpenSSH reporta el valor efectivo de `PermitRootLogin` como `without-password`, equivalente a `prohibit-password`.

Validaciones:

- nueva conexión root mediante clave: correcta;
- conexión password-only: rechazada con `Permission denied (publickey)`;
- no existe un usuario administrativo no-root;
- no existen miembros del grupo `sudo`.

### Decisión

Se acepta temporalmente la siguiente compensación:

> Root únicamente mediante clave pública, contraseña y teclado interactivo deshabilitados, y `MaxAuthTries 3`.

No se presenta como hardening SSH final. La deuda es crear una identidad administrativa nominal con una clave independiente, probar sudo de forma segura y, solo después, aplicar `PermitRootLogin no`.

Se evaluó crear `camilo-admin`, pero la operación se detuvo antes de ejecutarse porque reutilizar la clave root junto con `NOPASSWD: ALL` no proporcionaba una credencial independiente y ampliaba privilegios. Se confirmó que no quedaron usuario, archivo sudoers ni backup parcial.

### Resultado

**SSH_ROOT_KEY_COMPENSATION_ACCEPTED**

## 4. Gate C — persistencia del firewall

La persistencia declarada por WEB-0.6 continúa instalada:

```text
/usr/local/sbin/web06-docker-ingress-hardening.sh
/etc/systemd/system/docker.service.d/web06-ingress-hardening.conf
```

El `ExecStartPost` efectivo de Docker ejecuta:

```text
/usr/local/sbin/web06-docker-ingress-hardening.sh apply
```

Estado observado sin reinicio:

- reglas IPv4 completas;
- reglas IPv6 completas;
- interfaz pública `eth0`;
- puertos protegidos: `81 3000 3001 5433 8000 8001 8502`.

No se reinició Docker porque no había una ventana operativa confirmada y hacerlo habría interrumpido temporalmente Dentia y AdminPH.

### Resultado

**FIREWALL_PERSISTENCE_NOT_TESTED**

Prueba pendiente: reinicio controlado de Docker, recuperación de todos los contenedores, comprobación de reglas y nueva sonda externa.

## 5. Estado final de puertos

Prueba TCP externa directa:

| Puerto | Resultado | Uso |
|---:|---|---|
| 22 | OPEN | SSH por clave |
| 80 | OPEN | Reverse proxy HTTP |
| 443 | OPEN | Reverse proxy HTTPS |
| 81 | CLOSED_OR_FILTERED | NPM mediante túnel SSH |
| 3000 | CLOSED_OR_FILTERED | AdminPH mediante proxy |
| 3001 | CLOSED_OR_FILTERED | Dentia mediante proxy |
| 5432 | CLOSED_OR_FILTERED | PostgreSQL Dentia interno |
| 5433 | CLOSED_OR_FILTERED | PostgreSQL AdminPH interno |
| 8000 | CLOSED_OR_FILTERED | API AdminPH mediante proxy |
| 8001 | CLOSED_OR_FILTERED | API Dentia interna |
| 8502 | CLOSED_OR_FILTERED | AdminPH Streamlit mediante túnel |

## 6. Salud final

### Dentia

- `https://dentiapro.com`: HTTP 200;
- `/login`: HTTP 200;
- `/dashboard`: HTTP 200 como ruta frontend;
- `/pacientes`: HTTP 200 como ruta frontend;
- `/agenda`: HTTP 200 como ruta frontend;
- backend interno: `healthy` y HTTP 200;
- PostgreSQL: `healthy`;
- frontend, backend y base: cero reinicios y sin OOM.

**DENTIA_HEALTHY**

### AdminPH

- frontend HTTPS: HTTP 200;
- API HTTPS health: HTTP 200;
- API interna: `healthy`;
- PostgreSQL interno: acepta conexiones;
- servicios observados: cero reinicios y sin OOM.

**ADMINPH_HEALTHY**

## 7. Cambios realizados por WEB-0.7

- se añadió únicamente este documento al repositorio;
- no se modificó backend, frontend, RIPS, base de datos ni información clínica;
- no se creó usuario productivo;
- no se reinició Docker ni el VPS;
- no se modificaron DNS, TLS, virtual hosts, redirects ni `PUBLIC_FRONTEND_URL`;
- no se creó `app.dentiapro.com`.

WEB-0.7 no requiere rollback productivo porque no dejó mutaciones adicionales. Los controles y rollbacks de WEB-0.6 permanecen documentados en `WEB-0.6-PRE-DUAL-HOST-HARDENING.md`.

## 8. Riesgos restantes

1. carrera de refresh token entre contextos puede revocar una sesión válida;
2. administración SSH depende temporalmente de root por clave;
3. persistencia de `DOCKER-USER` no probada mediante reinicio;
4. reinicio del sistema pendiente reportado por Ubuntu;
5. deudas de WEB-0.6 continúan fuera de alcance: límite de uploads, swap y pinning de NPM.

## 9. Gates finales

### AUTH

**AUTH_CYCLE_FAIL**

La prueba manual existe, pero descubrió un defecto de concurrencia en la restauración de sesión. No corresponde usar `AUTH_CYCLE_PASS_WITH_SESSION_POLICY` porque la política actual es persistente y el login solicitado no fue intencional.

### SSH

**SSH_ROOT_KEY_COMPENSATION_ACCEPTED**

### FIREWALL

**FIREWALL_PERSISTENCE_NOT_TESTED**

### HARDENING

**HARDENING_ACCEPTABLE_WITH_DEBT**

Los controles de red y SSH son aceptables con deuda documentada. El defecto de concurrencia de autenticación queda como bloqueante funcional independiente para WEB-1A.

### WEB-1A

**DO_NOT_AUTHORIZE_WEB_1A**

WEB-1A podrá reconsiderarse después de corregir y probar la rotación concurrente, y obtener `AUTH_CYCLE_PASS` en recarga y apertura de una nueva pestaña. La persistencia del firewall continúa recomendada, pero no es por sí sola bloqueante si los puertos permanecen protegidos.

Al migrar a `app.dentiapro.com`, la cookie host-only de `dentiapro.com` no se enviará al nuevo host. Un login inicial en `app.dentiapro.com` es esperado y correcto. Esto no elimina el bloqueante: después de ese login, la restauración concurrente debe ser segura también en el nuevo host.

## 10. Seguimiento WEB-0.8

La corrección diseñada para este hallazgo se documenta en `WEB-0.8-REFRESH-TOKEN-CONCURRENCY.md`. Incluye generaciones firmadas, bloqueo transaccional, una ventana fija de dos segundos para la generación inmediatamente anterior y reintentos frontend acotados.

Las pruebas locales preservan la revocación ante replay verdadero. El gate de este documento no cambia todavía: continúa en `AUTH_CYCLE_FAIL` y `DO_NOT_AUTHORIZE_WEB_1A` hasta desplegar WEB-0.8 y completar la validación manual productiva en múltiples pestañas.

## 11. Seguimiento WEB-0.9

La prueba productiva de WEB-0.8 y su causa raíz final se documentan en `WEB-0.9-AUTH-PERSISTENCE-ROOT-CAUSE.md`. WEB-0.7 mantiene `DO_NOT_AUTHORIZE_WEB_1A` hasta completar el despliegue autorizado y la repetición manual del ciclo multitab.
