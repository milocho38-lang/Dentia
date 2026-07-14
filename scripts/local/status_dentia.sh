#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="$DENTIA_PROJECT_DIR"
RUN_DIR="$ROOT/.run"

show_process() {
  local name="$1"
  local pid_file="$2"
  local port="$3"
  local url="$4"
  if [ -f "$pid_file" ] && dentia_pid_alive "$(cat "$pid_file")"; then
    printf '%-10s active   PID=%s PORT=%s URL=%s\n' "$name" "$(cat "$pid_file")" "$port" "$url"
  else
    printf '%-10s inactive PORT=%s URL=%s\n' "$name" "$port" "$url"
  fi
}

show_process "backend" "$RUN_DIR/backend.pid" "$DENTIA_BACKEND_PORT" "http://127.0.0.1:${DENTIA_BACKEND_PORT}/docs"
show_process "frontend" "$RUN_DIR/frontend.pid" "$DENTIA_FRONTEND_PORT" "$DENTIA_FRONTEND_URL"

printf '\nPorts:\n'
dentia_port_owner "$DENTIA_BACKEND_PORT" || true
dentia_port_owner "$DENTIA_FRONTEND_PORT" || true

printf '\nAlembic:\n'
(cd "$ROOT/backend" && .venv/bin/alembic -c alembic.ini current 2>/dev/null || true)

printf '\nGit:\n'
(cd "$ROOT" && printf 'Branch: %s\n' "$(git rev-parse --abbrev-ref HEAD)" && printf 'Commit: %s\n' "$(git log -1 --oneline)" && if [ -n "$(git status --porcelain)" ]; then echo "Working tree: dirty"; else echo "Working tree: clean"; fi)
