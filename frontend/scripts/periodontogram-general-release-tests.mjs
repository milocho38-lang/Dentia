import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const patientDetail = read("../components/patients/PatientDetail.tsx");
const patientNavigation = read("../lib/patientNavigation.ts");
const platformCompanies = read("../components/platform/PlatformCompanyPages.tsx");
const service = read("../services/periodontogramService.ts");
const accessType = read("../types/periodontogram.ts");

assert.match(patientDetail, /getPeriodontogramAccess/);
assert.doesNotMatch(patientDetail, /Pilot|pilot/);
assert.match(patientDetail, /periodontogramAllowed/);
assert.match(patientDetail, /periodontogramVisible: periodontogramAllowed/);
assert.match(
  patientDetail,
  /hasPermission\("periodontogram\.view"\) && periodontogramAllowed/,
);
assert.match(patientNavigation, /tab: "periodontogram"/);
assert.match(patientNavigation, /permission: "periodontogram\.view"/);
assert.match(patientNavigation, /dynamicModule: "periodontogram"/);
assert.match(service, /getPeriodontogramAccess/);
assert.match(service, /\/api\/periodontograms\/access/);
assert.match(accessType, /interface PeriodontogramAccess/);
assert.doesNotMatch(accessType, /company_enabled|dentist_authorized/);
assert.doesNotMatch(platformCompanies, /PlatformPeriodontogramPilotCard/);
assert.doesNotMatch(platformCompanies, /Módulos \/ Pilotos/);

console.log("periodontogram-general-release-tests OK");
