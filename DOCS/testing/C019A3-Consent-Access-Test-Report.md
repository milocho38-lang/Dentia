# C019A.3 — Reporte de pruebas

Cobertura DB-backed: emisión desde instancia revisada, transición a pendiente, hash de token y OTP, ausencia de PII antes de verificar, denegación PLATFORM_ADMIN, aislamiento A/B, OTP incorrecto/correcto, cookie pública, snapshot, aclaración y reemisión invalidante.

Frontend: acceso privado, QR transitorio, portal OTP, documento sin acciones de firma y aclaración.

C019A.3-FIX1 añade proveedor SMTP capturado, timeout, destinatario inválido, fallo cerrado en producción, ausencia de OTP en logs, fallo de entrega sin éxito falso, reenvío invalidante y throttling persistente de aperturas. El Compose del buzón se valida y se prueba con un mensaje ficticio sin contenido clínico.

Resultados finales locales: 62 pruebas DB-backed aprobadas; 229 rutas registradas; 0 pendientes; 74/74 mutaciones críticas DB-backed; cinco rutas públicas C019A.3 con cobertura PostgreSQL; `pilot-hardening-tests OK`; 14 pruebas de fechas/hardening aprobadas.
