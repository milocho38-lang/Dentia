#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: stop_dentia.sh [--help]

Stops only Dentia local processes recorded in .run/*.pid. It validates the
process command before sending a signal and will not kill unknown PIDs.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
[ "$#" -eq 0 ] || dentia_fail "Unknown argument: $1"

RUN_DIR="$DENTIA_PROJECT_DIR/.run"

stop_one() {
  local name="$1"
  local pid_file="$2"
  local expected="$3"
  if [ ! -f "$pid_file" ]; then
    dentia_info "$name: no PID file."
    return 0
  fi
  local pid
  pid="$(cat "$pid_file")"
  if ! dentia_pid_alive "$pid"; then
    dentia_info "$name: PID $pid is not running. Cleaning PID file."
    rm -f "$pid_file"
    return 0
  fi
  if ! dentia_pid_matches "$pid" "$expected"; then
    dentia_warn "$name: PID $pid is alive but does not look like Dentia ($expected)."
    dentia_warn "Command: $(dentia_pid_command "$pid")"
    dentia_fail "Refusing to stop unknown process. Inspect and remove $pid_file manually if stale."
  fi
  dentia_info "Stopping $name PID $pid..."
  kill "$pid"
  local i
  for ((i = 1; i <= 10; i++)); do
    if ! dentia_pid_alive "$pid"; then
      rm -f "$pid_file"
      dentia_info "$name stopped."
      return 0
    fi
    sleep 1
  done
  dentia_warn "$name did not stop gracefully. Sending SIGKILL to PID $pid."
  kill -9 "$pid" >/dev/null 2>&1 || true
  rm -f "$pid_file"
}

stop_one "frontend" "$RUN_DIR/frontend.pid" "npm run dev"
stop_one "backend" "$RUN_DIR/backend.pid" "uvicorn app.main:app"
dentia_info "Done."
