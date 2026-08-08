# C019A.4 — Reporte de pruebas de aceptación

Estado: implementación local pendiente de revisión jurídica y validación clínica.

## Cobertura automatizada añadida

- adulto actuando en nombre propio;
- requisitos derivados de sesión OTP verificada;
- declaraciones sin valor `accepted` precargado;
- firma PNG y nombre;
- transición `PENDING_SIGNATURE → SIGNED`;
- PDF descargable y SHA-256;
- idempotencia por clave;
- revocación del enlace original;
- inmutabilidad frente a anulación;
- tenant A/B;
- secretaría sin evidencia sensible, con descarga y reenvío;
- frontend de seis etapas y canvas sin upload.
- conjuntos CO/es-CO y CL/es-CL sin fallback;
- draft bloqueado en producción y documento de prueba marcado;
- conjunto aprobado de prueba sin marca en entorno autorizado;
- PDF multipágina con marca en todas las páginas;
- identidad y mayoría de edad desde snapshot sellado;
- cumpleaños 18, menor, fecha ausente y futura;
- cambio posterior de nombre/fecha maestra sin alterar snapshot;
- cambio de correo después del OTP bloqueado;
- fallos inyectados en PDF, firma, manifiesto, hash, persistencia y commit;
- limpieza de staging/final, retry y reconciliación de huérfano;
- correo posterior al commit y fallo SMTP sin rollback.

Última ejecución REVIEW1: 78 pruebas DB-backed aprobadas, 236 rutas y 0 pendientes. Las pruebas no constituyen revisión jurídica.
