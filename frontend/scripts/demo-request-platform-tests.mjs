import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const navigation = read("config/navigation.ts");
const list = read("components/platform/DemoRequestsPage.tsx");
const detail = read("components/platform/DemoRequestDetailPage.tsx");
const service = read("services/demoRequestService.ts");
const listRoute = read("app/(private)/administracion/solicitudes-demo/page.tsx");
const detailRoute = read("app/(private)/administracion/solicitudes-demo/[demoRequestId]/page.tsx");

assert.match(navigation, /Solicitudes de demo/);
assert.match(navigation, /platform\.demo_requests\.view/);
assert.match(navigation, /section: "Administración"/);
assert.match(listRoute, /PermissionGate permission="platform\.demo_requests\.view"/);
assert.match(detailRoute, /PermissionGate permission="platform\.demo_requests\.view"/);
for (const label of ["Fecha", "Nombre", "País / ciudad", "Práctica", "Odontólogos", "Estado", "Responsable"]) {
  assert.ok(list.includes(`"${label}"`), `Missing list column ${label}`);
}
for (const filter of ["status", "country", "assigned_to_user_id", "created_from", "created_to", "search"]) {
  assert.ok(list.includes(filter), `Missing list filter ${filter}`);
}
assert.match(detail, /Datos de contacto/);
assert.match(detail, /Datos comerciales/);
assert.match(detail, /Notas internas/);
assert.match(detail, /Agendar demo/);
assert.match(detail, /Marcar como contactado/);
assert.match(detail, /Marcar demo realizada/);
assert.match(detail, /Marcar convertido/);
assert.match(detail, /No continúa/);
assert.match(detail, /platform\.demo_requests\.manage/);
assert.match(detail, /persistAndRefetchDemoRequest/);
assert.match(detail, /Contacto registrado\./);
assert.match(detail, /Nota interna guardada\./);
assert.match(detail, /if \(saved\) setNote\(""\)/);
assert.match(detail, /if \(saved\) setStatusReason\(""\)/);
assert.match(detail, /Agregar nota interna/);
assert.match(detail, /Motivo del cambio de estado/);
assert.doesNotMatch(detail, /\.then\(\(\) => setNote\(""\)\)/);
assert.doesNotMatch(detail, /\.then\(\(\) => setStatusReason\(""\)\)/);
assert.match(service, /JSON\.stringify\(\{ status, reason: reason \|\| null, row_version: rowVersion \}\)/);
assert.match(service, /JSON\.stringify\(\{ text, row_version: rowVersion \}\)/);
for (const endpoint of ["assignment", "status", "schedule", "notes", "owners"]) {
  assert.ok(service.includes(endpoint), `Missing service contract ${endpoint}`);
}

const { persistAndRefetchDemoRequest } = await import("../lib/demoRequestMutation.mjs");
const calls = [];
const persisted = await persistAndRefetchDemoRequest(
  async () => calls.push("PATCH /status CONTACTED"),
  async () => {
    calls.push("GET /detail");
    return { status: "CONTACTED", contacted_at: "2026-09-21T12:00:00Z" };
  },
);
assert.deepEqual(calls, ["PATCH /status CONTACTED", "GET /detail"]);
assert.equal(persisted.status, "CONTACTED");
assert.ok(persisted.contacted_at);

let refetchedAfterFailure = false;
await assert.rejects(
  persistAndRefetchDemoRequest(
    async () => { throw new Error("backend rejected mutation"); },
    async () => {
      refetchedAfterFailure = true;
      return {};
    },
  ),
  /backend rejected mutation/,
);
assert.equal(refetchedAfterFailure, false, "A failed mutation must not report/refetch success");

await assert.rejects(
  persistAndRefetchDemoRequest(
    async () => undefined,
    async () => { throw new Error("persisted state could not be confirmed"); },
  ),
  /persisted state could not be confirmed/,
);

console.log("demo-request-platform-tests OK");
