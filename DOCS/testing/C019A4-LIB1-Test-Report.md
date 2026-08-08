# C019A4-LIB1 — Reporte de pruebas

## Validaciones ejecutadas

| Validación | Resultado | Observación |
|------------|-----------|-------------|
| `python3 -m compileall -q backend/app` | OK | Backend compila correctamente. |
| `.venv/bin/python -m app.scripts.consent_library validate --source-pdf local_inputs/consent_library/CONSENTIMIENTOS_PROPUESTOS.pdf` | OK | Paquete canónico validado: 35 documentos, PDF fuente local verificado con SHA-256 correcto. |
| `.venv/bin/python -m app.scripts.consent_library dry-run/import/import/dry-run` | OK | Importación real PostgreSQL: 35 documentos y 70 versiones; reimportación sin duplicados. |
| `.venv/bin/python scripts/consent_library_package_tests.py` | OK | 35 documentos, 70 variantes, variables seguras y documentos especiales separados. |
| `pytest backend/tests/administration/test_consent_library_package.py` | OK | 11 pruebas DB-backed contra PostgreSQL aislado: fragmentos fuente, diffs, checklist, filtros, permisos, aprobación controlada, instalación, clonación, multiempresa, hash mismatch y rollback de paquete inválido. |
| `scripts/local/test_dentia_security.sh --full` | OK | 101 pruebas DB-backed, hardening piloto y 14 pruebas de fechas clínicas pasaron en entorno aislado. |
| `npm --prefix frontend run lint` | OK | Sin warnings ni errores ESLint. |
| `npm --prefix frontend run build` | OK | Build Next.js exitoso. |
| `docker compose config` con variables locales dummy | OK | Compose resuelve correctamente sin usar `.env.production`. |
| `alembic upgrade 20260801_0026 -> 20260801_0027 -> downgrade 20260801_0026 -> upgrade 20260801_0027` | OK | Ciclo real en PostgreSQL aislado; downgrade elimina objetos 0027 y conserva datos previos. |
| `alembic current/check` | OK | `20260801_0027 (head)` sin drift. |
| `bash -n` scripts `.sh` | OK | Sintaxis shell validada. |
| `git diff --check` | OK | Sin espacios conflictivos. |

## Casos cubiertos

- Inventario fuente: 35 documentos base.
- Variantes país/idioma: 70 versiones CO/CL.
- Fuente: SHA-256 `5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c`.
- PDF fuente: `local_inputs/consent_library/CONSENTIMIENTOS_PROPUESTOS.pdf`, 39 páginas, no versionado.
- Variables: solo catálogo Dentia permitido.
- Normalización: referencias institucionales fuente reemplazadas por variables seguras.
- Documentos especiales: rechazos, indicaciones, certificados, exenciones y aprobaciones no quedan como consentimiento común.
- Frontend: biblioteca visible solo para usuarios con permiso `consent.library.read`; instalar/clonar respeta permisos específicos.
- Seguridad: métricas C018R.4 actualizadas a 240 rutas privadas totales, 0 pendientes, 76 mutaciones críticas DB-backed y 6 descargas DB-backed.

## Resultado

C019A4-LIB1 queda validado localmente contra PostgreSQL aislado para revisión controlada. No se ejecutó deploy ni se tocó VPS.


## Estado de equivalencia VERIFY1

La fuente original se registra como aprobada para CO/CL; la versión normalizada queda en `PENDING_EQUIVALENCE_REVIEW` hasta revisión humana de equivalencia. No se afirma aprobación jurídica/clínica automática por la normalización.

## Estado de equivalencia REVIEW2

- Método de extracción fuente: Apple PDFKit vía Swift local, sin OCR repetitivo.
- Artefactos generados:
  - `DOCS/product/C019A4-LIB1-Source-Fragments.json`
  - `DOCS/product/C019A4-LIB1-Human-Equivalence-Review.md`
  - `DOCS/product/C019A4-LIB1-Human-Equivalence-Review.html`
  - `DOCS/product/C019A4-LIB1-Normalization-Equivalence-Checklist.md`
- Conteos: 35 fragmentos fuente, 35 documentos y 70 variantes CO/CL.
- Flujo de aprobación: una variante ficticia puede pasar a `APPROVED` únicamente con checklist completo y permiso `consent.library.manage`; una variante pendiente queda bloqueada para instalación oficial exacta.
- Reimportación: preserva aprobaciones humanas existentes para no devolver una versión aprobada a estado pendiente.
- Confirmación de seguridad: el PDF fuente local continúa ignorado por Git mediante `.git/info/exclude`.
