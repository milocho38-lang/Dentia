#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
cd "$ROOT"

dentia_info "Docker Compose services"
dentia_compose ps

printf '\nContainers resource usage:\n'
docker stats --no-stream "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" "$DENTIA_DB_CONTAINER" 2>/dev/null || true

printf '\nRestart count:\n'
docker inspect --format '{{.Name}} RestartCount={{.RestartCount}} State={{.State.Status}}' "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" "$DENTIA_DB_CONTAINER" 2>/dev/null || true

printf '\nGit:\n'
git log -1 --oneline || true

printf '\nAlembic current:\n'
docker exec "$DENTIA_BACKEND_CONTAINER" alembic -c alembic.ini current 2>/dev/null || true

printf '\nPostgreSQL size:\n'
docker exec "$DENTIA_DB_CONTAINER" psql -U "$DENTIA_DB_USER" -d "$DENTIA_DB_NAME" -tAc "SELECT pg_size_pretty(pg_database_size(current_database()));" 2>/dev/null || true

printf '\nStorage:\n'
du -sh "$ROOT/backend/storage" 2>/dev/null || echo "backend/storage not found"
find "$ROOT/backend/storage" -type f 2>/dev/null | wc -l | awk '{print "storage_file_count=" $1}'

printf '\nDisk:\n'
df -h "$ROOT" "$DENTIA_BACKUP_DIR" 2>/dev/null || df -h "$ROOT"

printf '\nDocker volumes:\n'
docker system df -v 2>/dev/null | sed -n '1,80p' || true

printf '\nBackups:\n'
du -sh "$DENTIA_BACKUP_DIR" 2>/dev/null || true
find "$DENTIA_BACKUP_DIR" -maxdepth 1 -type d -name 'dentia_*' 2>/dev/null | wc -l | awk '{print "backup_package_count=" $1}'
latest_backup="$(find "$DENTIA_BACKUP_DIR" -maxdepth 1 -type d -name 'dentia_*' 2>/dev/null | sort -r | head -n 1 || true)"
if [ -n "$latest_backup" ]; then
  echo "latest_backup=$latest_backup"
fi
latest_verified="$(find "$DENTIA_BACKUP_DIR" -maxdepth 2 -type f -name 'verification.txt' 2>/dev/null | sort -r | head -n 1 || true)"
if [ -n "$latest_verified" ]; then
  echo "latest_verified_backup=$(dirname "$latest_verified")"
fi
if [ -f "$ROOT/.run/last_deploy_backup" ]; then
  printf 'last_deploy_backup=%s\n' "$(cat "$ROOT/.run/last_deploy_backup")"
fi

printf '\nHTTP:\n'
curl -fsS --max-time 8 "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" >/dev/null && echo "backend OK $DENTIA_PRODUCTION_BACKEND_HEALTH_URL" || echo "backend FAIL $DENTIA_PRODUCTION_BACKEND_HEALTH_URL"
curl -fsS --max-time 8 "$DENTIA_PRODUCTION_FRONTEND_URL" >/dev/null && echo "frontend OK $DENTIA_PRODUCTION_FRONTEND_URL" || echo "frontend FAIL $DENTIA_PRODUCTION_FRONTEND_URL"
if [ -n "${DENTIA_DOMAIN_URL:-}" ]; then
  curl -fsS --max-time 8 "$DENTIA_DOMAIN_URL" >/dev/null && echo "domain OK $DENTIA_DOMAIN_URL" || echo "domain FAIL $DENTIA_DOMAIN_URL"
fi
