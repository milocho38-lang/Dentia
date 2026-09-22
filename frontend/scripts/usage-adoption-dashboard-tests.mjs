import assert from "node:assert/strict";
import fs from "node:fs";
import {
  hasOrthodonticActivity,
  hasUsageActivity,
  isPeriodComplete,
  managedAppointments,
} from "../lib/usageAdoptionView.mjs";
import { syntheticUsageReport } from "./fixtures/usage-adoption-synthetic.mjs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const navigation = read("config/navigation.ts");
const route = read("app/(private)/administracion/uso-adopcion/page.tsx");
const dashboard = read("components/platform/UsageAdoptionDashboard.tsx");
const service = read("services/usageAdoptionService.ts");

assert.match(navigation, /Uso y adopción/);
assert.match(navigation, /platform\.usage\.view/);
assert.match(route, /PermissionGate permission="platform\.usage\.view"/);
assert.match(service, /cache: "no-store"/);
assert.match(service, /\/api\/platform\/usage\/context/);
assert.match(service, /\/api\/platform\/usage\/users/);

for (const label of [
  "Empresa",
  "Usuario / odontólogo",
  "Sede",
  "Periodo",
  "Últimos 7 días",
  "Últimos 30 días",
  "Desde inicio del piloto",
  "Personalizado",
]) {
  assert.ok(dashboard.includes(label), `Missing filter ${label}`);
}
for (const state of [
  "DashboardSkeleton",
  "Sin actividad en el periodo",
  "No disponible",
  "Ortodoncia no habilitada",
]) {
  assert.ok(dashboard.includes(state), `Missing state ${state}`);
}
for (const section of [
  "Agenda",
  "Pacientes",
  "Historia clínica",
  "Tratamientos",
  "Consentimientos",
  "Ortodoncia",
  "Actividad administrativa",
  "Tendencia semanal",
]) {
  assert.ok(dashboard.includes(section), `Missing dashboard section ${section}`);
}

assert.equal(isPeriodComplete("last_7_days"), true);
assert.equal(isPeriodComplete("last_30_days"), true);
assert.equal(isPeriodComplete("pilot_to_date", ""), false);
assert.equal(isPeriodComplete("pilot_to_date", "2026-08-01"), true);
assert.equal(isPeriodComplete("custom", "2026-09-01", ""), false);
assert.equal(isPeriodComplete("custom", "2026-09-30", "2026-09-01"), false);
assert.equal(isPeriodComplete("custom", "2026-09-01", "2026-09-30"), true);
assert.equal(hasUsageActivity(syntheticUsageReport), true);
assert.equal(hasOrthodonticActivity(syntheticUsageReport.orthodontics), true);
assert.equal(managedAppointments(syntheticUsageReport.agenda), 51);
assert.equal(syntheticUsageReport.agenda.appointments_created, 18);
assert.equal(syntheticUsageReport.agenda.appointments_completed_by_actor, 14);
assert.equal(syntheticUsageReport.patients.unique_patients_with_actor_activity, 12);
assert.equal(syntheticUsageReport.clinical.clinical_evolutions_signed, 9);
assert.equal(syntheticUsageReport.treatments.treatments_created, 3);
assert.equal(syntheticUsageReport.consents.consents_created, 4);
assert.equal(syntheticUsageReport.orthodontics.orthodontic_cases_created, 2);

const empty = structuredClone(syntheticUsageReport);
for (const group of ["general", "agenda", "patients", "clinical", "treatments", "consents", "orthodontics", "administrative_activity"]) {
  for (const key of Object.keys(empty[group])) {
    if (typeof empty[group][key] === "number") empty[group][key] = 0;
  }
}
assert.equal(hasUsageActivity(empty), false);

const forbiddenKeys = new Set([
  "patient_id", "patient_name", "document", "diagnosis", "clinical_text",
  "evolution_text", "consent_content", "amount", "ip_address", "user_agent",
  "email", "phone",
]);
function assertPrivate(value) {
  if (Array.isArray(value)) return value.forEach(assertPrivate);
  if (value && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      assert.equal(forbiddenKeys.has(key), false, `Forbidden key rendered by fixture: ${key}`);
      assertPrivate(child);
    }
  }
}
assertPrivate(syntheticUsageReport);
assert.doesNotMatch(dashboard, /patient_id|patient_name|diagnosis|clinical_text|consent_content|amount|ip_address|user_agent/);

console.log("usage-adoption-dashboard-tests OK");
