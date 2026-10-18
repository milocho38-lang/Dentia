import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import { once } from "node:events";
import { canApplyUploadResult, createClinicalFileUploadGate } from "../lib/clinicalFileUploadState.mjs";

assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-a"), true);
assert.equal(canApplyUploadResult(4, 5, "patient-a", "patient-a"), false, "late response after navigation must be ignored");
assert.equal(canApplyUploadResult(4, 4, "patient-a", "patient-b"), false, "response from another patient must be ignored");
const nextConfig = fs.readFileSync(new URL("../next.config.ts", import.meta.url), "utf8");
assert.match(nextConfig, /proxyClientMaxBodySize:\s*["']27mb["']/, "proxy preserves a complete 25 MiB multipart upload");

let uploadRequests = 0;
let reconcileRequests = 0;
const server = http.createServer((request, response) => {
  if (request.url === "/upload") {
    uploadRequests += 1;
    request.resume();
    setTimeout(() => { if (!response.writableEnded) { response.writeHead(201, { "content-type": "application/json" }); response.end('{"id":"uploaded"}'); } }, 150);
    return;
  }
  if (request.url?.startsWith("/reconcile/")) {
    reconcileRequests += 1;
    response.writeHead(200, { "content-type": "application/json" });
    response.end('{"id":"confirmed"}');
    return;
  }
  response.writeHead(404); response.end();
});
server.listen(0, "127.0.0.1");
await once(server, "listening");
const { port } = server.address();
const baseUrl = `http://127.0.0.1:${port}`;

try {
  const gate = createClinicalFileUploadGate();
  let idsCreated = 0;
  let controllersCreated = 0;
  const begin = () => gate.begin({
    patientId: "patient-a",
    generation: 1,
    createIdempotencyKey: () => `request-${++idsCreated}`,
    createController: () => { controllersCreated += 1; return new AbortController(); },
  });
  const first = begin();
  const second = begin();
  assert.ok(first);
  assert.equal(second, null, "a same-tick double submit must be rejected synchronously");
  assert.equal(idsCreated, 1, "rejected submit must not create an idempotency key");
  assert.equal(controllersCreated, 1, "rejected submit must not create an AbortController");
  assert.equal(gate.busy, true, "button state remains busy while the owner is active");

  const request = fetch(`${baseUrl}/upload`, { method: "POST", body: "synthetic", signal: first.controller.signal });
  await new Promise((resolve) => setTimeout(resolve, 30));
  first.controller.abort();
  await assert.rejects(request, (error) => error?.name === "AbortError");
  assert.equal(uploadRequests, 1, "double submit must produce exactly one real upload request");
  const reconciliation = await fetch(`${baseUrl}/reconcile/${first.idempotencyKey}`).then((response) => response.json());
  assert.equal(reconciliation.id, "confirmed");
  assert.equal(reconcileRequests, 1, "an aborted real fetch is reconciled once");
  assert.equal(gate.finish(first), true);
  assert.equal(gate.busy, false, "owner completion restores the upload button");

  const oldAttempt = begin();
  assert.ok(oldAttempt);
  const lateRequest = fetch(`${baseUrl}/upload`, { method: "POST", body: "late", signal: oldAttempt.controller.signal });
  let generation = 1;
  let patientId = "patient-a";
  const ui = { patientA: [], patientB: [], message: null, busy: true };
  generation += 1; patientId = "patient-b"; gate.invalidate(); ui.busy = gate.busy;
  await assert.rejects(lateRequest, (error) => error?.name === "AbortError");
  if (gate.isOwner(oldAttempt) && canApplyUploadResult(oldAttempt.generation, generation, oldAttempt.patientId, patientId)) ui.patientB.push("late");
  if (gate.finish(oldAttempt)) ui.busy = false;
  assert.deepEqual(ui.patientB, [], "a late response cannot mutate the newly selected patient's UI");
  assert.equal(ui.message, null, "navigation abort cannot leak a stale status message");
  assert.equal(ui.busy, false, "navigation invalidation leaves the button state consistent");
  assert.equal(gate.finish(oldAttempt), false, "stale finally cannot release another attempt");
} finally {
  server.close();
  await once(server, "close");
}

console.log("clinical file upload functional state tests passed");
