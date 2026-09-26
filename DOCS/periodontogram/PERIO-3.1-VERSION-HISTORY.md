# PERIO-3.1 — Historial de versiones del periodontograma

## Alcance

La historia principal continúa mostrando controles periodontales independientes por fecha. Dentro de cada control, cuando existe más de una versión, la UI permite consultar las correcciones históricas del mismo examen.

## Contrato de lectura

- La versión actual conserva el editor y su lifecycle habitual.
- Las versiones anteriores se reconstruyen exclusivamente desde el `snapshot` inmutable ya entregado por `GET /api/periodontograms/{exam_id}`.
- La consulta histórica no escribe auditoría, no cambia `updated_at`, `row_version` ni `current_version_id`.
- El hash mostrado y su estado de integridad corresponden a la versión histórica seleccionada.
- El aislamiento tenant del endpoint de detalle protege conjuntamente el examen y todos sus snapshots; no existe un lookup independiente por `version_id`.

## UX

Cuando hay varias versiones se muestra un selector que diferencia la versión actual de las finalizadas anteriores. La vista histórica presenta una advertencia de solo lectura, fecha de finalización, profesional responsable, versión reemplazante y motivo de corrección. Guardar, finalizar y corregir no están disponibles hasta regresar a la versión actual.

No se añadió comparación entre versiones, PDF, gráfico avanzado ni historial longitudinal entre exámenes.
