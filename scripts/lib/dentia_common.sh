#!/usr/bin/env bash
set -Eeuo pipefail

dentia_script_dir() {
  local source_path="${BASH_SOURCE[0]}"
  while [ -L "$source_path" ]; do
    local dir
    dir="$(cd -P "$(dirname "$source_path")" >/dev/null 2>&1 && pwd)"
    source_path="$(readlink "$source_path")"
    [[ "$source_path" != /* ]] && source_path="$dir/$source_path"
  done
  cd -P "$(dirname "$source_path")" >/dev/null 2>&1 && pwd
}

DENTIA_COMMON_DIR="$(dentia_script_dir)"
DENTIA_SCRIPTS_DIR="$(cd "$DENTIA_COMMON_DIR/.." >/dev/null 2>&1 && pwd)"
DENTIA_REPO_ROOT="$(cd "$DENTIA_SCRIPTS_DIR/.." >/dev/null 2>&1 && pwd)"

if [ -f "$DENTIA_SCRIPTS_DIR/dentia.env" ]; then
  # shellcheck source=/dev/null
  source "$DENTIA_SCRIPTS_DIR/dentia.env"
fi

DENTIA_PROJECT_DIR="${DENTIA_PROJECT_DIR:-$DENTIA_REPO_ROOT}"
DENTIA_PRODUCTION_DIR="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
DENTIA_BACKUP_DIR="${DENTIA_BACKUP_DIR:-/opt/backups/dentia}"
DENTIA_BACKUP_RETENTION="${DENTIA_BACKUP_RETENTION:-30}"
DENTIA_FRONTEND_PORT="${DENTIA_FRONTEND_PORT:-3000}"
DENTIA_BACKEND_PORT="${DENTIA_BACKEND_PORT:-8000}"
DENTIA_FRONTEND_URL="${DENTIA_FRONTEND_URL:-http://localhost:${DENTIA_FRONTEND_PORT}}"
DENTIA_BACKEND_HEALTH_URL="${DENTIA_BACKEND_HEALTH_URL:-http://127.0.0.1:${DENTIA_BACKEND_PORT}/health}"
DENTIA_DOMAIN_URL="${DENTIA_DOMAIN_URL:-https://dentiapro.com}"
DENTIA_PRODUCTION_FRONTEND_URL="${DENTIA_PRODUCTION_FRONTEND_URL:-http://127.0.0.1:3001}"
DENTIA_PRODUCTION_BACKEND_HEALTH_URL="${DENTIA_PRODUCTION_BACKEND_HEALTH_URL:-http://127.0.0.1:8001/health}"
DENTIA_FRONTEND_CONTAINER="${DENTIA_FRONTEND_CONTAINER:-dentia-frontend}"
DENTIA_BACKEND_CONTAINER="${DENTIA_BACKEND_CONTAINER:-dentia-backend}"
DENTIA_DB_CONTAINER="${DENTIA_DB_CONTAINER:-dentia-db}"
DENTIA_DB_NAME="${DENTIA_DB_NAME:-dentia}"
DENTIA_DB_USER="${DENTIA_DB_USER:-dentia}"

dentia_info() {
  printf '[dentia] %s\n' "$*"
}

dentia_warn() {
  printf '[dentia][WARN] %s\n' "$*" >&2
}

dentia_fail() {
  printf '[dentia][ERROR] %s\n' "$*" >&2
  exit 1
}

dentia_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || dentia_fail "Required command not found: $1"
}

dentia_compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    dentia_fail "docker compose is not available."
  fi
}

dentia_port_owner() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  else
    dentia_warn "lsof is not available; cannot inspect port $port."
  fi
}

dentia_pid_alive() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1
}

dentia_wait_http() {
  local url="$1"
  local attempts="${2:-30}"
  local sleep_seconds="${3:-2}"
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_seconds"
  done
  return 1
}

dentia_git_summary() {
  git rev-parse --abbrev-ref HEAD 2>/dev/null || true
  git rev-parse --short HEAD 2>/dev/null || true
}
