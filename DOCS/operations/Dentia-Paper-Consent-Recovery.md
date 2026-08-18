# Recuperación de consentimientos en papel

## Principios

- Nunca sobrescribir el packet impreso ni el PDF final sellado.
- Nunca reconstruir texto o firma mediante OCR.
- Verificar SHA-256 antes de entregar una copia.
- Mantener el original físico conforme a la política documental aprobada por la clínica.

## Digitalización incompleta

Mientras el packet esté en `DIGITIZING`, el usuario autorizado puede eliminar, volver a cargar y reordenar páginas. Si la cantidad no coincide con el packet impreso, Dentia impide finalizar.

## Error después de finalizar

No reemplazar archivos en storage ni modificar hashes en base de datos. Preservar el expediente, documentar el incidente y crear una nueva instancia o aplicar el procedimiento administrativo de anulación aprobado. C019A.5 no habilita overwrite.

## Archivo ausente o hash inválido

1. Bloquear descarga/uso clínico de la copia afectada.
2. Conservar registros de auditoría y no borrar metadatos.
3. Restaurar desde backup validado de PostgreSQL y storage clínico como una unidad coherente.
4. Recalcular SHA-256 y compararlo con `final_pdf_sha256`.
5. Registrar el incidente fuera del contenido clínico.

No usar rutas públicas ni copiar artefactos a `frontend/public`.
