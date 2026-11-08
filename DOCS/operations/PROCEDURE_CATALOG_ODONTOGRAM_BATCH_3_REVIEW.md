# Revisión local: lote 3 de odontograma (13 filas)

Estado: borrador local, desconectado de onboarding, backfill, CLI y producción. No publicar ni activar.

## Fuente y alcance

- Excel definitivo de Kimberly, SHA-256 `1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df`, hoja literal `prestaciones `.
- Filas: 6, 231, 260, 261, 305, 308, 309, 310, 480, 481, 493, 517 y 518.
- Los nombres, alcances y precios CLP se conservan literalmente. COP es fijo, preparado una vez con tasa 3.291243 y redondeo a 1.000; no hay conversión en ejecución.
- Coronas e incrustaciones: círculo alrededor de la pieza, rojo al planificar y azul al firmar, en ambas vistas. Implante individual: símbolo rojo al planificar y azul al firmar.
- Las filas 260 y 261 preservan dentición temporal (`PRIMARY`). No se crea ni cierra un diagnóstico.

## Garantías del borrador

- Inserción idempotente con `ON CONFLICT DO NOTHING`; una colisión conserva el registro y precio de la clínica.
- La planificación se guarda en un evento `PLANNED_PROCEDURE_ADDED` separado, vinculado al procedimiento. La finalización crea un borrador realizado y la firma compensa solo su PLAN.
- Cancelar o eliminar compensa únicamente el PLAN propio y conserva el evento en historia. Editar anatomía/catálogo o usar la ruta abreviada `mark-done` se rechaza para estos procedimientos.
- Replay de creación valida empresa, tratamiento, paciente, catálogo y la identidad normalizada completa del payload antes de devolver un resultado; una clave histórica sin identidad sellada falla cerrada.
- El downgrade de 0054 es deliberadamente aditivo/fail-closed: una base sin datos del lote puede volver y re-subir; con `PLANNED_RESULT` o vínculos históricos rechaza el downgrade y no elimina historia.

## Checkpoint anterior recuperable

Antes de modificar archivos compartidos se guardó el bloque 20 en
`/Users/camilo/Documents/Codex/2026-11-02/task/checkpoints/dentia-batch20-20261108T0315Z`.
El patch rastreado tiene SHA-256 `4a0ba3493d7fda399588cab48bf27f7fd97d0f28b16af396a281f95ea8ca82b2`, el tar de archivos nuevos `3efd747cc9cd81fa7441b46bcfa1345aac1f1dd7981ae2af51e19d79bbff12e8` y el manifiesto de evidencia previo `ec33ae47c69c5ac5a3b9f247c0a129bf389ee7a3929e33bfb086d4701f9ad5d6`.
El inventario completo y sus hashes están dentro del checkpoint; no contiene `.env`, credenciales, dependencias ni datos reales.

## Límites

- Este lote no está conectado a cargas reales y sus flags permanecen apagados.
- Las capturas del playground solo validan el render de fixtures sintéticos; no sustituyen un recorrido completo de UI clínica.
- Las 42 filas claras restantes del inventario de 76 no forman parte de este checkpoint.
