#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: start_dentia.sh [--open] [--mailbox] [--lan] [--help]

Starts the local Dentia backend and frontend using PID files under .run/.
It refuses to kill or reuse unknown processes.

  --mailbox  Configure the backend for the isolated localhost OTP mailbox.
             Start it first with scripts/local/start_dentia_mailbox.sh.
  --lan      Bind only the frontend to 0.0.0.0 for a trusted-LAN QR test.
             Requires DENTIA_LAN_HOST with this computer's LAN IP/hostname.
EOF
}

OPEN=false
USE_MAILBOX=false
USE_LAN=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --open) OPEN=true ;;
    --mailbox) USE_MAILBOX=true ;;
    --lan) USE_LAN=true ;;
    *) dentia_fail "Unknown argument: $1" ;;
  esac
  shift
done

ROOT="$DENTIA_PROJECT_DIR"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
RUN_DIR="$ROOT/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"
LOCAL_API_PROXY_TARGET="http://127.0.0.1:${DENTIA_BACKEND_PORT}"
FRONTEND_BIND_HOST=127.0.0.1
if $USE_LAN; then
  [ -n "${DENTIA_LAN_HOST:-}" ] || dentia_fail "--lan requires DENTIA_LAN_HOST (for example 192.168.1.50)."
  [[ "$DENTIA_LAN_HOST" =~ ^[A-Za-z0-9.-]+$ ]] || dentia_fail "DENTIA_LAN_HOST must be an IP address or hostname without scheme or path."
  FRONTEND_BIND_HOST=0.0.0.0
  DENTIA_FRONTEND_URL="http://${DENTIA_LAN_HOST}:${DENTIA_FRONTEND_PORT}"
else
  DENTIA_FRONTEND_URL="http://localhost:${DENTIA_FRONTEND_PORT}"
fi
DENTIA_BACKEND_HEALTH_URL="http://127.0.0.1:${DENTIA_BACKEND_PORT}/health"

mkdir -p "$LOG_DIR"

dentia_info "Project: $ROOT"
[ -d "$BACKEND_DIR" ] || dentia_fail "Backend directory not found: $BACKEND_DIR"
[ -d "$FRONTEND_DIR" ] || dentia_fail "Frontend directory not found: $FRONTEND_DIR"

if [ -f "$FRONTEND_DIR/.env.local" ]; then
  configured_proxy="$(sed -n 's/^API_PROXY_TARGET=//p' "$FRONTEND_DIR/.env.local" | tail -n 1)"
  if [ -n "$configured_proxy" ] && [ "$configured_proxy" != "$LOCAL_API_PROXY_TARGET" ]; then
    dentia_warn "frontend/.env.local has a different API_PROXY_TARGET; the explicit local process value $LOCAL_API_PROXY_TARGET will take precedence."
  fi
fi

dentia_require_cmd python3
dentia_require_cmd npm
dentia_require_cmd node

if $USE_MAILBOX; then
  dentia_require_cmd curl
  curl -fsS --max-time 3 "http://127.0.0.1:${DENTIA_MAILBOX_UI_PORT}/readyz" >/dev/null \
    || dentia_fail "Local OTP mailbox is not ready. Run scripts/local/start_dentia_mailbox.sh first."
fi

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
  export PUBLIC_FRONTEND_URL="$DENTIA_FRONTEND_URL"
  if $USE_MAILBOX; then
    export APP_ENV=local
    export SMTP_HOST=127.0.0.1
    export SMTP_PORT="$DENTIA_MAILBOX_SMTP_PORT"
    export SMTP_USERNAME=dentia-local
    export SMTP_PASSWORD=dentia-local-only
    export SMTP_FROM_EMAIL=no-reply@dentia.local
    export SMTP_USE_TLS=false
    export SMTP_TIMEOUT_SECONDS=5
  fi
  exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$DENTIA_BACKEND_PORT"
) >"$LOG_DIR/backend.log" 2>&1 &
echo "$!" >"$BACKEND_PID"

dentia_info "Starting frontend on port $DENTIA_FRONTEND_PORT..."
(
  cd "$FRONTEND_DIR"
  DENTIA_BACKEND_PORT="$DENTIA_BACKEND_PORT" DENTIA_FRONTEND_PORT="$DENTIA_FRONTEND_PORT" API_PROXY_TARGET="$LOCAL_API_PROXY_TARGET" exec npm run dev -- --hostname "$FRONTEND_BIND_HOST" --port "$DENTIA_FRONTEND_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
echo "$!" >"$FRONTEND_PID"

sleep 2
dentia_info "Backend PID: $(cat "$BACKEND_PID")"
dentia_info "Frontend PID: $(cat "$FRONTEND_PID")"
dentia_info "Backend docs: http://127.0.0.1:${DENTIA_BACKEND_PORT}/docs"
dentia_info "Frontend: $DENTIA_FRONTEND_URL"
dentia_info "Frontend API proxy: $LOCAL_API_PROXY_TARGET"
$USE_MAILBOX && dentia_info "OTP mailbox: http://127.0.0.1:${DENTIA_MAILBOX_UI_PORT} (local fictitious data only)"
$USE_LAN && dentia_warn "Trusted-LAN frontend mode is active at $DENTIA_FRONTEND_URL. Stop Dentia immediately after the QR test."
dentia_info "Logs: $LOG_DIR"

if $OPEN && [[ "$(uname -s)" == "Darwin" ]]; then
  open "$DENTIA_FRONTEND_URL" >/dev/null 2>&1 || true
fi
