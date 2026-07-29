#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
TARGET_COMMIT=""
RESTORE_BACKUP=""
YES_RESTORE=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --restore-data)
      RESTORE_BACKUP="${2:-}"
      shift 2
      ;;
    --yes-i-understand)
      YES_RESTORE=true
      shift
      ;;
    *)
      if [ -z "$TARGET_COMMIT" ]; then
        TARGET_COMMIT="$1"
        shift
      else
        dentia_fail "Unknown argument: $1"
      fi
      ;;
  esac
done
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
- Data restore is separate and requires --restore-data plus explicit confirmation.
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

if [ -n "$RESTORE_BACKUP" ]; then
  [ "$YES_RESTORE" = true ] || dentia_fail "Data restore requested but --yes-i-understand was not provided."
  cat <<EOF

DATA RESTORE REQUESTED AFTER CODE ROLLBACK

Backup: $RESTORE_BACKUP

This is destructive for production data. Type RESTORE-AFTER-ROLLBACK to continue:
EOF
  read -r restore_confirmation
  [ "$restore_confirmation" = "RESTORE-AFTER-ROLLBACK" ] || dentia_fail "Data restore cancelled."
  "$SCRIPT_DIR/restore_dentia_backup.sh" --backup "$RESTORE_BACKUP" --production --yes-i-understand
fi
