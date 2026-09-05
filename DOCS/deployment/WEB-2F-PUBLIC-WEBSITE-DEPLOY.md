# WEB-2F — Publicación de la website comercial

## Alcance

Publicar la aplicación independiente `website/` en `https://dentiapro.com` y conservar la aplicación clínica canónica en `https://app.dentiapro.com`.

## Servicios

- `dentia-website`: website pública, puerto interno `3010`.
- `dentia-frontend`: aplicación autenticada, puerto interno `3001`.
- `dentia-backend`: API clínica, sin cambios funcionales de WEB-2F.

El nuevo puerto debe estar bloqueado desde la interfaz pública mediante `DOCKER-USER`. Nginx Proxy Manager puede acceder al upstream desde la red interna de Docker o mediante el patrón interno ya utilizado por los servicios existentes.

## Variables productivas

```text
NEXT_PUBLIC_SITE_URL=https://dentiapro.com
NEXT_PUBLIC_APP_URL=https://app.dentiapro.com
NEXT_PUBLIC_SITE_INDEXABLE=true
DENTIA_WEBSITE_BIND=3010
DENTIA_WEBSITE_CONTAINER=dentia-website
```

`PUBLIC_FRONTEND_URL` permanece en `https://app.dentiapro.com`.

## Compatibilidad de rutas

La website emite redirects temporales, conservando path y query string:

- `/consentimiento/*` → `https://app.dentiapro.com/consentimiento/*`.
- `/login`, `/dashboard`, `/pacientes/*`, `/agenda/*`, `/tratamientos/*`, `/finanzas/*`, `/reportes/*`, `/seguimientos/*`, `/configuracion/*`, `/cambiar-contrasena` y `/sin-acceso` → ruta equivalente en `app.dentiapro.com`.

La auditoría encontró `/consentimiento/<token>` como única ruta pública frontend con enlaces persistentes. Las rutas `/api/public/consents/*` son endpoints internos consumidos después de cargar el portal en el host de la aplicación; no son páginas comerciales ni enlaces frontend persistidos.

## Cutover NPM

El proxy host de `dentiapro.com` conserva dominio, TLS, Force SSL, HTTP/2 y protección de exploits. Solo cambia el upstream desde el frontend clínico en `3001` hacia `dentia-website` en `3010`.

El proxy host de `app.dentiapro.com` no se modifica.

## Rollback

No requiere cambios de base de datos:

1. Restaurar el upstream del proxy host `dentiapro.com` a puerto `3001`.
2. Validar sintaxis Nginx y recargar NPM.
3. Confirmar root y app en HTTP 200.
4. Detener `dentia-website` si fuera necesario; no detener frontend, backend ni base de datos.
5. Restaurar la configuración NPM desde el snapshot previo únicamente si la reversión puntual no fuera suficiente.

Los consentimientos históricos permanecen inmutables y vuelven a ser servidos directamente por el frontend anterior al restaurar el upstream.

## Deuda posterior

El formulario de demostración continúa deliberadamente deshabilitado y no transmite ni persiste información. Su activación requiere un canal de leads, política de privacidad, retención y controles antiabuso aprobados.
