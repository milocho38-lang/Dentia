# C019A.5 — Reporte de pruebas

Estado: automatización implementada; validación manual requerida antes de aprobar.

## Cobertura automatizada

- Packet adulto multipágina, hash y watermark de prueba.
- Packet de menor/adulto responsable con relación humana.
- Carga PDF multipágina y JPEG; detección por contenido.
- Orden, eliminación, conteo esperado y seis confirmaciones.
- Consolidación y hash del PDF final.
- Inmutabilidad y bloqueo de overwrite.
- Cambio electrónico a papel, revocación de acceso/OTP/QR.
- Bloqueo de aceptación electrónica posterior.
- PDF/imagen inválidos e incompletos.
- Aislamiento tenant A/B y denegación a `PLATFORM_ADMIN`.
- Regresión del consentimiento electrónico existente.
- Contrato frontend del flujo de cinco pasos.

## Comandos

```bash
./scripts/local/test_dentia_security.sh --full
node frontend/scripts/consent-paper-tests.mjs
npm --prefix frontend run lint
npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/dentia-pycache backend/.venv/bin/python -m compileall backend/app
backend/.venv/bin/pip check
git diff --check
```

La reversibilidad de `20260801_0030` debe validarse exclusivamente contra `dentia_test`, nunca contra una base operativa.
