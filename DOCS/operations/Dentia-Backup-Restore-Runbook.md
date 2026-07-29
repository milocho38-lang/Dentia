# Dentia — Runbook de backup y restauración

## Crear backup completo

En VPS:

```bash
cd /opt/apps/dentia
./scripts/production/backup_dentia.sh
```

La última línea imprime únicamente la ruta del paquete:

```text
/opt/backups/dentia/dentia_YYYYMMDD_HHMMSS
```

## Verificar backup

```bash
./scripts/production/verify_dentia_backup.sh /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS
```

Resultado esperado:

```text
BACKUP_VALID
```

## Restauración temporal

La restauración temporal no reemplaza producción.

```bash
./scripts/production/restore_dentia_backup.sh \
  --backup /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS \
  --temporary
```

Resultado esperado:

```text
RESTORE_VALID
database=dentia_restore_...
storage_dir=/tmp/dentia_restore_.../storage
```

## Restauración productiva

No ejecutar sin autorización explícita.

```bash
./scripts/production/restore_dentia_backup.sh \
  --backup /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS \
  --production \
  --yes-i-understand
```

El script exige escribir:

```text
RESTORE-DENTIA-DATA
```

## Deploy

`deploy_dentia.sh` ahora crea y verifica backup completo antes del `git pull`.

Si falla:

- PostgreSQL;
- storage;
- manifest;
- checksums;
- espacio en disco;

el deploy se aborta antes de modificar producción.

## Rollback

Rollback de código:

```bash
./scripts/production/rollback_dentia.sh <commit>
```

Rollback de código con restauración de datos:

```bash
./scripts/production/rollback_dentia.sh <commit> \
  --restore-data /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS \
  --yes-i-understand
```

Este flujo exige confirmación adicional.

## Qué hacer ante fallo

### Falla backup DB

- No continuar deploy.
- Revisar contenedor `dentia-db`.
- Revisar credenciales internas.
- Revisar espacio.

### Falla storage

- No continuar deploy.
- Revisar permisos sobre `backend/storage`.
- Revisar symlinks/rutas extrañas.

### Falla checksum

- No usar el backup.
- Crear uno nuevo.
- Revisar disco.

### Falla restore temporal

- No restaurar producción.
- Revisar `pg_restore`.
- Revisar compatibilidad de versión PostgreSQL.

## Datos sensibles

Los backups contienen datos clínicos.

No:

- subir a Git;
- enviar por chat;
- servir por web;
- abrir en equipos no autorizados;
- imprimir contenido clínico.

Sí:

- guardar con permisos restrictivos;
- rotar según política;
- mover a almacenamiento seguro;
- cifrar externamente cuando exista gestión de claves.
