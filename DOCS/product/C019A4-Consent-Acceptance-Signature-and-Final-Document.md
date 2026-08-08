# C019A.4 — Aceptación, firma capturada y documento final

Estado: **TECHNICALLY IMPLEMENTED — PRODUCTION BLOCKED**.

Implementación técnica provisional para un paciente adulto que actúa en nombre propio, con correo y OTP verificado. No afirma ni garantiza validez jurídica. El flujo conserva una única fuente clínica: la instancia sellada de C019A.2.

## Flujo incluido

Revisión → diez declaraciones jurisdiccionales no preseleccionadas → actuación propia y nombre → firma PNG generada por canvas → confirmación final → aceptación `COMPLETED` → instancia `SIGNED` → PDF y manifiesto inmutables → descarga temporal y entrega por correo.

`SIGNED` no puede editarse, anularse, reabrirse ni reemitir acceso. El fallo de PDF/storage impide `SIGNED`; el fallo de correo no revierte la aceptación.

## Exclusiones

Menores, representantes, testigos, intérpretes, múltiples firmantes, rechazo formal, revocación posterior, biometría, certificados, sello de tiempo externo y firma profesional en el portal permanecen fuera de alcance.

## Compuerta

`CONSENT_ACCEPTANCE_ENABLED` es `false` por defecto y el backend bloquea el flujo siempre que `APP_ENV=production`, aunque se intente activar la variable.

## Jurisdicción provisional

Los conjuntos `CO/es-CO` y `CL/es-CL` tienen código, versión, estado jurídico y SHA-256 independientes. Ambos están en `DRAFT_LEGAL_REVIEW`; no existe fallback entre países. País y locale provienen de `context_snapshot.document`, incluido en el sello de la instancia. Una aceptación congela el conjunto exacto y no cambia si el catálogo evoluciona.

Mientras el conjunto sea draft, portal, resumen, correo, manifiesto y todas las páginas del PDF muestran: **DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO**.

## Identidad

Nombre, documento y fecha de nacimiento provienen del snapshot sellado. La mayoría de edad se calcula en la fecha local de aceptación usando la zona horaria de la sede. Una fecha ausente, futura o inválida bloquea el flujo. El correo vivo solo puede utilizarse si conserva la misma máscara y huella HMAC del destinatario verificado por OTP.
