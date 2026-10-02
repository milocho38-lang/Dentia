import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  buildPatientNavigation,
  isPatientWorkspaceTab,
  patientNavigationGroupForTab,
  targetTabForPatientGroup,
} from "../lib/patientNavigation.ts";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const patientDetail = read("../components/patients/PatientDetail.tsx");
const navigationComponent = read("../components/patients/PatientWorkspaceNavigation.tsx");

const allowAll = () => true;
const completeNavigation = buildPatientNavigation({
  clinicalRecordLabel: "Historia clínica",
  orthodonticsVisible: true,
  periodontogramVisible: true,
  hasPermission: allowAll,
});

assert.deepEqual(
  completeNavigation.map((group) => group.label),
  ["Resumen", "Clínica", "Tratamientos", "Gestión", "Documentos"],
);
assert.deepEqual(
  completeNavigation.find((group) => group.key === "clinical")?.children.map((item) => item.label),
  ["Historia clínica", "Odontograma", "Periodontograma", "Ortodoncia"],
);
assert.deepEqual(
  completeNavigation.find((group) => group.key === "management")?.children.map((item) => item.label),
  ["Agenda", "Finanzas"],
);
assert.deepEqual(
  completeNavigation.find((group) => group.key === "documents")?.children.map((item) => item.label),
  ["Documentos", "Consentimientos", "Archivos"],
);

const treatments = completeNavigation.find((group) => group.key === "treatments");
assert.equal(treatments?.directTab, "treatments");
assert.deepEqual(treatments?.children, []);
assert.equal(targetTabForPatientGroup(treatments), "treatments");
const clinicalGroup = completeNavigation.find((group) => group.key === "clinical");
assert.equal(targetTabForPatientGroup(clinicalGroup, "periodontogram"), "periodontogram");
assert.equal(targetTabForPatientGroup(clinicalGroup, "finance"), "clinical");

const restrictedNavigation = buildPatientNavigation({
  clinicalRecordLabel: null,
  orthodonticsVisible: false,
  periodontogramVisible: false,
  hasPermission: allowAll,
});
assert.deepEqual(
  restrictedNavigation.find((group) => group.key === "clinical")?.children.map((item) => item.tab),
  ["clinical", "odontogram"],
);

const documentsOnlyPermissions = new Set([
  "consent.instance.read",
]);
const navigationWithoutClinicalOrManagement = buildPatientNavigation({
  orthodonticsVisible: false,
  periodontogramVisible: false,
  hasPermission: (permission) => documentsOnlyPermissions.has(permission),
});
assert.equal(
  navigationWithoutClinicalOrManagement.some((group) => group.key === "clinical"),
  false,
);
assert.equal(
  navigationWithoutClinicalOrManagement.some((group) => group.key === "management"),
  false,
);
assert.equal(
  navigationWithoutClinicalOrManagement.some((group) => group.key === "treatments"),
  false,
);

assert.equal(patientNavigationGroupForTab("periodontogram"), "clinical");
assert.equal(patientNavigationGroupForTab("orthodontics"), "clinical");
assert.equal(patientNavigationGroupForTab("agenda"), "management");
assert.equal(patientNavigationGroupForTab("finance"), "management");
assert.equal(patientNavigationGroupForTab("consents"), "documents");
assert.equal(patientNavigationGroupForTab("files"), "documents");
assert.equal(isPatientWorkspaceTab("periodontogram"), true);
assert.equal(isPatientWorkspaceTab("unknown"), false);
assert.equal(isPatientWorkspaceTab(null), false);

assert.match(patientDetail, /usePathname, useRouter, useSearchParams/);
assert.match(patientDetail, /setActiveTab\(isPatientWorkspaceTab\(tab\) \? tab : "summary"\)/);
assert.match(patientDetail, /router\.push\(`\$\{pathname\}\$\{query \? `\?\$\{query\}` : ""\}`/);
assert.match(patientDetail, /orthodonticsVisible: Boolean\(orthodontics\)/);
assert.match(patientDetail, /periodontogramVisible: periodontogramAllowed/);
assert.match(patientDetail, /<PatientWorkspaceNavigation/);
assert.doesNotMatch(patientDetail, /const tabs:/);

assert.match(navigationComponent, /aria-label="Navegación del paciente"/);
assert.match(navigationComponent, /aria-label="Secciones principales del paciente"/);
assert.match(navigationComponent, /aria-current=\{selected \? "page" : undefined\}/);
assert.match(navigationComponent, /focus-visible:ring-2/);
assert.match(navigationComponent, /overflow-x-auto overscroll-x-contain/);
assert.match(navigationComponent, /lg:overflow-visible/);
assert.match(navigationComponent, /min-h-11/);
assert.match(navigationComponent, /min-h-9/);
assert.match(navigationComponent, /data-patient-navigation-level="secondary"/);

console.log("patient-grouped-navigation-tests OK");
