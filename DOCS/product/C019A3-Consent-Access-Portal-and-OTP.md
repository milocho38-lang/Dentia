# C019A.3 — Acceso, portal y OTP de consentimientos

C019A.3 habilita una sesión revocable para que el paciente revise una instancia sellada. La emisión cambia `READY_FOR_REVIEW` a `PENDING_SIGNATURE`; esto no significa envío, aceptación ni firma.

El profesional emite una URL opaca, ve un QR transitorio y puede revocar o reemitir. El paciente verifica el correo maestro mediante OTP y recibe una sesión corta HttpOnly para una única instancia. El contenido proviene exclusivamente del snapshot C019A.2.

Quedan fuera aceptación, firma gráfica, rechazo formal, PDF final y paquete probatorio; pertenecen a C019A.4 y fases posteriores.

## Integración C019A.4

La sesión OTP verificada es un requisito técnico de C019A.4, no una garantía jurídica. Al completar una aceptación C019A.4, el enlace y las sesiones C019A.3 se revocan; la copia usa un token distinto, hasheado y temporal.

## Integración C019A4-LIB1

El portal de acceso consume instancias generadas desde plantillas tenant. Las plantillas provenientes de biblioteca conservan hash y procedencia en el snapshot de versión, sin exponer el PDF fuente ni contenido no aprobado.
