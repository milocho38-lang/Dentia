# C019A.4 — Actualización de decisión y compuerta

Veredicto: **TECHNICALLY IMPLEMENTED — PRODUCTION BLOCKED**.

## Decisiones provisionales

- Solo adulto y actuación propia.
- Un firmante paciente.
- Firma gráfica requerida en local/test.
- Conjuntos separados CO/es-CO y CL/es-CL `DRAFT_LEGAL_REVIEW_V1`, con código y hash propios, no aprobados jurídicamente.
- No existe fallback entre países o locales.
- Todo artefacto draft lleva una marca de prueba inequívoca.
- PNG de canvas; no SVG, uploads, trazos biométricos ni metadatos.
- Descarga temporal separada del enlace de firma.
- Correo fallido no revierte firma; PDF/storage fallido sí impide `SIGNED`.

## No habilitar hasta completar

Esta decisión histórica fue sustituida para C019A.6 por la compuerta verificable y el modelo de responsabilidades documentados en [C019 — Preparación productiva de consentimientos](../product/C019-Consent-Production-Readiness.md). El procedimiento técnico fue registrado como revisado; cada clínica debe revisar y adoptar el contenido exacto que publica. Producción permanece bloqueada si falta cualquier requisito técnico, operativo o de revisión tenant.

## Actualización C019A4-LIB1

La aceptación electrónica mantiene alcance adulto auto-firmante. Documentos con representante/apoderado importados por la biblioteca quedan fuera del flujo estándar hasta que exista flujo específico.
