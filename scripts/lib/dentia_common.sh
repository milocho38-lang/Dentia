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

DENTIA_ENV_FILE="${DENTIA_ENV_FILE:-$DENTIA_SCRIPTS_DIR/dentia.env}"

# Explicit invocation values take precedence over the optional shared env file.
_DENTIA_FRONTEND_PORT_OVERRIDE="${DENTIA_FRONTEND_PORT-}"
_DENTIA_BACKEND_PORT_OVERRIDE="${DENTIA_BACKEND_PORT-}"

if [ -f "$DENTIA_ENV_FILE" ]; then
  # shellcheck source=/dev/null
  source "$DENTIA_ENV_FILE"
fi

[ -z "$_DENTIA_FRONTEND_PORT_OVERRIDE" ] || DENTIA_FRONTEND_PORT="$_DENTIA_FRONTEND_PORT_OVERRIDE"
[ -z "$_DENTIA_BACKEND_PORT_OVERRIDE" ] || DENTIA_BACKEND_PORT="$_DENTIA_BACKEND_PORT_OVERRIDE"
unset _DENTIA_FRONTEND_PORT_OVERRIDE _DENTIA_BACKEND_PORT_OVERRIDE

DENTIA_PROJECT_DIR="${DENTIA_PROJECT_DIR:-$DENTIA_REPO_ROOT}"
DENTIA_PRODUCTION_DIR="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
DENTIA_BACKUP_DIR="${DENTIA_BACKUP_DIR:-/opt/backups/dentia}"
DENTIA_BACKUP_RETENTION="${DENTIA_BACKUP_RETENTION:-30}"
DENTIA_FRONTEND_PORT="${DENTIA_FRONTEND_PORT:-3000}"
DENTIA_BACKEND_PORT="${DENTIA_BACKEND_PORT:-8000}"
DENTIA_MAILBOX_SMTP_PORT="${DENTIA_MAILBOX_SMTP_PORT:-1025}"
DENTIA_MAILBOX_UI_PORT="${DENTIA_MAILBOX_UI_PORT:-8025}"
DENTIA_FRONTEND_URL="${DENTIA_FRONTEND_URL:-http://localhost:${DENTIA_FRONTEND_PORT}}"
DENTIA_BACKEND_HEALTH_URL="${DENTIA_BACKEND_HEALTH_URL:-http://127.0.0.1:${DENTIA_BACKEND_PORT}/health}"
DENTIA_DOMAIN_URL="${DENTIA_DOMAIN_URL:-https://dentiapro.com}"
DENTIA_PRODUCTION_FRONTEND_URL="${DENTIA_PRODUCTION_FRONTEND_URL:-http://127.0.0.1:3001}"
DENTIA_PRODUCTION_BACKEND_HEALTH_URL="${DENTIA_PRODUCTION_BACKEND_HEALTH_URL:-http://127.0.0.1:8001/health}"
DENTIA_FRONTEND_CONTAINER="${DENTIA_FRONTEND_CONTAINER:-dentia-frontend}"
DENTIA_BACKEND_CONTAINER="${DENTIA_BACKEND_CONTAINER:-dentia-backend}"
DENTIA_DB_CONTAINER="${DENTIA_DB_CONTAINER:-dentia-db}"
DENTIA_FRONTEND_SERVICE="${DENTIA_FRONTEND_SERVICE:-dentia-frontend}"
DENTIA_BACKEND_SERVICE="${DENTIA_BACKEND_SERVICE:-dentia-backend}"
DENTIA_DB_SERVICE="${DENTIA_DB_SERVICE:-dentia-db}"
DENTIA_DB_NAME="${DENTIA_DB_NAME:-dentia}"
DENTIA_DB_USER="${DENTIA_DB_USER:-dentia}"
DENTIA_STORAGE_PATHS="${DENTIA_STORAGE_PATHS:-backend/storage storage}"
DENTIA_BACKEND_STORAGE_HOST_PATH="${DENTIA_BACKEND_STORAGE_HOST_PATH:-backend/storage}"
DENTIA_BACKEND_STORAGE_CONTAINER_PATH="${DENTIA_BACKEND_STORAGE_CONTAINER_PATH:-/app/storage}"

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
    if [ -f "$DENTIA_ENV_FILE" ]; then
      docker compose --env-file "$DENTIA_ENV_FILE" "$@"
    else
      docker compose "$@"
    fi
  elif command -v docker-compose >/dev/null 2>&1; then
    if [ -f "$DENTIA_ENV_FILE" ]; then
      docker-compose --env-file "$DENTIA_ENV_FILE" "$@"
    else
      docker-compose "$@"
    fi
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

dentia_pid_command() {
  local pid="$1"
  ps -p "$pid" -o command= 2>/dev/null || true
}

dentia_pid_matches() {
  local pid="$1"
  local expected="$2"
  local command_line
  command_line="$(dentia_pid_command "$pid")"
  [ -n "$command_line" ] && [[ "$command_line" == *"$expected"* ]]
}

dentia_remove_stale_pid_file() {
  local pid_file="$1"
  if [ ! -f "$pid_file" ]; then
    return 0
  fi
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if ! dentia_pid_alive "$pid"; then
    rm -f "$pid_file"
    return 0
  fi
  return 1
}

dentia_copy_no_clobber() {
  local source="$1"
  local target="$2"
  if [ -e "$target" ]; then
    dentia_fail "Refusing to overwrite existing file: $target"
  fi
  cp "$source" "$target"
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

dentia_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$@"
  else
    dentia_fail "Neither sha256sum nor shasum is available."
  fi
}

dentia_file_size() {
  local path="$1"
  if stat -c '%s' "$path" >/dev/null 2>&1; then
    stat -c '%s' "$path"
  else
    stat -f '%z' "$path"
  fi
}

dentia_dir_size_bytes() {
  local path="$1"
  if [ ! -e "$path" ]; then
    printf '0\n'
    return 0
  fi
  if du -sb "$path" >/dev/null 2>&1; then
    du -sb "$path" | awk '{print $1}'
  else
    du -sk "$path" | awk '{print $1 * 1024}'
  fi
}

dentia_available_bytes() {
  local path="$1"
  if df -Pk "$path" >/dev/null 2>&1; then
    df -Pk "$path" | awk 'NR==2 {print $4 * 1024}'
  else
    printf '0\n'
  fi
}

dentia_assert_safe_restore_path() {
  local path="$1"
  local resolved
  [ -n "$path" ] || dentia_fail "Restore path is empty."
  resolved="$(cd "$(dirname "$path")" >/dev/null 2>&1 && pwd -P)/$(basename "$path")"
  case "$resolved" in
    /|/opt|/opt/apps|/opt/apps/dentia|"$HOME"|"$HOME"/..)
      dentia_fail "Refusing dangerous restore path: $resolved"
      ;;
  esac
}

dentia_require_env_file_permissions() {
  local env_file="${1:-$DENTIA_ENV_FILE}"
  [ -f "$env_file" ] || dentia_fail "Environment file not found: $env_file"
  local mode
  if stat -c '%a' "$env_file" >/dev/null 2>&1; then
    mode="$(stat -c '%a' "$env_file")"
  else
    mode="$(stat -f '%Lp' "$env_file")"
  fi
  [ "$mode" = "600" ] || dentia_fail "Unsafe environment file permissions for $env_file. Expected 600, found $mode."
}

dentia_storage_host_root() {
  local root="${1:-$DENTIA_PRODUCTION_DIR}"
  printf '%s/%s\n' "$root" "$DENTIA_BACKEND_STORAGE_HOST_PATH"
}

dentia_assert_storage_path_safe() {
  local path="$1"
  [ -n "$path" ] || dentia_fail "Storage path is empty."
  [ -e "$path" ] || return 0
  [ ! -L "$path" ] || dentia_fail "Storage path must not be a symlink: $path"
}
