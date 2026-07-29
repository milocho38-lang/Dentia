# C018R.3 — Backup completo PostgreSQL + storage clínico

Objetivo: resolver el P0 detectado en C018R.1: un backup de base de datos sin los PDFs/documentos persistentes no permite restaurar Dentia de forma completa.

## Resultado

Se actualizó la infraestructura de scripts para generar un paquete autocontenido:

```text
dentia_YYYYMMDD_HHMMSS/
├── database.dump
├── storage.tar.gz
├── document_inventory.tsv
├── document_inventory_metrics.json
├── document_inventory_archive_metrics.json
├── manifest.json
├── checksums.sha256
├── metadata.txt
└── verification.txt
```

## Rutas persistentes reales

| Ruta | Contenido | Persistente | Incluido |
|---|---|---:|---:|
| `backend/storage/branding/` | Logos, firmas y branding institucional | Sí | Sí |
| `backend/storage/clinical_documents/` | PDFs finalizados de informes, remisiones, certificados y cartas | Sí | Sí |
| `backend/storage/prescriptions/` | PDFs finalizados de recetas | Sí | Sí |
| `storage/` | Ruta legacy/placeholder | Potencial | Sí si existe |
| `output/` | Renderizados/salidas temporales | No | No |
| `.run/` | PID files, logs y estado runtime | No | No |

Evidencia de código:

- `backend/app/core/config.py`: `branding_storage_dir` apunta a `backend/storage/branding`.
- `backend/app/services/clinical_document_service.py`: usa `backend/storage/clinical_documents`.
- `backend/app/services/prescription_service.py`: usa `backend/storage/prescriptions`.

## Scripts modificados/creados

- `scripts/production/backup_dentia.sh`
- `scripts/production/verify_dentia_backup.sh`
- `scripts/production/restore_dentia_backup.sh`
- `scripts/production/prepare_dentia_persistent_storage.sh`
- `scripts/production/dentia_document_inventory.py`
- `scripts/production/deploy_dentia.sh`
- `scripts/production/rollback_dentia.sh`
- `scripts/production/status_dentia_production.sh`
- `scripts/lib/dentia_common.sh`
- `.gitignore`

## PostgreSQL

El backup usa:

```text
pg_dump -Fc --no-owner --no-privileges
```

Validación:

```text
pg_restore -l database.dump
```

## Storage

El backup crea `storage.tar.gz` con rutas relativas desde la raíz del repo productivo. No sigue symlinks fuera de storage porque no usa `tar -h`.

Desde C018R.3-FIX1, storage vacío solo es válido si PostgreSQL no referencia documentos finalizados/anulados con PDF histórico. Si existen recetas o documentos clínicos con `pdf_storage_path` y `pdf_sha256`, el backup falla cuando el archivo físico no existe o el SHA-256 no coincide.

Si storage está vacío y no hay documentos históricos que requieran PDF, el manifest registra:

```text
storage.file_count = 0
```

## Persistencia host ↔ contenedor

El Compose oficial monta:

```text
./backend/storage:/app/storage
```

La aplicación conserva sus rutas lógicas internas:

- branding: `/app/storage/branding`;
- documentos clínicos: `/app/storage/clinical_documents`;
- recetas: `/app/storage/prescriptions`.

Antes del primer recreate en un VPS donde existieron archivos dentro del contenedor sin mount, ejecutar primero:

```bash
./scripts/production/prepare_dentia_persistent_storage.sh --dry-run
./scripts/production/prepare_dentia_persistent_storage.sh --apply
```

El script copia únicamente faltantes desde `/app/storage` hacia `backend/storage`, aborta ante hashes distintos y no borra archivos.

## Inventario documental

`document_inventory.tsv` se construye desde PostgreSQL y contiene únicamente metadatos operativos:

- tipo de entidad (`prescription`, `clinical_document`);
- id del registro;
- empresa;
- estado;
- ruta lógica almacenada;
- ruta esperada dentro de `storage.tar.gz`;
- SHA-256 esperado;
- tamaño físico cuando existe;
- fecha de finalización;
- resultado de validación.

No incluye contenido clínico narrativo.

El backup aborta ante:

- `pdf_storage_path` vacío en registros finalizados/anulados que requieren PDF;
- rutas absolutas;
- `..` o escape de directorio;
- symlinks;
- archivo faltante;
- hash físico diferente;
- rutas duplicadas ambiguas.

## Manifest

`manifest.json` registra:

- fecha UTC;
- fecha local;
- servidor;
- entorno;
- rama;
- commit;
- revisión Alembic;
- versión PostgreSQL;
- rutas respaldadas;
- cantidad de archivos;
- tamaños;
- hashes SHA-256;
- inventario documental y métricas semánticas;
- resultado de verificación.

No guarda secretos ni `.env`.

## Checksums

`checksums.sha256` cubre:

- `database.dump`;
- `storage.tar.gz`;
- `document_inventory.tsv`;
- `document_inventory_metrics.json`;
- `document_inventory_archive_metrics.json`;
- `manifest.json`;
- `metadata.txt`.

## Integración con deploy

`deploy_dentia.sh` ahora exige:

```text
backup completo
→ verify_dentia_backup.sh
→ git fetch/pull
```

Si falla el backup o la verificación, el deploy aborta antes de modificar código o contenedores.

## Rollback vs restauración

`rollback_dentia.sh` sigue siendo rollback de código por defecto.

La restauración de datos requiere:

```text
--restore-data /ruta/al/backup --yes-i-understand
```

y confirmación manual fuerte.

## Retención

El backup conserva por defecto `DENTIA_BACKUP_RETENTION` paquetes verificados. Puede desactivarse con:

```bash
./scripts/production/backup_dentia.sh --no-prune
```

Nunca borra:

- el backup recién creado;
- el backup registrado como último deploy;
- backups no verificados.

## Seguridad

- Directorio de backup: `chmod 700`.
- Archivos de backup: `chmod 600`.
- No se imprimen contenidos clínicos.
- No se guardan secretos.
- Compose usa variables obligatorias y `.env.production.example` contiene solo marcadores.
- Los archivos reales `.env`, `.env.production` y variantes están ignorados por Git.
- Cifrado externo queda como hardening posterior con gestión real de claves.

## Incidente C018R.3-FIX1

Se confirmó en producción que el backend guardaba PDFs en `/app/storage` dentro del contenedor sin mount persistente. Un documento histórico podía existir físicamente dentro del contenedor y no en el host, por lo que un backup que solo archivara `backend/storage` podía declararse válido aunque faltara un PDF referenciado por PostgreSQL.

Corrección aplicada:

1. Mount persistente `./backend/storage:/app/storage`.
2. Script de preparación para rescatar/validar archivos previos al primer recreate.
3. Inventario documental consultando PostgreSQL.
4. Validación semántica en backup, verificación y restore temporal.
5. Runbook de secretos y rotación antes del piloto.

## Riesgo residual

La consistencia DB/storage no es snapshot transaccional único. Para piloto, la ventana se minimiza generando dump y storage en la misma ejecución, pero si se finaliza un PDF exactamente durante el backup podría haber desalineación. Para operación crítica, documentar una breve pausa de generación documental o implementar snapshot de filesystem.

## Validación esperada

```bash
bash -n scripts/production/backup_dentia.sh
bash -n scripts/production/verify_dentia_backup.sh
bash -n scripts/production/restore_dentia_backup.sh
bash -n scripts/production/deploy_dentia.sh
bash -n scripts/production/rollback_dentia.sh
bash -n scripts/production/status_dentia_production.sh
```

No ejecutar restore ni deploy sobre producción durante este ticket.
