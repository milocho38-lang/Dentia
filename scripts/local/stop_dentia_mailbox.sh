#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: stop_dentia_mailbox.sh [--help]

Stops and removes the isolated local OTP mailbox, its private network and all
captured messages. It does not touch Dentia production resources.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then usage; exit 0; fi
[ "$#" -eq 0 ] || dentia_fail "Unknown argument: $1"

dentia_require_cmd docker
dentia_info "Stopping and deleting isolated local OTP mailbox..."
docker compose -f "$DENTIA_PROJECT_DIR/docker-compose.mailbox.yml" -p dentia-local-mailbox down -v --remove-orphans
dentia_info "Mailbox removed, including captured local messages."
