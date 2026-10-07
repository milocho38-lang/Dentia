#!/usr/bin/env bash
set -Eeuo pipefail

SCENARIO="${1:-success}"
case "$SCENARIO" in
  success|pre_failure|post_failure_recovery) ;;
  *) printf 'usage: %s [success|pre_failure|post_failure_recovery]\n' "$0" >&2; exit 2 ;;
esac

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1 && pwd)"
OLD_SHA="d6ed416fe29426ac2b72301124a940630d627a4b"
HARNESS="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-docker.XXXXXX")"
ROOT="$HARNESS/repo"
BACKUPS="$HARNESS/backups"
SUFFIX="$$"
PROJECT="dentia-integration-$SUFFIX"
DB_CONTAINER="$PROJECT-db"
BACKEND_CONTAINER="$PROJECT-backend"
FRONTEND_CONTAINER="$PROJECT-frontend"
WEBSITE_CONTAINER="$PROJECT-website"
BACKEND_PORT=$((18000 + SUFFIX % 1000))
FRONTEND_PORT=$((28000 + SUFFIX % 1000))
WEBSITE_PORT=$((38000 + SUFFIX % 1000))
ENV_BACKUP_DIR="$BACKUPS"
[ "$SCENARIO" != pre_failure ] || ENV_BACKUP_DIR="/dev/null/dentia-integration-backups"
ENV_HEALTH_URL="http://127.0.0.1:$BACKEND_PORT/health"
[ "$SCENARIO" != post_failure_recovery ] || ENV_HEALTH_URL="http://127.0.0.1:1/health"

cleanup() {
  if [ -d "$ROOT" ]; then
    DENTIA_BACKEND_ENV_FILE="$ROOT/.env.production" \
      docker compose --env-file "$ROOT/.env.production" -f "$ROOT/docker-compose.yml" \
      -p "$PROJECT" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  for repository in "$PROJECT-dentia-backend" "$PROJECT-dentia-frontend" "$PROJECT-dentia-website"; do
    docker image rm "$repository:latest" >/dev/null 2>&1 || true
    if [ -n "${TARGET_SHA:-}" ]; then
      docker image rm "$repository:$TARGET_SHA" >/dev/null 2>&1 || true
    fi
  done
  case "$HARNESS" in
    "${TMPDIR:-/tmp}"/dentia-deploy-docker.*) rm -rf "$HARNESS" ;;
  esac
}
trap cleanup EXIT INT TERM

git clone --no-hardlinks "$SOURCE_ROOT" "$ROOT" >/dev/null
cp "$SOURCE_ROOT/docker-compose.yml" "$ROOT/docker-compose.yml"
cp "$SOURCE_ROOT/scripts/lib/dentia_common.sh" "$ROOT/scripts/lib/dentia_common.sh"
cp "$SOURCE_ROOT/scripts/production/deploy_dentia.sh" "$ROOT/scripts/production/deploy_dentia.sh"
git -C "$ROOT" config user.name "Dentia Integration"
git -C "$ROOT" config user.email "integration@dentia.invalid"
git -C "$ROOT" add docker-compose.yml scripts/lib/dentia_common.sh scripts/production/deploy_dentia.sh
GIT_AUTHOR_DATE=2026-10-07T00:00:00Z GIT_COMMITTER_DATE=2026-10-07T00:00:00Z \
  git -C "$ROOT" commit -m "integration target" >/dev/null
TARGET_SHA="$(git -C "$ROOT" rev-parse HEAD)"
git -C "$ROOT" branch -M master
git -C "$ROOT" remote set-url origin "$ROOT"
git -C "$ROOT" checkout "$OLD_SHA" >/dev/null

cat >"$ROOT/.env.production" <<EOF
APP_ENV=production
APP_DEBUG=false
DEFAULT_TENANT_MAX_ACTIVE_DENTISTS=1
POSTGRES_DB=dentia_integration
POSTGRES_USER=dentia_integration
POSTGRES_PASSWORD=DentiaIntegrationPassword_${SUFFIX}
DATABASE_URL=postgresql+psycopg://dentia_integration:DentiaIntegrationPassword_${SUFFIX}@dentia-db:5432/dentia_integration
JWT_SECRET=DentiaIntegrationJWTSecret_${SUFFIX}_long_enough_for_validation
DENTIA_BACKEND_ENV_FILE=$ROOT/.env.production
BRANDING_STORAGE_DIR=/app/storage/branding
API_PROXY_TARGET=http://dentia-backend:8000
PUBLIC_FRONTEND_URL=https://app.dentiapro.com
NEXT_PUBLIC_SITE_URL=https://dentiapro.com
NEXT_PUBLIC_APP_URL=https://app.dentiapro.com
NEXT_PUBLIC_SITE_INDEXABLE=true
REFRESH_TOKEN_RACE_GRACE_SECONDS=2
CONSENT_ACCEPTANCE_ENABLED=true
CONSENT_PUBLIC_COOKIE_SECURE=true
CONSENT_FINAL_STORAGE_DIR=/app/storage/consents
CONSENT_STORAGE_PERSISTENT=true
CONSENT_PROCEDURE_VERSION=DENTIA_CONSENT_PROCEDURE_V1
CONSENT_OTP_EXPIRE_MINUTES=10
CONSENT_OTP_MAX_ATTEMPTS=5
CONSENT_PUBLIC_SESSION_MINUTES=30
SMTP_HOST=smtp.integration.invalid
SMTP_FROM_EMAIL=integration@dentia.invalid
DEMO_REQUEST_NOTIFICATION_EMAILS=integration@dentia.invalid
COMPOSE_PROJECT_NAME=$PROJECT
DENTIA_DB_CONTAINER=$DB_CONTAINER
DENTIA_BACKEND_CONTAINER=$BACKEND_CONTAINER
DENTIA_FRONTEND_CONTAINER=$FRONTEND_CONTAINER
DENTIA_WEBSITE_CONTAINER=$WEBSITE_CONTAINER
DENTIA_BACKEND_IMAGE_REPOSITORY=$PROJECT-dentia-backend
DENTIA_FRONTEND_IMAGE_REPOSITORY=$PROJECT-dentia-frontend
DENTIA_WEBSITE_IMAGE_REPOSITORY=$PROJECT-dentia-website
DENTIA_BACKEND_BIND=$BACKEND_PORT
DENTIA_FRONTEND_BIND=$FRONTEND_PORT
DENTIA_WEBSITE_BIND=$WEBSITE_PORT
DENTIA_PRODUCTION_BACKEND_HEALTH_URL=$ENV_HEALTH_URL
DENTIA_PRODUCTION_FRONTEND_URL=http://127.0.0.1:$FRONTEND_PORT
DENTIA_PRODUCTION_WEBSITE_URL=http://127.0.0.1:$WEBSITE_PORT
DENTIA_BACKUP_DIR=$ENV_BACKUP_DIR
EOF
chmod 600 "$ROOT/.env.production"
mkdir -p "$ROOT/backend/storage" "$ROOT/.run" "$BACKUPS"

compose() {
  DENTIA_BACKEND_ENV_FILE="$ROOT/.env.production" \
    docker compose --env-file "$ROOT/.env.production" -f "$ROOT/docker-compose.yml" -p "$PROJECT" "$@"
}

cd "$ROOT"
DENTIA_BUILD_REVISION="$OLD_SHA" compose build
compose up -d dentia-db
for _ in $(seq 1 60); do
  compose exec -T dentia-db pg_isready -U dentia_integration -d dentia_integration >/dev/null 2>&1 && break
  sleep 1
done
compose run --rm --no-deps dentia-backend alembic -c alembic.ini upgrade 20260926_0045
printf 'SyntheticPassword!42\nSyntheticPassword!42\n' | compose run --rm -T --no-deps dentia-backend \
  python -m app.cli.bootstrap --company-name "Synthetic Clinic" --company-slug synthetic-clinic \
  --site-name "Synthetic Site" --admin-name "Synthetic Admin" --admin-email synthetic@example.invalid
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U dentia_integration -d dentia_integration -c \
  "INSERT INTO pacientes (id, empresa_id, nombres, apellidos, celular, celular_normalizado, texto_busqueda) SELECT '00000000-0000-4000-8000-000000000123', id, 'Paciente', 'Sintético', '3000000000', '3000000000', 'paciente sintetico' FROM empresas ORDER BY created_at LIMIT 1;" >/dev/null
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM pacientes')" = 1 ]
compose up -d dentia-backend dentia-frontend dentia-website
for _ in $(seq 1 60); do
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1 && \
    curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null 2>&1 && \
    curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null 2>&1 && break
  sleep 2
done

OLD_BACKEND_ID="$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")"
OLD_FRONTEND_ID="$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")"
OLD_WEBSITE_ID="$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")"
printf '%s\n' "$OLD_SHA" >"$ROOT/.run/last_deploy_commit"

git checkout master >/dev/null
RUN_BACKUP_DIR="$BACKUPS"
RUN_HEALTH_URL="http://127.0.0.1:$BACKEND_PORT/health"
if [ "$SCENARIO" = pre_failure ]; then
  RUN_BACKUP_DIR="$ENV_BACKUP_DIR"
elif [ "$SCENARIO" = post_failure_recovery ]; then
  RUN_HEALTH_URL="http://127.0.0.1:1/health"
fi
DEPLOY_STATUS=0
DENTIA_ENV_FILE="$ROOT/.env.production" DENTIA_PROJECT_DIR="$ROOT" DENTIA_PRODUCTION_DIR="$ROOT" \
DENTIA_BACKUP_DIR="$RUN_BACKUP_DIR" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER="dentia_integration" \
DENTIA_DB_NAME="dentia_integration" DENTIA_BACKEND_CONTAINER="$BACKEND_CONTAINER" \
DENTIA_FRONTEND_CONTAINER="$FRONTEND_CONTAINER" DENTIA_WEBSITE_CONTAINER="$WEBSITE_CONTAINER" \
DENTIA_PRODUCTION_BACKEND_HEALTH_URL="$RUN_HEALTH_URL" \
DENTIA_PRODUCTION_FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT" \
DENTIA_PRODUCTION_WEBSITE_URL="http://127.0.0.1:$WEBSITE_PORT" \
  "$ROOT/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" || DEPLOY_STATUS=$?

if [ "$SCENARIO" = pre_failure ]; then
  [ "$DEPLOY_STATUS" -ne 0 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20260926_0045 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name = 'username'")" = 0 ]
  [ "$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")" = "$OLD_BACKEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")" = "$OLD_FRONTEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")" = "$OLD_WEBSITE_ID" ]
  [ ! -e "$ROOT/.run/maintenance_active" ]
  [ ! -e "$ROOT/backend/storage/.dentia-maintenance" ]
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null
  curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null
  curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null
  printf 'docker_integration_pre_failure_recovered old_images_exact db=20260926_0045\n'
  exit 0
fi

if [ "$SCENARIO" = post_failure_recovery ]; then
  [ "$DEPLOY_STATUS" -ne 0 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261006_0047 ]
  for container in "$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$WEBSITE_CONTAINER"; do
    [ "$(docker inspect -f '{{.State.Running}}' "$container")" = false ]
  done
  [ -f "$ROOT/.run/maintenance_active" ]
  [ -f "$ROOT/backend/storage/.dentia-maintenance" ]
  BACKUP_PATH="$(find "$BACKUPS" -mindepth 1 -maxdepth 1 -type d -print -quit)"
  "$ROOT/scripts/production/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM patient_import_sources')" = 0 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM patient_external_references')" = 0 ]
  DENTIA_IMAGE_TAG="$TARGET_SHA" compose up -d --no-deps dentia-backend
  for _ in $(seq 1 60); do
    curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1 && break
    sleep 1
  done
  DENTIA_IMAGE_TAG="$TARGET_SHA" compose up -d --no-deps dentia-frontend dentia-website
  for _ in $(seq 1 60); do
    curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null 2>&1 && \
      curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null 2>&1 && break
    sleep 1
  done
  for container in "$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$WEBSITE_CONTAINER"; do
    [ "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$container")" = "$TARGET_SHA" ]
  done
  MANIFEST_TARGET_IDS="$(python3 - "$BACKUP_PATH/manifest.json" <<'PY'
import json, sys
images = json.load(open(sys.argv[1], encoding="utf-8"))["target_images"]
print("\n".join(images[name] for name in ("backend", "frontend", "website")))
PY
)"
  RUNTIME_TARGET_IDS="$(printf '%s\n' \
    "$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")" \
    "$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")" \
    "$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")")"
  [ "$RUNTIME_TARGET_IDS" = "$MANIFEST_TARGET_IDS" ]
  [ "$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$BACKEND_PORT/")" = 503 ]
  rm -f "$ROOT/.run/maintenance_active" "$ROOT/backend/storage/.dentia-maintenance"
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null
  printf 'docker_integration_post_failure_fail_closed_and_recovered db=20261006_0047 backup=%s\n' "$BACKUP_PATH"
  exit 0
fi

[ "$DEPLOY_STATUS" -eq 0 ]

[ "$(git rev-parse HEAD)" = "$TARGET_SHA" ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261006_0047 ]
[ "$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")" != "$OLD_BACKEND_ID" ]
[ "$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")" != "$OLD_FRONTEND_ID" ]
[ "$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")" != "$OLD_WEBSITE_ID" ]
[ "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$BACKEND_CONTAINER")" = "$TARGET_SHA" ]
[ "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$FRONTEND_CONTAINER")" = "$TARGET_SHA" ]
[ "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$WEBSITE_CONTAINER")" = "$TARGET_SHA" ]
[ ! -e "$ROOT/.run/maintenance_active" ]
[ ! -e "$ROOT/backend/storage/.dentia-maintenance" ]
curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null
curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null
curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null
BACKUP_PATH="$(find "$BACKUPS" -mindepth 1 -maxdepth 1 -type d -print -quit)"
"$ROOT/scripts/production/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null
! tar -tzf "$BACKUPS"/*/storage.tar.gz | grep -q '.dentia-maintenance'

printf 'docker_integration_success target=%s backup=%s\n' "$TARGET_SHA" "$BACKUP_PATH"
