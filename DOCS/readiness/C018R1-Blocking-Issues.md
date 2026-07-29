# C018R.1 — Bloqueantes y riesgos de piloto

## P0 — No iniciar piloto sin resolver

### P0-1 — Backup incompleto sin storage

Problema: `scripts/production/backup_dentia.sh` respalda solo PostgreSQL mediante `pg_dump`.
Evidencia: el script genera `dentia_*.sql.gz` y no copia `storage/`.
Impacto: documentos clínicos, recetas, comprobantes y presupuestos PDF pueden quedar irrecuperables aunque la DB restaure.
Estado C018R.3: **CERRADO**. Backup `dentia_20260729_040400` verificado con `BACKUP_VALID` y restore temporal con `RESTORE_VALID`.
Cierre: completado. Mantener como control recurrente antes/después de despliegues.

### P0-1B — Storage clínico no persistente en backend productivo

Problema: se confirmó que `dentia-backend` podía almacenar PDFs en `/app/storage` sin mount hacia el host.
Impacto: recrear el contenedor puede perder documentos históricos aunque PostgreSQL conserve rutas y hashes.
Estado C018R.3-FIX1: Compose oficial monta `./backend/storage:/app/storage` y existe `prepare_dentia_persistent_storage.sh` para copiar/validar faltantes antes del primer recreate.
Cierre C018R.3: **CERRADO**. Mount validado en producción hacia `/app/storage`, host `/opt/apps/dentia/backend/storage`, conservando volumen DB `dentia_dentia_db_data`.

### P0-1C — Secretos productivos fuera de control documental

Problema: configuración productiva puede exponer secretos si se versionan o comparten salidas expandidas de Compose.
Impacto: compromiso de base de datos, JWT o sesión.
Estado C018R.3-FIX1: se agregó `.env.production.example`, Compose con variables obligatorias, `DENTIA_ENV_FILE` y runbook de rotación.
Cierre C018R.3: estructura segura implementada. La rotación queda como mejora no bloqueante separada y debe ejecutarse en ventana controlada antes del piloto amplio.

### P0-2 — Funcionalidad clínica/documental sin commit

Problema: C017G.1/C017G.2 aparecen como archivos no rastreados/modificados.
Evidencia: `git status --short`.
Impacto: no puede desplegarse ni reproducirse de forma confiable.
Cierre: revisar, limpiar artefactos, commit, push, validar deploy.

### P0-3 — Prueba multiempresa A/B

Problema: aunque los servicios filtran por `company_id`, no hay evidencia en esta auditoría de una prueba formal con Empresa A/B para documentos, recetas, pagos y odontograma.
Impacto: cualquier fuga cross-company es inaceptable.
Estado C018R.4-FIX1: mitigado con suite automática de caracterización y suite DB-backed sobre PostgreSQL aislado. La suite crea fixtures ficticios Empresa A/B, actores por rol, sedes, pacientes, citas, tratamientos, presupuestos, evolución, odontograma, receta y documento clínico, y ejecuta ataques IDOR reales.
Estado C018R.4-FIX2: **CERRADO** para piloto controlado. Se amplió cobertura DB-backed a finanzas, pagos, comprobantes, presupuestos, reportes, usuarios, roles, sedes, empresa, branding, plataforma y registro maestro de 187 rutas.
Cierre: completado. Mantener como control recurrente que toda nueva ruta crítica entre registrada y con prueba DB-backed.

### P0-4 — K Astudillo no verificada operativamente

Problema: no se auditó en DB real que Kimberly tenga roles, sede, perfil odontológico, firma y branding correctos.
Impacto: piloto puede fallar por configuración, no por software.
Cierre: completar `C018R1-Pilot-Checklist.md`.

## P1 — Corregir durante preparación

### P1-0 — Rotación de secretos antes de piloto amplio

Estado: pendiente no bloqueante de C018R.3.
Alcance: rotar contraseña PostgreSQL y `JWT_SECRET`, actualizar `DATABASE_URL`, validar login, invalidar sesiones si existe mecanismo seguro y ejecutar backup posterior.

### P1-1 — Orden de deploy con migraciones después de levantar contenedores

Evidencia: `scripts/production/deploy_dentia.sh` ejecuta `docker compose up -d` antes de `alembic upgrade head`.
Riesgo: ventana de incompatibilidad app nueva/esquema viejo.
Cierre: rediseñar deploy para aplicar migraciones con imagen nueva antes de servir tráfico o con ventana controlada.

### P1-2 — Scripts locales con PID files inconsistentes

Evidencia: `./scripts/local/status_dentia.sh` reportó backend/frontend inactivos, pero puertos 8001/3001 ocupados.
Riesgo: confusión operacional y arranques fallidos.
Cierre: hardening de scripts para detectar y resolver procesos huérfanos de Dentia de forma segura.

### P1-3 — `.gitignore` no cubre explícitamente `backend/storage/`

Evidencia: `.gitignore` ignora `storage/*`, pero existen `backend/storage/clinical_documents/` y `backend/storage/prescriptions/` no rastreados.
Riesgo: PDFs locales podrían aparecer accidentalmente en Git.
Estado C018R.3-FIX1: mitigado agregando `backend/storage/**`, `backups/`, `*.dump`, `*.tar.gz`, `.env` reales y conservando `.example`.

### P1-4 — Fecha de duplicación de documentos/recetas usa `date.today()`

Evidencia:

- `backend/app/services/clinical_document_service.py`
- `backend/app/services/prescription_service.py`

Riesgo: en sedes no Bogotá o al operar cerca de medianoche puede usar fecha clínica equivocada.
Cierre: calcular fecha por zona de sede/empresa.

## P2 — Puede esperar durante piloto

- Mensajes genéricos de error en frontend.
- Mejoras de UX en pantallas densas.
- Refinamiento de reportes.
- Optimización de consultas para volúmenes altos.

## P3 — Post-MVP

- IA.
- WhatsApp.
- Inventario.
- Laboratorios.
- Analítica avanzada.
