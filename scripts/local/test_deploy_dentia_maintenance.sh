#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1 && pwd)"
DEPLOY_SOURCE="$REPO_ROOT/scripts/production/deploy_dentia.sh"
LAUNCHER_SOURCE="$REPO_ROOT/scripts/production/launch_maintenance_deploy.sh"
BACKUP_SOURCE="$REPO_ROOT/scripts/production/backup_dentia.sh"
COMMON_SOURCE="$REPO_ROOT/scripts/lib/dentia_common.sh"
OLD_SHA="1111111111111111111111111111111111111111"
TARGET_SHA="2222222222222222222222222222222222222222"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_order() {
  local log="$1"
  shift
  local previous=0 token line
  for token in "$@"; do
    line="$(grep -nF "$token" "$log" | head -n 1 | cut -d: -f1 || true)"
    [ -n "$line" ] || fail "missing log token: $token"
    [ "$line" -gt "$previous" ] || fail "out-of-order log token: $token"
    previous="$line"
  done
}

assert_absent() {
  local log="$1" token="$2"
  ! grep -Fq "$token" "$log" || fail "unexpected log token: $token"
}

make_harness() {
  local harness="$1"
  mkdir -p "$harness/scripts/production" "$harness/scripts/lib" "$harness/bin" \
    "$harness/root/.git" "$harness/root/backend/storage" "$harness/backup"
  mkdir -p "$harness/root/.run"
  printf 'services: {}\n' >"$harness/root/docker-compose.yml"
  printf '%s\n' "$OLD_SHA" >"$harness/root/.run/last_deploy_commit"
  cp "$DEPLOY_SOURCE" "$harness/scripts/production/deploy_dentia.sh"
  cp "$COMMON_SOURCE" "$harness/scripts/lib/dentia_common.sh"

  cat >"$harness/scripts/production/validate_dentia_production_config.sh" <<'MOCK'
#!/usr/bin/env bash
printf 'validate\n' >>"$DEPLOY_TEST_LOG"
MOCK
  cat >"$harness/scripts/production/backup_dentia.sh" <<'MOCK'
#!/usr/bin/env bash
printf 'backup\n' >>"$DEPLOY_TEST_LOG"
printf 'backup-meta:%s:%s:%s:%s\n' "$DENTIA_BACKUP_DEPLOYED_COMMIT" "$DENTIA_BACKUP_TARGET_COMMIT" "$DENTIA_BACKUP_BACKEND_IMAGE_ID" "$DENTIA_BACKUP_TARGET_BACKEND_IMAGE_ID" >>"$DEPLOY_TEST_LOG"
[ "${DEPLOY_TEST_SCENARIO:-success}" != "backup_fail" ] || exit 31
[ "${DEPLOY_TEST_SCENARIO:-success}" != "signal_wait" ] || sleep 3
path="$DEPLOY_TEST_HARNESS/backup/package"
mkdir -p "$path"
printf '%s\n' "$path"
MOCK
  cat >"$harness/scripts/production/verify_dentia_backup.sh" <<'MOCK'
#!/usr/bin/env bash
printf 'verify-backup\n' >>"$DEPLOY_TEST_LOG"
MOCK
  cat >"$harness/scripts/production/restore_dentia_backup.sh" <<'MOCK'
#!/usr/bin/env bash
printf 'restore:%s\n' "$*" >>"$DEPLOY_TEST_LOG"
[ "${DEPLOY_TEST_SCENARIO:-success}" != "restore_fail" ] || exit 32
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [ "${args[$i]}" = --storage-dir ]; then
    mkdir -p "${args[$((i+1))]}"
    printf 'clinical-sentinel\n' >"${args[$((i+1))]}/sentinel"
  fi
done
printf 'RESTORE_VALID\n'
MOCK
  chmod +x "$harness/scripts/production/"*.sh

  cat >"$harness/bin/git" <<'MOCK'
#!/usr/bin/env bash
case "$1 ${2:-}" in
  '-C '*) exit 0 ;;
  'rev-parse --abbrev-ref') printf 'master\n' ;;
  'rev-parse HEAD')
    if [ -f "$DEPLOY_TEST_HARNESS/pulled" ]; then printf '%s\n' "$DEPLOY_TEST_TARGET_SHA"; else printf '%s\n' "$DEPLOY_TEST_OLD_SHA"; fi ;;
  'rev-parse FETCH_HEAD') printf '%s\n' "$DEPLOY_TEST_TARGET_SHA" ;;
  'rev-parse refs/remotes/origin/master') printf '%s\n' "$DEPLOY_TEST_TARGET_SHA" ;;
  'status --porcelain'|'status --short') ;;
  'fetch origin') printf 'fetch\n' >>"$DEPLOY_TEST_LOG" ;;
  'merge-base --is-ancestor') exit 0 ;;
  'merge --ff-only') printf 'merge\n' >>"$DEPLOY_TEST_LOG"; touch "$DEPLOY_TEST_HARNESS/pulled" ;;
  'archive '*) tar -c -C "$DEPLOY_TEST_APPROVED_ROOT" scripts ;;
  *)
    if [ "$1" = rev-parse ] && [[ "${2:-}" == *'^{commit}' ]]; then
      printf '%s\n' "$DEPLOY_TEST_OLD_SHA"
    else
      printf 'unexpected git command: %s\n' "$*" >&2; exit 90
    fi ;;
esac
MOCK

  cat >"$harness/bin/docker" <<'MOCK'
#!/usr/bin/env bash
log="$DEPLOY_TEST_LOG"
state="$DEPLOY_TEST_HARNESS/state"
mkdir -p "$state"
for name in dentia-backend dentia-frontend dentia-website dentia-db; do
  [ -f "$state/$name" ] || printf 'true\n' >"$state/$name"
done

if [ "$1" = compose ] && [ "${2:-}" = version ]; then exit 0; fi
if [ "$1" = compose ]; then
  printf 'compose-command:%s\n' "$*" >>"$log"
  shift
  while [ "${1:-}" = --env-file ] || [ "${1:-}" = -f ]; do shift 2; done
  case "$1" in
    config)
      printf 'config\n' >>"$log"
      if [[ "$*" == *'--format json'* ]]; then
        printf '{"services":{"dentia-backend":{"image":"target-backend-ref"},"dentia-frontend":{"image":"target-frontend-ref"},"dentia-website":{"image":"target-website-ref"}}}\n'
      fi
      ;;
    build)
      [ "${DENTIA_BUILD_REVISION:-}" = "$DEPLOY_TEST_TARGET_SHA" ] || exit 97
      printf 'build-with-target-label\n' >>"$log" ;;
    run)
      if [[ "$*" == *' alembic '* ]]; then
        printf 'migrate\n' >>"$log"
        [ "${DEPLOY_TEST_SCENARIO:-success}" != migrate_fail ] || exit 33
        args=("$@")
        for ((i=0; i<${#args[@]}; i++)); do
          if [ "${args[$i]}" = --name ]; then touch "$state/target-${args[$((i+1))]}"; fi
        done
        touch "$DEPLOY_TEST_HARNESS/migrated"
      elif [[ "$*" == *' python -'* ]]; then
        cat >/dev/null
        [ -f "$DEPLOY_TEST_HARNESS/root/backend/storage/.dentia-maintenance" ] || exit 35
        printf 'internal-smoke-with-barrier\n' >>"$log"
        [ "${DEPLOY_TEST_SCENARIO:-success}" != internal_smoke_fail ] || exit 34
      else
        printf 'unexpected compose run: %s\n' "$*" >&2; exit 95
      fi ;;
    up)
      service="${@: -1}"
      printf 'up:%s\n' "$service" >>"$log"
      printf 'true\n' >"$state/$service"
      touch "$state/target-$service" ;;
    images) printf 'target-image-ref\n' ;;
    ps) printf 'compose-ps\n' >>"$log" ;;
    *) printf 'unexpected compose command: %s\n' "$*" >&2; exit 91 ;;
  esac
  exit 0
fi

case "$1" in
  inspect)
    if [[ "$*" == *'{{json .Mounts}}'* ]]; then
      printf '[{"Destination":"/app/storage"}]\n'
    elif [[ "$*" == *'{{.Image}}'* ]]; then
      name="${@: -1}"
      if [ -f "$state/target-$name" ]; then
        printf 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n'
      else
        printf 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'
      fi
    elif [[ "$*" == *'{{.State.Running}}'* ]]; then
      name="${@: -1}"
      cat "$state/$name"
    else
      exit 0
    fi ;;
  stop)
    shift
    printf 'stop:%s\n' "$*" >>"$log"
    for name in "$@"; do printf 'false\n' >"$state/$name"; done ;;
  start)
    shift
    printf 'start:%s\n' "$*" >>"$log"
    for name in "$@"; do printf 'true\n' >"$state/$name"; done ;;
  exec)
    if [[ "$*" == *'dropdb '* ]]; then
      printf 'cleanup-restore\n' >>"$log"
    elif [[ "$*" == *'psql '* ]]; then
      sql="${@: -1}"
      if [[ "$*" == *" -At -F "* ]]; then
        stdin_sql="$(cat)"
        if [[ "$stdin_sql" == *'FROM rol_permisos rp'* ]]; then
          if [ "${DEPLOY_TEST_SCENARIO:-success}" = clinical_permission_drift ] && \
             [ -f "$DEPLOY_TEST_HARNESS/migrated" ] && [[ "$*" == *" -d dentia "* ]]; then
            printf 'role-admin|ADMINISTRATOR|permission-view|clinical_files.view|t|assignment-view|f\n'
          else
            printf 'role-admin|ADMINISTRATOR|permission-view|clinical_files.view|t|assignment-view|t\n'
          fi
        elif [ "${DEPLOY_TEST_SCENARIO:-success}" = recovery_hash_mismatch ] && [[ "$*" == *" -d dentia "* ]]; then
          printf 'auditoria_eventos|1|changed\nauth_sessions|1|b\npacientes|1|c\npatient_external_references|0|d41d8\npatient_import_sources|1|source\nroles|1|d\nusuario_roles|1|e\nusuarios|1|f\n'
        else
          printf 'auditoria_eventos|1|a\nauth_sessions|1|b\npacientes|1|c\npatient_external_references|0|d41d8\npatient_import_sources|1|source\nroles|1|d\nusuario_roles|1|e\nusuarios|1|f\n'
        fi
      elif [[ "$sql" == *'SELECT version_num'* ]]; then
        if [ -f "$DEPLOY_TEST_HARNESS/migrated" ]; then printf '20261021_0051\n'; else printf '20261012_0049\n'; fi
      elif [[ "$sql" == *'pg_stat_activity'* ]]; then
        if [ "${DEPLOY_TEST_SCENARIO:-success}" = unknown_writers ]; then printf '1\n'; else printf '0\n'; fi
      elif [[ "$sql" == *"username_normalizado IS NULL"* ]]; then
        if [ "${DEPLOY_TEST_SCENARIO:-success}" = invalid_username_blank ]; then printf '1\n'; else printf '0\n'; fi
      elif [[ "$sql" == *'GROUP BY username_normalizado'* ]]; then
        if [ "${DEPLOY_TEST_SCENARIO:-success}" = invalid_username_duplicate ]; then printf '1\n'; else printf '0\n'; fi
      elif [[ "$sql" == *'GROUP BY empresa_id, correo_normalizado'* ]]; then
        if [ "${DEPLOY_TEST_SCENARIO:-success}" = invalid_tenant_email_duplicate ]; then printf '1\n'; else printf '0\n'; fi
      elif [[ "$sql" == *'GROUP BY correo_normalizado'* ]]; then
        printf '2\n'
      elif [[ "$sql" == *"permisos WHERE code = 'patients.import'"* ]]; then
        printf '1\n'
      elif [[ "$sql" == *"table_name='archivos_clinicos'"* ]] || [[ "$sql" == *"tgname='trg_archivos_clinicos_scope'"* ]]; then
        printf '1\n'
      elif [[ "$sql" == *"code IN ('clinical_files.view','clinical_files.create','clinical_files.manage')"* ]]; then
        if [[ "$*" == *" -d dentia_restore_"* ]] && \
           [ ! -f "$DEPLOY_TEST_HARNESS/recovery-backup-has-clinical-permissions" ]; then
          printf '0\n'
        else
          printf '3\n'
        fi
      elif [[ "$sql" == *"CROSS JOIN (VALUES ('clinical_files.view'),('clinical_files.create'))"* ]]; then
        if [ "${DEPLOY_TEST_SCENARIO:-success}" = recovery_0049_incomplete_authorized_role ]; then printf '1\n'; else printf '0\n'; fi
      elif [[ "$sql" == *"codigo='FIND_VENEER'"* ]]; then
        printf '1\n'
      else
        printf '0\n'
      fi
    else
      printf 'unexpected docker exec: %s\n' "$*" >&2; exit 92
    fi ;;
  logs) printf 'logs\n' ;;
  rm) exit 0 ;;
  image)
    if [[ "$*" == *'{{.Id}}'* ]]; then
      printf 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n'
    elif [[ "$*" == *'org.opencontainers.image.revision'* ]]; then
      printf '%s\n' "$DEPLOY_TEST_TARGET_SHA"
    else
      printf 'unexpected docker image command: %s\n' "$*" >&2; exit 96
    fi ;;
  *) printf 'unexpected docker command: %s\n' "$*" >&2; exit 93 ;;
esac
MOCK

  cat >"$harness/bin/curl" <<'MOCK'
#!/usr/bin/env bash
if [[ "$*" == *'%{http_code}'* ]]; then printf '503'; fi
exit 0
MOCK
  cat >"$harness/bin/python3" <<'MOCK'
#!/usr/bin/env bash
cat >/dev/null
if [ "${2:-}" = /app/storage ]; then
  printf 'yes\n'
else
  printf '[dentia] OK mocked configuration parser\n'
fi
MOCK
  cat >"$harness/bin/rm" <<'MOCK'
#!/usr/bin/env bash
if [ "${DEPLOY_TEST_SCENARIO:-success}" = barrier_remove_fail ] && [[ "$*" == *'.dentia-maintenance'* ]]; then
  exit 71
fi
exec /bin/rm "$@"
MOCK
  chmod +x "$harness/bin/"*
}

run_case() {
  local scenario="$1" expect_success="$2"
  local harness
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-test.XXXXXX")"
  make_harness "$harness"
  local log="$harness/commands.log"
  local output="$harness/output.log"
  local started=$SECONDS status=0
  DEPLOY_TEST_HARNESS="$harness" \
  DEPLOY_TEST_LOG="$log" \
  DEPLOY_TEST_SCENARIO="$scenario" \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" \
  DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" \
  DENTIA_PROJECT_DIR="$harness/root" \
  DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" \
  PATH="$harness/bin:$PATH" \
  DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >"$output" 2>&1 || status=$?

  if [ "$expect_success" = true ]; then
    [ "$status" -eq 0 ] || fail "$scenario exited $status"
  else
    [ "$status" -ne 0 ] || fail "$scenario unexpectedly succeeded"
  fi

  case "$scenario" in
    success)
      assert_order "$log" validate fetch merge build-with-target-label \
        'stop:dentia-website dentia-frontend dentia-backend' backup backup-meta verify-backup restore \
        cleanup-restore migrate up:dentia-backend up:dentia-frontend up:dentia-website \
        internal-smoke-with-barrier
      [ ! -e "$harness/root/.run/maintenance_active" ] || fail "success retained maintenance marker"
      [ ! -e "$harness/root/backend/storage/.dentia-maintenance" ] || fail "success retained write barrier"
      grep -Fq "backup-meta:$OLD_SHA:$TARGET_SHA:sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" "$log" || fail "backup metadata did not preserve deployed/target image identity"
      grep -Fq 'restore:--backup' "$log" || fail "restore did not receive the verified backup package"
      ;;
    backup_fail|restore_fail|unknown_writers)
      assert_absent "$log" migrate
      grep -Fq 'start:dentia-backend' "$log" || fail "$scenario did not restart old backend"
      grep -Fq 'start:dentia-frontend dentia-website' "$log" || fail "$scenario did not restart old frontend/website"
      [ ! -e "$harness/root/.run/maintenance_active" ] || fail "$scenario retained maintenance after safe recovery"
      ;;
    invalid_username_blank|invalid_username_duplicate|invalid_tenant_email_duplicate)
      assert_absent "$log" fetch
      assert_absent "$log" build-with-target-label
      assert_absent "$log" backup
      [ ! -e "$harness/root/.run/maintenance_active" ] || fail "$scenario entered maintenance"
      ;;
    migrate_fail|clinical_permission_drift|internal_smoke_fail|barrier_remove_fail)
      grep -Fq migrate "$log" || fail "migration was not attempted"
      assert_absent "$log" 'start:dentia-backend'
      [ -f "$harness/root/.run/maintenance_active" ] || fail "post-migration failure cleared maintenance"
      [ -f "$harness/root/backend/storage/.dentia-maintenance" ] || fail "post-migration failure did not retain or re-arm write barrier"
      if [ "$scenario" = barrier_remove_fail ]; then
        ! grep -Fq 'Deploy OK' "$output" || fail "barrier removal failure logged Deploy OK"
      fi
      ;;
  esac
  [ ! -e "$harness/root/.run/deploy.lock" ] || fail "$scenario retained deploy lock"
  printf '%s duration_seconds=%s\n' "$scenario" "$((SECONDS - started))"
  rm -rf "$harness"
}

run_retry_case() {
  local harness
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-retry.XXXXXX")"
  make_harness "$harness"
  local log="$harness/commands.log" first_status=0 second_status=0
  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$log" DEPLOY_TEST_SCENARIO=backup_fail \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" DENTIA_PROJECT_DIR="$harness/root" DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" PATH="$harness/bin:$PATH" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >/dev/null 2>&1 || first_status=$?
  [ "$first_status" -ne 0 ] || fail "retry setup unexpectedly succeeded"

  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$log" DEPLOY_TEST_SCENARIO=success \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" DENTIA_PROJECT_DIR="$harness/root" DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" PATH="$harness/bin:$PATH" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >/dev/null 2>&1 || second_status=$?
  [ "$second_status" -eq 0 ] || fail "safe pre-migration retry failed with $second_status"
  [ "$(grep -xc migrate "$log")" -eq 1 ] || fail "retry migrated an unexpected number of times"
  printf 'retry_after_backup_failure OK\n'
  rm -rf "$harness"
}

prepare_recovery_harness() {
  local harness="$1"
  make_harness "$harness"
  touch "$harness/migrated"
  printf 'failed\n' >"$harness/root/.run/maintenance_active"
  printf 'barrier\n' >"$harness/root/backend/storage/.dentia-maintenance"
  mkdir -p "$harness/state"
  printf 'false\n' >"$harness/state/dentia-backend"
  printf 'false\n' >"$harness/state/dentia-frontend"
  printf 'false\n' >"$harness/state/dentia-website"
  mkdir -p "$harness/recovery-backup"
  printf '{"alembic_revision":"20261012_0049"}\n' >"$harness/recovery-backup/manifest.json"
}

run_recovery_case() {
  local scenario="$1" expect_success="$2" backup_revision="${3:-20261012_0049}"
  local harness status=0 log
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-recovery.XXXXXX")"
  prepare_recovery_harness "$harness"
  if [ "$backup_revision" = 20261017_0050 ]; then
    printf '{"alembic_revision":"20261017_0050"}\n' >"$harness/recovery-backup/manifest.json"
    touch "$harness/recovery-backup-has-clinical-permissions"
  fi
  log="$harness/commands.log"
  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$log" DEPLOY_TEST_SCENARIO="$scenario" \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" DENTIA_PROJECT_DIR="$harness/root" DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" PATH="$harness/bin:$PATH" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
  DENTIA_EXPECTED_PRE_DEPLOY_REVISION=20261021_0051 DENTIA_EXPECTED_RECOVERY_BACKUP_REVISION="$backup_revision" \
  DENTIA_RECOVERY_BACKUP_PATH="$harness/recovery-backup" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >/dev/null 2>&1 || status=$?
  if [ "$expect_success" = true ]; then
    [ "$status" -eq 0 ] || fail "recovery $scenario failed with $status"
    [ ! -e "$harness/root/.run/maintenance_active" ] || fail "successful recovery retained maintenance"
    [ ! -e "$harness/root/backend/storage/.dentia-maintenance" ] || fail "successful recovery retained barrier"
  else
    [ "$status" -ne 0 ] || fail "recovery $scenario unexpectedly succeeded"
    assert_absent "$log" 'start:dentia-backend'
    [ -f "$harness/root/.run/maintenance_active" ] || fail "recovery $scenario cleared maintenance"
    [ -f "$harness/root/backend/storage/.dentia-maintenance" ] || fail "recovery $scenario cleared barrier"
  fi
  if [ "$scenario" = success ] || [ "$scenario" = backup_fail ] || [ "$scenario" = recovery_hash_mismatch ]; then
    [ -f "$harness/root/.run/deploy_recovery_baseline_${TARGET_SHA}.tsv" ] || fail "recovery $scenario did not preserve baseline"
  fi
  if [ "$backup_revision" = 20261012_0049 ]; then
    [ ! -e "$harness/root/.run/deploy_before_clinical_permissions.tsv" ] || \
      fail "recovery 0049 captured a post-migration clinical permission baseline"
  fi
  while IFS= read -r storage_path; do
    [ ! -e "$storage_path" ] || fail "recovery $scenario retained temporary clinical storage: $storage_path"
  done < <(awk '{for (i=1; i<=NF; i++) if ($i == "--storage-dir") print $(i+1)}' "$log")
  printf 'recovery_%s OK\n' "$scenario"
  rm -rf "$harness"
}

run_recovery_guard_case() {
  local guard="$1"
  local harness status=0 log
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-recovery-guard.XXXXXX")"
  prepare_recovery_harness "$harness"
  log="$harness/commands.log"
  case "$guard" in
    marker) rm -f "$harness/root/.run/maintenance_active" ;;
    barrier) rm -f "$harness/root/backend/storage/.dentia-maintenance" ;;
    revision) rm -f "$harness/migrated" ;;
    active) printf 'true\n' >"$harness/state/dentia-backend" ;;
  esac
  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$log" DEPLOY_TEST_SCENARIO=success \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" DENTIA_PROJECT_DIR="$harness/root" DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" PATH="$harness/bin:$PATH" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
  DENTIA_EXPECTED_PRE_DEPLOY_REVISION=20261021_0051 DENTIA_RECOVERY_BACKUP_PATH="$harness/recovery-backup" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >/dev/null 2>&1 || status=$?
  [ "$status" -ne 0 ] || fail "recovery guard $guard unexpectedly succeeded"
  assert_absent "$log" 'start:dentia-backend'
  printf 'recovery_guard_%s OK\n' "$guard"
  rm -rf "$harness"
}

run_signal_case() {
  local harness
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-deploy-signal.XXXXXX")"
  make_harness "$harness"
  local log="$harness/commands.log" status=0
  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$log" DEPLOY_TEST_SCENARIO=signal_wait \
  DEPLOY_TEST_OLD_SHA="$OLD_SHA" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DENTIA_PRODUCTION_DIR="$harness/root" DENTIA_PROJECT_DIR="$harness/root" DENTIA_BACKUP_DIR="$harness/backup" \
  DENTIA_ENV_FILE="$harness/missing.env" PATH="$harness/bin:$PATH" DENTIA_DEPLOY_TARGET_SHA="$TARGET_SHA" \
    "$harness/scripts/production/deploy_dentia.sh" --maintenance --target-sha "$TARGET_SHA" >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 1 50); do
    if [ -f "$harness/root/.run/maintenance_active" ] && grep -Fq 'backup' "$log" 2>/dev/null; then
      break
    fi
    sleep 0.1
  done
  grep -Fq 'backup' "$log" 2>/dev/null || fail "signal test never reached the pre-migration backup"
  kill -TERM "$pid"
  wait "$pid" || status=$?
  [ "$status" -eq 143 ] || fail "signal test exited $status instead of 143"
  grep -Fq 'start:dentia-backend' "$log" || fail "signal before migration did not recover old backend"
  [ ! -e "$harness/root/backend/storage/.dentia-maintenance" ] || fail "signal recovery retained write barrier"
  [ ! -e "$harness/root/.run/deploy.lock" ] || fail "signal recovery retained deploy lock"
  printf 'signal_before_migration OK\n'
  rm -rf "$harness"
}

run_launcher_case() {
  local harness
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-launcher-test.XXXXXX")"
  mkdir -p "$harness/root/.git" "$harness/bin" "$harness/approved/scripts/production"
  printf 'services: {}\n' >"$harness/root/docker-compose.yml"
  cat >"$harness/approved/scripts/production/deploy_dentia.sh" <<'MOCK'
#!/usr/bin/env bash
[ "$DENTIA_PRODUCTION_DIR" = "$DEPLOY_TEST_HARNESS/root" ] || exit 81
[ "$DENTIA_PROJECT_DIR" = "$DEPLOY_TEST_HARNESS/root" ] || exit 82
[ -f "$DENTIA_PROJECT_DIR/docker-compose.yml" ] || exit 83
[ ! -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/docker-compose.yml" ] || exit 84
printf 'runner:%s:%s:%s:%s\n' "$DENTIA_DEPLOY_TARGET_SHA" "$2" "$3" "$DENTIA_PROJECT_DIR" >"$DEPLOY_TEST_LOG"
MOCK
  chmod +x "$harness/approved/scripts/production/deploy_dentia.sh"
  cat >"$harness/bin/git" <<'MOCK'
#!/usr/bin/env bash
case "$1 ${2:-}" in
  'status --porcelain') ;;
  'fetch origin') ;;
  'rev-parse FETCH_HEAD') printf '%s\n' "$DEPLOY_TEST_TARGET_SHA" ;;
  'merge-base --is-ancestor') ;;
  'archive '*) tar -c -C "$DEPLOY_TEST_APPROVED_ROOT" scripts ;;
  *) printf 'unexpected launcher git command: %s\n' "$*" >&2; exit 94 ;;
esac
MOCK
  chmod +x "$harness/bin/git"

  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$harness/launcher.log" DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" \
  DEPLOY_TEST_APPROVED_ROOT="$harness/approved" DENTIA_PRODUCTION_DIR="$harness/root" \
  PATH="$harness/bin:$PATH" "$LAUNCHER_SOURCE" "$TARGET_SHA"
  grep -Fq "runner:$TARGET_SHA:--target-sha:$TARGET_SHA:$harness/root" "$harness/launcher.log" || fail "launcher did not execute the immutable runner with the exact SHA and production project path"

  local mismatch_status=0
  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$harness/mismatch.log" DEPLOY_TEST_TARGET_SHA="$OLD_SHA" \
  DEPLOY_TEST_APPROVED_ROOT="$harness/approved" DENTIA_PRODUCTION_DIR="$harness/root" \
  PATH="$harness/bin:$PATH" "$LAUNCHER_SOURCE" "$TARGET_SHA" >/dev/null 2>&1 || mismatch_status=$?
  [ "$mismatch_status" -ne 0 ] || fail "launcher accepted a SHA different from fetched origin/master"
  [ ! -e "$harness/mismatch.log" ] || fail "launcher executed runner after SHA mismatch"
  printf 'immutable_sha_launcher OK\n'
  rm -rf "$harness"
}

run_real_extracted_launcher_case() {
  local harness
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-real-launcher-test.XXXXXX")"
  make_harness "$harness"
  cp "$REPO_ROOT/scripts/production/validate_dentia_production_config.sh" \
    "$harness/scripts/production/validate_dentia_production_config.sh"
  mkdir -p "$harness/root/scripts"
  cat >"$harness/root/scripts/dentia.env" <<EOF
DENTIA_PROJECT_DIR=/must/not/override/verified/project
DENTIA_PRODUCTION_DIR=/must/not/override/verified/production
DENTIA_BACKUP_DIR=$harness/backup
EOF
  chmod 600 "$harness/root/scripts/dentia.env"

  DEPLOY_TEST_HARNESS="$harness" DEPLOY_TEST_LOG="$harness/commands.log" \
  DEPLOY_TEST_SCENARIO=success DEPLOY_TEST_OLD_SHA="$OLD_SHA" \
  DEPLOY_TEST_TARGET_SHA="$TARGET_SHA" DEPLOY_TEST_APPROVED_ROOT="$harness" \
  DENTIA_PRODUCTION_DIR="$harness/root" PATH="$harness/bin:$PATH" \
    env -u DENTIA_PROJECT_DIR -u DENTIA_ENV_FILE \
    "$LAUNCHER_SOURCE" "$TARGET_SHA" >"$harness/output.log" 2>&1

  local compose="$harness/root/docker-compose.yml"
  local env_file="$harness/root/scripts/dentia.env"
  grep -Fq "compose-command:compose --env-file $env_file -f $compose config --quiet" "$harness/commands.log" || \
    fail "real extracted validator did not resolve production compose/default env"
  for command in build run up; do
    grep -F "compose-command:compose --env-file $env_file -f $compose" "$harness/commands.log" | \
      grep -Fq " $command" || fail "real extracted runner did not use production compose for $command"
  done
  [ "$(grep -Fc "compose-command:compose --env-file $env_file -f $compose config --format json" "$harness/commands.log")" -eq 3 ] || \
    fail "real extracted runner did not resolve all three configured image references"
  [ ! -e "$harness/root/.run/maintenance_active" ] || fail "real extracted launcher retained maintenance"
  [ ! -e "$harness/root/backend/storage/.dentia-maintenance" ] || fail "real extracted launcher retained barrier"
  printf 'real_extracted_launcher_paths OK\n'
  rm -rf "$harness"
}

test_storage_archive_excludes_barrier() {
  grep -Fq 'tar --exclude="$MAINTENANCE_RELATIVE" -czf "$STORAGE_ARCHIVE"' "$BACKUP_SOURCE" || \
    fail "backup script does not exclude the exact maintenance marker"
  local harness archive restored
  harness="$(mktemp -d "${TMPDIR:-/tmp}/dentia-storage-archive.XXXXXX")"
  archive="$harness/storage.tar.gz"
  restored="$harness/restored"
  mkdir -p "$harness/root/backend/storage/clinical" "$restored"
  printf 'maintenance\n' >"$harness/root/backend/storage/.dentia-maintenance"
  printf 'normal-clinical-data\n' >"$harness/root/backend/storage/clinical/normal.txt"
  tar --exclude='backend/storage/.dentia-maintenance' -czf "$archive" -C "$harness/root" backend/storage
  tar -tzf "$archive" | grep -Fq 'backend/storage/clinical/normal.txt' || fail "normal storage data missing from archive"
  ! tar -tzf "$archive" | grep -Fq '.dentia-maintenance' || fail "maintenance marker leaked into archive"
  tar -xzf "$archive" -C "$restored"
  [ -f "$restored/backend/storage/clinical/normal.txt" ] || fail "normal storage data missing after restore"
  [ ! -e "$restored/backend/storage/.dentia-maintenance" ] || fail "restored storage retained maintenance marker"
  printf 'storage_archive_excludes_barrier OK\n'
  rm -rf "$harness"
}

test_existing_import_data_is_preserved() {
  grep -Fq "SELECT 'patient_import_sources', count(*)" "$DEPLOY_SOURCE" || \
    fail "patient import sources are missing from the stable-data snapshot"
  grep -Fq "SELECT 'patient_external_references', count(*)" "$DEPLOY_SOURCE" || \
    fail "patient external references are missing from the stable-data snapshot"
  ! grep -Fq 'Patient import sources must be empty immediately after rollout.' "$DEPLOY_SOURCE" || \
    fail "deploy still rejects legitimate existing patient import sources"
  ! grep -Fq 'Patient external references must be empty immediately after rollout.' "$DEPLOY_SOURCE" || \
    fail "deploy still rejects legitimate existing patient external references"
  printf 'existing_import_data_preservation OK\n'
}

test_intermediate_checkout_recovery_is_fail_closed() {
  for required in \
    'Recovery requires the explicit migrated revision guard.' \
    'Recovery requires the already migrated $EXPECTED_RECOVERY_REVISION database.' \
    'Recovery checkout requires the maintenance marker.' \
    'Recovery checkout requires the persistent write barrier.' \
    'Recovery checkout requires all application containers stopped:'; do
    grep -Fq "$required" "$DEPLOY_SOURCE" || fail "missing recovery guard: $required"
  done
  grep -Fq 'MAINTENANCE_ACTIVE=true' "$DEPLOY_SOURCE" || fail "recovery does not retain maintenance on failure"
  grep -Fq 'MIGRATION_STARTED=true' "$DEPLOY_SOURCE" || fail "recovery could restart old containers on failure"
  printf 'intermediate_checkout_recovery_fail_closed OK\n'
}

bash -n "$DEPLOY_SOURCE"
run_case success true
run_case invalid_username_blank false
run_case invalid_username_duplicate false
run_case invalid_tenant_email_duplicate false
run_case backup_fail false
run_case restore_fail false
run_case unknown_writers false
run_case migrate_fail false
run_case clinical_permission_drift false
run_case internal_smoke_fail false
run_case barrier_remove_fail false
run_retry_case
run_recovery_case success true
run_recovery_case backup_fail false
run_recovery_case recovery_hash_mismatch false
run_recovery_case recovery_0049_incomplete_authorized_role false
run_recovery_case clinical_permission_baseline_0050 true 20261017_0050
run_recovery_case clinical_permission_drift false 20261017_0050
run_recovery_guard_case marker
run_recovery_guard_case barrier
run_recovery_guard_case revision
run_recovery_guard_case active
run_signal_case
run_launcher_case
run_real_extracted_launcher_case
test_storage_archive_excludes_barrier
test_existing_import_data_is_preserved
test_intermediate_checkout_recovery_is_fail_closed
printf 'maintenance deploy command-mock tests OK\n'
