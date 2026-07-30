# C018R.1 — Plan de despliegue y preparación del piloto

Este plan no ejecuta despliegue. Define el camino seguro para pasar del estado local actual a piloto real.

## Estado actual

- Rama local: `master`.
- Commit local: `34fe4b8`.
- `origin/master`: `34fe4b8`.
- Cambios C017G.1/C017G.2: locales sin commit.
- Alembic local: `20260724_0022 (head)`.
- Producción: no verificada en vivo durante esta auditoría.
- C018R.3: cerrado posteriormente con backup `dentia_20260729_040400`, `BACKUP_VALID`, `RESTORE_VALID`, mount `/opt/apps/dentia/backend/storage:/app/storage` y Alembic `20260724_0022 (head)`.
- C018R.4-FIX2: compuerta multiempresa cerrada localmente para piloto controlado. Suite automática de caracterización, registro maestro de 187 rutas y suite DB-backed A/B incorporadas. Valida IDOR, roles, sedes, plataforma, presupuestos, pagos, comprobantes, reportes, branding y descargas críticas.
- C018R.2: hardening local implementado. El deploy valida configuración, crea/verifica backup, construye imágenes, ejecuta Alembic en contenedor one-off de la nueva imagen y solo después recrea backend/frontend.

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
   - `./scripts/local/test_dentia_security.sh`
   - `./scripts/local/test_dentia_security.sh --full`
   - `./scripts/local/test_dentia_security.sh --coverage` cuando se requiera reporte de cobertura.
6. Revisar diff completo.
7. Commit funcional.
8. Push a GitHub.

## Fase 2 — Backup completo

Estado C018R.3: cerrado. Este flujo pasa a ser control obligatorio recurrente antes de despliegues.

Antes de desplegar:

1. Crear y validar `/opt/apps/dentia/.env.production` con permisos `600`.
2. Ejecutar `scripts/production/prepare_dentia_persistent_storage.sh --dry-run`.
3. Ejecutar `scripts/production/prepare_dentia_persistent_storage.sh --apply` solo si hay faltantes y no hay conflictos.
4. Crear backup completo con `scripts/production/backup_dentia.sh`.
5. Verificarlo con `scripts/production/verify_dentia_backup.sh`.
6. Ejecutar restauración temporal con `scripts/production/restore_dentia_backup.sh --temporary`.
7. Confirmar que DB, storage restaurado e inventario documental son coherentes.

## Fase 3 — Despliegue recomendado

Flujo actual de `scripts/production/deploy_dentia.sh` después de C018R.2:

```text
validar configuración productiva
repo limpio y storage persistente validado
backup completo semántico
verificar backup semántico
git fetch/pull
docker compose build
alembic upgrade head en contenedor one-off de nueva imagen backend
verificar alembic current
recrear backend/frontend sin recrear DB
health checks backend/frontend
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
- [x] C018R.4 multiempresa A/B ejecutado con fixtures ficticios y ataques IDOR reales.
- [x] C018R.4-FIX2 financiero/administrativo ejecutado con 0 rutas críticas pendientes.
- [ ] No hay P0 abiertos.
