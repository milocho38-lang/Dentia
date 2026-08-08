# C019A4-LIB1 — Biblioteca oficial Dentia de documentos odontológicos

## Resumen

Se creó la biblioteca oficial Dentia como catálogo global separado de las plantillas propias de cada clínica. La biblioteca permite instalar una versión oficial exacta o crear una copia editable bajo responsabilidad de la clínica.

## Alcance implementado

- Inventario de 35 documentos fuente.
- Variantes independientes para Colombia y Chile (`es-CO`, `es-CL`).
- Hash de fuente, hash de texto fuente y hash de contenido normalizado.
- Clasificación por tipo documental, especialidad y alcance de firma.
- Separación entre documentos aptos para consentimiento común adulto y documentos especiales.
- Instalación exacta para documentos publicados y copia editable para revisión clínica.

## Reglas de uso

Una versión oficial exacta conserva contenido, hash, procedencia y estados de revisión. Una copia editable pierde la responsabilidad oficial del contenido y queda marcada como contenido de clínica.

Los documentos especiales no aparecen como consentimiento común en el flujo estándar de firma electrónica de adulto.

## Fuente

- Archivo local no versionado: `CONSENTIMIENTOS_PROPUESTOS.pdf`
- SHA-256: `5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c`
- Páginas analizadas: 39


## Estado de equivalencia VERIFY1

La fuente original se registra como aprobada; la versión normalizada queda en `PENDING_EQUIVALENCE_REVIEW` hasta revisión humana de equivalencia. No se afirma aprobación jurídica/clinica automática por la normalización.
