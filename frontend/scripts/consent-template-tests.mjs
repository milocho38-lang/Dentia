import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import ts from "typescript";

const root = process.cwd();
const sourcePath = path.join(root, "frontend/components/consents/consentTemplateUi.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const output = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  fileName: sourcePath,
}).outputText;
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "dentia-consent-template-tests-"));
fs.writeFileSync(path.join(tempDir, "consentTemplateUi.js"), output);
const requireFromTemp = createRequire(path.join(tempDir, "runner.cjs"));
const ui = requireFromTemp("./consentTemplateUi.js");

const visualSourcePath = path.join(root, "frontend/components/consents/consentVisualEditorUtils.ts");
const visualOutput = ts.transpileModule(fs.readFileSync(visualSourcePath, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  fileName: visualSourcePath,
}).outputText;
fs.writeFileSync(path.join(tempDir, "consentVisualEditor.js"), visualOutput);
const visual = requireFromTemp("./consentVisualEditor.js");

assert.equal(ui.buildConsentTemplateQuery({ search: " demo ", country: "CO", documentKind: "PROCEDURE_CONSENT", status: "DRAFT", siteId: "site", procedureId: "procedure", specialty: "ENDO" }), "?q=demo&country=CO&document_kind=PROCEDURE_CONSENT&status=DRAFT&site_id=site&procedure_id=procedure&specialty=ENDO");
assert.equal(ui.buildConsentTemplateQuery({ search: "", country: "", documentKind: "", status: "" }), "");

const inserted = ui.insertConsentVariable("Paciente: ", "patient.full_name", 10, 10);
assert.equal(inserted.content, "Paciente: {{ patient.full_name }}");
assert.equal(inserted.caret, inserted.content.length);

const firstCreateForm = ui.createEmptyConsentTemplateForm();
firstCreateForm.name = "Plantilla anterior";
firstCreateForm.site_ids.push("site-1");
const reopenedCreateForm = ui.createEmptyConsentTemplateForm();
assert.equal(reopenedCreateForm.name, "");
assert.deepEqual(reopenedCreateForm.site_ids, []);
assert.equal(reopenedCreateForm.document_kind, "PROCEDURE_CONSENT");
assert.equal(reopenedCreateForm.country_code, "CO");
assert.equal(reopenedCreateForm.scope_type, "GENERAL");
assert.equal(reopenedCreateForm.title, "");
assert.equal(reopenedCreateForm.customize_title, false);
const namedForm = ui.updateConsentTemplateName(reopenedCreateForm, "Consentimiento de endodoncia");
assert.equal(namedForm.title, "Consentimiento de endodoncia");
const customizedForm = ui.toggleCustomConsentTitle(namedForm, true);
const renamedCustomizedForm = ui.updateConsentTemplateName({ ...customizedForm, title: "Autorización para el paciente" }, "Plantilla administrativa");
assert.equal(renamedCustomizedForm.title, "Autorización para el paciente");
assert.equal(ui.toggleCustomConsentTitle(renamedCustomizedForm, false).title, "Plantilla administrativa");
assert.equal(ui.unregisteredVariablesError(["custom.unknown"]), "No se puede publicar. Corrige las siguientes variables no registradas: custom.unknown");

const visualCatalog = [
  { code: "patient.full_name", label: "Nombre completo del paciente", description: "Nombre registrado", category: "Paciente", sample_value: "Paciente demo" },
  { code: "professional.full_name", label: "Nombre completo del profesional", description: "Profesional responsable", category: "Profesional", sample_value: "Profesional demo" },
];
const legacyVisual = visual.technicalToVisualHtml("# Autorización\nPaciente: {{ patient.full_name }}", visualCatalog);
assert.ok(legacyVisual.includes("[Nombre completo del paciente]"));
assert.ok(legacyVisual.includes('data-consent-variable="patient.full_name"'));
assert.equal(legacyVisual.includes("{{ patient.full_name }}"), false);
const insertedVisual = visual.variableToVisualHtml("professional.full_name", visualCatalog);
assert.ok(insertedVisual.includes("[Nombre completo del profesional]"));
assert.ok(insertedVisual.includes('data-consent-variable="professional.full_name"'));
const structuredVariable = visual.restrictedMarkdownToVisualDocument("{{ patient.full_name }}", visualCatalog).blocks[0].children[0];
assert.deepEqual(structuredVariable, {
  type: "consentVariable",
  technicalName: "patient.full_name",
  displayLabel: "Nombre completo del paciente",
  description: "Nombre registrado",
  known: true,
});
const canonicalMarkdown = "# Consentimiento\n\nPaciente: **{{ patient.full_name }}** autoriza a {{ professional.full_name }}.\n\n- Primer punto\n2. Segundo punto\n---\nFin {{ patient.full_name }}{{ professional.full_name }}";
const structuredDocument = visual.restrictedMarkdownToVisualDocument(canonicalMarkdown, visualCatalog);
assert.equal(visual.visualDocumentToRestrictedMarkdown(structuredDocument), canonicalMarkdown);
assert.deepEqual(visual.extractTechnicalVariables(structuredDocument), ["patient.full_name", "professional.full_name"]);
assert.deepEqual(visual.validateVisualDocument(structuredDocument, visualCatalog), {
  valid: true,
  technicalVariables: ["patient.full_name", "professional.full_name"],
  unknownVariables: [],
});
assert.ok(visual.visualDocumentToHtml(structuredDocument).includes("<strong>"));
assert.ok(visual.visualDocumentToHtml(structuredDocument).includes('data-block="number"'));
const invalidVisual = visual.technicalToVisualHtml("{{ custom.unknown }}", visualCatalog);
assert.ok(invalidVisual.includes("[Dato automático no reconocido]"));
assert.ok(invalidVisual.includes("custom.unknown"));
assert.ok(invalidVisual.includes("bg-red-50"));
const unknownDocument = visual.restrictedMarkdownToVisualDocument("Antes {{ custom.unknown }} después", visualCatalog);
assert.deepEqual(visual.validateVisualDocument(unknownDocument, visualCatalog).unknownVariables, ["custom.unknown"]);
assert.equal(visual.visualDocumentToRestrictedMarkdown(unknownDocument), "Antes {{ custom.unknown }} después");
const numbered = visual.restrictedMarkdownToVisualDocument("1. Elemento", visualCatalog);
assert.equal(visual.toggleListBlock(numbered, 0, "number").blocks[0].type, "paragraph");
assert.equal(visual.toggleListBlock(numbered, 0, "bullet").blocks[0].type, "bullet");
const bullet = visual.restrictedMarkdownToVisualDocument("- Elemento", visualCatalog);
assert.equal(visual.toggleListBlock(bullet, 0, "bullet").blocks[0].type, "paragraph");
const emptyList = visual.restrictedMarkdownToVisualDocument("1. ", visualCatalog);
assert.equal(visual.exitEmptyListBlock(emptyList, 0).blocks[0].type, "paragraph");
assert.equal(visual.plainTextToRestrictedMarkdown("Párrafo\n\n• Uno\n2) Dos\u0000"), "Párrafo\n\n- Uno\n2. Dos");
assert.equal(visual.plainTextToRestrictedMarkdown("Texto<script>alert(1)</script><iframe src=x></iframe>javascript:fin"), "Textofin");
assert.deepEqual(visual.groupedConsentVariables(visualCatalog).map(([category]) => category), ["Paciente", "Profesional"]);

let actions = ui.consentVersionActions("DRAFT", new Set(["consent.template.edit_draft", "consent.template.publish", "consent.template.void_draft", "consent.template.create"]));
assert.deepEqual(actions, { edit: true, publish: true, voidDraft: true, retire: false, createFrom: true });
actions = ui.consentVersionActions("PUBLISHED", new Set(["consent.template.read"]));
assert.deepEqual(actions, { edit: false, publish: false, voidDraft: false, retire: false, createFrom: false });

const component = fs.readFileSync(path.join(root, "frontend/components/consents/ConsentTemplatesPage.tsx"), "utf8");
for (const expected of ["Nueva plantilla", "Nombre del consentimiento", "Personalizar título visible", "Título visible", "Nombre con el que encontrará esta plantilla en Dentia.", "Encabezado que aparecerá en el documento para el paciente.", "Editor de borrador", "Vista previa", "Revisar y publicar", "Historial de versiones", "Confirmar revisión clínica", "Retirar", "Anular borrador", "disabled={saving}", "openCreateModal", "closeCreateModal", "resetCreateModalState", "ConsentVisualEditor", "borrador"] ) {
  assert.ok(component.includes(expected), `missing characterized UI contract: ${expected}`);
}
for (const expected of [
  "const canReadLibrary = hasPermission(\"consent.library.read\")",
  "const canManageLibrary = isPlatformAdmin && hasPermission(\"consent.library.manage\")",
  "Biblioteca Dentia",
  "{canReadLibrary && <button",
  "setLibraryError",
  "Reintentar",
  "La Biblioteca Dentia todavía no tiene documentos disponibles en esta base de datos.",
  "Plantilla sugerida por Dentia.",
  "Pendiente de revisión por la clínica",
  "Contenido revisado por la clínica",
  "consent.template.review_content",
  "Normalización:",
  "Apto para adulto en nombre propio",
  "Adulto responsable requerido",
  "Versión actual: v",
  "Ver historial",
  "Versión histórica no apta para nuevos consentimientos.",
  "Firmante:",
  "No requiere firma",
  "Versión anterior no apta para nuevos consentimientos",
  "getConsentLibrarySourceReview",
  "Texto fuente de procedencia",
  "Contenido normalizado para paciente",
  "Agregar plantilla sugerida",
  "Crear copia editable",
  "{canManageLibrary && <button",
  "Revisar equivalencia",
  "const isPlatformAdmin = user?.roles.includes(\"PLATFORM_ADMIN\") ?? false",
  "const canManageLibrary = isPlatformAdmin && hasPermission(\"consent.library.manage\")",
  "libraryCurrentVersion",
  "version.is_current",
  "libraryAction(version.id, \"clone\")",
]) {
  assert.ok(component.includes(expected), `missing library UI contract: ${expected}`);
}
assert.equal(component.includes("libraryItems.length > 0 &&"), false, "library tab must not depend on non-empty items");
assert.equal(component.includes("consent.library.manage\") && <button type=\"button\" onClick={() => setActiveTab(\"library\")"), false, "tenant library tab must not require manage permission");
assert.equal(component.includes("item.versions.find((version) => version.country_code === \"CO\") ?? item.versions[0]"), false, "library cards must not select legacy v1 as current by insertion order");
assert.equal(component.includes("item.versions.find((version) => version.country_code === \"CL\") ?? item.versions[0]"), false, "library cards must not select legacy v1 as current by insertion order");
for (const expected of [
  "País de la empresa:",
  "isPlatformAdmin && country",
  "disabled={!isPlatformAdmin}",
  "El país corresponde a la configuración de la empresa.",
]) {
  assert.ok(component.includes(expected), `missing tenant-country UI guardrail: ${expected}`);
}
const visualComponent = fs.readFileSync(path.join(root, "frontend/components/consents/ConsentVisualEditor.tsx"), "utf8");
for (const expected of ["Insertar dato automático", "Ver código de plantilla", "Volver al editor visual", "Quitar lista", "onPaste", "richTextHtmlToRestrictedMarkdown", "onEditorKeyDown", "role=\"toolbar\"", "aria-label=\"Contenido del consentimiento\""] ) {
  assert.ok(visualComponent.includes(expected), `missing visual editor contract: ${expected}`);
}
const visualUtilsSource = fs.readFileSync(visualSourcePath, "utf8");
for (const expected of ["DOMParser", "script,style,iframe,object,embed,img,link,meta,svg,math", "node.tagName === \"STRONG\"", "node.tagName === \"OL\""]) {
  assert.ok(visualUtilsSource.includes(expected), `missing safe rich-paste contract: ${expected}`);
}
assert.equal(visualComponent.includes("document.execCommand"), false, "legacy execCommand must not drive editor state");
for (const forbidden of ["patientId", "/api/patients/", "OTP", "QR", "firma gráfica", "portal público"]) {
  assert.equal(component.includes(forbidden), false, `out-of-scope patient/signing UI found: ${forbidden}`);
}

console.log("consent-template-tests OK: filters, variables, permissions, lifecycle UI and scope guardrails");
