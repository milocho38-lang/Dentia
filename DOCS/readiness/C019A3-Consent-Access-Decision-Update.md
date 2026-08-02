# C019A.3 — Decisiones y compuerta para C019A.4

Decisiones provisionales: correo como canal inicial; SMTP configurable con fallo cerrado; adaptador de memoria solo en test; una sesión activa por instancia; reemisión revoca; sesión pública persistida para revocación inmediata.

C019A.3-FIX1 agrega un buzón Mailpit local efímero y un modo LAN explícito para validar QR sin usar credenciales reales. Las aperturas públicas quedan limitadas persistentemente a 30 por minuto por sesión. Next se actualiza a 15.5.22; PostCSS directo a 8.5.18. Los hallazgos transitivos PostCSS/Sharp quedan P2 no alcanzables bajo la configuración actual y documentados en `DOCS/security/C019A3-Npm-Audit-Triage.md`.

C019A.4 no queda autorizada para producción. Requiere validación jurídica de suficiencia del mecanismo, configuración real de correo, revisión clínica y aprobación explícita de aceptación, firma y evidencia.
