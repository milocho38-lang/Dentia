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
1. Partir del SHA completo aprobado y ejecutar su launcher inmutable.
2. Validar configuración, repositorio limpio, commit desplegado, Alembic
   esperado, storage persistente y contenedores actuales.
3. Comprobar origin/master y hacer fast-forward exacto al SHA aprobado.
4. Construir referencias inmutables etiquetadas con ese SHA mientras los
   contenedores antiguos siguen activos.
5. Resolver los tres IDs objetivo y verificar sus etiquetas OCI antes de
   interrumpir el servicio.
6. Activar la barrera y maintenance_active; detener backend, frontend y
   website, y confirmar que no quedan sesiones cliente desconocidas en DB.
7. Crear y verificar backup de PostgreSQL + storage con escritores detenidos;
   restaurarlo temporalmente y comprobar datos sintéticos/estables.
8. Ejecutar Alembic en un contenedor backend objetivo nombrado; inspeccionar
   su ID exacto antes de eliminarlo.
9. Verificar Alembic, invariantes de rollout y preservación de datos estables.
10. Iniciar sólo backend objetivo; comparar ID, OCI y health.
11. Iniciar sólo frontend y website objetivo; comparar sus IDs, OCI y health.
12. Ejecutar smoke interno y confirmar HTTP 503 mientras la barrera permanece.
13. Registrar commit y backup; retirar maintenance_active y la barrera como
    transición final única de disponibilidad.
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

## Recuperación fail-closed después de migrar a `20261006_0047`

Este procedimiento sólo aplica cuando el runner ya inició migraciones, la base
está exactamente en `20261006_0047` y conserva tanto `.run/maintenance_active`
como `backend/storage/.dentia-maintenance`. No se deben iniciar las imágenes
antiguas sobre la base migrada.

Precondiciones obligatorias:

1. Mantener backend, frontend y website detenidos.
2. Resolver el backup registrado para el intento fallido y ejecutar
   `verify_dentia_backup.sh` sobre ese directorio.
3. Confirmar Alembic `20261006_0047`, las invariantes de usernames y permisos,
   y que `patient_import_sources` y `patient_external_references` permanecen
   vacías inmediatamente después del rollout.
4. Leer `target_images.backend`, `target_images.frontend` y
   `target_images.website` de `manifest.json`; son los tres IDs exactos
   autorizados para recuperar.
5. Mantener activa la barrera durante toda la recuperación.

Secuencia revisada y ensayada:

```text
1. Verificar backup e invariantes 0047 con los servicios detenidos.
2. Resolver las referencias inmutables etiquetadas con el SHA objetivo.
3. Iniciar sólo el backend objetivo y esperar /health.
4. Comparar docker inspect .Image del backend con target_images.backend.
5. Iniciar sólo frontend y website objetivo y esperar sus healthchecks.
6. Comparar sus dos IDs exactos con target_images del manifest.
7. Comprobar las etiquetas OCI del SHA en los tres contenedores.
8. Confirmar HTTP 503 en el backend mientras la barrera sigue activa.
9. Retirar maintenance_active y la barrera como transición final única.
10. Repetir healthchecks y registrar backup, SHA e IDs usados.
```

Si cualquier ID, invariante, backup, healthcheck o respuesta 503 no coincide,
dejar todos los servicios de aplicación detenidos y conservar ambos marcadores.
Nunca ejecutar `up` sobre las imágenes antiguas después de alcanzar `0047`.

## Limpieza Docker

No ejecutar limpieza automática de caché o volúmenes durante deploy.

Limpieza manual, solo con ventana y revisión:

```bash
docker system df
docker image ls
docker image rm <referencia-inequívoca-creada-por-el-ensayo>
```

Nunca usar `docker image prune`/`docker system prune` como parte del despliegue
o de sus ensayos. Nunca borrar volúmenes PostgreSQL ni storage clínico.
