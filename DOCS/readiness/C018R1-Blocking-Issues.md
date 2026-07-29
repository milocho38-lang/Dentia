# C018R.1 — Bloqueantes y riesgos de piloto

## P0 — No iniciar piloto sin resolver

### P0-1 — Backup incompleto sin storage

Problema: `scripts/production/backup_dentia.sh` respalda solo PostgreSQL mediante `pg_dump`.  
Evidencia: el script genera `dentia_*.sql.gz` y no copia `storage/`.  
Impacto: documentos clínicos, recetas, comprobantes y presupuestos PDF pueden quedar irrecuperables aunque la DB restaure.  
Estado C018R.3: mitigado en scripts locales mediante paquete completo PostgreSQL + storage + manifest + checksums + verificador + restore temporal.
Cierre definitivo: ejecutar backup y restauración temporal en el VPS real antes del piloto.

### P0-2 — Funcionalidad clínica/documental sin commit

Problema: C017G.1/C017G.2 aparecen como archivos no rastreados/modificados.  
Evidencia: `git status --short`.  
Impacto: no puede desplegarse ni reproducirse de forma confiable.  
Cierre: revisar, limpiar artefactos, commit, push, validar deploy.

### P0-3 — Prueba multiempresa A/B pendiente

Problema: aunque los servicios filtran por `company_id`, no hay evidencia en esta auditoría de una prueba formal con Empresa A/B para documentos, recetas, pagos y odontograma.  
Impacto: cualquier fuga cross-company es inaceptable.  
Cierre: ejecutar suite/manual script multiempresa y documentar resultados.

### P0-4 — K Astudillo no verificada operativamente

Problema: no se auditó en DB real que Kimberly tenga roles, sede, perfil odontológico, firma y branding correctos.  
Impacto: piloto puede fallar por configuración, no por software.  
Cierre: completar `C018R1-Pilot-Checklist.md`.

## P1 — Corregir durante preparación

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
Estado C018R.3: mitigado agregando `backend/storage/**`, `backups/`, `*.dump` y `*.tar.gz` a `.gitignore`.

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
