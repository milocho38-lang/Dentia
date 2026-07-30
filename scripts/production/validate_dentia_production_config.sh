#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"

usage() {
  cat <<'EOF'
Usage: DENTIA_ENV_FILE=/secure/path/.env.production validate_dentia_production_config.sh [--help]

Validates Dentia production configuration without printing secret values and
without starting or recreating Docker services.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
[ "$#" -eq 0 ] || { printf '[dentia][ERROR] Unknown argument: %s\n' "$1" >&2; exit 1; }

info() {
  printf '[dentia] %s\n' "$*"
}

fail() {
  printf '[dentia][ERROR] %s\n' "$*" >&2
  exit 1
}

ok() {
  printf '[dentia] OK %s\n' "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

file_mode() {
  local path="$1"
  if stat -c '%a' "$path" >/dev/null 2>&1; then
    stat -c '%a' "$path"
  else
    stat -f '%Lp' "$path"
  fi
}

file_uid() {
  local path="$1"
  if stat -c '%u' "$path" >/dev/null 2>&1; then
    stat -c '%u' "$path"
  else
    stat -f '%u' "$path"
  fi
}

ENV_FILE="${DENTIA_ENV_FILE:-}"
[ -n "$ENV_FILE" ] || fail "DENTIA_ENV_FILE is required."

case "$(basename "$ENV_FILE")" in
  *.example|*.sample|env.production.example|.env.production.example)
    fail "Refusing to validate an example env file as production config."
    ;;
esac

[ -f "$ENV_FILE" ] || fail "Environment file not found."
[ ! -L "$ENV_FILE" ] || fail "Environment file must not be a symlink."
ok "environment file exists"

MODE="$(file_mode "$ENV_FILE")"
case "$MODE" in
  600|400) ok "environment file permissions are restricted ($MODE)" ;;
  *) fail "Unsafe environment file permissions. Expected max 600, found $MODE." ;;
esac

OWNER_UID="$(file_uid "$ENV_FILE")"
CURRENT_UID="$(id -u)"
if [ "$OWNER_UID" = "$CURRENT_UID" ] || [ "$OWNER_UID" = "0" ]; then
  ok "environment file owner is acceptable"
else
  fail "Environment file owner must be the current user or root."
fi

require_cmd python3
python3 - "$ENV_FILE" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

path = Path(sys.argv[1])

required = {
    "APP_ENV",
    "APP_DEBUG",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "JWT_SECRET",
    "DENTIA_BACKEND_ENV_FILE",
    "BRANDING_STORAGE_DIR",
    "API_PROXY_TARGET",
}

placeholder_patterns = [
    "change_me",
    "example",
    "placeholder",
    "your-secret",
    "replace",
    "password_change_me",
    "__required",
    "__user__",
    "__database__",
    "__url_encoded_password__",
]

def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise SystemExit(f"[dentia][ERROR] Invalid env syntax at line {line_number}.")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise SystemExit(f"[dentia][ERROR] Invalid env key at line {line_number}.")
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key] = value
    return values

env = parse_env(path.read_text())
missing = sorted(key for key in required if key not in env)
if missing:
    raise SystemExit(f"[dentia][ERROR] Missing required variables: {', '.join(missing)}")

empty = sorted(key for key in required if not env[key].strip())
if empty:
    raise SystemExit(f"[dentia][ERROR] Empty required variables: {', '.join(empty)}")

bad_values = []
for key, value in env.items():
    lowered = value.casefold()
    if any(pattern in lowered for pattern in placeholder_patterns):
        bad_values.append(key)
if bad_values:
    raise SystemExit(f"[dentia][ERROR] Placeholder-like values detected in: {', '.join(sorted(bad_values))}")

jwt_secret = env["JWT_SECRET"]
if len(jwt_secret) < 32:
    raise SystemExit("[dentia][ERROR] JWT_SECRET is shorter than 32 characters.")
if len(set(jwt_secret)) < 8 or jwt_secret.casefold() in {"secret", "jwt_secret", "dentia_secret"}:
    raise SystemExit("[dentia][ERROR] JWT_SECRET is too trivial.")

database_url = env["DATABASE_URL"]
parsed = urlparse(database_url)
if parsed.scheme not in {"postgresql", "postgresql+psycopg", "postgresql+psycopg2"}:
    raise SystemExit("[dentia][ERROR] DATABASE_URL must use a PostgreSQL scheme.")
if not parsed.hostname:
    raise SystemExit("[dentia][ERROR] DATABASE_URL host is missing.")
if not parsed.path or parsed.path == "/":
    raise SystemExit("[dentia][ERROR] DATABASE_URL database name is missing.")

db_name = unquote(parsed.path.lstrip("/"))
db_user = unquote(parsed.username or "")
if db_name != env["POSTGRES_DB"]:
    raise SystemExit("[dentia][ERROR] DATABASE_URL database does not match POSTGRES_DB.")
if db_user != env["POSTGRES_USER"]:
    raise SystemExit("[dentia][ERROR] DATABASE_URL user does not match POSTGRES_USER.")

print("[dentia] OK required variables are present")
print("[dentia] OK secrets are non-placeholder and structurally valid")
print(f"[dentia] OK database URL parsed for host={parsed.hostname} db={db_name} user={db_user}")
PY

if case "$ENV_FILE" in "$REPO_ROOT"/*) true ;; *) false ;; esac; then
  require_cmd git
  if git -C "$REPO_ROOT" check-ignore -q "$ENV_FILE"; then
    ok "environment file is ignored by Git"
  else
    fail "Environment file is inside the repository but is not ignored by Git."
  fi
else
  ok "environment file is outside the repository"
fi

require_cmd docker
info "Validating Docker Compose resolution..."
(
  cd "$REPO_ROOT"
  DENTIA_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" config --quiet
)
ok "Docker Compose config resolves without starting services"

info "Production configuration validation completed."
