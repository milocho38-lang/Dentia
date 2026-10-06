# Dentia — Runbook de despliegue seguro

## Principio

Un despliegue de Dentia no debe dejar la aplicación nueva corriendo sobre una base sin migrar, ni debe recrear PostgreSQL.

## Precondiciones

- Repositorio limpio.
- Backup productivo configurado.
- Storage persistente verificado.
- `.env.production` fuera de Git, permisos máximos `600`.
- `DENTIA_ENV_FILE` apunta al archivo real.
- No usar `.env.production.example` como archivo real.

## Validación de configuración

```bash
export DENTIA_ENV_FILE=/opt/apps/dentia/.env.production
scripts/production/validate_dentia_production_config.sh
```

El comando no imprime secretos y no inicia servicios.

## Orden oficial de despliegue

```text
1. Validar configuración productiva.
2. Crear backup PostgreSQL + storage.
3. Verificar backup semánticamente.
4. Confirmar repositorio limpio.
5. git fetch + git pull --ff-only.
6. docker compose build.
7. Ejecutar Alembic en contenedor one-off usando la nueva imagen backend.
8. Verificar Alembic current.
9. Recrear backend.
10. Verificar health backend.
11. Recrear frontend.
12. Verificar frontend y dominio.
13. Registrar commit y backup usado.
```

## Bootstrap inmutable por SHA

El primer despliegue del runner de mantenimiento no debe ejecutar el
`deploy_dentia.sh` que exista en el checkout productivo ni hacer `git pull`
antes de seleccionar el runner. Partiendo de un repositorio limpio, use el SHA
completo aprobado y extraiga el launcher directamente del objeto Git:

```bash
cd /opt/apps/dentia
TARGET_SHA=<SHA_APROBADO_DE_40_CARACTERES>
git fetch origin master
test "$(git rev-parse FETCH_HEAD)" = "$TARGET_SHA"

LAUNCHER="$(mktemp /tmp/dentia-launcher.XXXXXX)"
git show "$TARGET_SHA:scripts/production/launch_maintenance_deploy.sh" >"$LAUNCHER"
test "$(git hash-object "$LAUNCHER")" = \
  "$(git rev-parse "$TARGET_SHA:scripts/production/launch_maintenance_deploy.sh")"
chmod 700 "$LAUNCHER"
"$LAUNCHER" "$TARGET_SHA"
rm -f "$LAUNCHER"
```

El launcher vuelve a comprobar `origin/master`, fast-forward y SHA, extrae el
directorio `scripts/` del mismo objeto Git en un directorio temporal y ejecuta
ese runner inmutable. No usa un script parcialmente actualizado.

## Comando oficial

```bash
scripts/production/launch_maintenance_deploy.sh <SHA_APROBADO_DE_40_CARACTERES>
```

## Estado productivo

```bash
scripts/production/status_dentia_production.sh
```

Debe reportar:

- validación de configuración;
- contenedores;
- reinicios;
- Alembic;
- storage/mount;
- backup más reciente;
- healthchecks.

## Fallo de migración

Si Alembic falla:

- el deploy se aborta antes de recrear backend/frontend;
- el backup ya existe y fue verificado;
- revisar logs de la ejecución one-off;
- no ejecutar `up -d` manualmente hasta resolver la migración.

## Limpieza Docker

No ejecutar limpieza automática de caché o volúmenes durante deploy.

Limpieza manual, solo con ventana y revisión:

```bash
docker system df
docker image prune
```

Nunca borrar volúmenes PostgreSQL ni storage clínico.
