# WEB-1A — Dual-host seguro para Dentia

**Fecha de ejecución:** 2026-09-03 (America/Bogota) / 2026-09-04 (UTC)

**Alcance:** habilitar `app.dentiapro.com` como segundo host de la misma aplicación, conservando `dentiapro.com` como host canónico y operativo.

**Estado:** infraestructura activa; WEB-1A.1 identificó y corrigió localmente un defecto de bootstrap de autenticación pendiente de publicación y validación productiva.

## 1. Resultado ejecutivo

`app.dentiapro.com` resuelve a la IP productiva, presenta un certificado TLS independiente válido, redirige HTTP a HTTPS y sirve mediante HTTP/2 el mismo frontend que `dentiapro.com`.

No se modificaron:

- `PUBLIC_FRONTEND_URL`, que continúa en `https://dentiapro.com`;
- el proxy host, certificado o DNS de `dentiapro.com`;
- backend, frontend, base de datos o migraciones;
- DNS, TLS o servicios de AdminPH;
- puertos publicados ni reglas `DOCKER-USER`.

WEB-1B no está autorizado en este punto.

## 2. Baseline y backups

Antes de habilitar el host se confirmó:

- `https://dentiapro.com`: HTTP 200;
- frontend disponible y backend saludable;
- Dentia frontend, backend y PostgreSQL sin reinicios ni OOM;
- AdminPH web y API disponibles;
- puertos internos filtrados externamente;
- reglas IPv4 e IPv6 de `DOCKER-USER` presentes.

Backups disponibles:

- paquete completo Dentia: `/opt/backups/dentia/dentia_20260904_043536`;
- snapshot específico WEB-1A: `/opt/backups/dentia/web1a_20260903_233628`.

El snapshot WEB-1A contiene copia transaccional de la base SQLite de Nginx Proxy Manager, configuración de proxy, certificados, configuración productiva Dentia, reglas IPv4/IPv6, baseline y `SHA256SUMS`. Sus checksums fueron verificados antes del cambio. Las rutas se registran como referencias operativas del VPS y no contienen credenciales en este documento.

## 3. DNS

Se creó manualmente únicamente:

```text
A app.dentiapro.com → 2.25.66.123
TTL 300
```

La propagación fue confirmada contra servidores autoritativos y resolvers públicos de Cloudflare, Google y Quad9. Todos devolvieron `2.25.66.123`. El resolver local y el del VPS mostraron inicialmente caché negativo, que expiró sin intervención adicional.

No se modificaron otros registros DNS.

## 4. TLS y HTTP

Nginx Proxy Manager emitió un certificado Let's Encrypt independiente:

- nombre/SAN: `app.dentiapro.com`;
- certificado NPM: `npm-8`;
- inicio: 2026-09-04 03:52:55 UTC;
- expiración: 2026-12-03 03:52:54 UTC;
- renovación administrada por NPM.

Pruebas finales:

```text
http://app.dentiapro.com/  → 301 Location: https://app.dentiapro.com/
https://app.dentiapro.com → 200 mediante HTTP/2
```

HSTS permanece desactivado según el alcance aprobado de WEB-1A.

## 5. Nginx Proxy Manager

Proxy host creado:

```text
app.dentiapro.com
→ http://2.25.66.123:3001
```

Configuración observada:

- host ID `4`;
- certificado ID `8`;
- Force SSL activo;
- HTTP/2 activo;
- HSTS inactivo;
- Block Common Exploits activo;
- Websocket Support activo;
- mismo upstream del host raíz;
- `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` y `X-Forwarded-Host` preservados por los includes compartidos;
- sintaxis Nginx validada correctamente con `nginx -t`.

El registro NPM del host raíz fue comparado contra el snapshot previo y coincide en dominio, upstream, certificado, SSL, HTTP/2, HSTS, WebSocket, protección de exploits y configuración avanzada.

## 6. Aplicación y rutas

Se comprobaron en ambos hosts, con HTTP 200:

- `/` y `/login`;
- `/dashboard`;
- `/pacientes`;
- `/agenda`;
- `/tratamientos`;
- `/finanzas`;
- `/reportes`;
- `/seguimientos`;
- `/configuracion/empresa`;
- `/configuracion/usuarios`;
- `/configuracion/sedes`;
- `/configuracion/odontologos`;
- `/configuracion/procedimientos`;
- `/configuracion/consentimientos`.

Los cuerpos obtenidos en root y app tuvieron el mismo SHA-256 para las rutas comparadas, confirmando que ambos hosts sirven el mismo build. Esta comprobación valida disponibilidad y paridad del shell frontend; no reemplaza el recorrido funcional autenticado de datos reales.

`/api` continúa siendo same-origin. No se creó `api.dentiapro.com` ni se habilitó CORS. Una preflight desde un origen no autorizado no recibió `Access-Control-Allow-Origin`.

## 7. Cookies y autenticación

Configuración productiva observada:

```text
cookie: dentia_refresh
Secure: true
HttpOnly: true (definido por el endpoint)
SameSite: lax
Path: /api/auth
Domain: no configurado (host-only)
Max-Age: 8 horas
idle timeout: 60 minutos
```

El `AuthProvider` intenta restaurar la sesión mediante `POST /api/auth/refresh` al montar una pestaña nueva. La rotación usa bloqueo entre pestañas y reintentos acotados para carreras de refresh.

Resultados técnicos:

- refresh sin cookie en root: 401 controlado `No autenticado.`;
- refresh sin cookie en app: 401 controlado `No autenticado.`;
- prueba productiva `auth-refresh-concurrency-tests.mjs`: `OK`;
- ninguna cookie usa `Domain=.dentiapro.com`.

Consecuencia intencional: una sesión de `dentiapro.com` no inicia sesión automáticamente en `app.dentiapro.com`. El usuario debe autenticarse una vez en app y, desde ese momento, app mantiene su propia cookie host-only.

La primera prueba manual autenticada de app detectó un fallo al abrir una segunda pestaña. La investigación WEB-1A.1 encontró esta secuencia exacta en producción:

1. Login correcto y cookie enviada al backend.
2. La segunda pestaña abrió `/`, una ruta estática que redirige inmediatamente a `/dashboard`.
3. El `AuthProvider` inició un refresh durante la ruta intermedia.
4. Safari canceló la petición al navegar; NPM registró `499`, pero el backend ya había confirmado `TOKEN_REFRESHED` y rotado la sesión.
5. `/dashboard` reintentó con la cookie anterior: cuatro respuestas `409 REFRESH_RACE_RETRY`.
6. Al terminar la ventana de gracia, el backend rechazó el token con `401 REFRESH_TOKEN_REUSE` y revocó la sesión.

La cookie no estaba ausente: la auditoría demuestra que fue recibida y validada antes de la rotación. Tampoco hubo dependencia de `PUBLIC_FRONTEND_URL` ni defecto de headers del proxy.

La corrección local evita iniciar el bootstrap en `/`, que solo redirige, y lo ejecuta al llegar a `/dashboard`. Mantiene cookies host-only, bloqueo entre pestañas, reintentos acotados y protección contra replay. Queda pendiente publicar, desplegar y repetir manualmente login, segunda pestaña, refresh simultáneo, cierre/reapertura, persistencia durante 2–3 minutos, logout y acceso posterior a una ruta privada.

## 8. Consentimientos

El portal público responde en ambos hosts y conserva:

- `Cache-Control: no-store, max-age=0`;
- `Pragma: no-cache`;
- `X-Frame-Options: DENY`;
- `X-Robots-Tag: noindex, nofollow`;
- CSP con `connect-src 'self'` y `frame-ancestors 'none'`.

Un token sintético inválido devolvió 404 controlado en ambos hosts sin exponer información.

El backend construye enlaces emitidos con `settings.public_frontend_url`. Como el valor productivo permanece en `https://dentiapro.com`, los nuevos enlaces server-side y sus QR continúan apuntando al root durante WEB-1A. La navegación manual a un enlace válido mediante app debería funcionar por ser el mismo frontend y API same-origin, pero no se generó ni firmó un consentimiento productivo porque no se dispuso de una cuenta y paciente de prueba expresamente seguros.

Los consentimientos históricos de root no se modificaron y root continúa sirviendo la aplicación.

## 9. Compatibilidad del root

`dentiapro.com` continúa con HTTPS y HTTP/2, responde 200 en las rutas representativas y produce el mismo contenido que app. Su registro NPM actual coincide con el snapshot anterior a WEB-1A.

No existe redirección entre root y app.

## 10. Seguridad de red

Sonda externa posterior al cambio:

| Puerto | Resultado |
|---:|---|
| 80 | público mediante reverse proxy; app redirige a HTTPS |
| 443 | público mediante reverse proxy |
| 81 | cerrado/filtrado |
| 3000 | cerrado/filtrado |
| 3001 | cerrado/filtrado |
| 5432 | cerrado/filtrado |
| 5433 | cerrado/filtrado |
| 8000 | cerrado/filtrado |
| 8001 | cerrado/filtrado |
| 8502 | cerrado/filtrado |

Las reglas `DOCKER-USER` siguen presentes para IPv4 e IPv6 en `eth0`, incluidos 81, 3000, 3001, 5433, 8000, 8001 y 8502. El backend no quedó expuesto directamente.

## 11. AdminPH

- `https://adminph.com.co`: HTTP 200 y certificado válido;
- `https://api.adminph.com.co/health`: HTTP 200;
- frontend, API, PostgreSQL y Streamlit: en ejecución, sin reinicios y sin OOM;
- sus registros NPM coinciden exactamente con el snapshot previo a WEB-1A.

Se detectó una deuda previa no causada por WEB-1A: `www.adminph.com.co` enruta y responde 200, pero el certificado asociado contiene únicamente `DNS:adminph.com.co`, por lo que la validación TLS del alias `www` falla. No se modificó AdminPH dentro de este ticket.

## 12. Observabilidad

Después de las pruebas:

- backend Dentia: saludable;
- PostgreSQL Dentia: saludable;
- frontend Dentia: disponible;
- cero reinicios y cero OOM en Dentia, NPM y AdminPH;
- logs recientes del backend: healthchecks 200 y únicamente los 401/404/405 esperados de las sondas negativas;
- logs recientes del frontend: sin errores;
- logs NPM: emisión del certificado y recargas Nginx exitosas, sin errores de upstream;
- Alembic continúa en `20260801_0035 (head)`;
- validación oficial de configuración productiva: OK.

## 13. Rollback

WEB-1A puede revertirse sin tocar la base de datos:

1. Desactivar el proxy host ID `4` de `app.dentiapro.com` en NPM.
2. Confirmar que `dentiapro.com` continúa en HTTP 200.
3. Si se requiere retirar completamente el host, eliminar únicamente el registro DNS A de `app.dentiapro.com`.
4. Conservar o retirar posteriormente el certificado `npm-8`; no afecta al root.
5. Si la configuración NPM se corrompiera, restaurar el snapshot `/opt/backups/dentia/web1a_20260903_233628` mediante el procedimiento operativo aprobado.
6. Volver a validar Nginx, root, AdminPH y puertos externos.

No se requiere rollback de código, migraciones, cookies ni datos clínicos.

## 14. Gates actuales

| Gate | Estado | Evidencia pendiente |
|---|---|---|
| DNS | `APP_DNS_OK` | Ninguna |
| TLS | `APP_TLS_OK` | Ninguna |
| APP | `APP_SUBDOMAIN_HEALTHY` | Recorrido privado manual para cierre funcional |
| ROOT | `ROOT_APP_HEALTHY` | Ninguna técnica; recorrido autenticado recomendado |
| AUTH | `APP_AUTH_FAIL` | Fix WEB-1A.1 local pendiente de publicación y validación productiva |
| CONSENTS | `APP_CONSENTS_NOT_FULLY_TESTED` | Flujo real con cuenta/paciente seguro |
| ADMINPH | `ADMINPH_HEALTHY` para host principal y API | Deuda TLS preexistente en alias `www` |
| WEB-1B | `DO_NOT_AUTHORIZE_WEB_1B` | Instrucción expresa y gates manuales pendientes |

El gate final de autenticación se emitirá únicamente después de registrar la prueba manual en `app.dentiapro.com`. No se debe avanzar automáticamente a WEB-1B.
