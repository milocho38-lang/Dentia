# C019A.5 — Firma en papel y digitalización

Después de la revisión profesional, Dentia permite elegir firma electrónica o firma manuscrita. Ambos métodos parten exactamente del mismo contenido clínico congelado y producen evidencias diferentes.

## Flujo papel

1. Preparar e imprimir el packet identificado por Dentia.
2. Registrar que el paciente o adulto responsable firmó el original físico.
3. Cargar PDF, JPEG o PNG de todas las páginas.
4. Revisar miniaturas, orden y cantidad; eliminar o volver a cargar antes de sellar.
5. Confirmar las seis verificaciones humanas y finalizar la copia digital.

La UI diferencia “Pendiente de firma electrónica”, “Firmado electrónicamente”, “Firmado en papel — pendiente de digitalización” y “Firmado en papel — copia digitalizada”.

El packet para menor identifica al paciente y al **adulto responsable**, su relación humana y documento. Solo muestra “Representante legal” cuando esa fue la relación seleccionada; no usa “tutor legal” como denominación genérica.

Los documentos con `SPECIAL_WORKFLOW` o `NO_PATIENT_SIGNATURE` continúan bloqueados. Los documentos pendientes de equivalencia o generados en local/test conservan `DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO`.

> El documento físico firmado continúa bajo custodia de la clínica. Dentia almacena una copia digitalizada y su evidencia técnica.

No se define en este ticket un periodo legal universal de conservación ni se envía automáticamente la copia digitalizada por correo.
