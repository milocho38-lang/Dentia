# C018R.2 — Hardening integral previo al piloto controlado

Fecha de registro: 2026-07-29.

Estado: **IMPLEMENTADO LOCALMENTE, pendiente de validación completa y despliegue controlado**.

## Objetivo

Cerrar pendientes operativos previos al piloto real sin modificar datos productivos ni debilitar seguridad clínica/multiempresa.

## Cambios aplicados

### Configuración y secretos

- Se agregó `scripts/production/validate_dentia_production_config.sh`.
- El validador usa `DENTIA_ENV_FILE`.
- Rechaza archivos `.example` como configuración real.
- Rechaza permisos inseguros; el archivo real debe tener permisos máximos `600`.
- Valida variables obligatorias sin imprimir secretos.
- Detecta placeholders y secretos triviales.
- Verifica coherencia entre `DATABASE_URL`, `POSTGRES_DB` y `POSTGRES_USER`.
- Ejecuta `docker compose config --quiet` sin iniciar servicios.

### Despliegue seguro

`scripts/production/deploy_dentia.sh` quedó con orden:

```text
validar configuración
↓
backup obligatorio
↓
verificación semántica
↓
git fetch/pull
↓
build de imágenes
↓
alembic upgrade head en contenedor one-off de la nueva imagen
↓
verificación de Alembic
↓
recrear backend/frontend
↓
healthchecks
```

La base de datos no se recrea durante deploy.

### Scripts locales

- `start_dentia.sh`, `stop_dentia.sh`, `status_dentia.sh`, `logs_dentia.sh` y `update_dentia_local.sh` admiten `--help`.
- Los PID se validan contra el comando esperado antes de detener procesos.
- Los PID stale se detectan y limpian o reportan.
- No se usan `pkill` ni `killall`.
- Los logs fallan con mensaje claro si Dentia no ha sido iniciado.

### Fechas clínicas

- Se creó `backend/app/utils/clinical_dates.py`.
- La duplicación de recetas y documentos clínicos usa la fecha local de la sede, luego empresa, luego `America/Bogota`.
- Los formularios frontend dejan de usar `toISOString().slice(0, 10)` para fecha por defecto y usan calendario local del navegador.
- No se creó columna nueva ni migración.

### Anulación visible

- La acción visible quedó como `Anular documento` y `Anular receta`.
- El modal exige motivo, bloquea doble submit y confirma que el PDF histórico se conserva.
- Solo se muestra para estado `FINALIZED` y permiso correspondiente.

### Pruebas de caracterización

- Se agregó `frontend/scripts/pilot-hardening-tests.mjs`.
- Se agregó `backend/tests/operations/test_clinical_dates.py`.

## Hallazgos reales

- Antes de C018R.2, el deploy recreaba contenedores y luego ejecutaba Alembic dentro del backend ya actualizado.
- La duplicación de recetas/documentos usaba `date.today()`, dependiente del calendario del servidor.
- Los formularios nuevos usaban `new Date().toISOString().slice(0, 10)`, vulnerable a bordes UTC.
- La UI de anulación existía, pero podía mejorar su claridad y doble-submit.
- El backend Docker corre como root. No se cambió en esta fase porque el bind mount productivo `/app/storage` requiere validación de ownership/UID antes de modificar el usuario efectivo.

## Riesgo residual aceptado temporalmente

Backend continúa ejecutándose como root dentro del contenedor.

Tratamiento recomendado antes de producción ampliada:

1. Crear usuario no privilegiado en `backend/Dockerfile`.
2. Preparar ownership del bind mount `/opt/apps/dentia/backend/storage`.
3. Probar escritura de PDFs, branding, recetas, documentos clínicos y comprobantes.
4. Ejecutar backup/restore completo.
5. Cambiar imagen y desplegar en ventana controlada.

## Comandos de validación

```bash
./scripts/local/test_dentia_security.sh --hardening
node frontend/scripts/pilot-hardening-tests.mjs
PYTHONPATH=backend backend/.venv/bin/pytest --confcutdir=backend/tests/operations backend/tests/operations/test_clinical_dates.py
node frontend/scripts/classic-orientation-tests.mjs
node frontend/scripts/dental-inspector-tests.mjs
node frontend/scripts/clinical-commercial-characterization-tests.mjs
npm --prefix frontend run lint
npm --prefix frontend run build
python3 -m compileall backend/app
cd backend && .venv/bin/alembic current && .venv/bin/alembic check
git diff --check
```

`--hardening` ejecuta:

- camino exitoso y errores esperados del validador productivo con secretos ficticios;
- caracterización del orden seguro de deploy;
- smoke tests de scripts locales con procesos temporales controlados;
- prueba pytest pura de fechas clínicas sin cargar `backend/tests/conftest.py`.

## No realizado

- No se rotaron secretos reales.
- No se leyó `.env.production`.
- No se conectó al VPS.
- No se modificó storage productivo.
- No se creó migración.
- No se hizo commit ni despliegue.
