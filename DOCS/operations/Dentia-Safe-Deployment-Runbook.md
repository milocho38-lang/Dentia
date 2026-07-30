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

## Comando oficial

```bash
scripts/production/deploy_dentia.sh
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
