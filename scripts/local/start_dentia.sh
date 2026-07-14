#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

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

if [ -f "$BACKEND_PID" ] && dentia_pid_alive "$(cat "$BACKEND_PID")"; then
  dentia_fail "Backend appears already running with PID $(cat "$BACKEND_PID"). Run ./status.sh or ./stop.sh."
fi
if [ -f "$FRONTEND_PID" ] && dentia_pid_alive "$(cat "$FRONTEND_PID")"; then
  dentia_fail "Frontend appears already running with PID $(cat "$FRONTEND_PID"). Run ./status.sh or ./stop.sh."
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

if [[ "${1:-}" == "--open" ]] && [[ "$(uname -s)" == "Darwin" ]]; then
  open "$DENTIA_FRONTEND_URL" >/dev/null 2>&1 || true
fi
