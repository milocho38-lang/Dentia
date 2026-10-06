#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_SHA="${1:-}"
ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"

if [[ ! "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  printf '[dentia][ERROR] A full 40-character target SHA is required.\n' >&2
  exit 1
fi
[ -d "$ROOT/.git" ] || { printf '[dentia][ERROR] Git repository not found at %s\n' "$ROOT" >&2; exit 1; }
cd "$ROOT"
[ -z "$(git status --porcelain)" ] || { printf '[dentia][ERROR] Production repository has local changes.\n' >&2; exit 1; }

git fetch origin master
REMOTE_MASTER="$(git rev-parse FETCH_HEAD)"
[ "$REMOTE_MASTER" = "$TARGET_SHA" ] || {
  printf '[dentia][ERROR] Requested SHA does not match fetched origin/master. requested=%s fetched=%s\n' "$TARGET_SHA" "$REMOTE_MASTER" >&2
  exit 1
}
git merge-base --is-ancestor HEAD "$TARGET_SHA" || {
  printf '[dentia][ERROR] Target SHA is not a fast-forward of the production checkout.\n' >&2
  exit 1
}

RUNNER_ROOT="$(mktemp -d "/tmp/dentia-maintenance-runner.${TARGET_SHA}.XXXXXX")"
cleanup() {
  if [[ "$RUNNER_ROOT" == /tmp/dentia-maintenance-runner."$TARGET_SHA".* ]]; then
    rm -rf "$RUNNER_ROOT"
  fi
}
trap cleanup EXIT INT TERM

git archive "$TARGET_SHA" scripts | tar -x -C "$RUNNER_ROOT"
RUNNER="$RUNNER_ROOT/scripts/production/deploy_dentia.sh"
[ -x "$RUNNER" ] || { printf '[dentia][ERROR] Approved deploy runner is missing or not executable.\n' >&2; exit 1; }

DENTIA_PRODUCTION_DIR="$ROOT" \
DENTIA_PROJECT_DIR="$ROOT" \
DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
  "$RUNNER" --maintenance --target-sha "$TARGET_SHA"
