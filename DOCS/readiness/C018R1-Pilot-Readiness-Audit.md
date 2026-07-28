# C018R.1 — Auditoría de preparación para piloto real

Fecha de auditoría: 2026-07-28  
Clínica piloto: K Astudillo  
Resultado recomendado: **LISTO CON CONDICIONES**

Dentia tiene suficiente funcionalidad local para ejecutar un piloto clínico controlado, pero **no debe iniciar varias semanas de uso real sin cerrar primero los P0/P1 documentados**. El punto más delicado no es la interfaz: es la preparación operacional para producción, especialmente Git limpio, despliegue, backup completo y validación multiempresa/permisos con datos reales.

## 1. Resumen ejecutivo

### Fortalezas verificadas

- El flujo clínico-comercial principal existe en código: pacientes, agenda, historia clínica, evoluciones, odontograma, tratamientos, presupuestos, pagos, documentos clínicos y recetas.
- El backend compila correctamente: `python3 -m compileall backend/app`.
- El frontend compila y tipa correctamente: `npm --prefix frontend run build`.
- Las pruebas/scripts de caracterización clínica pasan:
  - `frontend/scripts/clinical-commercial-characterization-tests.mjs`
  - `frontend/scripts/dental-inspector-tests.mjs`
  - `frontend/scripts/classic-orientation-tests.mjs`
- Alembic local está en `20260724_0022 (head)` y `alembic check` reporta `No new upgrade operations detected`.
- Los servicios críticos filtran en general por `company_id` usando `context.user.company_id`, por ejemplo:
  - `backend/app/services/odontogram_service.py`
  - `backend/app/services/clinical_record_service.py`
  - `backend/app/services/treatment_service.py`
  - `backend/app/services/clinical_document_service.py`
  - `backend/app/services/prescription_service.py`

### Riesgos principales

- **P0:** el script de backup de producción respalda solo PostgreSQL; no incluye `storage/`. Los PDFs finalizados quedan referenciados por DB pero almacenados en disco. Sin storage, una restauración no recupera documentos clínicos, recetas, comprobantes o presupuestos PDF.
- **P0:** los módulos C017G.1/C017G.2 y ajustes asociados están **sin commit**. `HEAD == origin/master`, pero hay archivos modificados/no rastreados con funcionalidad clínica nueva.
- **P1:** el deploy de producción aplica migraciones después de recrear/levantar contenedores. Si una versión nueva requiere esquema nuevo, puede existir ventana de fallo entre `docker compose up -d` y `alembic upgrade head`.
- **P1:** los archivos generados locales están sin seguimiento y no deben entrar accidentalmente a Git:
  - `backend/storage/clinical_documents/`
  - `backend/storage/prescriptions/`
  - `Imagenes/*.png`
- **P1:** el estado local reporta puertos ocupados por procesos aunque los PID files aparecen inactivos; los scripts locales pueden requerir limpieza manual si quedan procesos huérfanos.

## 2. Estado local

Evidencia:

```text
Branch: master
HEAD: 34fe4b8 feat(clinical): support treatment-first odontogram workflow
origin/master: 34fe4b8
origin/master..HEAD: vacío
Alembic local: 20260724_0022 (head)
```

`git status --short` muestra cambios locales relevantes:

- Documentación modificada:
  - `DOCS/D002 - REGLAS DE NEGOCIO.md`
  - `DOCS/D003B - MODELO DATOS.md`
  - `DOCS/D005 - ROADMAP DESARROLLO.md`
  - `DOCS/HISTORIAL_DECISIONES.md`
  - `DOCS/README.md`
  - `DOCS/clinical/README.md`
- Seguridad/routing/modelos:
  - `backend/app/core/security_catalog.py`
  - `backend/app/main.py`
  - `backend/app/models/__init__.py`
- UI:
  - `frontend/components/patients/PatientDetail.tsx`
- Corrección reciente:
  - `backend/app/services/patient_service.py`
- Archivos nuevos no rastreados:
  - `backend/app/models/clinical_document.py`
  - `backend/app/models/prescription.py`
  - `backend/app/routers/clinical_document_router.py`
  - `backend/app/routers/prescription_router.py`
  - `backend/app/schemas/clinical_document_schema.py`
  - `backend/app/schemas/prescription_schema.py`
  - `backend/app/services/clinical_document_service.py`
  - `backend/app/services/prescription_service.py`
  - `backend/migrations/versions/20260724_0021_clinical_documents.py`
  - `backend/migrations/versions/20260724_0022_prescriptions.py`
  - `frontend/services/clinicalDocumentService.ts`
  - `frontend/services/prescriptionService.ts`
  - `frontend/types/clinicalDocument.ts`
  - `frontend/types/prescription.ts`

Conclusión local: **funcionalmente avanzado, técnicamente validado, pero no listo para producción hasta commit/revisión de cambios no rastreados**.

## 3. Estado GitHub

Evidencia local de Git:

```text
HEAD -> master
origin/master -> 34fe4b8
origin/master..HEAD -> vacío
```

Conclusión:

- C017F.2 / tratamiento-first odontogram está en GitHub según `HEAD == origin/master`.
- C017G.1 documentos clínicos, C017G.2 recetas y el fix de edad de recetas están implementados localmente pero **no están en GitHub**.
- No se ejecutó `git fetch` ni se consultó red externa durante esta auditoría.

## 4. Estado producción

No se ejecutó ningún script de producción ni se modificó el VPS.

Evidencia revisada:

- `scripts/production/deploy_dentia.sh`
- `scripts/production/backup_dentia.sh`
- `scripts/production/rollback_dentia.sh`
- `scripts/production/status_dentia_production.sh`
- `scripts/production/logs_dentia_production.sh`
- `scripts/production/start_dentia_production.sh`
- `scripts/production/stop_dentia_production.sh`

No existen en el repo local:

- `scripts/production/restart_dentia_production.sh`

Conclusión producción: **NO VERIFICADA EN VIVO**. Por evidencia local, producción no puede contener C017G.1/C017G.2 si no hay commit/push.

## 5. Migraciones pendientes

| Migración | Down revision | Estado local | Estado GitHub | Estado producción | Riesgo | Resultado |
|---|---:|---|---|---|---|---|
| `20260724_0020_treatment_first_odontogram_config.py` | `20260724_0019` | En head local | Commit `34fe4b8` | Probable si VPS está en master | Medio | Crea config tratamiento→odontograma; tiene downgrade |
| `20260724_0021_clinical_documents.py` | `20260724_0020` | Aplicada local | No rastreada | No desplegada | Medio/Alto | Seeding usa `gen_random_uuid()` e idempotencia por `code` |
| `20260724_0022_prescriptions.py` | `20260724_0021` | Aplicada local | No rastreada | No desplegada | Medio/Alto | Seeding usa `gen_random_uuid()` e idempotencia por `code` |

Validaciones ejecutadas:

```text
backend/.venv/bin/alembic current -> 20260724_0022 (head)
backend/.venv/bin/alembic check -> No new upgrade operations detected
```

Observaciones:

- `0021` y `0022` usan `gen_random_uuid()` en migración. En esta DB funciona; para producción se debe confirmar extensión disponible o existencia de soporte en PostgreSQL 17.
- Los downgrades eliminan relaciones `rol_permisos` por códigos de permisos, pero no eliminan los permisos en `permisos`. Esto evita borrar permisos preexistentes, pero puede dejar catálogo residual si se baja versión. Es aceptable si el patrón del proyecto prefiere conservar catálogo; documentarlo.
- `0021` y `0022` aún no están rastreadas por Git; no deben considerarse entregadas.

## 6. Configuración K Astudillo

Checklist obligatorio antes del piloto:

- Empresa:
  - Nombre correcto.
  - Identificación.
  - País.
  - Zona horaria `America/Bogota` o la real según operación.
  - Correo, teléfono y dirección.
  - Branding completo: logo, colores, encabezado, pie, firma.
- Sedes:
  - Sede real activa.
  - Dirección y ciudad.
  - Zona horaria efectiva.
  - Horario operativo.
- Usuario Kimberly Astudillo:
  - Usuario activo.
  - Empresa K Astudillo.
  - Roles clínicos correctos.
  - No `PLATFORM_ADMIN`.
  - Sede asignada.
  - Cierre e inicio de sesión posterior al cambio de permisos.
- Perfil odontológico:
  - Vinculado al mismo `user_id`.
  - Misma empresa.
  - Sede asignada.
  - Registro profesional.
  - Especialidad.
  - Firma gráfica coherente.

Procedimientos sugeridos para piloto, sin crearlos automáticamente:

1. Valoración inicial.
2. Profilaxis.
3. Sellante.
4. Resina una superficie.
5. Resina dos superficies.
6. Resina MOD.
7. Endodoncia unirradicular.
8. Endodoncia multirradicular.
9. Corona provisional.
10. Corona definitiva.
11. Exodoncia simple.
12. Exodoncia quirúrgica.
13. Implante.
14. Control postoperatorio.
15. Radiografía/periapical si se cobra.
16. Blanqueamiento.

Configurar como `NO_CHANGE` procedimientos generales que no modifican odontograma.

## 7. Flujo clínico completo

| Transición | Estado | Evidencia | Riesgo |
|---|---|---|---|
| Paciente → cita | FUNCIONA | `backend/app/services/agenda_service.py`, `frontend/components/agenda/AgendaView.tsx` | Bajo |
| Cita → historia clínica | FUNCIONA | `backend/app/services/clinical_record_service.py` | Bajo/Medio |
| Historia → evolución | FUNCIONA | `clinical_evolutions.*` en `security_catalog.py` y servicios clínicos | Bajo |
| Evolución simplificada | FUNCIONA | `frontend/components/patients/ClinicalRecordPage.tsx` | Fricción posible por UI extensa |
| Odontograma → diagnóstico → tratamiento | FUNCIONA | `create_planned_procedure_from_odontogram_event` en `odontogram_router.py` / `treatment_service.py` | Medio |
| Tratamiento → procedimiento → odontograma | FUNCIONA | `clinical-completion`, `mark_procedure_done`, integración C017E.3 | Medio |
| Tratamiento → presupuesto versionado | FUNCIONA | `create_budget`, snapshots en `treatment_service.py` | Medio |
| Aprobación → pago | FUNCIONA | Presupuestos/pagos en `treatment_service.py` | Medio por concurrencia |
| Pago → comprobante PDF | FUNCIONA | `generate_payment_receipt_pdf` en `treatment_service.py` | Medio por storage backup |
| Receta/remisión | FUNCIONA LOCAL | `prescription_service.py`, `clinical_document_service.py` | Alto hasta commit/deploy/backup |

## 8. Dos rutas clínicas

Ruta A: Odontograma → diagnóstico → tratamiento  
Estado: **FUNCIONA CON FRICCIÓN CONTROLADA**

- Evidencia: `backend/app/routers/odontogram_router.py` expone creación de procedimiento planificado desde evento odontográfico.
- Evidencia: `backend/app/services/treatment_service.py` contiene vínculos a `source_odontogram_event_id`.

Ruta B: Tratamiento → procedimiento → diagnóstico confirmado → odontograma  
Estado: **FUNCIONA CON FRICCIÓN CONTROLADA**

- Evidencia: `backend/app/routers/treatment_router.py` expone `clinical-completion`.
- Riesgo: requiere disciplina clínica al vincular evolución y procedimiento; recomendable checklist del piloto.

## 9. Evolución clínica simplificada

Estado: **ACEPTABLE PARA PILOTO**

Evidencia:

- Permisos: `clinical_evolutions.create`, `update_draft`, `sign`, `add_addendum` en `backend/app/core/security_catalog.py`.
- Servicio: `backend/app/services/clinical_record_service.py`.
- UI: `frontend/components/patients/ClinicalRecordPage.tsx`.

Fricciones:

- Página clínica grande, posible carga cognitiva.
- Debe validarse manualmente que “una sola narrativa obligatoria” sea clara para Kimberly.

## 10. Documentos clínicos

Estado: **FUNCIONA LOCAL / NO ENTREGADO A PRODUCCIÓN**

Evidencia:

- Router: `backend/app/routers/clinical_document_router.py`.
- Servicio: `backend/app/services/clinical_document_service.py`.
- Modelo: `backend/app/models/clinical_document.py`.
- PDF final con snapshot y SHA-256: `download_document_pdf()` verifica archivo y hash.
- Anulación existe en backend: `void_document()`.
- Anulación existe en frontend local: `frontend/services/clinicalDocumentService.ts` y `PatientDetail.tsx`.

Pendiente:

- Como los archivos son no rastreados, no se puede afirmar que la UI de anulación esté en GitHub/producción.
- Storage PDF es crítico para restauración.

## 11. Recetas

Estado: **FUNCIONA LOCAL / NO ENTREGADO A PRODUCCIÓN**

Evidencia:

- Router: `backend/app/routers/prescription_router.py`.
- Servicio: `backend/app/services/prescription_service.py`.
- Modelo: `backend/app/models/prescription.py`.
- Permisos: `prescriptions.*` en `security_catalog.py`.
- Anulación existe en backend: `void_prescription()`.
- Anulación existe en frontend local: `frontend/services/prescriptionService.ts` y `PatientDetail.tsx`.
- No hay cálculo automático de dosis ni interacción farmacológica; correcto para alcance C017G.2.

Fix reciente:

- `prescription_service._snapshot_patient()` ya no debe leer `patient.age`; usa `calculate_age()` contra `prescription.clinical_date`.
- Prueba local: `backend/scripts/prescription_age_snapshot_tests.py`.

## 12. Permisos

Matriz resumida real desde `backend/app/core/security_catalog.py`:

| Rol | Alcance |
|---|---|
| `PLATFORM_ADMIN` | Solo `platform.companies.view/manage`. No recibe permisos clínicos por catálogo. |
| `ADMINISTRATOR` | `CLINIC_ADMIN_PERMISSION_CODES`: excluye permisos clínicos sensibles y plataforma. |
| `SECRETARY` | Operación administrativa, agenda, pagos básicos, reportes operativos, sin odontograma/documentos clínicos/recetas. |
| `DENTIST` | Clínica, odontograma, tratamientos, documentos clínicos y recetas sin anulación. |
| `DENTIST_ADMIN` | Unión secretaria+odontólogo + configuración + reportes financieros + anulación clínica/documental. |

Riesgos:

- Cambios de roles requieren reinicio de sesión del usuario para reflejar permisos.
- Se debe probar con K Astudillo que Kimberly tenga `DENTIST_ADMIN` y perfil odontológico, no solo `ADMINISTRATOR`.

## 13. Multiempresa

Estado: **BUENA BASE, REQUIERE PRUEBAS P0 ANTES DEL PILOTO**

Evidencia positiva:

- Servicios críticos usan `context.user.company_id`.
- Documentos y recetas descargan por `id` + `company_id`.
- Storage path usa company id en ruta relativa y `_storage_path()` valida path traversal.

Endpoints críticos a probar con datos A/B:

| Área | Filtro esperado | Riesgo |
|---|---|---|
| Pacientes | `Patient.company_id == context.user.company_id` | Bajo |
| Historia clínica | company + patient | Bajo |
| Odontograma | company + patient | Bajo |
| Tratamientos | company + treatment/patient | Medio por múltiples relaciones |
| Pagos | company + payment/treatment | Medio |
| Documentos | company + document | Medio por storage |
| Recetas | company + prescription | Medio por storage |
| Usuarios plataforma | validación cross-tenant explícita | Medio |

## 14. Finanzas

Fuentes oficiales:

- Venta: presupuesto aprobado.
- Producción: procedimiento realizado.
- Ingreso: pago válido.
- Cartera: saldo financiero.
- Estado dental: evento odontográfico confirmado.

Evidencia:

- Reportes separan finanzas en `backend/app/services/report_service.py`.
- Pagos y reversas en `backend/app/services/treatment_service.py`.
- Comprobante PDF en `generate_payment_receipt_pdf()`.

Riesgos:

- Concurrencia de consecutivos: presupuestos/pagos usan bloqueos o conteos según flujo; se debe probar con dos usuarios antes de piloto intensivo.
- Backup de PDFs afecta comprobantes.

## 15. PDFs y storage

Inventario:

- Presupuesto: `treatment_service.py`.
- Comprobante: `treatment_service.py`.
- Documento clínico: `clinical_document_service.py`.
- Receta: `prescription_service.py`.

Evidencia de integridad:

- Documentos y recetas guardan `pdf_sha256` y verifican hash al descargar.
- Nombres sanitizados con `_sanitize_filename()`.
- `_storage_path()` valida que el path resuelto permanezca bajo raíz esperada.

Hallazgo crítico:

- `.gitignore` ignora `storage/*`, pero los PDFs están bajo `backend/storage/...`, que aparece no rastreado.
- `backend/storage/clinical_documents/`: 6.8 MB local.
- `backend/storage/prescriptions/`: 2.3 MB local.
- `scripts/production/backup_dentia.sh` respalda solo PostgreSQL (`pg_dump | gzip`) y **no incluye storage**.

Clasificación: **P0 para piloto real con documentos/PDFs**.

## 16. Backup y rollback

### Backup

Script: `scripts/production/backup_dentia.sh`

Qué respalda:

- PostgreSQL completo vía `pg_dump`.

Qué no respalda:

- `storage/`.
- PDFs clínicos.
- Recetas.
- Comprobantes.
- Logos/firma si viven fuera de DB y dentro de storage.
- Manifest/hashes de archivos.

Retención:

- `DENTIA_BACKUP_RETENTION`, default 30 archivos `.sql.gz`.

Estado: **INSUFICIENTE**.

### Deploy

Script: `scripts/production/deploy_dentia.sh`

Flujo real:

1. Verifica repo limpio.
2. Ejecuta backup obligatorio.
3. `git fetch`.
4. `git pull --ff-only origin master`.
5. Build de imágenes.
6. `docker compose up -d`.
7. `docker exec backend alembic upgrade head`.
8. Health checks backend/frontend/dominio.
9. Registra commit anterior, commit nuevo y backup.

Riesgo:

- Migraciones corren después de levantar contenedores nuevos.

### Rollback

Script: `scripts/production/rollback_dentia.sh`

Qué hace:

- Vuelve código a commit objetivo.
- Build + up.

Qué no hace:

- No ejecuta downgrade.
- No restaura DB.
- No restaura storage.

Estado: **PARCIAL**.

## 17. Zona horaria

Estado general: **ACEPTABLE CON RIESGOS PUNTUALES**

Evidencia positiva:

- Empresa y sede guardan zona horaria: `backend/app/models/company.py`, `backend/app/models/site.py`.
- Agenda usa `ZoneInfo` y fallback `America/Bogota`: `backend/app/services/agenda_service.py`.
- Odontograma y evolución normalizan fechas locales a UTC: `odontogram_service.py`, `clinical_record_service.py`.
- Reportes usan `_local_bounds()` con zona de empresa: `report_service.py`.

Riesgos:

- `followup_service.py` usa `BOGOTA_TZ = ZoneInfo("America/Bogota")`; si K Astudillo opera fuera de Colombia o se habilita Chile, seguimientos requieren revisión.
- `prescription_service.py` y `clinical_document_service.py` usan `date.today()` al duplicar documentos/recetas; no está contextualizado por sede/empresa.
- `treatment_service.py` tiene rangos con `datetime.combine(..., timezone.utc)` para algunos filtros; revisar si reportes/filtrados mensuales deben usar zona local.

## 18. Errores y observabilidad

Estado: **PARCIAL**

Evidencia:

- `health_router.py` existe.
- Scripts locales y producción tienen logs.
- Auditoría cubre eventos relevantes.
- Servicios lanzan errores de negocio específicos.

Riesgos:

- Frontend todavía usa mensajes genéricos en varios lugares: “No fue posible...”.
- No hay sistema centralizado de captura de errores para piloto.
- No hay runbook claro para que Kimberly reporte errores sin enviar datos sensibles.

## 19. Rendimiento

Clasificación: **ACEPTABLE PARA PILOTO CONTROLADO**

Riesgos a vigilar:

- `PatientDetail.tsx` concentra mucha UI y lógica.
- Reportes hacen agregaciones sobre módulos grandes; aceptable para volumen piloto.
- Odontograma de 32 piezas + Dental Inspector ya tiene scripts de caracterización, pero debe probarse con pacientes con mucho historial.
- PDFs se generan sin cola; aceptable para piloto bajo, no para carga alta.

## 20. Seguridad clínica y legal

Bloqueante para piloto controlado:

- Backup completo PostgreSQL + storage.
- Validación multiempresa con datos A/B.
- Confirmar firma gráfica y textos institucionales de K Astudillo.

Bloqueante para comercialización abierta:

- Consentimientos informados.
- Términos y privacidad.
- Política de retención de historia clínica.
- Prueba formal de restauración.
- Exportación de datos.
- Gestión legal de medicamentos controlados si se ofrece.

Post-MVP:

- Acceso del paciente.
- IA.
- WhatsApp.
- Analítica avanzada.

## 21. Bloqueantes P0–P3

### P0 — No iniciar piloto sin resolver

1. Backup no restaurable completamente porque falta `storage/`.
2. Cambios C017G.1/C017G.2 sin commit/push/deploy.
3. Prueba multiempresa A/B no ejecutada formalmente en esta auditoría.
4. Validación real de K Astudillo pendiente: roles, sedes, odontólogo, firma, branding.

### P1 — Corregir durante preparación

1. Orden de deploy: migraciones después de `up -d`.
2. Scripts locales pueden dejar discrepancia entre PID files y puertos.
3. Anulación documental/recetas está en local, pero debe confirmarse tras commit/deploy.
4. `.gitignore` no cubre explícitamente `backend/storage/`; riesgo de PDFs no rastreados.
5. Fechas de duplicación de documentos/recetas usan `date.today()`, no zona local.

### P2 — Puede esperar durante piloto

1. Mensajes de error genéricos.
2. Fricción visual menor en pantallas densas.
3. Mejoras de rendimiento preventivas.
4. Refinamientos de reportes.

### P3 — Post-MVP

1. IA.
2. Inventario.
3. Laboratorio.
4. WhatsApp.
5. Analítica avanzada.

## 22. Validaciones técnicas ejecutadas

```text
python3 -m compileall backend/app -> OK
npm --prefix frontend run lint -> OK
npm --prefix frontend run build -> OK
node frontend/scripts/clinical-commercial-characterization-tests.mjs -> OK
node frontend/scripts/dental-inspector-tests.mjs -> OK
node frontend/scripts/classic-orientation-tests.mjs -> OK
backend/.venv/bin/alembic current -> 20260724_0022 (head)
backend/.venv/bin/alembic check -> No new upgrade operations detected
git diff --check -> OK
```

`./scripts/local/status_dentia.sh` mostró:

- Backend/frontend reportados como inactivos por PID files.
- Puertos 8001/3001 ocupados por procesos locales.
- Alembic no se imprimió en esa corrida del script aunque `alembic current` directo sí funcionó.

## 23. Recomendación final

**LISTO CON CONDICIONES.**

Dentia puede pasar a piloto real controlado con K Astudillo únicamente si antes se completa:

1. Commit/push/deploy de C017G.1, C017G.2 y fix de recetas.
2. Backup completo PostgreSQL + storage.
3. Prueba de restauración o al menos ensayo local de restore.
4. Checklist de K Astudillo completado.
5. Pruebas multiempresa/permisos con datos A/B.

No declarar “LISTO PARA PILOTO” hasta cerrar los P0.
