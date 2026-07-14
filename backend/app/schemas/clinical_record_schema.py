from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


CLINICAL_RECORD_STATUSES = {"ACTIVA", "INACTIVA"}
ALLERGY_GLOBAL_STATES = {"NIEGA_ALERGIAS", "NO_CONFIRMADA", "CON_ALERGIAS"}
MEDICAL_HISTORY_GLOBAL_STATES = {"NIEGA_ANTECEDENTES", "NO_CONFIRMADO", "CON_ANTECEDENTES"}
PRESENT_VALUES = {"SI", "NO", "DESCONOCIDO"}
ALLERGY_TYPES = {"medicamento", "anestésico", "látex", "alimento", "otro"}
ALLERGY_SEVERITIES = {"leve", "moderada", "severa", "anafilaxia", "desconocida"}
ALLERGY_STATUSES = {"confirmada", "no confirmada", "descartada"}
MEDICATION_STATUSES = {"activo", "suspendido"}
EVOLUTION_STATUSES = {"DRAFT", "SIGNED", "VOIDED_BY_COMPENSATING_RECORD"}
EVOLUTION_PROCEDURE_ACTIONS = {"PLANNED", "PERFORMED", "REVIEWED", "SUSPENDED"}

INITIAL_MEDICAL_HISTORY_TYPES = {
    "hipertensión",
    "enfermedad cardiovascular",
    "diabetes",
    "trastorno de coagulación",
    "enfermedad respiratoria",
    "enfermedad renal",
    "enfermedad hepática",
    "enfermedad neurológica",
    "inmunosupresión",
    "cáncer",
    "hospitalización",
    "cirugía",
    "transfusión",
    "prótesis o dispositivo",
    "embarazo",
    "lactancia",
    "otro",
}


class HabitsInput(BaseModel):
    tobacco: str | None = Field(default=None, max_length=300)
    alcohol: str | None = Field(default=None, max_length=300)
    substances: str | None = Field(default=None, max_length=300)
    bruxism: str | None = Field(default=None, max_length=300)
    oral_hygiene: str | None = Field(default=None, max_length=500)
    brushing_frequency: str | None = Field(default=None, max_length=120)
    dental_floss: str | None = Field(default=None, max_length=120)
    sugary_diet: str | None = Field(default=None, max_length=300)
    others: str | None = Field(default=None, max_length=1000)


class DentalHistoryInput(BaseModel):
    last_visit: str | None = Field(default=None, max_length=200)
    previous_treatments: str | None = Field(default=None, max_length=1000)
    orthodontics: str | None = Field(default=None, max_length=500)
    implants: str | None = Field(default=None, max_length=500)
    surgeries: str | None = Field(default=None, max_length=500)
    trauma: str | None = Field(default=None, max_length=500)
    bleeding: str | None = Field(default=None, max_length=500)
    sensitivity: str | None = Field(default=None, max_length=500)
    pain: str | None = Field(default=None, max_length=500)
    oral_habits: str | None = Field(default=None, max_length=500)
    previous_experiences: str | None = Field(default=None, max_length=1000)
    observations: str | None = Field(default=None, max_length=1500)


class ClinicalRecordBaseInput(BaseModel):
    opening_site_id: UUID | None = None
    opening_dentist_id: UUID | None = None
    chief_complaint: str | None = Field(default=None, max_length=4000)
    current_situation: str | None = Field(default=None, max_length=4000)
    situation_start: str | None = Field(default=None, max_length=200)
    situation_evolution: str | None = Field(default=None, max_length=4000)
    symptoms: str | None = Field(default=None, max_length=3000)
    previous_treatments: str | None = Field(default=None, max_length=3000)
    informant_type: str | None = Field(default=None, max_length=50)
    informant_responsible_id: UUID | None = None
    informant_name: str | None = Field(default=None, max_length=200)
    informant_relationship: str | None = Field(default=None, max_length=100)
    informant_document: str | None = Field(default=None, max_length=80)
    observations: str | None = Field(default=None, max_length=4000)
    habits: HabitsInput = Field(default_factory=HabitsInput)
    dental_history: DentalHistoryInput = Field(default_factory=DentalHistoryInput)
    allergies_state: str = "NO_CONFIRMADA"
    medical_history_state: str = "NO_CONFIRMADO"

    @field_validator(
        "chief_complaint",
        "current_situation",
        "situation_start",
        "situation_evolution",
        "symptoms",
        "previous_treatments",
        "informant_type",
        "informant_name",
        "informant_relationship",
        "informant_document",
        "observations",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("allergies_state")
    @classmethod
    def validate_allergy_state(cls, value: str) -> str:
        if value not in ALLERGY_GLOBAL_STATES:
            raise ValueError("Estado global de alergias no válido.")
        return value

    @field_validator("medical_history_state")
    @classmethod
    def validate_medical_state(cls, value: str) -> str:
        if value not in MEDICAL_HISTORY_GLOBAL_STATES:
            raise ValueError("Estado global de antecedentes no válido.")
        return value


class ClinicalRecordCreateRequest(ClinicalRecordBaseInput):
    pass


class ClinicalRecordDraftUpdateRequest(ClinicalRecordBaseInput):
    version: int = Field(ge=1)


class ClinicalRecordResponse(BaseModel):
    id: UUID
    patient_id: UUID
    status: str
    opened_at: datetime
    opening_site_id: UUID | None
    opening_dentist_id: UUID | None
    chief_complaint: str | None
    current_situation: str | None
    situation_start: str | None
    situation_evolution: str | None
    symptoms: str | None
    previous_treatments: str | None
    informant_type: str | None
    informant_name: str | None
    informant_relationship: str | None
    informant_document: str | None
    observations: str | None
    habits: HabitsInput
    dental_history: DentalHistoryInput
    allergies_state: str
    medical_history_state: str
    version: int
    created_at: datetime
    updated_at: datetime
    terminology: dict[str, str]


class ClinicalRecordEnvelope(BaseModel):
    exists: bool
    record: ClinicalRecordResponse | None = None
    terminology: dict[str, str]


class MedicalHistoryItemInput(BaseModel):
    type: str = Field(min_length=2, max_length=120)
    present: str = "DESCONOCIDO"
    detail: str | None = Field(default=None, max_length=3000)
    severity: str | None = Field(default=None, max_length=40)
    status: str = Field(default="activo", max_length=40)
    source: str | None = Field(default=None, max_length=120)
    version: int | None = Field(default=None, ge=1)

    @field_validator("type", "present", "status")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("detail", "severity", "source")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("present")
    @classmethod
    def validate_present(cls, value: str) -> str:
        if value not in PRESENT_VALUES:
            raise ValueError("Valor de antecedente no válido.")
        return value


class MedicalHistoryItemResponse(BaseModel):
    id: UUID
    type: str
    present: str
    detail: str | None
    severity: str | None
    status: str
    source: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class MedicalHistoryUpsertRequest(BaseModel):
    record_version: int = Field(ge=1)
    items: list[MedicalHistoryItemInput] = Field(default_factory=list)
    medical_history_state: str = "NO_CONFIRMADO"

    @field_validator("medical_history_state")
    @classmethod
    def validate_medical_state(cls, value: str) -> str:
        if value not in MEDICAL_HISTORY_GLOBAL_STATES:
            raise ValueError("Estado global de antecedentes no válido.")
        return value


class MedicalHistoryResponse(BaseModel):
    items: list[MedicalHistoryItemResponse]
    record_version: int
    medical_history_state: str


class AllergyInput(BaseModel):
    type: str
    substance: str = Field(min_length=1, max_length=200)
    reaction: str | None = Field(default=None, max_length=300)
    severity: str = "desconocida"
    status: str = "no confirmada"
    critical_alert: bool = False
    observations: str | None = Field(default=None, max_length=3000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in ALLERGY_TYPES:
            raise ValueError("Tipo de alergia no válido.")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in ALLERGY_SEVERITIES:
            raise ValueError("Severidad no válida.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLERGY_STATUSES:
            raise ValueError("Estado de alergia no válido.")
        return value

    @field_validator("substance", "reaction", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class AllergyUpdateRequest(AllergyInput):
    version: int = Field(ge=1)


class AllergyResponse(BaseModel):
    id: UUID
    type: str
    substance: str
    reaction: str | None
    severity: str
    status: str
    critical_alert: bool
    observations: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class AllergyListResponse(BaseModel):
    items: list[AllergyResponse]
    record_version: int
    allergies_state: str


class MedicationInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dose: str | None = Field(default=None, max_length=120)
    frequency: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    since: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=300)
    prescriber: str | None = Field(default=None, max_length=200)
    status: str = "activo"
    observations: str | None = Field(default=None, max_length=3000)

    @field_validator(
        "name",
        "dose",
        "frequency",
        "route",
        "since",
        "reason",
        "prescriber",
        "observations",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in MEDICATION_STATUSES:
            raise ValueError("Estado de medicamento no válido.")
        return value


class MedicationUpdateRequest(MedicationInput):
    version: int = Field(ge=1)


class ClinicalEvolutionProcedureInput(BaseModel):
    treatment_id: UUID | None = None
    procedure_id: UUID
    action: str = "PERFORMED"
    observations: str | None = Field(default=None, max_length=1500)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in EVOLUTION_PROCEDURE_ACTIONS:
            raise ValueError("Acción de procedimiento no válida.")
        return normalized

    @field_validator("observations")
    @classmethod
    def strip_observations(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ClinicalEvolutionBaseInput(BaseModel):
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    site_id: UUID | None = None
    dentist_id: UUID | None = None
    attended_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=4000)
    subjective: str | None = Field(default=None, max_length=6000)
    objective: str | None = Field(default=None, max_length=6000)
    assessment: str | None = Field(default=None, max_length=6000)
    performed_procedure: str | None = Field(default=None, max_length=6000)
    anesthesia: str | None = Field(default=None, max_length=3000)
    materials: str | None = Field(default=None, max_length=3000)
    administered_medications: str | None = Field(default=None, max_length=3000)
    findings: str | None = Field(default=None, max_length=5000)
    complications: str | None = Field(default=None, max_length=5000)
    indications: str | None = Field(default=None, max_length=5000)
    recommendations: str | None = Field(default=None, max_length=5000)
    next_control_at: datetime | None = None
    next_control_reason: str | None = Field(default=None, max_length=2000)
    followup_id: UUID | None = None
    observations: str | None = Field(default=None, max_length=4000)
    procedures: list[ClinicalEvolutionProcedureInput] = Field(default_factory=list)

    @field_validator(
        "reason",
        "subjective",
        "objective",
        "assessment",
        "performed_procedure",
        "anesthesia",
        "materials",
        "administered_medications",
        "findings",
        "complications",
        "indications",
        "recommendations",
        "next_control_reason",
        "observations",
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ClinicalEvolutionCreateRequest(ClinicalEvolutionBaseInput):
    pass


class ClinicalEvolutionDraftUpdateRequest(ClinicalEvolutionBaseInput):
    version: int = Field(ge=1)


class ClinicalEvolutionSignRequest(BaseModel):
    version: int = Field(ge=1)
    confirm_complete: bool = True


class ClinicalEvolutionProcedureResponse(BaseModel):
    id: UUID
    treatment_id: UUID | None
    procedure_id: UUID
    procedure_name: str | None = None
    action: str
    observations: str | None
    created_at: datetime


class ClinicalEvolutionAddendumCreateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=3000)
    content: str = Field(min_length=3, max_length=8000)
    dentist_id: UUID | None = None
    site_id: UUID | None = None

    @field_validator("reason", "content")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()


class ClinicalEvolutionAddendumResponse(BaseModel):
    id: UUID
    evolution_id: UUID
    reason: str
    content: str
    dentist_id: UUID
    dentist_name: str | None = None
    site_id: UUID
    site_name: str | None = None
    content_hash: str | None
    created_by: UUID
    created_at: datetime


class ClinicalEvolutionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_record_id: UUID
    appointment_id: UUID | None
    treatment_id: UUID | None
    treatment_name: str | None = None
    site_id: UUID
    site_name: str | None = None
    dentist_id: UUID
    dentist_name: str | None = None
    attended_at: datetime
    timezone_name: str
    reason: str | None
    subjective: str | None
    objective: str | None
    assessment: str | None
    performed_procedure: str | None
    anesthesia: str | None
    materials: str | None
    administered_medications: str | None
    findings: str | None
    complications: str | None
    indications: str | None
    recommendations: str | None
    next_control_at: datetime | None
    next_control_reason: str | None
    followup_id: UUID | None
    observations: str | None
    status: str
    version: int
    content_hash: str | None
    signed_at: datetime | None
    signed_by: UUID | None
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
    procedures: list[ClinicalEvolutionProcedureResponse] = Field(default_factory=list)
    addenda: list[ClinicalEvolutionAddendumResponse] = Field(default_factory=list)
    terminology: dict[str, str]


class ClinicalEvolutionListResponse(BaseModel):
    items: list[ClinicalEvolutionResponse]


class ClinicalTimelineItemResponse(BaseModel):
    id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID | None
    title: str
    summary: str | None
    clinical_date: datetime
    site_id: UUID | None
    site_name: str | None = None
    dentist_id: UUID | None
    dentist_name: str | None = None
    metadata: dict | None = None


class ClinicalTimelineResponse(BaseModel):
    items: list[ClinicalTimelineItemResponse]
    terminology: dict[str, str]


class MedicationResponse(BaseModel):
    id: UUID
    name: str
    dose: str | None
    frequency: str | None
    route: str | None
    since: str | None
    reason: str | None
    prescriber: str | None
    status: str
    observations: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class MedicationListResponse(BaseModel):
    items: list[MedicationResponse]
    record_version: int


class ClinicalSummaryResponse(BaseModel):
    patient_id: UUID
    exists: bool
    terminology: dict[str, str]
    limited: bool
    has_critical_alerts: bool
    requires_clinical_precaution: bool
    message: str | None = None
    opened_at: datetime | None = None
    updated_at: datetime | None = None
    allergies_state: str | None = None
    medical_history_state: str | None = None
    critical_allergies: list[AllergyResponse] = Field(default_factory=list)
    active_medications: list[MedicationResponse] = Field(default_factory=list)
    relevant_medical_history: list[MedicalHistoryItemResponse] = Field(default_factory=list)
    active_diagnoses: list = Field(default_factory=list)
    last_evolution: dict | None = None

    @model_validator(mode="after")
    def validate_limited_payload(self):
        if self.limited:
            self.critical_allergies = []
            self.active_medications = []
            self.relevant_medical_history = []
            self.active_diagnoses = []
            self.last_evolution = None
        return self
