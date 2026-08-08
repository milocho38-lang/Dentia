# C019A.4 — Arquitectura de evidencia y PDF

Estado: **TECHNICALLY IMPLEMENTED — PRODUCTION BLOCKED**.

## Fuente de verdad y consistencia DB/storage

PostgreSQL y filesystem no comparten una transacción ACID; por tanto, Dentia no describe este proceso como una transacción distribuida atómica. La estrategia real es staging, promoción de paquete, compensación y reconciliación en retry:

1. se bloquea la instancia con `FOR UPDATE`;
2. firma, PDF y manifiesto se generan desde snapshots sellados;
3. los tres artefactos se escriben en `.staging-{acceptance_id}` mediante temporales, `fsync` y verificación SHA-256;
4. referencias, aceptación y transición a `SIGNED` se preparan sin commit;
5. el directorio staging completo se promociona por rename a `final`;
6. se vuelven a verificar los tres hashes;
7. se confirma PostgreSQL;
8. cualquier excepción previa al commit ejecuta rollback y elimina staging/final promovido;
9. un retry elimina artefactos definitivos sin referencia DB antes de regenerar;
10. el correo se intenta únicamente después del commit.

Un crash de proceso en la ventana entre promoción y commit puede dejar un paquete sin referencia hasta el siguiente retry o la reconciliación operativa. Nunca se marca `SIGNED` antes de que los tres archivos finales existan y superen verificación.

## Entidades

- `ConsentAcceptance` y declaraciones exactas versionadas.
- `ConsentSignatureArtifact`: PNG de canvas validado, hash, dimensiones y ruta técnica.
- `ConsentEvidenceManifest`: JSON canónico, hash y snapshots congelados sin OTP/token.
- `ConsentFinalDocument`: PDF único, hash, renderer, indicador inmutable y token temporal hasheado.
- `ConsentCopyDelivery`: un registro por intento de entrega.

## Storage

`consents/{empresa_id}/{instance_id}/final/`, con staging hermano temporal. No contiene nombre, documento ni token. Los tres archivos forman parte del storage persistente cubierto por backup/restore C018R.3.

## Seguridad

El token de firma se revoca al completar. La descarga pública usa un token opaco distinto, hasheado, limitado al PDF y con expiración corta. La evidencia completa solo está disponible con permiso clínico específico.

No se implementa HMAC del manifiesto: manejo, rotación y recuperación de claves quedan pendientes.
