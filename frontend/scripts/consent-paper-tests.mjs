import assert from "node:assert/strict";
import fs from "node:fs";

const panel=fs.readFileSync("frontend/components/consents/ConsentPaperPanel.tsx","utf8");
const workspace=fs.readFileSync("frontend/components/consents/PatientConsentsWorkspace.tsx","utf8");
const service=fs.readFileSync("frontend/services/consentInstanceService.ts","utf8");
const patient=fs.readFileSync("frontend/components/patients/PatientDetail.tsx","utf8");
for(const text of ["Preparar e imprimir","Registrar firma","Digitalizar","Verificar","Finalizar","todas las páginas","orden correcto","contenido es legible","firma manuscrita","original físico","Páginas cargadas en orden","Código de integridad"])assert.ok(panel.includes(text),text);
for(const endpoint of ["/paper/print-document","/paper/record-signed","/paper/pages","/paper/finalize","/paper/final-document"])assert.ok(service.includes(endpoint),endpoint);
for(const permission of ["consent.paper.read","consent.paper.prepare","consent.paper.record_signed","consent.paper.upload","consent.paper.finalize"])assert.ok(patient.includes(permission),permission);
assert.ok(workspace.includes('selected.completion_channel !== "PAPER"'));
assert.ok(workspace.includes('selected.completion_channel === "PAPER"'));
assert.ok(panel.includes('accept="application/pdf,image/jpeg,image/png"'));
assert.equal(panel.includes("manifest"),false);
console.log("consent-paper-tests OK: five-step paper workflow, channel distinction, safe formats and permissions");
