import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const treatmentPage = readFileSync(
  new URL("../components/treatments/TreatmentPages.tsx", import.meta.url),
  "utf8",
);
const patientDetail = readFileSync(
  new URL("../components/patients/PatientDetail.tsx", import.meta.url),
  "utf8",
);
const service = readFileSync(
  new URL("../services/treatmentService.ts", import.meta.url),
  "utf8",
);

for (const component of [treatmentPage, patientDetail]) {
  assert.match(component, /Mostrar saldo pendiente después de este pago/);
  assert.match(component, /Si lo activas, el comprobante incluirá el saldo resultante del paciente\./);
  assert.match(component, /useState\(false\)/);
  assert.match(component, /show_remaining_balance: showRemainingBalance/);
  assert.match(component, /setShowRemainingBalance\(false\)/);
}

assert.match(service, /show_remaining_balance\?: boolean/);
assert.doesNotMatch(treatmentPage, /country.*showRemainingBalance/i);
assert.doesNotMatch(patientDetail, /country.*showRemainingBalance/i);

console.log("payment-receipt-balance-tests OK");
