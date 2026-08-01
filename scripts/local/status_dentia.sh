#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: status_dentia.sh [--help]

Shows local Dentia process, port, Alembic and Git status.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
[ "$#" -eq 0 ] || dentia_fail "Unknown argument: $1"

ROOT="$DENTIA_PROJECT_DIR"
RUN_DIR="$ROOT/.run"
LOCAL_API_PROXY_TARGET="http://127.0.0.1:${DENTIA_BACKEND_PORT}"
DENTIA_FRONTEND_URL="http://localhost:${DENTIA_FRONTEND_PORT}"
DENTIA_BACKEND_HEALTH_URL="http://127.0.0.1:${DENTIA_BACKEND_PORT}/health"

show_process() {
  local name="$1"
  local pid_file="$2"
  local port="$3"
  local url="$4"
  local expected="$5"
  if [ -f "$pid_file" ] && dentia_pid_alive "$(cat "$pid_file")"; then
    local pid
    pid="$(cat "$pid_file")"
    if dentia_pid_matches "$pid" "$expected"; then
      printf '%-10s active   PID=%s PORT=%s URL=%s\n' "$name" "$pid" "$port" "$url"
    else
      printf '%-10s foreign  PID=%s PORT=%s URL=%s\n' "$name" "$pid" "$port" "$url"
      printf '  command=%s\n' "$(dentia_pid_command "$pid")"
    fi
  elif [ -f "$pid_file" ]; then
    printf '%-10s stale    PORT=%s URL=%s PID_FILE=%s\n' "$name" "$port" "$url" "$pid_file"
  else
    printf '%-10s inactive PORT=%s URL=%s\n' "$name" "$port" "$url"
  fi
}

show_process "backend" "$RUN_DIR/backend.pid" "$DENTIA_BACKEND_PORT" "http://127.0.0.1:${DENTIA_BACKEND_PORT}/docs" "uvicorn app.main:app"
show_process "frontend" "$RUN_DIR/frontend.pid" "$DENTIA_FRONTEND_PORT" "$DENTIA_FRONTEND_URL" "npm run dev"
printf '%-10s %s\n' "api-proxy" "$LOCAL_API_PROXY_TARGET"

printf '\nPorts:\n'
dentia_port_owner "$DENTIA_BACKEND_PORT" || true
dentia_port_owner "$DENTIA_FRONTEND_PORT" || true

printf '\nAlembic:\n'
if [ -d "$ROOT/backend" ] && [ -x "$ROOT/backend/.venv/bin/alembic" ]; then
  (cd "$ROOT/backend" && .venv/bin/alembic -c alembic.ini current 2>/dev/null || true)
else
  echo "Alembic unavailable: backend virtualenv not found."
fi

printf '\nGit:\n'
if [ -d "$ROOT/.git" ]; then
  (cd "$ROOT" && printf 'Branch: %s\n' "$(git rev-parse --abbrev-ref HEAD)" && printf 'Commit: %s\n' "$(git log -1 --oneline)" && if [ -n "$(git status --porcelain)" ]; then echo "Working tree: dirty"; else echo "Working tree: clean"; fi)
else
  echo "Git unavailable: repository metadata not found."
fi
