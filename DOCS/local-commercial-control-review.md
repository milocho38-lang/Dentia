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
