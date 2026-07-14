#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

RUN_DIR="$DENTIA_PROJECT_DIR/.run"

stop_one() {
  local name="$1"
  local pid_file="$2"
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

stop_one "frontend" "$RUN_DIR/frontend.pid"
stop_one "backend" "$RUN_DIR/backend.pid"
dentia_info "Done."
