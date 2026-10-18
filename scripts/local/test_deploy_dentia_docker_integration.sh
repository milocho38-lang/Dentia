#!/usr/bin/env bash
set -Eeuo pipefail

SCENARIO="${1:-success}"
case "$SCENARIO" in
  success|pre_failure|post_failure_recovery|next_release_rollback) ;;
  *) printf 'usage: %s [success|pre_failure|post_failure_recovery|next_release_rollback]\n' "$0" >&2; exit 2 ;;
esac

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1 && pwd)"
SOURCE_SHA="$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
OLD_SHA="da88346d97583a0d11a50644d118e05593f7e6b3"
INITIAL_REVISION="20261012_0049"
if [ "$SCENARIO" = next_release_rollback ]; then
  OLD_SHA="40a76d6d028bd22356194fcec9fdcb9882f727f1"
  INITIAL_REVISION="20261017_0050"
fi
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
EVIDENCE_DIR="${DENTIA_INTEGRATION_EVIDENCE_DIR:-}"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

export_evidence() {
  local outcome="$1" revision="unavailable" evidence_file patients="unavailable" clinical_files="unavailable"
  local storage_inventory="$EVIDENCE_DIR/docker-${SCENARIO}-${TARGET_SHA:-unknown}-storage.sha256"
  [ -n "$EVIDENCE_DIR" ] || return 0
  mkdir -p "$EVIDENCE_DIR"
  chmod 700 "$EVIDENCE_DIR"
  if docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
    revision="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version' 2>/dev/null || printf unavailable)"
    patients="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM pacientes' 2>/dev/null || printf unavailable)"
    clinical_files="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT CASE WHEN to_regclass('public.archivos_clinicos') IS NULL THEN 0 ELSE (SELECT count(*) FROM archivos_clinicos) END" 2>/dev/null || printf unavailable)"
  fi
  evidence_file="$EVIDENCE_DIR/docker-${SCENARIO}-${TARGET_SHA:-unknown}.txt"
  umask 077
  {
    printf 'scenario=%s\n' "$SCENARIO"
    printf 'outcome=%s\n' "$outcome"
    printf 'source_base_sha=%s\n' "$OLD_SHA"
    printf 'source_worktree_sha=%s\n' "$SOURCE_SHA"
    printf 'target_sha=%s\n' "${TARGET_SHA:-unknown}"
    printf 'alembic_revision=%s\n' "$revision"
    printf 'patients=%s\n' "$patients"
    printf 'clinical_files=%s\n' "$clinical_files"
    for container in "$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$WEBSITE_CONTAINER"; do
      if docker inspect "$container" >/dev/null 2>&1; then
        printf 'container=%s image_id=%s revision=%s running=%s\n' "$container" \
          "$(docker inspect -f '{{.Image}}' "$container")" \
          "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$container")" \
          "$(docker inspect -f '{{.State.Running}}' "$container")"
      fi
    done
  } >"$evidence_file"
  if docker inspect "$BACKEND_CONTAINER" >/dev/null 2>&1; then
    docker exec "$BACKEND_CONTAINER" sh -c \
      'if [ -d /app/storage/clinical_files ]; then find /app/storage/clinical_files -type f -exec sha256sum {} \; | sort; fi' \
      >"$storage_inventory"
    printf 'storage_inventory_sha256=%s\n' "$(dentia_sha256 "$storage_inventory" | awk '{print $1}')" >>"$evidence_file"
  fi
  chmod 600 "$evidence_file" "$storage_inventory" 2>/dev/null || true
}

completed_backup_path() {
  local manifest
  manifest="$(find "$BACKUPS" -mindepth 2 -maxdepth 2 -type f -name manifest.json -print -quit)"
  [ -n "$manifest" ]
  dirname "$manifest"
}

cleanup() {
  if [ -d "$ROOT" ]; then
    if docker inspect "$BACKEND_CONTAINER" >/dev/null 2>&1; then
      # Root-owned bind-mount entries are expected on Linux. Remove only this
      # disposable harness storage from inside its owning container so host
      # cleanup does not need widened permissions. Restart a stopped harness
      # container if necessary and include hidden entries in the cleanup.
      if ! docker inspect -f '{{.State.Running}}' "$BACKEND_CONTAINER" 2>/dev/null | grep -qx true; then
        docker start "$BACKEND_CONTAINER" >/dev/null 2>&1 || true
      fi
      docker exec "$BACKEND_CONTAINER" find /app/storage -mindepth 1 -delete >/dev/null 2>&1 || true
    fi
    DENTIA_BACKEND_ENV_FILE="$ROOT/.env.production" \
      docker compose --env-file "$ROOT/.env.production" -f "$ROOT/docker-compose.yml" \
      -p "$PROJECT" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  for repository in "$PROJECT-dentia-backend" "$PROJECT-dentia-frontend" "$PROJECT-dentia-website"; do
    docker image rm "$repository:latest" >/dev/null 2>&1 || true
    if [ -n "${TARGET_SHA:-}" ]; then
      docker image rm "$repository:$TARGET_SHA" >/dev/null 2>&1 || true
    fi
    docker image rm "$repository:$OLD_SHA" >/dev/null 2>&1 || true
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
cp "$SOURCE_ROOT/scripts/production/rollback_dentia.sh" "$ROOT/scripts/production/rollback_dentia.sh"
git -C "$ROOT" config user.name "Dentia Integration"
git -C "$ROOT" config user.email "integration@dentia.invalid"
git -C "$ROOT" add docker-compose.yml scripts/lib/dentia_common.sh scripts/production/deploy_dentia.sh scripts/production/rollback_dentia.sh
if ! git -C "$ROOT" diff --cached --quiet; then
  GIT_AUTHOR_DATE=2026-10-07T00:00:00Z GIT_COMMITTER_DATE=2026-10-07T00:00:00Z \
    git -C "$ROOT" commit -m "integration target" >/dev/null
fi
TARGET_SHA="$(git -C "$ROOT" rev-parse HEAD)"
# GitHub Actions checks pull requests out at a detached merge commit. Create the
# harness branch explicitly so the deployment simulation behaves the same from
# branch and detached-HEAD source checkouts.
git -C "$ROOT" checkout -B master "$TARGET_SHA" >/dev/null
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
CLINICAL_FILE_STORAGE_DIR=/app/storage/clinical_files
CLINICAL_FILE_MAX_BYTES=26214400
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

compose() (
  # Compose gives exported shell variables precedence over --env-file. Load the
  # synthetic production environment in a subshell so CI job variables (for
  # example its localhost DATABASE_URL) cannot leak into this isolated stack.
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/.env.production"
  set +a
  docker compose --env-file "$ROOT/.env.production" -f "$ROOT/docker-compose.yml" -p "$PROJECT" "$@"
)

cd "$ROOT"
DENTIA_BUILD_REVISION="$OLD_SHA" compose build
compose up -d dentia-db
for _ in $(seq 1 60); do
  compose exec -T dentia-db pg_isready -U dentia_integration -d dentia_integration >/dev/null 2>&1 && break
  sleep 1
done
compose run --rm --no-deps dentia-backend alembic -c alembic.ini upgrade 20261012_0049
printf 'SyntheticPassword!42\nSyntheticPassword!42\n' | compose run --rm -T --no-deps dentia-backend \
  python -m app.cli.bootstrap --company-name "Synthetic Clinic" --company-slug synthetic-clinic \
  --site-name "Synthetic Site" --admin-name "Synthetic Admin" --admin-username synthetic-admin \
  --admin-email synthetic@example.invalid
if [ "$INITIAL_REVISION" != 20261012_0049 ]; then
  # Reproduce the real production history: tenant roles existed before 0050,
  # so the migration grants the new clinical-file permissions to those roles.
  compose run --rm --no-deps dentia-backend alembic -c alembic.ini upgrade "$INITIAL_REVISION"
fi
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U dentia_integration -d dentia_integration -c \
  "INSERT INTO pacientes (id, empresa_id, nombres, apellidos, celular, celular_normalizado, texto_busqueda) SELECT '00000000-0000-4000-8000-000000000123', id, 'Paciente', 'Sintético', '3000000000', '3000000000', 'paciente sintetico' FROM empresas ORDER BY created_at LIMIT 1;" >/dev/null
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U dentia_integration -d dentia_integration -c \
  "INSERT INTO roles (id, empresa_id, code, nombre, descripcion, is_system, is_active, created_at, updated_at) SELECT '00000000-0000-4000-8000-000000000124', id, 'CUSTOM_REVIEW', 'Rol sintético', 'No debe recibir permisos clínicos implícitos', false, true, now(), now() FROM empresas ORDER BY created_at LIMIT 1;" >/dev/null
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
docker image tag "$OLD_BACKEND_ID" "$PROJECT-dentia-backend:$OLD_SHA"
docker image tag "$OLD_FRONTEND_ID" "$PROJECT-dentia-frontend:$OLD_SHA"
docker image tag "$OLD_WEBSITE_ID" "$PROJECT-dentia-website:$OLD_SHA"
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
DENTIA_EXPECTED_PRE_DEPLOY_REVISION="$INITIAL_REVISION" \
DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER="dentia_integration" \
DENTIA_DB_NAME="dentia_integration" DENTIA_BACKEND_CONTAINER="$BACKEND_CONTAINER" \
DENTIA_FRONTEND_CONTAINER="$FRONTEND_CONTAINER" DENTIA_WEBSITE_CONTAINER="$WEBSITE_CONTAINER" \
DENTIA_PRODUCTION_BACKEND_HEALTH_URL="$RUN_HEALTH_URL" \
DENTIA_PRODUCTION_FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT" \
DENTIA_PRODUCTION_WEBSITE_URL="http://127.0.0.1:$WEBSITE_PORT" \
  "$ROOT/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" || DEPLOY_STATUS=$?

if [ "$SCENARIO" = pre_failure ]; then
  [ "$DEPLOY_STATUS" -ne 0 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261012_0049 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name = 'username'")" = 1 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'platform_commercial_accounts'")" = 0 ]
  [ "$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")" = "$OLD_BACKEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")" = "$OLD_FRONTEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")" = "$OLD_WEBSITE_ID" ]
  [ ! -e "$ROOT/.run/maintenance_active" ]
  [ ! -e "$ROOT/backend/storage/.dentia-maintenance" ]
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null
  curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null
  curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null
  printf 'docker_integration_pre_failure_recovered old_images_exact db=20261012_0049\n'
  export_evidence passed
  exit 0
fi

if [ "$SCENARIO" = post_failure_recovery ]; then
  [ "$DEPLOY_STATUS" -ne 0 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
  for container in "$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$WEBSITE_CONTAINER"; do
    [ "$(docker inspect -f '{{.State.Running}}' "$container")" = false ]
  done
  [ -f "$ROOT/.run/maintenance_active" ]
  [ -f "$ROOT/backend/storage/.dentia-maintenance" ]
  BACKUP_PATH="$(completed_backup_path)"
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
  printf 'docker_integration_post_failure_fail_closed_and_recovered db=20261017_0050 backup=%s\n' "$BACKUP_PATH"
  export_evidence passed
  exit 0
fi

[ "$DEPLOY_STATUS" -eq 0 ]

[ "$(git rev-parse HEAD)" = "$TARGET_SHA" ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM pacientes')" = 1 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM permisos WHERE code LIKE 'clinical_files.%' AND is_active")" = 3 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM rol_permisos rp JOIN permisos p ON p.id=rp.permiso_id WHERE rp.rol_id='00000000-0000-4000-8000-000000000124' AND p.code LIKE 'clinical_files.%' AND rp.is_active")" = 0 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM pg_trigger WHERE tgname='trg_archivos_clinicos_scope' AND NOT tgisinternal")" = 1 ]
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

mkdir -p "$HARNESS/symlink-storage"
ln -s /tmp/escaped-clinical-files "$HARNESS/symlink-storage/clinical_files"
SYMLINK_STORAGE_STATUS=0
docker run --rm --env-file "$ROOT/.env.production" \
  -v "$HARNESS/symlink-storage:/app/storage" \
  --entrypoint python "$PROJECT-dentia-backend:$TARGET_SHA" -c \
  'from app.services.clinical_file_service import _root; _root()' >/dev/null 2>&1 || SYMLINK_STORAGE_STATUS=$?
[ "$SYMLINK_STORAGE_STATUS" -ne 0 ]
printf 'CLINICAL_RUNTIME_SYMLINK_GUARD_OK status=%s\n' "$SYMLINK_STORAGE_STATUS"

# The previous application must remain operable against the additive 0050 schema;
# this is the supported code-only rollback path.
docker run --rm --network "${PROJECT}_dentia-network" --env-file "$ROOT/.env.production" \
  --entrypoint python "$OLD_BACKEND_ID" -c \
  "from sqlalchemy import text; from app.database.session import SessionLocal; s=SessionLocal(); assert s.scalar(text('SELECT count(*) FROM pacientes')) == 1; s.close(); print('OLD_CODE_ON_0050_OK')"

# Exercise multipart requests through the same frontend proxy used by browsers.
# An 11 MiB valid PDF must pass the historical 10 MiB boundary, while a 26 MiB
# payload must reach the backend and be rejected by the configured 25 MiB limit.
LOGIN_RESPONSE="$(curl -fsS -X POST "http://127.0.0.1:$FRONTEND_PORT/api/auth/login" \
  -H 'Content-Type: application/json' \
  --data '{"identifier":"synthetic-admin","password":"SyntheticPassword!42"}')"
ACCESS_TOKEN="$(printf '%s' "$LOGIN_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
PROXY_PDF="$HARNESS/proxy-upload.pdf"
docker exec "$BACKEND_CONTAINER" python -c \
  'import pymupdf; d=pymupdf.open(); d.new_page(); d.save("/tmp/proxy-upload.pdf")'
docker cp "$BACKEND_CONTAINER:/tmp/proxy-upload.pdf" "$PROXY_PDF" >/dev/null
truncate -s 11534336 "$PROXY_PDF"
PROXY_UPLOAD_STATUS="$(curl -sS -o "$HARNESS/proxy-upload-response.json" -w '%{http_code}' \
  -X POST "http://127.0.0.1:$FRONTEND_PORT/api/patients/00000000-0000-4000-8000-000000000123/clinical-files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F 'tipo=DOCUMENT' -F 'categoria=GENERAL' \
  -F 'idempotency_key=00000000-0000-4000-8000-000000000127' \
  -F "archivo=@$PROXY_PDF;type=application/pdf")"
[ "$PROXY_UPLOAD_STATUS" = 201 ]
PROXY_CLINICAL_KEY="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc \
  "SELECT ruta_archivo FROM archivos_clinicos WHERE idempotency_key='00000000-0000-4000-8000-000000000127'")"
[ -n "$PROXY_CLINICAL_KEY" ]
[ "$(docker exec "$BACKEND_CONTAINER" stat -c '%a' "/app/storage/clinical_files/$PROXY_CLINICAL_KEY")" = 600 ]
[ "$(docker exec "$BACKEND_CONTAINER" stat -c '%a' "$(dirname "/app/storage/clinical_files/$PROXY_CLINICAL_KEY")")" = 700 ]
! docker exec --user 65534 "$BACKEND_CONTAINER" test -r "/app/storage/clinical_files/$PROXY_CLINICAL_KEY"
! docker exec --user 65534 "$BACKEND_CONTAINER" test -w "/app/storage/clinical_files/$PROXY_CLINICAL_KEY"
truncate -s 27262976 "$PROXY_PDF"
PROXY_OVERSIZE_STATUS="$(curl -sS -o "$HARNESS/proxy-oversize-response.json" -w '%{http_code}' \
  -X POST "http://127.0.0.1:$FRONTEND_PORT/api/patients/00000000-0000-4000-8000-000000000123/clinical-files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F 'tipo=DOCUMENT' -F 'categoria=GENERAL' \
  -F 'idempotency_key=00000000-0000-4000-8000-000000000128' \
  -F "archivo=@$PROXY_PDF;type=application/pdf")"
[ "$PROXY_OVERSIZE_STATUS" = 413 ]
printf 'CLINICAL_PROXY_LIMIT_OK accepted_bytes=11534336 rejected_bytes=27262976\n'

# Three simultaneous 11 MiB browser uploads exercise bounded proxy buffering.
# The 192 MiB delta ceiling allows the configured 27 MiB request allowance per
# upload plus more than 100 MiB of runtime/multipart overhead, while still
# catching an unbounded multi-copy regression.
truncate -s 11534336 "$PROXY_PDF"
PROXY_BASELINE_RSS_KIB="$(docker exec "$FRONTEND_CONTAINER" awk '/VmRSS:/ {print $2}' /proc/1/status)"
PROXY_PEAK_RSS_KIB="$PROXY_BASELINE_RSS_KIB"
for index in 1 2 3; do
  curl -sS -o "$HARNESS/proxy-concurrent-$index-response.json" -w '%{http_code}' \
    -X POST "http://127.0.0.1:$FRONTEND_PORT/api/patients/00000000-0000-4000-8000-000000000123/clinical-files" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F 'tipo=DOCUMENT' -F 'categoria=GENERAL' \
    -F "idempotency_key=00000000-0000-4000-8000-00000000013$((index + 4))" \
    -F "archivo=@$PROXY_PDF;type=application/pdf" \
    >"$HARNESS/proxy-concurrent-$index-status" &
  eval "PROXY_PID_$index=$!"
done
while kill -0 "$PROXY_PID_1" 2>/dev/null || kill -0 "$PROXY_PID_2" 2>/dev/null || kill -0 "$PROXY_PID_3" 2>/dev/null; do
  CURRENT_RSS_KIB="$(docker exec "$FRONTEND_CONTAINER" awk '/VmRSS:/ {print $2}' /proc/1/status)"
  [ "$CURRENT_RSS_KIB" -le "$PROXY_PEAK_RSS_KIB" ] || PROXY_PEAK_RSS_KIB="$CURRENT_RSS_KIB"
  sleep 0.05
done
wait "$PROXY_PID_1"; wait "$PROXY_PID_2"; wait "$PROXY_PID_3"
for index in 1 2 3; do [ "$(cat "$HARNESS/proxy-concurrent-$index-status")" = 201 ]; done
PROXY_RSS_DELTA_KIB=$((PROXY_PEAK_RSS_KIB - PROXY_BASELINE_RSS_KIB))
[ "$PROXY_RSS_DELTA_KIB" -le 196608 ]
printf 'CLINICAL_PROXY_CONCURRENCY_OK uploads=3 bytes_each=11534336 baseline_rss_kib=%s peak_rss_kib=%s delta_rss_kib=%s threshold_kib=196608\n' \
  "$PROXY_BASELINE_RSS_KIB" "$PROXY_PEAK_RSS_KIB" "$PROXY_RSS_DELTA_KIB"

# Add one synthetic private binary after the migration, then prove that a new
# complete backup inventories and restores its bytes and SHA-256.
# Preserve the real root-owned bind-mount permissions seen on Linux runners.
# Fixtures are written through the owning backend container rather than by the
# non-root host runner.
! docker exec --user 65534 "$BACKEND_CONTAINER" test -w /app/storage/clinical_files
write_clinical_fixture() {
  local relative_path="$1" contents="$2"
  printf '%s\n' "$contents" | docker exec -i "$BACKEND_CONTAINER" sh -c \
    'umask 077; target="$1"; mkdir -p "${target%/*}"; chmod 700 "${target%/*}"; cat >"$target"; chmod 600 "$target"' sh \
    "/app/storage/clinical_files/$relative_path"
}
clinical_fixture_sha256() {
  docker exec "$BACKEND_CONTAINER" sha256sum "/app/storage/clinical_files/$1" | awk '{print $1}'
}
clinical_fixture_size() {
  docker exec "$BACKEND_CONTAINER" wc -c "/app/storage/clinical_files/$1" | awk '{print $1}'
}
clinical_fixture_matches() {
  docker exec "$BACKEND_CONTAINER" cat "/app/storage/clinical_files/$1" | cmp - "$2"
}
CLINICAL_ID="00000000-0000-4000-8000-000000000125"
COMPANY_ID="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT id FROM empresas ORDER BY created_at LIMIT 1')"
USER_ID="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT id FROM usuarios ORDER BY created_at LIMIT 1')"
CLINICAL_KEY="company_${COMPANY_ID}/uploads/${CLINICAL_ID}"
write_clinical_fixture "$CLINICAL_KEY" synthetic-clinical-binary-for-backup
CLINICAL_SHA="$(clinical_fixture_sha256 "$CLINICAL_KEY")"
CLINICAL_SIZE="$(clinical_fixture_size "$CLINICAL_KEY")"
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U dentia_integration -d dentia_integration -c \
  "INSERT INTO archivos_clinicos (id,empresa_id,paciente_id,tipo_archivo,categoria,nombre_archivo,ruta_archivo,idempotency_key,request_fingerprint,storage_status,mime_type,tamano_bytes,sha256,fecha_carga,cargado_por_usuario_id,is_active,created_at,updated_at) VALUES ('$CLINICAL_ID','$COMPANY_ID','00000000-0000-4000-8000-000000000123','DOCUMENT','GENERAL','synthetic.pdf','$CLINICAL_KEY','00000000-0000-4000-8000-000000000126',repeat('a',64),'AVAILABLE','application/pdf',$CLINICAL_SIZE,'$CLINICAL_SHA',now(),'$USER_ID',true,now(),now());" >/dev/null
RETIRED_ID="00000000-0000-4000-8000-000000000129"
PENDING_ID="00000000-0000-4000-8000-000000000130"
FAILED_ID="00000000-0000-4000-8000-000000000131"
RETIRED_KEY="company_${COMPANY_ID}/uploads/${RETIRED_ID}"
PENDING_KEY="company_${COMPANY_ID}/uploads/${PENDING_ID}"
write_clinical_fixture "$RETIRED_KEY" synthetic-retired-clinical-binary
write_clinical_fixture "${PENDING_KEY}.uploading" synthetic-interrupted-upload
RETIRED_SHA="$(clinical_fixture_sha256 "$RETIRED_KEY")"
PENDING_SHA="$(clinical_fixture_sha256 "${PENDING_KEY}.uploading")"
RETIRED_SIZE="$(clinical_fixture_size "$RETIRED_KEY")"
PENDING_SIZE="$(clinical_fixture_size "${PENDING_KEY}.uploading")"
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U dentia_integration -d dentia_integration -c \
  "INSERT INTO archivos_clinicos (id,empresa_id,paciente_id,tipo_archivo,categoria,nombre_archivo,ruta_archivo,idempotency_key,request_fingerprint,storage_status,mime_type,tamano_bytes,sha256,fecha_carga,cargado_por_usuario_id,is_active,created_at,updated_at) VALUES
  ('$RETIRED_ID','$COMPANY_ID','00000000-0000-4000-8000-000000000123','DOCUMENT','GENERAL','retired.pdf','$RETIRED_KEY','00000000-0000-4000-8000-000000000132',repeat('b',64),'AVAILABLE','application/pdf',$RETIRED_SIZE,'$RETIRED_SHA',now(),'$USER_ID',false,now(),now()),
  ('$PENDING_ID','$COMPANY_ID','00000000-0000-4000-8000-000000000123','DOCUMENT','GENERAL','pending.pdf','$PENDING_KEY','00000000-0000-4000-8000-000000000133',repeat('c',64),'PENDING','application/pdf',$PENDING_SIZE,'$PENDING_SHA',now(),'$USER_ID',true,now(),now()),
  ('$FAILED_ID','$COMPANY_ID','00000000-0000-4000-8000-000000000123','DOCUMENT','GENERAL','failed.pdf','company_${COMPANY_ID}/uploads/${FAILED_ID}','00000000-0000-4000-8000-000000000134',repeat('d',64),'FAILED','application/pdf',1,repeat('e',64),now(),'$USER_ID',true,now(),now());" >/dev/null
# Production keeps the restrictive modes asserted above. The disposable Linux
# harness now hands only the bind-mount ownership to its host runner so the
# host-side backup inventory and tar can read it without weakening 0700/0600.
docker exec "$BACKEND_CONTAINER" chown -R "$HOST_UID:$HOST_GID" /app/storage
[ "$(docker exec "$BACKEND_CONTAINER" stat -c '%a' "/app/storage/clinical_files/$CLINICAL_KEY")" = 600 ]
[ "$(docker exec "$BACKEND_CONTAINER" stat -c '%a' "$(dirname "/app/storage/clinical_files/$CLINICAL_KEY")")" = 700 ]
DOWNGRADE_STATUS=0
DENTIA_IMAGE_TAG="$TARGET_SHA" compose run --rm -T --no-deps dentia-backend \
  alembic -c alembic.ini downgrade 20261012_0049 \
  >"$HARNESS/downgrade-with-clinical-data.log" 2>&1 || DOWNGRADE_STATUS=$?
[ "$DOWNGRADE_STATUS" -ne 0 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc "SELECT count(*) FROM archivos_clinicos WHERE id='$CLINICAL_ID'")" = 1 ]
printf 'CLINICAL_DOWNGRADE_GUARD_OK revision=20261017_0050 status=%s\n' "$DOWNGRADE_STATUS"
PRE_0050_BACKUP_PATH="$(completed_backup_path)"
PRE_RESTORE_COUNT="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM archivos_clinicos')"
OLD_BACKUP_TARGET_DB="dentia_restore_old_backup_${SUFFIX}"
docker exec "$DB_CONTAINER" createdb -U dentia_integration "$OLD_BACKUP_TARGET_DB"
docker exec "$DB_CONTAINER" pg_dump -Fc --no-owner --no-privileges -U dentia_integration dentia_integration | \
  docker exec -i "$DB_CONTAINER" pg_restore --no-owner --no-privileges -U dentia_integration -d "$OLD_BACKUP_TARGET_DB"
OLD_BACKUP_STATUS=0
DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$PRE_0050_BACKUP_PATH" --temporary \
  --database-name "$OLD_BACKUP_TARGET_DB" --storage-dir "$HARNESS/old-backup-reject-storage" >/dev/null 2>&1 || OLD_BACKUP_STATUS=$?
[ "$OLD_BACKUP_STATUS" -ne 0 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d "$OLD_BACKUP_TARGET_DB" -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d "$OLD_BACKUP_TARGET_DB" -tAc 'SELECT count(*) FROM archivos_clinicos')" = "$PRE_RESTORE_COUNT" ]
[ ! -e "$HARNESS/old-backup-reject-storage" ]
[ "$(clinical_fixture_sha256 "$CLINICAL_KEY")" = "$CLINICAL_SHA" ]
docker exec "$DB_CONTAINER" dropdb -U dentia_integration "$OLD_BACKUP_TARGET_DB"
printf 'CLINICAL_OLD_BACKUP_REJECTED_WITHOUT_MUTATION status=%s\n' "$OLD_BACKUP_STATUS"
POST_BACKUP_PATH="$(DENTIA_PRODUCTION_DIR="$ROOT" DENTIA_BACKUP_DIR="$BACKUPS/post-0050" DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration DENTIA_BACKEND_CONTAINER="$BACKEND_CONTAINER" "$ROOT/scripts/production/backup_dentia.sh" --no-prune | tail -n 1)"
grep -Fq $'clinical_file\t00000000-0000-4000-8000-000000000125' "$POST_BACKUP_PATH/document_inventory.tsv"
grep -Fq $'clinical_file\t00000000-0000-4000-8000-000000000129' "$POST_BACKUP_PATH/document_inventory.tsv"
grep -Fq $'clinical_file\t00000000-0000-4000-8000-000000000130' "$POST_BACKUP_PATH/document_inventory.tsv"
grep -Fq $'clinical_file_temporary\t00000000-0000-4000-8000-000000000130' "$POST_BACKUP_PATH/document_inventory.tsv"
grep -Fq $'clinical_file\t00000000-0000-4000-8000-000000000131' "$POST_BACKUP_PATH/document_inventory.tsv"
docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -c \
  "CREATE TABLE restore_temporary_guard_probe (value text NOT NULL); INSERT INTO restore_temporary_guard_probe VALUES ('preserved');" >/dev/null
PRODUCTION_DB_GUARD_STORAGE="$HARNESS/production-db-guard-storage"
PRODUCTION_DB_GUARD_STATUS=0
DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$POST_BACKUP_PATH" --temporary \
  --database-name dentia_integration --storage-dir "$PRODUCTION_DB_GUARD_STORAGE" >/dev/null 2>&1 || PRODUCTION_DB_GUARD_STATUS=$?
[ "$PRODUCTION_DB_GUARD_STATUS" -ne 0 ]
[ ! -e "$PRODUCTION_DB_GUARD_STORAGE" ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM archivos_clinicos')" = "$PRE_RESTORE_COUNT" ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT value FROM restore_temporary_guard_probe')" = preserved ]
[ "$(clinical_fixture_sha256 "$CLINICAL_KEY")" = "$CLINICAL_SHA" ]

PRODUCTION_STORAGE_GUARD_DB="dentia_restore_production_storage_${SUFFIX}"
PRODUCTION_STORAGE_GUARD_STATUS=0
DENTIA_PRODUCTION_DIR="$ROOT" DENTIA_DB_CONTAINER="$DB_CONTAINER" \
  DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$POST_BACKUP_PATH" --temporary \
  --database-name "$PRODUCTION_STORAGE_GUARD_DB" --storage-dir "$ROOT/backend/storage" >/dev/null 2>&1 || PRODUCTION_STORAGE_GUARD_STATUS=$?
[ "$PRODUCTION_STORAGE_GUARD_STATUS" -ne 0 ]
! docker exec "$DB_CONTAINER" psql -U dentia_integration -d postgres -tAc 'SELECT datname FROM pg_database' | \
  grep -Fqx "$PRODUCTION_STORAGE_GUARD_DB"
[ "$(clinical_fixture_sha256 "$CLINICAL_KEY")" = "$CLINICAL_SHA" ]
printf 'CLINICAL_TEMPORARY_TARGET_GUARDS_OK database_status=%s storage_status=%s\n' \
  "$PRODUCTION_DB_GUARD_STATUS" "$PRODUCTION_STORAGE_GUARD_STATUS"

REAL_DOCKER="$(command -v docker)"
mkdir -p "$HARNESS/failing-docker-bin"
cat >"$HARNESS/failing-docker-bin/docker" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"SELECT datname FROM pg_database;"* ]]; then
  exit 97
fi
exec "$REAL_DOCKER" "\$@"
EOF
chmod +x "$HARNESS/failing-docker-bin/docker"
DB_QUERY_FAILURE_DB="dentia_restore_db_query_failure_${SUFFIX}"
DB_QUERY_FAILURE_STORAGE="$HARNESS/db-query-failure-storage"
DB_QUERY_FAILURE_STATUS=0
PATH="$HARNESS/failing-docker-bin:$PATH" DENTIA_DB_CONTAINER="$DB_CONTAINER" \
  DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$POST_BACKUP_PATH" --temporary \
  --database-name "$DB_QUERY_FAILURE_DB" --storage-dir "$DB_QUERY_FAILURE_STORAGE" >/dev/null 2>&1 || DB_QUERY_FAILURE_STATUS=$?
[ "$DB_QUERY_FAILURE_STATUS" -ne 0 ]
[ ! -e "$DB_QUERY_FAILURE_STORAGE" ]
! docker exec "$DB_CONTAINER" psql -U dentia_integration -d postgres -tAc 'SELECT datname FROM pg_database' | \
  grep -Fqx "$DB_QUERY_FAILURE_DB"
printf 'CLINICAL_DB_EXISTENCE_QUERY_FAIL_CLOSED_OK status=%s\n' "$DB_QUERY_FAILURE_STATUS"
RESTORE_DB="dentia_restore_clinical_${SUFFIX}"
RESTORE_STORAGE="$HARNESS/restored-clinical-storage"
RESTORE_OUTPUT="$(DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$POST_BACKUP_PATH" --temporary \
  --database-name "$RESTORE_DB" --storage-dir "$RESTORE_STORAGE")"
printf '%s\n' "$RESTORE_OUTPUT" | grep -qx 'RESTORE_VALID'
clinical_fixture_matches "$CLINICAL_KEY" "$RESTORE_STORAGE/clinical_files/$CLINICAL_KEY"
clinical_fixture_matches "$RETIRED_KEY" "$RESTORE_STORAGE/clinical_files/$RETIRED_KEY"
clinical_fixture_matches "${PENDING_KEY}.uploading" "$RESTORE_STORAGE/clinical_files/${PENDING_KEY}.uploading"
[ ! -e "$RESTORE_STORAGE/clinical_files/$PENDING_KEY" ]
[ ! -e "$RESTORE_STORAGE/clinical_files/company_${COMPANY_ID}/uploads/${FAILED_ID}" ]
docker exec "$DB_CONTAINER" psql -U dentia_integration -d "$RESTORE_DB" -c \
  "CREATE TABLE restore_preflight_probe (value text NOT NULL); INSERT INTO restore_preflight_probe VALUES ('preserved');" >/dev/null
printf 'corrupted-existing-destination\n' >"$RESTORE_STORAGE/clinical_files/$CLINICAL_KEY"
COLLISION_STATUS=0
DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_DB_USER=dentia_integration DENTIA_DB_NAME=dentia_integration \
  "$ROOT/scripts/production/restore_dentia_backup.sh" --backup "$POST_BACKUP_PATH" --temporary \
  --database-name "$RESTORE_DB" --storage-dir "$RESTORE_STORAGE" >/dev/null 2>&1 || COLLISION_STATUS=$?
[ "$COLLISION_STATUS" -ne 0 ]
grep -Fqx 'corrupted-existing-destination' "$RESTORE_STORAGE/clinical_files/$CLINICAL_KEY"
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d "$RESTORE_DB" -tAc 'SELECT value FROM restore_preflight_probe')" = preserved ]
[ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d "$RESTORE_DB" -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
docker exec "$DB_CONTAINER" dropdb -U dentia_integration --if-exists "$RESTORE_DB" >/dev/null
BACKUP_PATH="$PRE_0050_BACKUP_PATH"
DENTIA_DB_CONTAINER="$DB_CONTAINER" \
  "$ROOT/scripts/production/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null
! tar -tzf "$BACKUPS"/*/storage.tar.gz | grep -q '.dentia-maintenance'

printf 'docker_integration_success target=%s backup=%s\n' "$TARGET_SHA" "$BACKUP_PATH"
if [ "$SCENARIO" = next_release_rollback ]; then
  # Exercise the real production code-only rollback procedure. Migration 0050
  # is additive and intentionally remains applied.
  PRE_ROLLBACK_PATIENTS="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM pacientes')"
  PRE_ROLLBACK_FILES="$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM archivos_clinicos')"
  DENTIA_ENV_FILE="$ROOT/.env.production" DENTIA_PROJECT_DIR="$ROOT" DENTIA_PRODUCTION_DIR="$ROOT" \
  DENTIA_DB_CONTAINER="$DB_CONTAINER" DENTIA_BACKEND_CONTAINER="$BACKEND_CONTAINER" \
  DENTIA_FRONTEND_CONTAINER="$FRONTEND_CONTAINER" DENTIA_WEBSITE_CONTAINER="$WEBSITE_CONTAINER" \
  DENTIA_PRODUCTION_BACKEND_HEALTH_URL="http://127.0.0.1:$BACKEND_PORT/health" \
  DENTIA_PRODUCTION_FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT" \
  DENTIA_PRODUCTION_WEBSITE_URL="http://127.0.0.1:$WEBSITE_PORT" \
    "$ROOT/scripts/production/rollback_dentia.sh" --maintenance --target-sha "$OLD_SHA"
  [ "$(docker inspect -f '{{.Image}}' "$BACKEND_CONTAINER")" = "$OLD_BACKEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$FRONTEND_CONTAINER")" = "$OLD_FRONTEND_ID" ]
  [ "$(docker inspect -f '{{.Image}}' "$WEBSITE_CONTAINER")" = "$OLD_WEBSITE_ID" ]
  for container in "$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$WEBSITE_CONTAINER"; do
    [ "$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$container")" = "$OLD_SHA" ]
  done
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT version_num FROM alembic_version')" = 20261017_0050 ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM pacientes')" = "$PRE_ROLLBACK_PATIENTS" ]
  [ "$(docker exec "$DB_CONTAINER" psql -U dentia_integration -d dentia_integration -tAc 'SELECT count(*) FROM archivos_clinicos')" = "$PRE_ROLLBACK_FILES" ]
  [ "$(clinical_fixture_sha256 "$CLINICAL_KEY")" = "$CLINICAL_SHA" ]
  [ "$(tr -d '[:space:]' <"$ROOT/.run/last_deploy_commit")" = "$OLD_SHA" ]
  [ ! -e "$ROOT/.run/maintenance_active" ]
  [ ! -e "$ROOT/backend/storage/.dentia-maintenance" ]
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null
  curl -fsS "http://127.0.0.1:$FRONTEND_PORT" >/dev/null
  curl -fsS "http://127.0.0.1:$WEBSITE_PORT" >/dev/null
  printf 'NEXT_RELEASE_ROLLBACK_OK sha=%s db=20261017_0050 patients=%s clinical_files=%s\n' \
    "$OLD_SHA" "$PRE_ROLLBACK_PATIENTS" "$PRE_ROLLBACK_FILES"
fi
export_evidence passed
