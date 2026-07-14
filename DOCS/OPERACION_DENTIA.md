# Operación Dentia

Guía corta para operar Dentia en local y en el VPS sin recordar comandos largos.

No guardar secretos en estos scripts. Si necesitas personalizar rutas o puertos, copia:

```bash
cp scripts/dentia.env.example scripts/dentia.env
```

`scripts/dentia.env` está ignorado por Git.

## Local Mac

Desde cualquier carpeta dentro del proyecto puedes usar los wrappers de raíz:

```bash
./start.sh
./status.sh
./stop.sh
```

### Arrancar

```bash
./start.sh
```

Hace lo siguiente:

- verifica Python, `.venv`, Node, npm y `node_modules`;
- verifica que los puertos 8000 y 3000 estén libres;
- no mata procesos desconocidos;
- aplica migraciones con Alembic;
- inicia backend y frontend en background;
- guarda PID en `.run/`;
- guarda logs en `.run/logs/`.

URLs:

- Backend docs: <http://127.0.0.1:8000/docs>
- Frontend: <http://localhost:3000>

Para abrir navegador en macOS:

```bash
./start.sh --open
```

### Estado

```bash
./status.sh
```

Muestra:

- backend/frontend activo o inactivo;
- PID y puerto;
- propietario de puertos si existe;
- versión Alembic;
- rama Git;
- último commit;
- si el working tree está limpio o sucio.

### Logs

```bash
./scripts/local/logs_dentia.sh backend
./scripts/local/logs_dentia.sh frontend
./scripts/local/logs_dentia.sh all
```

### Detener

```bash
./stop.sh
```

Solo detiene procesos cuyos PID fueron creados por `start_dentia.sh`.
No usa `pkill`, `killall`, ni mata procesos ajenos.

### Actualizar local

```bash
./scripts/local/update_dentia_local.sh
```

Requiere working tree limpio. Ejecuta:

- `git pull --ff-only origin master`;
- `pip install -r backend/requirements.txt`;
- `alembic upgrade head`;
- `npm ci` si existe `package-lock.json`;
- limpia `.next`;
- `npm run build`.

Para actualizar y reiniciar:

```bash
./scripts/local/update_dentia_local.sh --restart
```

## Producción VPS

Ejecutar desde el VPS. Ruta esperada:

```bash
/opt/apps/dentia
```

Contenedores esperados:

- `dentia-frontend`
- `dentia-backend`
- `dentia-db`

### Backup

```bash
./scripts/production/backup_dentia.sh
```

Crea un archivo:

```text
/opt/backups/dentia/dentia_YYYYMMDD_HHMMSS.sql.gz
```

Usa `pg_dump` dentro del contenedor `dentia-db`.
No guarda contraseñas en el script.
No borra backups viejos si el backup actual falla.

### Deploy

```bash
./scripts/production/deploy_dentia.sh
```

Flujo:

1. verifica repo limpio;
2. crea backup obligatorio;
3. `git fetch origin`;
4. `git pull --ff-only origin master`;
5. guarda commit anterior;
6. `docker compose build`;
7. `docker compose up -d`;
8. ejecuta Alembic dentro de `dentia-backend`;
9. valida backend, frontend y dominio.

No usa `docker compose down`.
No elimina volúmenes.

Si falla el build, los contenedores existentes no se bajan.

### Estado producción

```bash
./scripts/production/status_dentia_production.sh
```

Muestra:

- `docker compose ps`;
- uso básico de recursos;
- restart count;
- commit desplegado;
- Alembic current;
- espacio en disco;
- tamaño de backups;
- respuesta HTTP de frontend/backend/dominio.

### Logs producción

```bash
./scripts/production/logs_dentia_production.sh backend
./scripts/production/logs_dentia_production.sh frontend
./scripts/production/logs_dentia_production.sh db
./scripts/production/logs_dentia_production.sh all
```

### Reiniciar servicios Dentia

```bash
./scripts/production/restart_dentia.sh
```

Reinicia solo:

- `dentia-db`
- `dentia-backend`
- `dentia-frontend`

No toca Nginx Proxy Manager.

### Detener producción

```bash
./scripts/production/stop_dentia_production.sh
```

Pide confirmación explícita:

```text
STOP-DENTIA
```

No elimina volúmenes.

### Arrancar producción

```bash
./scripts/production/start_dentia_production.sh
```

Levanta servicios existentes y valida:

- base de datos;
- backend;
- frontend.

### Rollback de código

```bash
./scripts/production/rollback_dentia.sh <commit>
```

Si no pasas commit, intenta usar el commit anterior guardado por el último deploy.

Importante:

- no ejecuta downgrade de Alembic automáticamente;
- las migraciones pueden no ser reversibles sin revisión;
- si necesitas retroceder base de datos, restaura manualmente el backup correspondiente.

## Si falla algo

### Falla build en deploy

- No ejecutar `docker compose down`.
- Revisar logs del build.
- Corregir código o dependencias.
- Reintentar deploy.

### Falla Alembic

- No borrar volumen PostgreSQL.
- Revisar error exacto.
- Revisar migración nueva.
- Si el sistema quedó parcialmente actualizado, evaluar rollback de código y/o restauración de backup.

### Restaurar backup

Procedimiento general, requiere ventana controlada y revisión previa:

```bash
gunzip -c /opt/backups/dentia/dentia_YYYYMMDD_HHMMSS.sql.gz | docker exec -i dentia-db psql -U dentia dentia
```

Antes de restaurar:

- crear backup adicional del estado actual;
- detener tráfico si aplica;
- confirmar que el backup corresponde al punto deseado.

## Comandos que nunca deben ejecutarse a la ligera

No ejecutar en producción:

```bash
docker compose down -v
docker volume rm ...
rm -rf /var/lib/docker/volumes/...
```

No eliminar manualmente el volumen de PostgreSQL.

## Validación recomendada

Local:

- arrancar con todos los servicios apagados;
- revisar URLs;
- ejecutar status;
- revisar logs;
- detener;
- confirmar puertos liberados;
- intentar arrancar con puerto ocupado y verificar que no mata procesos ajenos;
- ejecutar dos veces start y verificar que evita duplicados.

Producción:

- backup no vacío;
- deploy sin `docker compose down`;
- migraciones OK;
- contenedores arriba;
- healthchecks OK;
- logs accesibles;
- restart OK;
- stop no borra volumen;
- start conserva datos;
- rollback probado primero en ambiente temporal si es posible.
