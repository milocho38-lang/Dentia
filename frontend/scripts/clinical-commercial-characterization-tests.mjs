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
    treatmentService.indexOf("def cancel_procedure("),
  ),
  "OdontogramEvent(",
  "Current mark_procedure_done does not create odontogram events automatically.",
);
notIncludes(
  treatmentService.slice(
    treatmentService.indexOf("def mark_procedure_done("),
    treatmentService.indexOf("def cancel_procedure("),
  ),
  "create_event(",
  "Current mark_procedure_done does not call odontogram create_event.",
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
notIncludes(
  clinicalRecordService.slice(
    clinicalRecordService.indexOf("def sign_clinical_evolution("),
    clinicalRecordService.indexOf("def list_evolution_addenda("),
  ),
  "confirm_event(",
  "Current evolution signing does not confirm odontogram events automatically.",
);
notIncludes(
  clinicalRecordService.slice(
    clinicalRecordService.indexOf("def sign_clinical_evolution("),
    clinicalRecordService.indexOf("def list_evolution_addenda("),
  ),
  "ODONTOGRAM_EVENT_CONFIRMED",
  "Current evolution signing does not audit odontogram confirmation.",
);

includes(
  odontogramService,
  "def create_event(",
  "Odontogram event creation exists.",
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

console.log("clinical-commercial characterization tests OK");
