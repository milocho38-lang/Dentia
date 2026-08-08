# C019A4-LIB1 — Reporte de normalización

## Fuente

`CONSENTIMIENTOS_PROPUESTOS.pdf` — SHA-256 `5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c`.

## Transformaciones aplicadas

- Sustitución de referencias institucionales de la fuente por `{{company.name}}`, `{{site.name}}`, `{{site.address}}` y variables equivalentes.
- Eliminación de espacios/firma manual redundante cuando se reemplaza por bloque de firma Dentia.
- Conservación de texto clínico fuente y términos locales.
- Separación de documentos especiales para evitar que sean tratados como consentimientos comunes.
- Generación de hashes por variante CO/CL.

## Variables permitidas

Solo se usan variables del catálogo existente de C019A.1: paciente, empresa, sede, profesional, tratamiento, procedimiento y documento.

## Resultado

35 documentos base, 70 variantes por país, 0 imágenes fuente versionadas, 0 datos reales de pacientes incorporados.


## Estado de equivalencia VERIFY1

La fuente original se registra como aprobada; la versión normalizada queda en `PENDING_EQUIVALENCE_REVIEW` hasta revisión humana de equivalencia. No se afirma aprobación jurídica/clinica automática por la normalización.
