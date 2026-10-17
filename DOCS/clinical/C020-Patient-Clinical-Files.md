# C020 — Archivos clínicos por paciente

Estado: implementación local inicial, pendiente de aceptación integrada.

## Alcance

Implementa CU016 y CU017 para cargar, clasificar, listar, descargar y retirar de la vista activa radiografías, exámenes, fotografías y documentos. Es un repositorio de adjuntos y no sustituye los documentos clínicos narrativos ni los consentimientos.

## Decisiones

- Storage local privado, configurable con `CLINICAL_FILE_STORAGE_DIR`; 25 MB por defecto, configurable con `CLINICAL_FILE_MAX_BYTES`.
- Claves físicas opacas bajo empresa y paciente; el nombre original sólo se conserva como metadato seguro.
- Validación de firma y estructura de PDF, JPEG, PNG y WebP, sin confiar en extensión o `Content-Type` del cliente. DOCX y DICOM quedan restringidos hasta incorporar validadores específicos y límites seguros.
- Esta validación rechaza archivos truncados y límites de imágenes descomprimidas, pero no sustituye análisis antimalware.
- Descarga exclusivamente autenticada por backend, con permiso y filtro de empresa, verificación SHA-256 y `no-store`.
- Los archivos se desactivan con motivo y auditoría; no se eliminan físicamente.
- Cada carga usa una clave idempotente por empresa; tras una interrupción el cliente reconcilia la lista antes de sugerir reintento.
- La huella idempotente incluye contenido, nombre, clasificación, descripción y relaciones. Reutilizar la clave con otro payload produce conflicto.
- Antes de promover bytes se registra y audita un intento `PENDING`. Un bloqueo advisory por empresa + clave arbitra solicitudes concurrentes. La ruta física única se deriva sólo de esa identidad opaca, no de paciente, tipo o MIME. Un reintento idéntico recupera `PENDING`; los payloads distintos reciben conflicto antes de tocar el archivo. Nunca se ejecuta limpieza amplia o por comodines.
- El temporal también es determinístico (`<id>.uploading`) y sólo se manipula bajo el mismo lock. Si hay caída entre escritura y promoción, el retry valida tamaño y SHA-256 contra el registro `PENDING` antes de promoverlo.
- La migración entrega permisos a administrador, odontólogo administrador y odontólogo. No se habilita para secretaría de forma implícita; esa decisión debe tomarse en la matriz de roles de cada clínica.

## Fuera de alcance

Visor DICOM, PACS, OCR, servicios externos, versionado de binarios, borrado físico, despliegue y migración productiva.

## Aceptación pendiente

Ejecutar la migración `20261017_0050` y pruebas API multiempresa contra una base PostgreSQL de prueba aislada, además de revisión visible de carga correcta, rechazo por tipo/tamaño, doble clic, cancelación y navegación durante carga.
