# Dentia — Runbook de pruebas de seguridad C018R.4

Fecha: 2026-07-29.

## Comandos oficiales

Caracterización + registro de rutas:

```bash
./scripts/local/test_dentia_security.sh --quick
```

DB-backed sobre PostgreSQL aislado:

```bash
./scripts/local/test_dentia_security.sh --db
```

DB-backed con coverage y métricas de riesgo:

```bash
./scripts/local/test_dentia_security.sh --coverage
```

Suite completa:

```bash
./scripts/local/test_dentia_security.sh --full
```

Mantener la DB para depuración:

```bash
./scripts/local/test_dentia_security.sh --db --keep-db
```

## Infraestructura

La suite DB-backed usa:

```text
docker-compose.test.yml
```

Valores esperados:

```text
Compose project: dentia-test
Container: dentia-test-db
Database: dentia_test
User: dentia_test
Port: 127.0.0.1:55432
```

## Dependencias

```bash
backend/.venv/bin/pip install -r backend/requirements-test.txt
```

Versiones validadas:

```text
FastAPI 0.115.6
Starlette 0.41.3
HTTPX 0.27.2
Pytest 8.3.4
```

## Resultado esperado

`--quick`:

```text
Ran 16 tests
OK
pending: 0
downloads: 5
downloads_db_backed: 5
critical_mutations: 50
critical_mutations_db_backed: 50
```

`--db`:

```text
45 passed
```

`--coverage`:

```text
45 passed
coverage total aproximado: 51%
```

## Guardrails anti-producción

La suite falla si detecta:

- `APP_ENV` distinto de `test`;
- ausencia de `DENTIA_TEST_DATABASE_CONFIRMATION`;
- base sin `test`;
- base llamada `dentia`;
- host no local;
- dominios productivos;
- nombres Compose productivos;
- `DATABASE_URL` con `prod`, `production`, `dentiapro.com` u `/opt/apps/dentia`.

Prueba manual del guardrail:

```bash
env DATABASE_URL=postgresql://example-production.invalid/dentia ./scripts/local/test_dentia_security.sh --quick
```

Debe fallar con rechazo explícito.

## Registro de rutas

Archivos:

```text
backend/tests/route_security_registry.py
backend/scripts/route_security_metrics.py
```

El registro falla si:

- aparece ruta privada nueva sin clasificación;
- una ruta crítica queda `PENDING`;
- una descarga no tiene DB-backed;
- una mutación crítica no tiene DB-backed;
- una ruta `NOT_APPLICABLE` no tiene justificación.

## Limpieza

El script elimina contenedor, red y volumen al terminar. Si una ejecución se interrumpe:

```bash
docker compose -f docker-compose.test.yml -p dentia-test down -v
```

No usar contra Compose productivo.

## CI

Workflow:

```text
.github/workflows/security-tests.yml
```

Ejecuta:

- Alembic sobre PostgreSQL 17 de servicio;
- caracterización;
- métricas de rutas;
- DB-backed;
- coverage en terminal.
