import assert from "node:assert/strict";
import { canApplyUploadResult } from "../lib/clinicalFileUploadState.mjs";

assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-a"), true);
assert.equal(canApplyUploadResult(4, 5, "patient-a", "patient-a"), false, "late response after navigation must be ignored");
assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-b"), false, "response from another patient must be ignored");
console.log("clinical file upload state tests passed");
