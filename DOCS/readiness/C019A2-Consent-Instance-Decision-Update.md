# C019A.2 — Decisiones y compuerta para C019A.3

## Decisiones incorporadas desde la validación en Chile

- Una cita o tratamiento puede requerir varias instancias independientes.
- Una instancia puede cubrir varios procedimientos de la misma atención.
- Secretaría puede preparar el contexto, pero no confirmar clínicamente.
- El profesional seleccionado debe ver y confirmar el contenido completo.
- Un cambio clínico posterior exige nueva instancia; no se sobrescribe el sello.
- Las instancias se consultan desde el expediente del paciente en escritorio y móvil.

Estas decisiones configuran el flujo, pero no convierten plantillas concretas en obligatorias ni universales.

## Diferencia entre prompt y contrato canónico

El prompt de implementación propuso usar `PENDING_SIGNATURE` como sinónimo de “confirmado por profesional, sin sesión emitida”. C019A.0 define expresamente:

- `READY_FOR_REVIEW`: contenido y participantes validados; versión congelada.
- `PENDING_SIGNATURE`: sesión, enlace o QR ya emitido.

Se conserva C019A.0. C019A.2 termina en `READY_FOR_REVIEW`; el endpoint de transición queda reservado y responde `409`. La decisión deja de estar pendiente para implementación técnica, pero cualquier cambio de significado exige una revisión versionada del contrato maestro.

## Pendientes para Colombia

- Validar terminología operativa con el fundador colombiano.
- Confirmar qué plantillas y asociaciones se configurarán, sin sembrar textos legales.
- Revisar especialidad y registro profesional por usuario frente al modelo institucional actual.
- Validar experiencia móvil y flujo de corrección de datos maestros.

## Reservado para revisión jurídica

- Menores, representación y asentimiento.
- Suficiencia de OTP/firma y canales de entrega.
- Rechazo, revocación, testigo, intérprete y contingencia física.
- Retención documental y paquete probatorio por país.

## Compuerta C019A.3

C019A.3 puede iniciar solo después de revisión funcional y clínica de C019A.2 y deberá garantizar:

1. sesión opaca, tenant-scoped, expirable y resistente a replay;
2. transición atómica desde `READY_FOR_REVIEW`;
3. ningún cambio a contenido, contexto o versión sellados;
4. auditoría sin datos sensibles;
5. revisión de seguridad y cumplimiento antes de exposición pública.

Estado: `IMPLEMENTADO LOCALMENTE — PENDIENTE DE REVISIÓN FUNCIONAL, CLÍNICA Y JURÍDICA`.
