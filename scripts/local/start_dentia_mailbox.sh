#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: start_dentia_mailbox.sh [--open] [--help]

Starts the isolated Dentia local OTP mailbox. SMTP and Web UI bind only to
127.0.0.1 and no mailbox data is persisted after stop.
EOF
}

OPEN=false
case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --open) OPEN=true ;;
  "") ;;
  *) dentia_fail "Unknown argument: $1" ;;
esac

COMPOSE_FILE="$DENTIA_PROJECT_DIR/docker-compose.mailbox.yml"
PROJECT="dentia-local-mailbox"
UI_URL="http://127.0.0.1:${DENTIA_MAILBOX_UI_PORT}"

dentia_require_cmd docker
[ -f "$COMPOSE_FILE" ] || dentia_fail "Mailbox Compose file not found: $COMPOSE_FILE"
for port in "$DENTIA_MAILBOX_SMTP_PORT" "$DENTIA_MAILBOX_UI_PORT"; do
  if dentia_port_owner "$port" | grep -q .; then
    dentia_warn "Local mailbox port $port is already in use."
    dentia_port_owner "$port"
    dentia_fail "Stop the owning process or change DENTIA_MAILBOX_*_PORT in scripts/dentia.env."
  fi
done

dentia_info "Starting isolated local OTP mailbox..."
DENTIA_MAILBOX_SMTP_PORT="$DENTIA_MAILBOX_SMTP_PORT" DENTIA_MAILBOX_UI_PORT="$DENTIA_MAILBOX_UI_PORT" \
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT" up -d --wait
dentia_info "Mailbox UI: $UI_URL"
dentia_info "SMTP: 127.0.0.1:${DENTIA_MAILBOX_SMTP_PORT}"
dentia_info "Use only fictitious patients and stop with scripts/local/stop_dentia_mailbox.sh."

if $OPEN && [[ "$(uname -s)" == "Darwin" ]]; then
  open "$UI_URL" >/dev/null 2>&1 || true
fi
