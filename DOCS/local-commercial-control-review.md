# Revisión local del control comercial

Esta versión se revisa únicamente con PostgreSQL local y datos ficticios. No usar
credenciales, transferencias ni comprobantes reales.

## Configuración

Crear `backend/.env` local (ignorado por Git) a partir de `backend/.env.example` y
definir, sin guardar secretos en el repositorio:

```text
APP_ENV=local
DATABASE_URL=<postgresql local de revisión>
JWT_SECRET=<secreto local de al menos 32 bytes>
PUBLIC_FRONTEND_URL=http://localhost:13000
```

Configurar puertos aislados en `scripts/dentia.env` (también ignorado por Git):

```text
DENTIA_BACKEND_PORT=18000
DENTIA_FRONTEND_PORT=13000
```

## Abrir y detener

```bash
docker compose -f docker-compose.test.yml up -d dentia-test-db
scripts/local/start_dentia.sh --open
scripts/local/status_dentia.sh
```

Ingresar con un administrador de plataforma ficticio creado localmente. Al terminar:

```bash
scripts/local/stop_dentia.sh
docker compose -f docker-compose.test.yml stop
```

La pantalla está en `/administracion/control-comercial`. Verificar al menos:

- registro pendiente y verificación separada;
- abono insuficiente sin concesión de cobertura;
- descuento anual explícito;
- reintento del mismo envío;
- cancelación y confirmación de reversión;
- bloqueo de cambio de moneda con historial.

## Compatibilidad de migraciones locales

La revisión `20261012_0048` es inmutable. `20261012_0049` admite tanto una base
limpia como una base que ya estaba en la `0048` original. Los pagos heredados
insuficientes vuelven conservadoramente a `PENDING`: se conserva el importe
recibido, la referencia y la fila histórica, pero no se inventa crédito ni
cobertura. La migración añade una conciliación `LEGACY_PARTIAL_REVIEW` con el
déficit y el motivo de la revisión. El administrador puede completar el faltante
como un abono verificado y volver a verificar el movimiento pendiente; en ese
momento el importe recibido original y el saldo a favor completan juntos el
acuerdo. Las claves de idempotencia de
`0048` no incluían la carga canónica; por eso un reintento heredado se trata como
conflicto conservador y debe revisarse manualmente.

El commit local intermedio `2f0a8b7` llegó a reutilizar el identificador `0048`
con un esquema distinto. Solo las bases locales conocidas con datos ficticios
pueden reconstruirse desde cero para salir de ese estado. Para cualquier base
desconocida, detenerse, respaldar e identificar exactamente el esquema y los
datos antes de diseñar una migración especial; nunca borrar ni reconstruirlos
automáticamente.
