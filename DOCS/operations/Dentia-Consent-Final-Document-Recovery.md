# Recuperación de documentos finales de consentimiento

Estado: procedimiento local preliminar; no ejecutar en producción sin aprobación.

1. Restaurar PostgreSQL y el storage clínico del mismo punto de backup.
2. Verificar que cada `consentimiento_documentos_finales.storage_key` permanezca bajo `consents/{empresa_id}/{instance_id}/final/`.
3. Recalcular SHA-256 de PDF, firma y manifiesto y compararlo con la base y el manifiesto.
4. Confirmar que una instancia `SIGNED` tenga aceptación `COMPLETED`, PDF, firma y manifiesto.
5. Si falta un artefacto, no regenerarlo desde datos actuales ni sustituirlo; aislar el caso y restaurar desde otro backup.
6. No exponer storage directamente ni copiar tokens, OTP o contenido a logs.
7. Revisar directorios `.staging-*`: solo pueden corresponder a una operación interrumpida y nunca deben descargarse.
8. Si existe `final/` sin fila en `consentimiento_documentos_finales`, aislarlo como huérfano; el retry controlado lo reconcilia antes de generar el paquete definitivo.
9. No marcar una instancia como `SIGNED` manualmente. La transición exige firma, manifiesto y PDF verificados.

PostgreSQL y filesystem no forman una transacción ACID. La recuperación se basa en staging, promoción por directorio, compensación y reconciliación. La restauración debe incluir verificación semántica C018R.3. No se define todavía retención o destrucción legal por país.
