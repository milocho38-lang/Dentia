import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  calculateDraftIndicators,
  toggleBinaryFinding,
} from "../lib/periodontalCharting.ts";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const editor = read("../components/periodontogram/RapidPeriodontalEditor.tsx");
const workspace = read("../components/periodontogram/PeriodontogramWorkspace.tsx");
const patientDetail = read("../components/patients/PatientDetail.tsx");
const privateShell = read("../components/layout/PrivateShell.tsx");
const sidebar = read("../components/layout/Sidebar.tsx");
const appHeader = read("../components/layout/AppHeader.tsx");

assert.equal(toggleBinaryFinding(null), true);
assert.equal(toggleBinaryFinding(false), true);
assert.equal(toggleBinaryFinding(true), false);

const sites = Array.from({ length: 6 }, (_, index) => ({
  site_code: `SITE_${index}`,
  probing_depth_mm: index === 0 ? 4 : null,
  gingival_margin_mm: index === 0 ? 0 : null,
  bleeding_on_probing: index === 0,
  plaque: false,
  suppuration: false,
}));
const indicators = calculateDraftIndicators([
  { fdi_number: 16, state: "PRESENT", sites },
  { fdi_number: 12, state: "IMPLANT", sites },
  { fdi_number: 11, state: "ABSENT", sites },
]);
assert.deepEqual(indicators.indices.bop, {
  positive_sites: 2,
  evaluated_sites: 12,
  percentage: 16.67,
});
assert.deepEqual(indicators.indices.plaque, {
  positive_sites: 0,
  evaluated_sites: 12,
  percentage: 0,
});

assert.match(editor, /suppuration: eligible \? site\.suppuration === true : null/);
assert.match(editor, /const disabledForState = tooth\.state === "ABSENT"/);
assert.doesNotMatch(editor, /suppuration" && tooth\.state !== "IMPLANT"/);
assert.match(editor, /SiteBinaryToggle/);
assert.match(editor, /QuickBinaryToggle/);
assert.match(editor, /aria-pressed=\{active\}/);
assert.doesNotMatch(editor, /TriState/);
assert.doesNotMatch(editor, /No marcado/);

assert.match(editor, /data-periodontal-context-panel="sticky"/);
assert.match(editor, /data-context-panel-layout="compact"/);
assert.match(editor, /data-context-panel-target-max-height="120"/);
assert.match(editor, /data-periodontal-selected-tooth/);
assert.match(editor, /sticky top-20/);
assert.match(editor, /setActiveFdi\(fdiNumber\)/);
assert.match(editor, /<summary[^>]*>Nota clínica<\/summary>/);
assert.doesNotMatch(editor, /Panel contextual/);
assert.doesNotMatch(editor, /Pieza seleccionada:/);

assert.match(workspace, /Expandir periodontograma/);
assert.match(workspace, /Mostrar menú/);
assert.match(workspace, /setSidebarCollapsed/);
assert.match(workspace, /data-periodontogram-expanded/);
assert.match(patientDetail, /activeTab === "periodontogram" \? "mx-auto max-w-none"/);
assert.match(privateShell, /sidebarCollapsed \? "lg:pl-0" : "lg:pl-72"/);
assert.match(sidebar, /desktopCollapsed \? "lg:-translate-x-full" : "lg:translate-x-0"/);
assert.match(appHeader, /Mostrar menú principal/);

const expandedArchWidth = 1120;
const expandedMainPadding = 72;
const editorPaddingAndScrollbar = 50;
const availableAt1440 = 1440 - expandedMainPadding - editorPaddingAndScrollbar;
assert.ok(
  availableAt1440 >= expandedArchWidth,
  "1440px expanded viewport must fit all 16 tooth columns without meaningful horizontal scroll",
);
assert.match(editor, /min-w-\[1120px\] max-w-\[1600px\]/);
assert.match(editor, /min-w-\[1200px\]/);
assert.match(editor, /data-periodontal-expanded-fit/);
assert.match(editor, /gridTemplateColumns: `144px repeat/);
assert.match(privateShell, /sm:px-7/);
assert.match(editor, /max-w-full overflow-x-auto/);

console.log("periodontogram-pilot-fixes-tests OK");
