import assert from "node:assert/strict";
import fs from "node:fs";
import { canApplyUploadResult } from "../lib/clinicalFileUploadState.mjs";

assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-a"), true);
assert.equal(canApplyUploadResult(4, 5, "patient-a", "patient-a"), false, "late response after navigation must be ignored");
assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-b"), false, "response from another patient must be ignored");
const nextConfig = fs.readFileSync(new URL("../next.config.ts", import.meta.url), "utf8");
assert.match(nextConfig, /proxyClientMaxBodySize:\s*["']27mb["']/, "proxy preserves a complete 25 MiB multipart upload");
console.log("clinical file upload state tests passed");
