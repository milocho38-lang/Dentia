# C019A.3 — Arquitectura de seguridad del acceso

Se separan cuatro entidades: sesión de acceso, desafío OTP, sesión pública verificada y solicitud de aclaración. Los tokens de URL y cookie se generan con CSPRNG y se guardan como SHA-256; el OTP de seis dígitos se guarda como HMAC-SHA-256 con el secreto de aplicación. Ningún secreto aparece en listados o auditoría.

Valores provisionales configurables: enlace 72 horas, OTP 10 minutos y cinco intentos, reenvío mínimo 60 segundos, tres envíos y sesión pública 30 minutos. Reemitir revoca el canal anterior. Anular la instancia invalida acceso, OTP y sesión pública.

El portal resuelve tenant solo por hash, responde de forma genérica, no muestra PII antes del OTP y usa `no-store`, `noindex`, `DENY` y `no-referrer`. La cookie pública es HttpOnly, SameSite Strict y Secure en producción.
