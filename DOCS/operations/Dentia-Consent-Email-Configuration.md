# Configuración de correo para consentimientos

## Contrato de seguridad

Fuera de `APP_ENV=test`, Dentia usa SMTP y falla de forma cerrada si faltan `SMTP_HOST` o `SMTP_FROM_EMAIL`. El adaptador en memoria no puede activarse en `production`. El correo OTP es genérico: no incluye diagnóstico, procedimiento, identificación, token público, contenido clínico ni PDF.

Variables admitidas: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` y `SMTP_TIMEOUT_SECONDS`. Nunca usar `.env.production` en pruebas ni registrar cuerpo, OTP o destinatario completo.

## Buzón local aislado

`docker-compose.mailbox.yml` ejecuta `axllent/mailpit:v1.30.0` con:

- proyecto, contenedor y red `dentia-local-mailbox`;
- SMTP `127.0.0.1:1025`;
- UI `http://127.0.0.1:8025`;
- almacenamiento efímero en `tmpfs`;
- sin red, volumen ni credenciales productivas;
- eliminación de mensajes al ejecutar el script de parada.

Los puertos pueden cambiarse mediante `DENTIA_MAILBOX_SMTP_PORT` y `DENTIA_MAILBOX_UI_PORT` en el archivo ignorado `scripts/dentia.env`. La interfaz nunca debe publicarse en `0.0.0.0`.

## Prueba manual local completa

1. Obtenga la IP LAN del Mac conectado a una red privada confiable:

   ```bash
   ipconfig getifaddr en0
   ```

   Si usa otra interfaz, identifique su IP local con `ifconfig`. No use una IP pública.

2. Inicie el buzón y abra su interfaz:

   ```bash
   ./scripts/local/start_dentia_mailbox.sh --open
   ./scripts/local/status_dentia_mailbox.sh
   ```

3. Inicie Dentia habilitando explícitamente SMTP local y acceso LAN del frontend:

   ```bash
   DENTIA_LAN_HOST=192.168.1.50 ./scripts/local/start_dentia.sh --mailbox --lan --open
   ```

   Reemplace `192.168.1.50` por la IP obtenida. `--lan` publica únicamente el frontend; backend, base de datos y buzón permanecen en localhost. El script configura credenciales SMTP ficticias solo en el proceso local y no crea `.env.local`.

4. Use exclusivamente un paciente ficticio con correo como `patient@dentia.local`.
5. Cree la instancia, confirme la revisión profesional y genere el acceso.
6. Confirme que la URL se muestra una sola vez y escanee el QR desde un segundo dispositivo conectado a la misma red confiable.
7. Antes del OTP, confirme que no aparecen nombre, documento, procedimiento ni diagnóstico.
8. Pulse **Enviar código**.
9. Abra `http://127.0.0.1:8025`, seleccione el mensaje y copie el código. No consulte la bandeja mediante logs o endpoints de Dentia.
10. Verifique el código en el dispositivo y compruebe el snapshot sellado.
11. Solicite una aclaración, atiéndala en Dentia, reemita y compruebe que el enlace anterior falla.
12. Revoque el acceso nuevo y confirme que deja de funcionar. Anule la instancia y compruebe la invalidación.
13. Confirme que no existe firma, aceptación ni PDF firmado.
14. Detenga Dentia y elimine el buzón con sus mensajes:

   ```bash
   ./scripts/local/stop_dentia.sh
   ./scripts/local/stop_dentia_mailbox.sh
   ```

## Ayuda y diagnóstico

```bash
./scripts/local/start_dentia_mailbox.sh --help
./scripts/local/status_dentia_mailbox.sh --help
./scripts/local/stop_dentia_mailbox.sh --help
./scripts/local/start_dentia.sh --help
```

No se implementó ningún endpoint Dentia para leer la bandeja o revelar el OTP. En tests, `get_test_email_outbox()` sigue siendo una fixture interna disponible únicamente con `APP_ENV=test`.
