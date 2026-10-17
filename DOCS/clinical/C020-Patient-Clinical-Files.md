# C020 — Archivos clínicos por paciente

Estado: implementación local inicial, pendiente de aceptación integrada.

## Alcance

Implementa CU016 y CU017 para cargar, clasificar, listar, descargar y retirar de la vista activa radiografías, exámenes, fotografías y documentos. Es un repositorio de adjuntos y no sustituye los documentos clínicos narrativos ni los consentimientos.

## Decisiones

- Storage local privado, configurable con `CLINICAL_FILE_STORAGE_DIR`; 25 MB por defecto, configurable con `CLINICAL_FILE_MAX_BYTES`.
- Claves físicas opacas bajo empresa y paciente; el nombre original sólo se conserva como metadato seguro.
- Validación por firma real de PDF, JPEG, PNG, WebP, DOCX y DICOM, sin confiar en extensión o `Content-Type` del cliente.
- Descarga exclusivamente autenticada por backend, con permiso y filtro de empresa, verificación SHA-256 y `no-store`.
- Los archivos se desactivan con motivo y auditoría; no se eliminan físicamente.
- La migración entrega permisos a administrador, odontólogo administrador y odontólogo. No se habilita para secretaría de forma implícita; esa decisión debe tomarse en la matriz de roles de cada clínica.

## Fuera de alcance

Visor DICOM, PACS, OCR, servicios externos, versionado de binarios, borrado físico, despliegue y migración productiva.

## Aceptación pendiente

Ejecutar la migración `20261017_0050` y pruebas API multiempresa contra una base PostgreSQL de prueba aislada, además de revisión visible de carga correcta, rechazo por tipo/tamaño, doble clic, cancelación y navegación durante carga.
