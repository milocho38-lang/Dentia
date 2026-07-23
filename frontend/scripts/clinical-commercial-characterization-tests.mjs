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

notIncludes(
  treatmentModel,
  "source_odontogram_event_id",
  "TreatmentProcedure does not yet store source_odontogram_event_id.",
);
notIncludes(
  treatmentSchema,
  "source_odontogram_event_id",
  "Procedure create/update API does not yet accept source_odontogram_event_id.",
);

console.log("clinical-commercial characterization tests OK");
