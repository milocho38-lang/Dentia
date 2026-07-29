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

El paquete incluye `document_inventory.tsv`. El backup falla si PostgreSQL referencia un PDF finalizado/anulado que no existe físicamente o cuyo SHA-256 no coincide.

## Verificar backup

```bash
./scripts/production/verify_dentia_backup.sh /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS
```

Resultado esperado:

```text
BACKUP_VALID
```

`BACKUP_VALID` significa:

- checksums del paquete correctos;
- `database.dump` legible por `pg_restore -l`;
- `storage.tar.gz` legible y sin rutas inseguras;
- inventario documental completo;
- cada registro documental inventariado tiene archivo físico y hash coincidente.

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

La restauración temporal consulta la base restaurada y valida nuevamente:

```text
PostgreSQL restaurado → archivo en storage restaurado → SHA-256
```

Si falta un archivo o el hash no coincide, no se emite `RESTORE_VALID`.

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
- inventario documental DB → archivo → SHA-256;
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
- Si el backend no tenía mount y existieron archivos dentro del contenedor, ejecutar primero `prepare_dentia_persistent_storage.sh`.

### Falla inventario documental

- No usar el backup.
- Revisar si hay PDFs rescatados pendientes de copiar a `backend/storage`.
- Comparar `document_inventory.tsv` y métricas del paquete.
- No recrear el backend hasta que el storage host contenga los documentos referenciados.

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
