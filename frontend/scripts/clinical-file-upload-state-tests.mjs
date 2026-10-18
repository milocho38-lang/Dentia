import assert from "node:assert/strict";
import fs from "node:fs";
import { canApplyUploadResult } from "../lib/clinicalFileUploadState.mjs";

assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-a"), true);
assert.equal(canApplyUploadResult(4, 5, "patient-a", "patient-a"), false, "late response after navigation must be ignored");
assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-b"), false, "response from another patient must be ignored");
const nextConfig = fs.readFileSync(new URL("../next.config.ts", import.meta.url), "utf8");
assert.match(nextConfig, /proxyClientMaxBodySize:\s*["']27mb["']/, "proxy preserves a complete 25 MiB multipart upload");
const workspace = fs.readFileSync(new URL("../components/patients/PatientFilesWorkspace.tsx", import.meta.url), "utf8");
assert.match(workspace, /useRef<AbortController \| null>/, "upload keeps one cancellable request controller");
assert.match(workspace, /if \(!selected \|\| busy\) return/, "concurrent form submissions are rejected");
assert.match(workspace, /upload\.current\?\.abort\(\)/, "navigation and explicit cancellation abort in-flight uploads");
assert.match(workspace, /canApplyUploadResult\(currentGeneration, generation\.current, uploadPatientId, patientId\)/, "late upload results are tenant-patient scoped before state changes");
assert.match(workspace, /URL\.revokeObjectURL\(url\)/, "download object URLs are released after use");
console.log("clinical file upload state tests passed");
