# Validación local de aceptación de consentimientos

Uso exclusivo con pacientes ficticios. No usar `.env.production` ni datos clínicos reales.

## Activación temporal

Desde la raíz del repositorio:

```bash
./scripts/local/start_dentia_mailbox.sh
CONSENT_ACCEPTANCE_ENABLED=true APP_ENV=local ./scripts/local/start_dentia.sh --mailbox --open
./scripts/local/status_dentia.sh
./scripts/local/status_dentia_mailbox.sh
```

La variable se aplica únicamente al proceso iniciado y no se escribe en ningún `.env`. El frontend no puede habilitarla. Incluso con `CONSENT_ACCEPTANCE_ENABLED=true`, `APP_ENV=production` permanece bloqueado por backend.

## Reglas de prueba

- Usar exclusivamente empresa, profesional y paciente ficticios.
- Verificar que portal, resumen, correo y cada página PDF muestren `DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO`.
- Consultar el correo únicamente en Mailpit local.
- No copiar enlaces, OTP, firma o PDF a servicios externos.

## Cierre y limpieza

```bash
./scripts/local/stop_dentia.sh
./scripts/local/stop_dentia_mailbox.sh
```

Los artefactos se almacenan bajo `backend/storage/consents/{empresa_id}/{instance_id}/`. Para eliminarlos, identificar primero la empresa e instancia ficticias y borrar únicamente ese directorio concreto. No ejecutar limpiezas globales ni borrar artefactos referenciados por una base que se conservará.
