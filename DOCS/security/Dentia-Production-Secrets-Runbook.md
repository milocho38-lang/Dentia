# Dentia — Runbook de secretos de producción

## Principio

Los secretos reales no deben estar versionados ni compartirse en salidas operativas.

El repositorio contiene únicamente:

- `.env.production.example`;
- nombres de variables;
- marcadores no funcionales.

## Archivo real

Ruta recomendada en VPS:

```text
/opt/apps/dentia/.env.production
```

Permisos:

```bash
chmod 600 /opt/apps/dentia/.env.production
```

Si se usa otra ruta:

```bash
export DENTIA_ENV_FILE=/ruta/segura/.env.production
```

## Variables mínimas

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET`
- `DENTIA_BACKEND_ENV_FILE`
- `BRANDING_STORAGE_DIR`
- `API_PROXY_TARGET`

`DATABASE_URL` debe usar credenciales URL-encoded cuando la contraseña contenga caracteres especiales.

## Validación obligatoria

Antes de desplegar:

```bash
export DENTIA_ENV_FILE=/opt/apps/dentia/.env.production
scripts/production/validate_dentia_production_config.sh
```

El validador:

- no imprime valores secretos;
- rechaza `.env.production.example`;
- exige permisos máximos `600`;
- detecta placeholders y secretos triviales;
- verifica coherencia de `DATABASE_URL`;
- comprueba que Compose resuelva sin iniciar servicios.

## No compartir `docker compose config`

`docker compose config` puede expandir secretos. No debe pegarse en chats, tickets ni documentación sin una revisión/redacción previa.

## Rotación segura antes del piloto

1. Crear archivo de entorno root-only con permisos `600`.
2. Ejecutar `validate_dentia_production_config.sh`.
3. Cambiar credencial de PostgreSQL de forma coordinada.
4. Actualizar `DATABASE_URL` con contraseña URL-encoded.
5. Rotar `JWT_SECRET`.
6. Recrear servicios en ventana controlada.
7. Validar salud backend/frontend.
8. Validar login.
9. Invalidar sesiones anteriores si el mecanismo seguro existe.
10. Ejecutar backup completo y verificación semántica.

## Reglas

- No versionar `.env`, `.env.production` ni variantes reales.
- No escribir secretos en runbooks.
- No dejar contraseñas funcionales de ejemplo.
- No rotar credenciales durante tickets locales de código.
