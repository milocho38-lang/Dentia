import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const read = (path) => fs.readFileSync(new URL(`../../${path}`, import.meta.url), "utf8");

const deploy = read("scripts/production/deploy_dentia.sh");
const status = read("scripts/production/status_dentia_production.sh");
const validator = read("scripts/production/validate_dentia_production_config.sh");
const localStart = read("scripts/local/start_dentia.sh");
const localStop = read("scripts/local/stop_dentia.sh");
const localStatus = read("scripts/local/status_dentia.sh");
const patientDetail = read("frontend/components/patients/PatientDetail.tsx");
const prescriptionService = read("backend/app/services/prescription_service.py");
const clinicalDocumentService = read("backend/app/services/clinical_document_service.py");
const common = read("scripts/lib/dentia_common.sh");

const repoRoot = new URL("../..", import.meta.url).pathname;
const validatorPath = new URL("../../scripts/production/validate_dentia_production_config.sh", import.meta.url).pathname;

function run(command, args, options = {}) {
  try {
    const stdout = execFileSync(command, args, {
      cwd: repoRoot,
      encoding: "utf8",
      stderr: "pipe",
      ...options,
    });
    return { status: 0, stdout, stderr: "" };
  } catch (error) {
    return {
      status: error.status ?? 1,
      stdout: error.stdout?.toString() ?? "",
      stderr: error.stderr?.toString() ?? "",
    };
  }
}

function makeEnvContent(overrides = {}) {
  const values = {
    APP_ENV: "production",
    APP_DEBUG: "false",
    POSTGRES_DB: "dentia_test_config",
    POSTGRES_USER: "dentia_config_user",
    POSTGRES_PASSWORD: "FictionalStrongPassword2026NotSecret",
    DATABASE_URL: "postgresql+psycopg://dentia_config_user:FictionalStrongPassword2026NotSecret@dentia-db:5432/dentia_test_config",
    JWT_SECRET: "FictionalJWTSecretForDentiaHardeningChecks2026",
    DENTIA_BACKEND_ENV_FILE: "",
    BRANDING_STORAGE_DIR: "/app/storage/branding",
    API_PROXY_TARGET: "http://dentia-backend:8000",
    PUBLIC_FRONTEND_URL: "https://app.dentiapro.com",
    CONSENT_ACCEPTANCE_ENABLED: "true",
    CONSENT_PUBLIC_COOKIE_SECURE: "true",
    CONSENT_FINAL_STORAGE_DIR: "/app/storage/consents",
    CONSENT_STORAGE_PERSISTENT: "true",
    CONSENT_PROCEDURE_VERSION: "DENTIA_CONSENT_PROCEDURE_V1",
    CONSENT_OTP_EXPIRE_MINUTES: "10",
    CONSENT_OTP_MAX_ATTEMPTS: "5",
    CONSENT_PUBLIC_SESSION_MINUTES: "30",
    SMTP_HOST: "smtp.dentia.invalid",
    SMTP_FROM_EMAIL: "consents@dentia.invalid",
    DENTIA_BACKEND_BIND: "8001",
    DENTIA_FRONTEND_BIND: "3001",
    DENTIA_DB_CONTAINER: "dentia-db",
    DENTIA_BACKEND_CONTAINER: "dentia-backend",
    DENTIA_FRONTEND_CONTAINER: "dentia-frontend",
  };
  Object.assign(values, overrides);
  return Object.entries(values)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n") + "\n";
}

function writeEnvFile(directory, name, overrides = {}, mode = 0o600) {
  const file = path.join(directory, name);
  const content = makeEnvContent({ DENTIA_BACKEND_ENV_FILE: file, ...overrides });
  fs.writeFileSync(file, content, { mode });
  fs.chmodSync(file, mode);
  return file;
}

function runValidator(envFile) {
  return run(validatorPath, [], {
    env: {
      ...process.env,
      DENTIA_ENV_FILE: envFile,
    },
  });
}

function assertNoSecretLeak(output) {
  assert.doesNotMatch(output, /FictionalStrongPassword2026NotSecret/, "validator output does not leak password");
  assert.doesNotMatch(output, /FictionalJWTSecretForDentiaHardeningChecks2026/, "validator output does not leak JWT");
  assert.doesNotMatch(output, /postgresql\+psycopg:\/\/dentia_config_user:/, "validator output does not leak URL credentials");
}

function indexOfOrThrow(source, text, message) {
  const index = source.indexOf(text);
  assert.notEqual(index, -1, message);
  return index;
}

const validateIndex = indexOfOrThrow(
  deploy,
  "validate_dentia_production_config.sh",
  "deploy validates production config first",
);
const backupIndex = indexOfOrThrow(deploy, "Creating mandatory backup", "deploy creates mandatory backup");
const buildIndex = indexOfOrThrow(deploy, "dentia_compose build", "deploy builds before migration");
const migrationIndex = indexOfOrThrow(
  deploy,
  "dentia_compose run --rm --no-deps",
  "deploy runs Alembic as a one-off container",
);
const recreateIndex = indexOfOrThrow(
  deploy,
  "dentia_compose up -d --no-deps",
  "deploy recreates application containers after migration",
);
const verifyBackupIndex = indexOfOrThrow(deploy, "Verifying mandatory backup", "deploy verifies mandatory backup");
const gitPullIndex = indexOfOrThrow(deploy, "git pull --ff-only", "deploy fast-forwards code");
const migrationVerifyIndex = indexOfOrThrow(deploy, "Verifying Alembic head", "deploy verifies Alembic after migration");
const backendHealthIndex = indexOfOrThrow(deploy, "Backend healthcheck failed after backend recreate", "deploy checks backend health");
const frontendHealthIndex = indexOfOrThrow(deploy, "Frontend check failed", "deploy checks frontend health");

assert.ok(validateIndex < backupIndex, "config validation happens before backup");
assert.ok(backupIndex < verifyBackupIndex, "backup happens before verification");
assert.ok(verifyBackupIndex < gitPullIndex, "backup verification happens before code update");
assert.ok(gitPullIndex < buildIndex, "code update happens before build");
assert.ok(buildIndex < migrationIndex, "build happens before migration");
assert.ok(migrationIndex < migrationVerifyIndex, "migration happens before Alembic verification");
assert.ok(migrationVerifyIndex < recreateIndex, "Alembic verification happens before recreate");
assert.ok(recreateIndex < backendHealthIndex, "backend healthcheck happens after recreate");
assert.ok(backendHealthIndex < frontendHealthIndex, "frontend healthcheck happens after backend validation");
assert.doesNotMatch(deploy, /docker exec "\$DENTIA_BACKEND_CONTAINER" alembic/, "deploy no longer migrates inside already recreated backend");
assert.doesNotMatch(deploy, /dentia_compose up -d\s*(?:\n|$)/, "deploy does not perform full compose recreate");
assert.doesNotMatch(deploy, /up -d[^\n]*\$DENTIA_DB_SERVICE|up -d[^\n]*dentia-db/, "deploy does not deliberately recreate the DB service");
assert.match(deploy, /run --rm --no-deps/, "one-off migration container is removed after execution");
assert.match(deploy, /dentia_assert_storage_path_safe/, "deploy performs storage safety preflight");
assert.match(deploy, /Persistent storage directory is missing/, "deploy aborts when storage preflight fails");
assert.match(status, /config_validation=/, "production status reports config validation");

assert.match(validator, /DENTIA_ENV_FILE is required/, "validator requires DENTIA_ENV_FILE");
assert.match(validator, /Refusing to validate an example env file/, "validator rejects example files");
assert.match(validator, /JWT_SECRET is shorter than 32 characters/, "validator checks JWT length");
assert.match(validator, /DATABASE_URL database does not match POSTGRES_DB/, "validator checks database URL coherence");
assert.match(validator, /config --quiet/, "validator resolves compose without starting services");

assert.match(localStart, /--help/, "local start supports help");
assert.match(localStop, /dentia_pid_matches/, "local stop validates PID command");
assert.match(localStatus, /foreign/, "local status distinguishes foreign PID");
assert.doesNotMatch(`${localStart}\n${localStop}\n${common}`, /pkill -f|killall/, "local scripts do not use broad process killing");
assert.doesNotMatch(`${localStart}\n${localStop}`, /kill -9[\s\S]{0,80}Stopping/, "SIGKILL is not the first stop action");
assert.match(localStart, /Dentia will not kill unknown processes/, "start refuses occupied ports instead of killing by port");

assert.match(patientDetail, /function localCalendarDate/, "frontend uses local calendar date helper");
assert.doesNotMatch(patientDetail, /clinical_date: new Date\(\)\.toISOString\(\)\.slice\(0, 10\)/, "document forms do not default with UTC ISO slicing");
assert.match(patientDetail, /Anular receta/, "visible prescription void action remains present");
assert.match(patientDetail, /Anular documento/, "visible clinical document void action remains present");
assert.match(patientDetail, /Confirmar anulación/, "void modal requires explicit confirmation action");
assert.match(patientDetail, /document\.status === "FINALIZED" && canVoidClinicalDocuments/, "clinical document void action is visible only for FINALIZED with permission");
assert.match(patientDetail, /prescription\.status === "FINALIZED" && canVoidPrescriptions/, "prescription void action is visible only for FINALIZED with permission");
assert.doesNotMatch(patientDetail, /document\.status !== "DRAFT" && canVoidClinicalDocuments/, "clinical document void action is not shown generically for VOIDED");
assert.doesNotMatch(patientDetail, /prescription\.status !== "DRAFT" && canVoidPrescriptions/, "prescription void action is not shown generically for VOIDED");
assert.match(patientDetail, /voidReason\.trim\(\)\.length < 5/, "clinical document empty or whitespace-only void reason is rejected");
assert.match(patientDetail, /prescriptionVoidReason\.trim\(\)\.length < 5/, "prescription empty or whitespace-only void reason is rejected");
assert.match(patientDetail, /voidingBusy \|\| voidReason\.trim\(\)\.length < 5/, "clinical document double submit is blocked");
assert.match(patientDetail, /prescriptionVoidingBusy \|\| prescriptionVoidReason\.trim\(\)\.length < 5/, "prescription double submit is blocked");
assert.match(patientDetail, /No fue posible anular el documento/, "clinical document void errors are handled");
assert.match(patientDetail, /No fue posible anular la receta/, "prescription void errors are handled");
assert.match(patientDetail, /await loadClinicalDocuments\(\)/, "clinical document list refreshes after void success");
assert.match(patientDetail, /await loadPrescriptions\(\)/, "prescription list refreshes after void success");
assert.match(patientDetail, /PDF histórico/, "void confirmation states that historical PDF is preserved");

assert.match(prescriptionService, /local_clinical_date\(company, site\)/, "duplicated prescriptions use backend local clinical date");
assert.match(clinicalDocumentService, /local_clinical_date\(company, site\)/, "duplicated clinical documents use backend local clinical date");

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "dentia-hardening-"));
try {
  const goodEnv = writeEnvFile(tempRoot, ".env.production");
  const success = runValidator(goodEnv);
  assert.equal(success.status, 0, `validator success path should pass: ${success.stdout}${success.stderr}`);
  assert.match(success.stdout, /Production configuration validation completed/, "validator reports success");
  assertNoSecretLeak(success.stdout + success.stderr);

  const missing = runValidator(path.join(tempRoot, "missing.env"));
  assert.notEqual(missing.status, 0, "validator rejects missing env file");
  assert.match(missing.stderr, /Environment file not found/, "missing env file error is explicit");
  assertNoSecretLeak(missing.stdout + missing.stderr);

  const example = runValidator(path.join(repoRoot, ".env.production.example"));
  assert.notEqual(example.status, 0, "validator rejects .env.production.example");
  assert.match(example.stderr, /Refusing to validate an example env file/, "example rejection is explicit");

  for (const mode of [0o640, 0o644]) {
    const file = writeEnvFile(tempRoot, `mode-${mode.toString(8)}.env`, {}, mode);
    const result = runValidator(file);
    assert.notEqual(result.status, 0, `validator rejects ${mode.toString(8)} permissions`);
    assert.match(result.stderr, /Unsafe environment file permissions/, "permission error is explicit");
  }

  const cases = [
    ["missing-variable.env", { JWT_SECRET: undefined }, /Missing required variables/],
    ["empty-variable.env", { JWT_SECRET: "" }, /Empty required variables/],
    ["change-me.env", { POSTGRES_PASSWORD: "change_me" }, /Placeholder-like values/],
    ["example-value.env", { POSTGRES_DB: "example" }, /Placeholder-like values/],
    ["placeholder.env", { POSTGRES_USER: "placeholder" }, /Placeholder-like values/],
    ["short-jwt.env", { JWT_SECRET: "short" }, /JWT_SECRET is shorter than 32 characters/],
    ["trivial-jwt.env", { JWT_SECRET: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }, /JWT_SECRET is too trivial/],
    ["invalid-url.env", { DATABASE_URL: "not-a-url" }, /DATABASE_URL must use a PostgreSQL scheme/],
    [
      "wrong-user.env",
      { DATABASE_URL: "postgresql+psycopg://other_user:FictionalStrongPassword2026NotSecret@dentia-db:5432/dentia_test_config" },
      /DATABASE_URL user does not match POSTGRES_USER/,
    ],
    [
      "wrong-db.env",
      { DATABASE_URL: "postgresql+psycopg://dentia_config_user:FictionalStrongPassword2026NotSecret@dentia-db:5432/other_db" },
      /DATABASE_URL database does not match POSTGRES_DB/,
    ],
    [
      "legacy-root-public-url.env",
      { PUBLIC_FRONTEND_URL: "https://dentiapro.com" },
      /PUBLIC_FRONTEND_URL must be https:\/\/app\.dentiapro\.com/,
    ],
  ];

  for (const [name, overrides, expected] of cases) {
    const cleanOverrides = Object.fromEntries(Object.entries(overrides).filter(([, value]) => value !== undefined));
    const removeJwtSecret = Object.prototype.hasOwnProperty.call(overrides, "JWT_SECRET") && overrides.JWT_SECRET === undefined;
    const file = path.join(tempRoot, name);
    const content = makeEnvContent({ DENTIA_BACKEND_ENV_FILE: file, ...cleanOverrides })
      .split("\n")
      .filter((line) => !(removeJwtSecret && line.startsWith("JWT_SECRET=")))
      .join("\n");
    fs.writeFileSync(file, content, { mode: 0o600 });
    fs.chmodSync(file, 0o600);
    const result = runValidator(file);
    assert.notEqual(result.status, 0, `validator rejects ${name}`);
    assert.match(result.stderr + result.stdout, expected, `${name} returns expected error`);
    assertNoSecretLeak(result.stdout + result.stderr);
  }

  const notIgnored = path.join(repoRoot, "dentia-production-config-for-hardening-test");
  try {
    fs.writeFileSync(notIgnored, makeEnvContent({ DENTIA_BACKEND_ENV_FILE: notIgnored }), { mode: 0o600 });
    fs.chmodSync(notIgnored, 0o600);
    const result = runValidator(notIgnored);
    assert.notEqual(result.status, 0, "validator rejects non-ignored env-like file inside repo");
    assert.match(result.stderr, /not ignored by Git/, "non-ignored Git error is explicit");
    assertNoSecretLeak(result.stdout + result.stderr);
  } finally {
    fs.rmSync(notIgnored, { force: true });
  }

  const localRoot = fs.mkdtempSync(path.join(os.tmpdir(), "dentia-local-scripts-"));
  fs.mkdirSync(path.join(localRoot, ".run"), { recursive: true });
  fs.mkdirSync(path.join(localRoot, ".run", "logs"), { recursive: true });
  const localEnvFile = path.join(localRoot, "dentia.env");
  fs.writeFileSync(
    localEnvFile,
    [
      `DENTIA_PROJECT_DIR=${localRoot}`,
      "DENTIA_BACKEND_PORT=58080",
      "DENTIA_FRONTEND_PORT=53030",
      "DENTIA_FRONTEND_URL=http://localhost:53030",
      "DENTIA_BACKEND_HEALTH_URL=http://127.0.0.1:58080/health",
      "",
    ].join("\n"),
    { mode: 0o600 },
  );

  for (const script of [
    "scripts/local/start_dentia.sh",
    "scripts/local/stop_dentia.sh",
    "scripts/local/status_dentia.sh",
    "scripts/local/logs_dentia.sh",
    "scripts/local/update_dentia_local.sh",
  ]) {
    const help = run(new URL(`../../${script}`, import.meta.url).pathname, ["--help"], {
      env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
    });
    assert.equal(help.status, 0, `${script} --help works`);
    assert.match(help.stdout, /Usage:/, `${script} prints usage`);
  }

  const stopWithoutPid = run(new URL("../../scripts/local/stop_dentia.sh", import.meta.url).pathname, [], {
    env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
  });
  assert.equal(stopWithoutPid.status, 0, "stop without PID succeeds safely");

  fs.writeFileSync(path.join(localRoot, ".run", "backend.pid"), "999999\n");
  const staleStatus = run(new URL("../../scripts/local/status_dentia.sh", import.meta.url).pathname, [], {
    env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
  });
  assert.equal(staleStatus.status, 0, "status handles stale PID");
  assert.match(staleStatus.stdout, /stale/, "status reports stale PID");

  const sleepProcess = spawn("sleep", ["30"], { stdio: "ignore" });
  try {
    fs.writeFileSync(path.join(localRoot, ".run", "frontend.pid"), `${sleepProcess.pid}\n`);
    const foreignStatus = run(new URL("../../scripts/local/status_dentia.sh", import.meta.url).pathname, [], {
      env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
    });
    assert.equal(foreignStatus.status, 0, "status handles foreign PID");
    assert.match(foreignStatus.stdout, /foreign/, "status reports foreign PID");

    const foreignStop = run(new URL("../../scripts/local/stop_dentia.sh", import.meta.url).pathname, [], {
      env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
    });
    assert.notEqual(foreignStop.status, 0, "stop refuses foreign PID");
    assert.match(foreignStop.stderr, /Refusing to stop unknown process/, "stop refusal is explicit");
    assert.doesNotThrow(() => process.kill(sleepProcess.pid, 0), "foreign process remains alive");
  } finally {
    sleepProcess.kill("SIGTERM");
  }

  const logsMissing = run(new URL("../../scripts/local/logs_dentia.sh", import.meta.url).pathname, ["backend"], {
    env: { ...process.env, DENTIA_ENV_FILE: localEnvFile },
  });
  assert.notEqual(logsMissing.status, 0, "logs reports missing log file");
  assert.match(logsMissing.stderr, /Backend log not found/, "logs missing message is clear");
} finally {
  fs.rmSync(tempRoot, { recursive: true, force: true });
}

for (const script of [
  "scripts/production/validate_dentia_production_config.sh",
  "scripts/production/deploy_dentia.sh",
  "scripts/production/status_dentia_production.sh",
  "scripts/local/start_dentia.sh",
  "scripts/local/stop_dentia.sh",
  "scripts/local/status_dentia.sh",
  "scripts/local/logs_dentia.sh",
  "scripts/local/update_dentia_local.sh",
]) {
  execFileSync("bash", ["-n", new URL(`../../${script}`, import.meta.url).pathname]);
}

console.log("pilot-hardening-tests OK");
