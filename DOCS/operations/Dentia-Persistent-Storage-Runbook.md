# Dentia — Runbook de storage persistente

## Problema que resuelve

El backend escribe documentos históricos en `/app/storage`. Si el contenedor no tiene mount hacia el host, los PDFs pueden quedar dentro del contenedor y perderse al recrearlo.

## Ruta oficial

```text
Host:       /opt/apps/dentia/backend/storage
Contenedor: /app/storage
Compose:    ./backend/storage:/app/storage
```

Esta es la misma carpeta respaldada por `backup_dentia.sh`.

## Antes del primer recreate

Ejecutar en el VPS, sin reiniciar contenedores:

```bash
cd /opt/apps/dentia
./scripts/production/prepare_dentia_persistent_storage.sh --dry-run
```

Revisar:

- `storage_mount_detected`;
- conteo de archivos host;
- conteo de archivos dentro del contenedor;
- faltantes;
- conflictos.

Si no hay conflictos:

```bash
./scripts/production/prepare_dentia_persistent_storage.sh --apply
```

El script:

- copia desde `/app/storage` a staging temporal;
- compara rutas, tamaños y SHA-256;
- copia solo archivos ausentes al host;
- no sobrescribe;
- aborta si una misma ruta tiene hash diferente;
- no elimina archivos del host ni del contenedor;
- deja inventarios en `.run/storage_prepare_*`.

## Validación posterior

Crear un backup:

```bash
./scripts/production/backup_dentia.sh --no-prune
```

Verificarlo:

```bash
./scripts/production/verify_dentia_backup.sh /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS
```

Resultado esperado:

```text
BACKUP_VALID
```

## Primer deploy seguro

Orden recomendado:

1. Confirmar `.env.production` con permisos `600`.
2. Ejecutar preparación en `--dry-run`.
3. Ejecutar preparación en `--apply` si hay faltantes y cero conflictos.
4. Ejecutar backup completo.
5. Ejecutar verify.
6. Solo entonces ejecutar deploy.

No usar `docker compose down -v`.

## Conflictos

Si el script reporta una misma ruta con hash diferente:

- no desplegar;
- no recrear backend;
- conservar ambos archivos;
- revisar manualmente cuál corresponde al hash guardado en PostgreSQL;
- documentar la resolución antes de continuar.
