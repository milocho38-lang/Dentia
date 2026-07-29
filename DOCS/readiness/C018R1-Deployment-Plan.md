# C018R.1 — Plan de despliegue y preparación del piloto

Este plan no ejecuta despliegue. Define el camino seguro para pasar del estado local actual a piloto real.

## Estado actual

- Rama local: `master`.
- Commit local: `34fe4b8`.
- `origin/master`: `34fe4b8`.
- Cambios C017G.1/C017G.2: locales sin commit.
- Alembic local: `20260724_0022 (head)`.
- Producción: no verificada en vivo durante esta auditoría.

## Fase 1 — Limpieza y revisión local

1. Revisar `git status --short`.
2. Separar artefactos generados:
   - `backend/storage/clinical_documents/`
   - `backend/storage/prescriptions/`
   - imágenes locales no documentales.
3. Confirmar si `Imagenes/DDS-04A.png` y `Imagenes/mockupDDS-04.png` son assets oficiales o solo referencias locales.
4. Actualizar `.gitignore` en ticket posterior para `backend/storage/**`.
5. Reejecutar:
   - `python3 -m compileall backend/app`
   - `npm --prefix frontend run lint`
   - `npm --prefix frontend run build`
   - scripts de caracterización.
6. Revisar diff completo.
7. Commit funcional.
8. Push a GitHub.

## Fase 2 — Backup completo

Antes de desplegar:

1. Crear y validar `/opt/apps/dentia/.env.production` con permisos `600`.
2. Ejecutar `scripts/production/prepare_dentia_persistent_storage.sh --dry-run`.
3. Ejecutar `scripts/production/prepare_dentia_persistent_storage.sh --apply` solo si hay faltantes y no hay conflictos.
4. Crear backup completo con `scripts/production/backup_dentia.sh`.
5. Verificarlo con `scripts/production/verify_dentia_backup.sh`.
6. Ejecutar restauración temporal con `scripts/production/restore_dentia_backup.sh --temporary`.
7. Confirmar que DB, storage restaurado e inventario documental son coherentes.

## Fase 3 — Despliegue recomendado

Flujo actual de `scripts/production/deploy_dentia.sh`:

```text
repo limpio
storage persistente validado
backup completo semántico
verify backup semántico
git fetch/pull
docker compose build
docker compose up -d
alembic upgrade head dentro del backend
health checks
```

Riesgo: migración después de levantar contenedores.

Flujo recomendado para ticket posterior:

```text
repo limpio
backup DB + storage
git fetch/pull
docker compose build
ejecutar migraciones con imagen nueva en comando one-off o ventana controlada
docker compose up -d
health checks
verificar dominio
registrar commit/backup
```

## Fase 4 — Validación post-deploy

1. Confirmar commit en VPS.
2. Confirmar `alembic current`.
3. Confirmar `/health`.
4. Login con usuario plataforma.
5. Login con Kimberly.
6. Confirmar permisos clínicos.
7. Crear paciente de prueba.
8. Ejecutar flujo corto:
   - cita;
   - evolución;
   - odontograma;
   - tratamiento;
   - presupuesto;
   - pago;
   - receta;
   - documento clínico.
9. Descargar PDFs.
10. Verificar que storage guarda archivos.
11. Ejecutar backup post-deploy.

## Rollback

El rollback actual:

- Revierte código a commit objetivo.
- No revierte migraciones.
- No restaura DB.
- No restaura storage.

Para piloto, un rollback real debe incluir:

- decisión explícita de si se revierte DB;
- restore de PostgreSQL;
- restore de storage;
- validación de hashes;
- verificación de PDFs históricos.

## Criterio para habilitar piloto

El piloto puede iniciar solo si:

- [ ] GitHub contiene el commit exacto validado.
- [ ] Producción corre ese commit.
- [ ] Alembic está en head.
- [ ] Backup completo DB + storage existe.
- [ ] Restore fue probado o ensayado localmente.
- [ ] K Astudillo está configurada.
- [ ] Kimberly puede completar flujo clínico-comercial básico.
- [ ] No hay P0 abiertos.
