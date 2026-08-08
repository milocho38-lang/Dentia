# C019A4-LIB1 — Arquitectura de biblioteca e importación

## Decisión principal

La biblioteca oficial se implementa como catálogo global independiente de las plantillas tenant. Esto evita duplicar documentos oficiales en todas las clínicas y conserva una frontera clara entre contenido Dentia y contenido personalizado.

## Modelo funcional

- `consentimiento_biblioteca_documentos`: identidad global del documento, clasificación, procedencia y página fuente.
- `consentimiento_biblioteca_versiones`: variante por país/idioma, contenido normalizado, texto fuente preservado y hashes.
- `consentimiento_biblioteca_instalaciones`: trazabilidad de instalación o clonación por clínica.
- `consentimiento_plantillas`: recibe metadatos de origen cuando se instala o clona una versión.
- `consentimiento_plantilla_versiones`: conserva referencia a la versión fuente y estado de revisión heredado o requerido.

## Instalación

- Instalación exacta: solo para versiones publicadas, adulto auto-firmante y consentimiento informado común.
- Copia editable: permitida para análisis o adaptación; queda bajo responsabilidad de la clínica y requiere revisión propia.

## Importación

El paquete canónico vive en `backend/app/library_data/consents/v1/documents.json`. El importador valida hashes, variables permitidas, país/idioma y duplicados antes de escribir. La importación es idempotente.


## Estado de equivalencia VERIFY1

La fuente original se registra como aprobada; la versión normalizada queda en `PENDING_EQUIVALENCE_REVIEW` hasta revisión humana de equivalencia. No se afirma aprobación jurídica/clinica automática por la normalización.
