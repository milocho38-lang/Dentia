#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
TARGET_COMMIT="${1:-}"
cd "$ROOT"

if [ -z "$TARGET_COMMIT" ] && [ -f "$STATE_DIR/last_deploy_previous_commit" ]; then
  TARGET_COMMIT="$(cat "$STATE_DIR/last_deploy_previous_commit")"
fi
[ -n "$TARGET_COMMIT" ] || dentia_fail "Usage: $0 <commit>. No previous deploy commit was found."

cat <<EOF
Rollback target: $TARGET_COMMIT

Important:
- This rolls back application code only.
- Alembic downgrades are NOT executed automatically.
- If database state must be reverted, restore the backup manually after careful review.
- Last deploy backup, if available: $(cat "$STATE_DIR/last_deploy_backup" 2>/dev/null || echo "unknown")
EOF

printf 'Type ROLLBACK-DENTIA to continue: '
read -r confirmation
[ "$confirmation" = "ROLLBACK-DENTIA" ] || dentia_fail "Cancelled."

if [ -n "$(git status --porcelain)" ]; then
  git status --short
  dentia_fail "Repository has local changes. Aborting rollback."
fi

git fetch origin
git checkout "$TARGET_COMMIT"
dentia_compose build
dentia_compose up -d
sleep 5
dentia_compose ps

dentia_warn "Alembic downgrade was not run. Review migrations manually if the rollback requires database changes."
dentia_info "Rollback code deploy complete."
