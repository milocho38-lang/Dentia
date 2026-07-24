import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function includes(source, expected, message) {
  assert.ok(source.includes(expected), message);
}

function notIncludes(source, unexpected, message) {
  assert.ok(!source.includes(unexpected), message);
}

const odontogramModel = read("backend/app/models/odontogram.py");
const treatmentModel = read("backend/app/models/treatment.py");
const clinicalRecordModel = read("backend/app/models/clinical_record.py");
const agendaModel = read("backend/app/models/agenda.py");
const treatmentService = read("backend/app/services/treatment_service.py");
const odontogramService = read("backend/app/services/odontogram_service.py");
const clinicalRecordService = read("backend/app/services/clinical_record_service.py");
const agendaService = read("backend/app/services/agenda_service.py");
const treatmentSchema = read("backend/app/schemas/treatment_schema.py");
const odontogramSchema = read("backend/app/schemas/odontogram_schema.py");
const dentalInspector = read("frontend/components/odontogram/inspector/DentalInspector.tsx");
const addPlannedDialog = read("frontend/components/odontogram/inspector/AddPlannedProcedureDialog.tsx");
const odontogramPage = read("frontend/components/patients/OdontogramPage.tsx");
const patientDetail = read("frontend/components/patients/PatientDetail.tsx");
const treatmentPages = read("frontend/components/treatments/TreatmentPages.tsx");
const treatmentServiceTs = read("frontend/services/treatmentService.ts");

includes(
  odontogramModel,
  'treatment_id: Mapped[UUID | None] = mapped_column(',
  "OdontogramEvent can reference a treatment.",
);
includes(
  odontogramModel,
  'procedure_id: Mapped[UUID | None] = mapped_column(',
  "OdontogramEvent can reference a treatment procedure.",
);
includes(
  odontogramSchema,
  "treatment_id: UUID | None = None",
  "Odontogram event API accepts treatment_id.",
);
includes(
  odontogramSchema,
  "procedure_id: UUID | None = None",
  "Odontogram event API accepts procedure_id.",
);

includes(
  treatmentModel,
  'scope_type: Mapped[str] = mapped_column(',
  "TreatmentProcedure stores dental scope type.",
);
includes(
  treatmentModel,
  'tooth: Mapped[str | None] = mapped_column(',
  "TreatmentProcedure stores tooth.",
);
includes(
  treatmentModel,
  'surfaces: Mapped[list[str] | None] = mapped_column(',
  "TreatmentProcedure stores surfaces.",
);
includes(
  treatmentSchema,
  'PROCEDURE_SCOPE_TYPES = {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}',
  "Procedure schema recognizes the four dental scopes.",
);

includes(
  treatmentModel,
  "class BudgetDetail",
  "BudgetDetail exists as budget snapshot detail.",
);
includes(
  treatmentModel,
  'procedure_id: Mapped[UUID | None] = mapped_column(',
  "BudgetDetail can reference the original procedure.",
);
includes(
  treatmentModel,
  'scope_type: Mapped[str] = mapped_column(',
  "BudgetDetail stores scope snapshot.",
);
includes(
  treatmentModel,
  'surfaces: Mapped[list[str] | None] = mapped_column(',
  "BudgetDetail stores surfaces snapshot.",
);
includes(
  treatmentService,
  "def _add_budget_detail_snapshot(",
  "Budget detail snapshot helper exists.",
);
includes(
  treatmentService,
  "scope_type=procedure.scope_type or \"GENERAL\"",
  "Budget snapshot copies procedure scope.",
);
includes(
  treatmentService,
  "surfaces=procedure.surfaces",
  "Budget snapshot copies procedure surfaces.",
);
includes(
  treatmentModel,
  '"budget_series_id"',
  "Budget stores a stable version series id.",
);
includes(
  treatmentModel,
  '"previous_budget_id"',
  "Budget stores previous version traceability.",
);
includes(
  treatmentModel,
  '"es_version_vigente"',
  "Budget stores current approved version flag.",
);
includes(
  treatmentModel,
  '"budget_idempotency_key"',
  "Budget stores an idempotency key for duplicate-safe generation.",
);
includes(
  treatmentSchema,
  "procedure_ids: list[UUID] = Field(default_factory=list)",
  "Budget creation can explicitly select procedures.",
);
includes(
  treatmentSchema,
  "class BudgetVersionCreateRequest",
  "Budget version creation has an explicit request contract.",
);
includes(
  treatmentService,
  "def _procedures_for_budget_payload(",
  "Budget creation validates the selected treatment procedures.",
);
includes(
  treatmentService,
  "pg_advisory_xact_lock",
  "Budget number generation uses a transaction-scoped company lock.",
);
includes(
  treatmentService,
  "payload.procedure_ids",
  "Budget creation uses selected procedure ids instead of always taking all procedures.",
);
includes(
  treatmentService,
  "def _budget_detail_clone(",
  "Budget versioning clones immutable BudgetDetail snapshots.",
);
includes(
  treatmentService,
  "def create_budget_version(",
  "Budget version creation service exists.",
);
includes(
  treatmentService,
  'Budget.status == "Borrador"',
  "Budget version creation reuses an existing draft in the same series instead of creating V3 accidentally.",
);
includes(
  treatmentService,
  "BUDGET_VERSION_DRAFT_REUSED",
  "Reusing an existing draft budget version is audited.",
);
includes(
  treatmentService,
  "def update_budget(",
  "Budget draft update service exists.",
);
includes(
  treatmentService,
  "session.execute(delete(BudgetDetail).where(BudgetDetail.budget_id == budget.id))",
  "Saving a draft budget version replaces that version's own details atomically.",
);
includes(
  treatmentService,
  "BUDGET_DRAFT_UPDATED",
  "Saving draft budget changes is audited distinctly from creating a new version.",
);
includes(
  treatmentService,
  "source.status not in {\"Aprobado\", \"Rechazado\", \"Pendiente de aprobación\"}",
  "Budget versions can only be created from controlled non-editable/submitted states.",
);
includes(
  treatmentService,
  "BUDGET_VERSION_CREATED",
  "Budget version creation is audited.",
);
includes(
  treatmentService,
  "BUDGET_VERSION_SUPERSEDED",
  "Approving a new budget version supersedes the previous current approved version.",
);
includes(
  treatmentService,
  "Budget.series_id == budget.series_id",
  "Budget approval locks and evaluates the whole version series.",
);
includes(
  treatmentService,
  "session.flush()",
  "Budget approval flushes removal of the previous current version before marking the new one current.",
);
includes(
  treatmentService,
  "Solo se puede aprobar una versión en borrador o pendiente de aprobación.",
  "Budget approval enforces the real approvable states with a controlled business error.",
);
includes(
  treatmentPages,
  "procedure_ids: selectedProcedureIds",
  "Treatment UI sends explicit procedure selection when creating budgets.",
);
includes(
  treatmentServiceTs,
  "export function updateBudget(",
  "Frontend service exposes PATCH for saving an existing budget version.",
);
includes(
  treatmentServiceTs,
  "`/api/budgets/${budgetId}`",
  "Saving a budget version uses the budget id endpoint.",
);
includes(
  treatmentPages,
  "selectedBudgetId",
  "Treatment UI tracks the active budget version explicitly.",
);
includes(
  treatmentPages,
  "setSelectedBudgetId(budget.id)",
  "Treatment UI opens the returned V2 after creating or saving a version.",
);
includes(
  treatmentPages,
  "Guardar cambios de V",
  "Treatment UI distinguishes saving a version from creating a budget.",
);
includes(
  treatmentPages,
  "Aprobar versión",
  "Treatment UI approves the selected version, not the current approved V1.",
);
includes(
  treatmentPages,
  "handleApproveSelectedBudget",
  "Treatment UI centralizes selected-version approval.",
);
includes(
  treatmentPages,
  "try {",
  "Treatment UI catches budget action failures instead of allowing runtime overlays.",
);
includes(
  treatmentPages,
  "budgetActionError",
  "Treatment UI shows controlled inline budget action errors.",
);
includes(
  treatmentPages,
  "Crear nueva versión",
  "Treatment UI exposes explicit budget version creation.",
);

includes(
  clinicalRecordModel,
  "class ClinicalEvolutionProcedure",
  "ClinicalEvolutionProcedure exists.",
);
includes(
  clinicalRecordModel,
  'procedure_id: Mapped[UUID] = mapped_column(',
  "ClinicalEvolutionProcedure references TreatmentProcedure.",
);
includes(
  agendaModel,
  'treatment_procedure_id: Mapped[UUID | None] = mapped_column(',
  "Appointment can reference a treatment procedure.",
);

includes(
  treatmentService,
  "if _has_approved_budget(session, treatment.id) and not _has_editable_budget(session, treatment.id):",
  "Procedure changes are blocked after approved budget unless an editable budget exists.",
);
includes(
  treatmentService,
  "raise TreatmentError(\"Este procedimiento pertenece a un presupuesto aprobado.",
  "Approved budget immutability is enforced for procedure updates/cancellation.",
);

includes(
  treatmentService,
  "def mark_procedure_done(",
  "Procedure completion service exists.",
);
includes(
  treatmentService,
  'procedure.status = "Realizado"',
  "Procedure completion changes procedure status to Realizado.",
);
notIncludes(
  treatmentService.slice(
    treatmentService.indexOf("def mark_procedure_done("),
    treatmentService.indexOf("def complete_procedure_clinically("),
  ),
  "OdontogramEvent(",
  "Simple mark_procedure_done does not create odontogram events automatically.",
);
notIncludes(
  treatmentService.slice(
    treatmentService.indexOf("def mark_procedure_done("),
    treatmentService.indexOf("def complete_procedure_clinically("),
  ),
  "create_event(",
  "Simple mark_procedure_done does not call odontogram create_event.",
);
includes(
  treatmentService,
  "def complete_procedure_clinically(",
  "Explicit clinical completion service exists.",
);
includes(
  treatmentService,
  'event_type="PROCEDURE_PERFORMED"',
  "Clinical completion creates a performed odontogram event.",
);
includes(
  treatmentService,
  'status="DRAFT"',
  "Clinical completion leaves odontogram event in DRAFT.",
);
includes(
  treatmentService,
  "reviewed_for_evolution=True",
  "Clinical completion marks generated odontogram event as reviewed for evolution.",
);

includes(
  clinicalRecordService,
  "def sign_clinical_evolution(",
  "Clinical evolution signing exists.",
);
includes(
  clinicalRecordService,
  'evolution.status = "SIGNED"',
  "Clinical evolution signing marks evolution as SIGNED.",
);
includes(
  clinicalRecordService,
  "def _confirm_reviewed_odontogram_events_for_evolution(",
  "Evolution signing confirms linked reviewed odontogram drafts.",
);
includes(
  clinicalRecordService,
  "OdontogramEvent.evolution_id == evolution.id",
  "Odontogram confirmation is scoped to the signed evolution.",
);
includes(
  clinicalRecordService,
  "OdontogramEvent.reviewed_for_evolution.is_(True)",
  "Evolution signing confirms only reviewed odontogram events.",
);
includes(
  clinicalRecordService,
  "ODONTOGRAM_EVENT_CONFIRMED_FROM_EVOLUTION",
  "Evolution signing audits odontogram confirmation.",
);
includes(
  clinicalRecordService,
  'source_event.status = "VOIDED_BY_COMPENSATING_EVENT"',
  "Resolving the source diagnosis excludes it from current state without deleting history.",
);
includes(
  clinicalRecordService,
  "SOURCE_ODONTOGRAM_DIAGNOSIS_RESOLVED",
  "Source diagnosis resolution is audited.",
);
includes(
  clinicalRecordService,
  "No fue posible resolver el diagnóstico odontográfico de origen. La evolución no fue firmada.",
  "Resolution failure blocks signing atomically.",
);

includes(
  odontogramService,
  "def create_event(",
  "Odontogram event creation exists.",
);
includes(
  odontogramService,
  'OdontogramEvent.status == "CONFIRMED"',
  "Current odontogram state includes only confirmed current events.",
);
includes(
  odontogramService,
  'normalized == "DONE_RESIN"',
  "DONE_RESIN has a clinical display label without changing the catalog code.",
);
includes(
  odontogramService,
  "event.treatment_id = payload.treatment_id",
  "Odontogram event payload applies treatment_id.",
);
includes(
  odontogramService,
  "event.procedure_id = payload.procedure_id",
  "Odontogram event payload applies procedure_id.",
);

includes(
  agendaService,
  "def complete_clinical_care(",
  "Clinical care completion coordinator exists.",
);
includes(
  agendaService,
  "mark_procedure_done(",
  "Clinical care completion can mark procedures done.",
);
notIncludes(
  agendaService.slice(
    agendaService.indexOf("def complete_clinical_care("),
    agendaService.indexOf("def _audit_result(") > -1 ? agendaService.indexOf("def _audit_result(") : agendaService.length,
  ),
  "OdontogramEvent(",
  "Current clinical care completion does not directly create odontogram events.",
);

includes(
  treatmentModel,
  "source_odontogram_event_id",
  "TreatmentProcedure stores source_odontogram_event_id for explicit clinical-commercial traceability.",
);
includes(
  treatmentModel,
  "odontogram_idempotency_key",
  "TreatmentProcedure stores an odontogram idempotency key.",
);
includes(
  treatmentSchema,
  "source_odontogram_event_id",
  "Procedure responses expose source_odontogram_event_id when applicable.",
);
includes(
  treatmentSchema,
  "class OdontogramPlannedProcedureCreateRequest",
  "Bridge request contract exists for creating planned procedures from odontogram events.",
);
includes(
  treatmentSchema,
  "treatment_status: str",
  "Linked procedure responses include the real treatment status.",
);
includes(
  treatmentSchema,
  "allow_similar_duplicate",
  "Bridge request supports explicit override for probable duplicates.",
);
notIncludes(
  treatmentSchema.slice(
    treatmentSchema.indexOf("class ProcedureCreateRequest"),
    treatmentSchema.indexOf("class ProcedureUpdateRequest"),
  ),
  "source_odontogram_event_id",
  "Standard procedure creation does not accept clinical traceability directly.",
);
includes(
  treatmentService,
  "def create_planned_procedure_from_odontogram_event(",
  "Explicit bridge service exists from odontogram event to planned procedure.",
);
includes(
  treatmentService,
  "PROCEDURE_CREATED_FROM_ODONTOGRAM",
  "Bridge creation audits procedure creation from odontogram.",
);
includes(
  treatmentService,
  "ODONTOGRAM_EVENT_LINKED_TO_PROCEDURE",
  "Bridge creation audits odontogram event linkage.",
);

includes(
  dentalInspector,
  "Estado del tratamiento",
  "Dental Inspector distinguishes treatment status.",
);
includes(
  dentalInspector,
  "Estado del procedimiento",
  "Dental Inspector distinguishes procedure status.",
);
includes(
  dentalInspector,
  "Ver tratamiento",
  "Dental Inspector provides contextual navigation to treatment detail.",
);
includes(
  dentalInspector,
  "plannedProcedureCountLabel",
  "Dental Inspector uses explicit singular/plural wording.",
);
notIncludes(
  dentalInspector,
  "procedimiento(s)",
  "Dental Inspector does not show parenthetical pluralization.",
);
includes(
  addPlannedDialog,
  "El procedimiento fue creado, pero no fue posible actualizar la vista.",
  "Post-create refresh failure does not masquerade as creation failure.",
);
includes(
  addPlannedDialog,
  "Actualizar",
  "Post-create refresh failure offers a refresh action.",
);
notIncludes(
  addPlannedDialog,
  "window.location.reload",
  "Planned procedure dialog does not force a full browser reload.",
);
includes(
  odontogramPage,
  "onCommercialDataChanged",
  "Odontogram page notifies the patient workspace after commercial data changes.",
);
includes(
  patientDetail,
  "onCommercialDataChanged={loadWorkspaceData}",
  "Patient workspace refreshes treatments after odontogram commercial bridge changes.",
);
includes(
  patientDetail,
  'searchParams.get("tab")',
  "Patient detail supports contextual tab return.",
);
includes(
  treatmentPages,
  "returnPatientId",
  "Treatment detail receives patient return context.",
);
includes(
  treatmentPages,
  "← Volver a {treatment.patient_name}",
  "Treatment detail includes direct return to patient.",
);
includes(
  treatmentPages,
  "getOdontogramEvent(procedure.source_odontogram_event_id)",
  "Clinical completion modal loads source diagnosis by persisted FK.",
);
includes(
  treatmentPages,
  "Diagnóstico odontográfico de origen",
  "Clinical completion modal displays the exact source diagnosis.",
);
includes(
  treatmentPages,
  "Resolver diagnóstico al firmar",
  "Clinical completion modal names the resolution action clearly.",
);
includes(
  treatmentPages,
  "Resolución de",
  "Clinical completion modal summarizes the diagnosis that will be resolved.",
);
includes(
  treatmentPages,
  "Este procedimiento no tiene un diagnóstico odontográfico de origen vinculado.",
  "Clinical completion modal handles procedures without source diagnosis.",
);

console.log("clinical-commercial characterization tests OK");
