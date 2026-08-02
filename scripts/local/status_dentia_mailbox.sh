#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: status_dentia_mailbox.sh [--help]

Shows the isolated local OTP mailbox status without printing captured messages.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then usage; exit 0; fi
[ "$#" -eq 0 ] || dentia_fail "Unknown argument: $1"

dentia_require_cmd docker
docker compose -f "$DENTIA_PROJECT_DIR/docker-compose.mailbox.yml" -p dentia-local-mailbox ps
if curl -fsS --max-time 3 "http://127.0.0.1:${DENTIA_MAILBOX_UI_PORT}/readyz" >/dev/null 2>&1; then
  dentia_info "Mailbox ready: http://127.0.0.1:${DENTIA_MAILBOX_UI_PORT}"
else
  dentia_warn "Mailbox UI is not ready on 127.0.0.1:${DENTIA_MAILBOX_UI_PORT}."
fi
