#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

RUN_CHARACTERIZATION=false
RUN_DB=false
RUN_COVERAGE=false
RUN_HARDENING=false
KEEP_DB=false
VERBOSE=false

usage() {
  cat <<'EOF'
Usage: test_dentia_security.sh [--help] [--characterization] [--db] [--hardening] [--quick] [--full] [--coverage] [--keep-db] [--verbose]

Runs C018R.4 security tests.

Modes:
  --characterization  Run dependency-light structural characterization tests.
  --db                Run DB-backed PostgreSQL isolation/IDOR tests.
  --hardening         Run C018R.2 pilot hardening tests without production data.
  --quick             Run characterization only.
  --full              Run characterization + DB-backed + pilot hardening suites.
  --coverage          Run DB-backed suite with coverage.
  --keep-db           Keep isolated test PostgreSQL resources for debugging.
  --verbose           Increase pytest verbosity.

Default:
  --full

The DB-backed suite uses docker-compose.test.yml with project dentia-test,
container dentia-test-db and database dentia_test. It refuses production-like
database targets before running migrations or tests.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --characterization)
      RUN_CHARACTERIZATION=true
      ;;
    --db)
      RUN_DB=true
      ;;
    --hardening)
      RUN_HARDENING=true
      ;;
    --quick)
      RUN_CHARACTERIZATION=true
      RUN_DB=false
      ;;
    --full)
      RUN_CHARACTERIZATION=true
      RUN_DB=true
      RUN_HARDENING=true
      ;;
    --coverage)
      RUN_DB=true
      RUN_COVERAGE=true
      ;;
    --keep-db)
      KEEP_DB=true
      ;;
    --verbose)
      VERBOSE=true
      ;;
    *)
      dentia_fail "Unknown argument: $1"
      ;;
  esac
  shift
done

cd "$DENTIA_REPO_ROOT"

case "${DATABASE_URL:-}" in
  *prod*|*production*|*dentiapro.com*|*opt/apps/dentia*)
    dentia_fail "Refusing to run security tests with a production-looking DATABASE_URL."
    ;;
esac

if [ -z "${DENTIA_PYTHON:-}" ] && [ -x "$DENTIA_REPO_ROOT/backend/.venv/bin/python" ]; then
  DENTIA_PYTHON="$DENTIA_REPO_ROOT/backend/.venv/bin/python"
fi
DENTIA_PYTHON="${DENTIA_PYTHON:-python3}"

if [ "$RUN_CHARACTERIZATION" = false ] && [ "$RUN_DB" = false ]; then
  if [ "$RUN_HARDENING" = false ]; then
    RUN_CHARACTERIZATION=true
    RUN_DB=true
    RUN_HARDENING=true
  fi
fi

if [ "$RUN_CHARACTERIZATION" = true ]; then
  dentia_info "Running C018R.4 security characterization tests..."
  PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/dentia_security_pycache" \
    "$DENTIA_PYTHON" backend/scripts/security_characterization_tests.py
  dentia_info "Printing C018R.4 route security metrics..."
  PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/dentia_security_pycache" \
    PYTHONPATH="$DENTIA_REPO_ROOT/backend" \
    "$DENTIA_PYTHON" backend/scripts/route_security_metrics.py
fi

if [ "$RUN_CHARACTERIZATION" = false ] && [ "$RUN_COVERAGE" = true ]; then
  dentia_info "Printing C018R.4 route security metrics..."
  PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/dentia_security_pycache" \
    PYTHONPATH="$DENTIA_REPO_ROOT/backend" \
    "$DENTIA_PYTHON" backend/scripts/route_security_metrics.py
fi

run_db_suite() {
  local compose_file="docker-compose.test.yml"
  local project="dentia-test"
  local database_url="postgresql+psycopg://dentia_test:dentia_test_password@127.0.0.1:55432/dentia_test"
  local storage_root="${TMPDIR:-/tmp}/dentia-security-storage"
  local pytest_args=(
    "backend/tests/security"
    "backend/tests/multitenancy"
    "backend/tests/permissions"
    "backend/tests/storage"
    "backend/tests/finance"
    "backend/tests/administration"
  )

  if [ ! -x "backend/.venv/bin/pytest" ]; then
    dentia_fail "pytest is not installed. Run: backend/.venv/bin/pip install -r backend/requirements-test.txt"
  fi

  dentia_info "Using isolated PostgreSQL service: dentia-test-db"
  dentia_info "Using isolated database: dentia_test"
  dentia_info "Using isolated storage root: $storage_root"

  docker compose -f "$compose_file" -p "$project" up -d dentia-test-db
  if [ "$KEEP_DB" = false ]; then
    trap 'docker compose -f docker-compose.test.yml -p dentia-test down -v >/dev/null 2>&1 || true' EXIT
  else
    dentia_info "Keeping dentia-test resources because --keep-db was provided."
  fi

  dentia_info "Waiting for dentia-test-db health..."
  for _ in $(seq 1 60); do
    if docker compose -f "$compose_file" -p "$project" exec -T dentia-test-db pg_isready -U dentia_test -d dentia_test >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker compose -f "$compose_file" -p "$project" exec -T dentia-test-db pg_isready -U dentia_test -d dentia_test >/dev/null

  dentia_info "Running Alembic migrations against dentia_test..."
  APP_ENV=test \
    DENTIA_TEST_DATABASE_CONFIRMATION=DENTIA_TEST_DATABASE_CONFIRMED \
    DATABASE_URL="$database_url" \
    JWT_SECRET="dentia-test-secret-that-is-long-enough-for-local-tests" \
    BRANDING_STORAGE_DIR="$storage_root/branding" \
    PYTHONPATH="$DENTIA_REPO_ROOT/backend" \
    backend/.venv/bin/alembic -c backend/alembic.ini upgrade head

  dentia_info "Running DB-backed security tests..."
  if [ "$RUN_COVERAGE" = true ]; then
    pytest_args=(
      --cov=backend/app
      --cov-report=term-missing:skip-covered
      --cov-report=html:backend/htmlcov-security
      "${pytest_args[@]}"
    )
  fi
  APP_ENV=test \
    DENTIA_TEST_DATABASE_CONFIRMATION=DENTIA_TEST_DATABASE_CONFIRMED \
    DATABASE_URL="$database_url" \
    JWT_SECRET="dentia-test-secret-that-is-long-enough-for-local-tests" \
    BRANDING_STORAGE_DIR="$storage_root/branding" \
    DENTIA_TEST_STORAGE_ROOT="$storage_root" \
    PYTHONPATH="$DENTIA_REPO_ROOT/backend" \
    backend/.venv/bin/pytest $([ "$VERBOSE" = true ] && printf '%s' '-vv') "${pytest_args[@]}"
}

if [ "$RUN_DB" = true ]; then
  run_db_suite
fi

if [ "$RUN_HARDENING" = true ]; then
  dentia_info "Running C018R.2 pilot hardening tests..."
  node frontend/scripts/pilot-hardening-tests.mjs
  dentia_info "Running WEB-0.8 refresh concurrency tests..."
  node frontend/scripts/auth-refresh-concurrency-tests.mjs
  PYTHONPATH="$DENTIA_REPO_ROOT/backend" \
    backend/.venv/bin/pytest \
      --confcutdir=backend/tests/operations \
      backend/tests/operations/test_clinical_dates.py
fi
