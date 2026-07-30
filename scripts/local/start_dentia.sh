#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: start_dentia.sh [--open] [--help]

Starts the local Dentia backend and frontend using PID files under .run/.
It refuses to kill or reuse unknown processes.
EOF
}

OPEN=false
case "${1:-}" in
  --help|-h)
    usage
    exit 0
    ;;
  --open)
    OPEN=true
    ;;
  "")
    ;;
  *)
    dentia_fail "Unknown argument: $1"
    ;;
esac

ROOT="$DENTIA_PROJECT_DIR"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
RUN_DIR="$ROOT/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"

mkdir -p "$LOG_DIR"

dentia_info "Project: $ROOT"
[ -d "$BACKEND_DIR" ] || dentia_fail "Backend directory not found: $BACKEND_DIR"
[ -d "$FRONTEND_DIR" ] || dentia_fail "Frontend directory not found: $FRONTEND_DIR"

dentia_require_cmd python3
dentia_require_cmd npm
dentia_require_cmd node

[ -x "$BACKEND_DIR/.venv/bin/python" ] || dentia_fail "Backend virtualenv not found at backend/.venv. Create it before starting Dentia."
[ -x "$BACKEND_DIR/.venv/bin/alembic" ] || dentia_fail "Alembic not found in backend/.venv."
[ -x "$BACKEND_DIR/.venv/bin/uvicorn" ] || dentia_fail "Uvicorn not found in backend/.venv."
[ -d "$FRONTEND_DIR/node_modules" ] || dentia_fail "frontend/node_modules not found. Run npm install in frontend first."

for port in "$DENTIA_BACKEND_PORT" "$DENTIA_FRONTEND_PORT"; do
  if dentia_port_owner "$port" | grep -q .; then
    dentia_warn "Port $port is already in use. Dentia will not kill unknown processes."
    dentia_port_owner "$port"
    dentia_fail "Free port $port or adjust scripts/dentia.env."
  fi
done

dentia_remove_stale_pid_file "$BACKEND_PID" || true
dentia_remove_stale_pid_file "$FRONTEND_PID" || true

if [ -f "$BACKEND_PID" ] && dentia_pid_alive "$(cat "$BACKEND_PID")"; then
  if dentia_pid_matches "$(cat "$BACKEND_PID")" "uvicorn app.main:app"; then
    dentia_fail "Backend appears already running with PID $(cat "$BACKEND_PID"). Run scripts/local/status_dentia.sh or scripts/local/stop_dentia.sh."
  fi
  dentia_fail "Backend PID file points to a non-Dentia process. Remove stale file manually after inspection: $BACKEND_PID"
fi
if [ -f "$FRONTEND_PID" ] && dentia_pid_alive "$(cat "$FRONTEND_PID")"; then
  if dentia_pid_matches "$(cat "$FRONTEND_PID")" "npm run dev"; then
    dentia_fail "Frontend appears already running with PID $(cat "$FRONTEND_PID"). Run scripts/local/status_dentia.sh or scripts/local/stop_dentia.sh."
  fi
  dentia_fail "Frontend PID file points to a non-Dentia process. Remove stale file manually after inspection: $FRONTEND_PID"
fi

dentia_info "Applying backend migrations..."
(cd "$BACKEND_DIR" && .venv/bin/alembic -c alembic.ini upgrade head)

dentia_info "Starting backend on port $DENTIA_BACKEND_PORT..."
(
  cd "$BACKEND_DIR"
  exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$DENTIA_BACKEND_PORT"
) >"$LOG_DIR/backend.log" 2>&1 &
echo "$!" >"$BACKEND_PID"

dentia_info "Starting frontend on port $DENTIA_FRONTEND_PORT..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --hostname 127.0.0.1 --port "$DENTIA_FRONTEND_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
echo "$!" >"$FRONTEND_PID"

sleep 2
dentia_info "Backend PID: $(cat "$BACKEND_PID")"
dentia_info "Frontend PID: $(cat "$FRONTEND_PID")"
dentia_info "Backend docs: http://127.0.0.1:${DENTIA_BACKEND_PORT}/docs"
dentia_info "Frontend: $DENTIA_FRONTEND_URL"
dentia_info "Logs: $LOG_DIR"

if $OPEN && [[ "$(uname -s)" == "Darwin" ]]; then
  open "$DENTIA_FRONTEND_URL" >/dev/null 2>&1 || true
fi
