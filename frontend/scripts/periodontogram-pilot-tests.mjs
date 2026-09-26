import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const patientDetail = readFileSync(
  new URL("../components/patients/PatientDetail.tsx", import.meta.url),
  "utf8",
);
const platformCard = readFileSync(
  new URL(
    "../components/periodontogram/PlatformPeriodontogramPilotCard.tsx",
    import.meta.url,
  ),
  "utf8",
);
const service = readFileSync(
  new URL("../services/periodontogramPilotService.ts", import.meta.url),
  "utf8",
);

assert.match(patientDetail, /getPeriodontogramPilotAccess/);
assert.match(patientDetail, /periodontogramAllowed/);
assert.match(patientDetail, /\.\.\.\(periodontogramAllowed/);
assert.match(
  patientDetail,
  /hasPermission\("periodontogram\.view"\) && periodontogramAllowed/,
);

assert.match(platformCard, /Piloto clínico/);
assert.match(platformCard, /Habilitar para la empresa/);
assert.match(platformCard, /Odontólogos autorizados/);
assert.match(platformCard, /No corresponde a un cupo comercial/);
assert.match(platformCard, /El histórico clínico permanece intacto/);
assert.match(service, /periodontogram-pilot/);
assert.match(service, /\/api\/periodontograms\/access/);

console.log("periodontogram-pilot-tests OK");
