import assert from "node:assert/strict";
import {
  buildPatientImportCsv,
  sanitizeSpreadsheetCell,
} from "../lib/patientImportCsv.mjs";

for (const value of [
  "=HYPERLINK(\"https://invalid\")",
  "+SUM(1,1)",
  "-2+3",
  "@SUM(1,1)",
  "   =cmd|' /C calc'!A0",
  "\t+formula",
  "\r\n@formula",
  "\u0000-formula",
]) {
  const safe = sanitizeSpreadsheetCell(value);
  assert.ok(safe.startsWith("'"), `${JSON.stringify(value)} was not neutralized`);
  assert.ok(!/[\u0000-\u001f\u007f-\u009f]/.test(safe));
}

assert.equal(sanitizeSpreadsheetCell("patient-123"), "patient-123");
const csv = buildPatientImportCsv([
  ["fila", "id_origen", "motivo"],
  ["2", "=SOURCE-ID", "línea\nnueva"],
]);
assert.match(csv, /"'=SOURCE-ID"/);
assert.ok(!csv.includes("línea\nnueva"));
assert.ok(csv.includes("línea nueva"));
console.log("patient import CSV security tests OK");
