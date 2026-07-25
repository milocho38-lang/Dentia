from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


TREATMENT_STATUSES = {
    "Borrador",
    "Presupuestado",
    "Aprobado",
    "En ejecución",
    "Pausado",
    "Finalizado",
    "Cancelado",
}
PROCEDURE_STATUSES = {
    "Pendiente",
    "Agendado",
    "En proceso",
    "Realizado",
    "Cancelado",
}
BUDGET_STATUSES = {
    "Borrador",
    "Pendiente de aprobación",
    "Aprobado",
    "Rechazado",
    "En ejecución",
    "Finalizado",
}
PAYMENT_METHODS = {"Efectivo", "Transferencia", "Tarjeta", "Otro"}
PROCEDURE_SCOPE_TYPES = {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}
PROCEDURE_ZONES = {
    "UPPER_ARCH",
    "LOWER_ARCH",
    "FULL_MOUTH",
    "QUADRANT_1",
    "QUADRANT_2",
    "QUADRANT_3",
    "QUADRANT_4",
    "ANTERIOR",
    "POSTERIOR",
}
PROCEDURE_SURFACES = {
    "VESTIBULAR",
    "LINGUAL",
    "PALATAL",
    "MESIAL",
    "DISTAL",
    "OCCLUSAL",
    "INCISAL",
}
PROCEDURE_ODONTOGRAM_BEHAVIORS = {
    "UNCONFIGURED",
    "NO_CHANGE",
    "OPTIONAL_DIAGNOSIS",
    "REQUIRES_DIAGNOSIS",
}
PROCEDURE_DIAGNOSIS_MODES = {"NONE", "CREATE_NEW", "USE_EXISTING"}


class TreatmentCreateRequest(BaseModel):
    patient_id: UUID
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    specialty: str | None = Field(default=None, max_length=120)
    responsible_dentist_id: UUID | None = None
    main_site_id: UUID | None = None
    start_date: date | None = None
    observations: str | None = None

    @field_validator("name", "description", "specialty", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class TreatmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    specialty: str | None = Field(default=None, max_length=120)
    responsible_dentist_id: UUID | None = None
    main_site_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    observations: str | None = None

    @field_validator("name", "description", "specialty", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class StatusReasonRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class TreatmentSummaryResponse(BaseModel):
    gross_value: Decimal
    discount_value: Decimal
    final_value: Decimal
    paid_value: Decimal
    balance: Decimal
    procedures_total: int
    procedures_done: int


class TreatmentListItemResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    name: str
    status: str
    responsible_dentist_id: UUID | None
    responsible_dentist_name: str | None
    main_site_id: UUID | None
    main_site_name: str | None
    final_value: Decimal
    paid_value: Decimal
    balance: Decimal
    updated_at: datetime


class TreatmentListResponse(BaseModel):
    items: list[TreatmentListItemResponse]
    total: int


class TreatmentResponse(TreatmentListItemResponse):
    description: str | None
    specialty: str | None
    start_date: date | None
    end_date: date | None
    observations: str | None
    created_at: datetime
    summary: TreatmentSummaryResponse


class ProcedureCreateRequest(BaseModel):
    catalog_procedure_id: UUID | None = None
    name: str = Field(min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    unit_value: Decimal = Field(default=Decimal("0"), ge=0)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    status: str = "Pendiente"
    estimated_date: date | None = None
    observations: str | None = None
    requires_tooth: bool = False
    scope_type: str = "GENERAL"
    zone: str | None = Field(default=None, max_length=40)
    tooth: str | None = Field(default=None, max_length=30)
    surfaces: list[str] | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in PROCEDURE_STATUSES:
            raise ValueError("Estado de procedimiento no válido.")
        return value

    @field_validator("scope_type")
    @classmethod
    def valid_scope_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance dental no válido.")
        return normalized

    @field_validator("zone")
    @classmethod
    def valid_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ZONES:
            raise ValueError("Zona dental no válida.")
        return normalized

    @field_validator("surfaces")
    @classmethod
    def valid_surfaces(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [surface.strip().upper() for surface in value if surface and surface.strip()]
        invalid = [surface for surface in normalized if surface not in PROCEDURE_SURFACES]
        if invalid:
            raise ValueError("Cara dental no válida.")
        return normalized

    @field_validator("name", "category", "observations", "tooth")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ProcedureUpdateRequest(BaseModel):
    catalog_procedure_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    unit_value: Decimal | None = Field(default=None, ge=0)
    quantity: Decimal | None = Field(default=None, gt=0)
    status: str | None = None
    estimated_date: date | None = None
    observations: str | None = None
    requires_tooth: bool | None = None
    scope_type: str | None = None
    zone: str | None = Field(default=None, max_length=40)
    tooth: str | None = Field(default=None, max_length=30)
    surfaces: list[str] | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str | None) -> str | None:
        if value is not None and value not in PROCEDURE_STATUSES:
            raise ValueError("Estado de procedimiento no válido.")
        return value

    @field_validator("scope_type")
    @classmethod
    def valid_scope_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance dental no válido.")
        return normalized

    @field_validator("zone")
    @classmethod
    def valid_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ZONES:
            raise ValueError("Zona dental no válida.")
        return normalized

    @field_validator("surfaces")
    @classmethod
    def valid_surfaces(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [surface.strip().upper() for surface in value if surface and surface.strip()]
        invalid = [surface for surface in normalized if surface not in PROCEDURE_SURFACES]
        if invalid:
            raise ValueError("Cara dental no válida.")
        return normalized

    @field_validator("name", "category", "observations", "tooth")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class LinkProcedureAppointmentRequest(BaseModel):
    appointment_id: UUID


class ProcedureResponse(BaseModel):
    id: UUID
    treatment_id: UUID
    patient_id: UUID
    catalog_procedure_id: UUID | None
    name: str
    category: str | None
    dentist_id: UUID | None
    dentist_name: str | None
    site_id: UUID | None
    site_name: str | None
    appointment_id: UUID | None
    source_odontogram_event_id: UUID | None = None
    unit_value: Decimal
    quantity: Decimal
    total_value: Decimal
    status: str
    estimated_date: date | None
    performed_at: datetime | None
    observations: str | None
    requires_tooth: bool
    scope_type: str
    zone: str | None
    tooth: str | None
    surfaces: list[str] | None
    scope_label: str


class ProcedureWithDiagnosisCreateRequest(ProcedureCreateRequest):
    idempotency_key: str = Field(min_length=8, max_length=120)
    diagnosis_mode: str = "CREATE_NEW"
    diagnosis_catalog_item_id: UUID | None = None
    existing_odontogram_event_id: UUID | None = None
    dentition: str = "PERMANENT"
    diagnosis_observation: str | None = Field(default=None, max_length=3000)
    allow_existing_duplicate: bool = False

    @field_validator("idempotency_key", "diagnosis_observation")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("diagnosis_mode")
    @classmethod
    def valid_diagnosis_mode(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_DIAGNOSIS_MODES:
            raise ValueError("Modo de diagnóstico odontográfico no válido.")
        return normalized

    @field_validator("dentition")
    @classmethod
    def valid_dentition(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"PERMANENT", "PRIMARY", "SUPERNUMERARY"}:
            raise ValueError("Dentición no válida.")
        return normalized


class ProcedureWithDiagnosisCreateResponse(BaseModel):
    procedure: ProcedureResponse | None
    diagnosis_event_id: UUID | None = None
    diagnosis_created: bool = False
    diagnosis_reused: bool = False
    compatible_existing_event_id: UUID | None = None
    idempotency_key: str
    idempotent_replay: bool = False
    message: str


SOURCE_DIAGNOSIS_ACTIONS = {"KEEP_ACTIVE", "RESOLVE_ON_SIGN"}


class ProcedureClinicalCompletionRequest(BaseModel):
    clinical_evolution_id: UUID
    odontogram_catalog_item_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=120)
    source_odontogram_event_id: UUID | None = None
    source_diagnosis_action: str = "KEEP_ACTIVE"
    scope_type: str = "TOOTH"
    zone: str | None = Field(default=None, max_length=40)
    tooth: str | None = Field(default=None, max_length=30)
    surfaces: list[str] | None = None
    dentition: str = "PERMANENT"
    observation: str | None = Field(default=None, max_length=3000)

    @field_validator("idempotency_key", "zone", "tooth", "observation")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("source_diagnosis_action")
    @classmethod
    def valid_source_diagnosis_action(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SOURCE_DIAGNOSIS_ACTIONS:
            raise ValueError("Acción sobre diagnóstico origen no válida.")
        return normalized

    @field_validator("scope_type")
    @classmethod
    def valid_scope_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance dental no válido.")
        return normalized

    @field_validator("zone")
    @classmethod
    def valid_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ZONES:
            raise ValueError("Zona dental no válida.")
        return normalized

    @field_validator("surfaces")
    @classmethod
    def valid_surfaces(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = sorted({
            surface.strip().upper()
            for surface in value
            if surface and surface.strip()
        })
        invalid = [surface for surface in normalized if surface not in PROCEDURE_SURFACES]
        if invalid:
            raise ValueError("Cara dental no válida.")
        return normalized or None


class ProcedureClinicalCompletionResponse(BaseModel):
    procedure: ProcedureResponse
    odontogram_event_id: UUID
    odontogram_event_status: str
    clinical_evolution_id: UUID
    idempotency_key: str
    idempotent_replay: bool = False
    message: str


class OdontogramPlannedProcedureTreatmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    specialty: str | None = Field(default=None, max_length=120)
    responsible_dentist_id: UUID | None = None
    main_site_id: UUID | None = None
    observations: str | None = None

    @field_validator("name", "description", "specialty", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class OdontogramPlannedProcedureCreateRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=120)
    treatment_id: UUID | None = None
    new_treatment: OdontogramPlannedProcedureTreatmentCreate | None = None
    catalog_procedure_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    unit_value: Decimal = Field(default=Decimal("0"), ge=0)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    estimated_date: date | None = None
    observations: str | None = None
    requires_tooth: bool = False
    scope_type: str = "GENERAL"
    zone: str | None = Field(default=None, max_length=40)
    tooth: str | None = Field(default=None, max_length=30)
    surfaces: list[str] | None = None
    allow_similar_duplicate: bool = False

    @model_validator(mode="after")
    def validate_target_treatment(self):
        if bool(self.treatment_id) == bool(self.new_treatment):
            raise ValueError("Seleccione un tratamiento existente o cree uno nuevo.")
        return self

    @field_validator("idempotency_key", "name", "category", "observations", "tooth")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("scope_type")
    @classmethod
    def valid_scope_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance dental no válido.")
        return normalized

    @field_validator("zone")
    @classmethod
    def valid_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ZONES:
            raise ValueError("Zona dental no válida.")
        return normalized

    @field_validator("surfaces")
    @classmethod
    def valid_surfaces(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = sorted({
            surface.strip().upper()
            for surface in value
            if surface and surface.strip()
        })
        invalid = [surface for surface in normalized if surface not in PROCEDURE_SURFACES]
        if invalid:
            raise ValueError("Cara dental no válida.")
        return normalized


class OdontogramLinkedProcedureResponse(BaseModel):
    procedure_id: UUID
    treatment_id: UUID
    treatment_name: str
    treatment_status: str
    patient_id: UUID
    source_odontogram_event_id: UUID
    catalog_procedure_id: UUID | None
    name: str
    category: str | None
    status: str
    unit_value: Decimal
    quantity: Decimal
    total_value: Decimal
    scope_type: str
    zone: str | None
    tooth: str | None
    surfaces: list[str] | None
    scope_label: str
    created_at: datetime


class OdontogramLinkedProcedureListResponse(BaseModel):
    items: list[OdontogramLinkedProcedureResponse]
    total: int


class OdontogramPlannedProcedureCreateResponse(BaseModel):
    procedure: ProcedureResponse | None
    linked_procedures: list[OdontogramLinkedProcedureResponse] = []
    source_odontogram_event_id: UUID
    treatment_id: UUID | None = None
    idempotency_key: str
    idempotent_replay: bool = False
    similar_duplicate_detected: bool = False
    message: str


class ProcedureCatalogBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    suggested_value: Decimal | None = Field(default=None, ge=0)
    suggested_scope_type: str | None = None
    odontogram_behavior: str = "UNCONFIGURED"
    odontogram_scope_type: str | None = None
    allowed_diagnosis_catalog_item_ids: list[UUID] = Field(default_factory=list)
    default_performed_catalog_item_id: UUID | None = None
    is_active: bool = True

    @field_validator("suggested_scope_type", "odontogram_scope_type")
    @classmethod
    def valid_suggested_scope_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance sugerido no válido.")
        return normalized

    @field_validator("odontogram_behavior")
    @classmethod
    def valid_odontogram_behavior(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ODONTOGRAM_BEHAVIORS:
            raise ValueError("Comportamiento odontográfico no válido.")
        return normalized

    @field_validator("allowed_diagnosis_catalog_item_ids")
    @classmethod
    def unique_allowed_diagnoses(cls, value: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(value))

    @field_validator("name", "category", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ProcedureCatalogCreateRequest(ProcedureCatalogBase):
    pass


class ProcedureCatalogUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    suggested_value: Decimal | None = Field(default=None, ge=0)
    suggested_scope_type: str | None = None
    odontogram_behavior: str | None = None
    odontogram_scope_type: str | None = None
    allowed_diagnosis_catalog_item_ids: list[UUID] | None = None
    default_performed_catalog_item_id: UUID | None = None
    is_active: bool | None = None

    @field_validator("suggested_scope_type", "odontogram_scope_type")
    @classmethod
    def valid_suggested_scope_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_SCOPE_TYPES:
            raise ValueError("Tipo de alcance sugerido no válido.")
        return normalized

    @field_validator("odontogram_behavior")
    @classmethod
    def valid_odontogram_behavior(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PROCEDURE_ODONTOGRAM_BEHAVIORS:
            raise ValueError("Comportamiento odontográfico no válido.")
        return normalized

    @field_validator("allowed_diagnosis_catalog_item_ids")
    @classmethod
    def unique_allowed_diagnoses(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None
        return list(dict.fromkeys(value))

    @field_validator("name", "category", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ProcedureCatalogItemResponse(BaseModel):
    id: UUID
    name: str
    category: str | None
    description: str | None
    suggested_value: Decimal | None
    suggested_scope_type: str | None
    odontogram_behavior: str
    odontogram_scope_type: str | None
    allowed_diagnosis_catalog_item_ids: list[UUID]
    allowed_diagnoses: list[dict] = Field(default_factory=list)
    default_performed_catalog_item_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProcedureCatalogListResponse(BaseModel):
    items: list[ProcedureCatalogItemResponse]
    total: int


class BudgetCreateRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)
    procedure_ids: list[UUID] = Field(default_factory=list)
    discount_type: str | None = Field(default=None, pattern="^(porcentaje|valor)$")
    discount_value: Decimal = Field(default=Decimal("0"), ge=0)
    observations: str | None = None
    expires_on: date | None = None

    @field_validator("idempotency_key", "observations")
    @classmethod
    def strip_observations(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("procedure_ids")
    @classmethod
    def unique_procedure_ids(cls, value: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(value))


class BudgetUpdateRequest(BudgetCreateRequest):
    pass


class BudgetVersionCreateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)

    @field_validator("reason", "idempotency_key")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class BudgetDetailResponse(BaseModel):
    id: UUID
    procedure_id: UUID | None
    name: str
    category: str | None
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal
    order: int
    observations: str | None
    scope_type: str
    zone: str | None
    tooth: str | None
    surfaces: list[str] | None
    scope_label: str


class BudgetResponse(BaseModel):
    id: UUID
    patient_id: UUID
    treatment_id: UUID
    number: str | None
    series_id: UUID
    previous_budget_id: UUID | None
    superseded_by_id: UUID | None
    version: int
    is_current: bool
    is_editable: bool
    is_current_draft: bool
    version_reason: str | None
    status: str
    gross_value: Decimal
    discount_type: str | None
    discount_value: Decimal
    discount_calculated_value: Decimal
    final_value: Decimal
    observations: str | None
    issued_at: datetime
    expires_on: date | None
    approved_at: datetime | None
    rejected_at: datetime | None
    details: list[BudgetDetailResponse] = []


class BudgetListResponse(BaseModel):
    items: list[BudgetResponse]
    total: int


class PaymentCreateRequest(BaseModel):
    site_id: UUID
    dentist_id: UUID | None = None
    procedure_ids: list[UUID] = Field(default_factory=list)
    paid_at: datetime
    value: Decimal = Field(gt=0)
    payment_method: str
    reference: str | None = Field(default=None, max_length=120)
    observation: str | None = None

    @field_validator("payment_method")
    @classmethod
    def valid_method(cls, value: str) -> str:
        if value not in PAYMENT_METHODS:
            raise ValueError("Medio de pago no válido.")
        return value

    @field_validator("reference", "observation")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_timezone(self):
        if self.paid_at.tzinfo is None:
            raise ValueError("La fecha de pago debe incluir zona horaria.")
        return self


class PaymentReverseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class PaymentResponse(BaseModel):
    id: UUID
    receipt_number: str
    patient_id: UUID
    patient_name: str
    treatment_id: UUID
    treatment_name: str
    budget_id: UUID | None
    site_id: UUID
    site_name: str
    dentist_id: UUID | None
    dentist_name: str | None
    paid_at: datetime
    value: Decimal
    payment_method: str
    reference: str | None
    observation: str | None
    status: str
    reversed_at: datetime | None
    reversal_reason: str | None
    procedure_ids: list[UUID] = Field(default_factory=list)


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int


class FinanceDashboardResponse(BaseModel):
    income_today: Decimal
    income_month: Decimal
    income_year: Decimal
    receivables_total: Decimal
    active_treatments: int
    average_ticket: Decimal


class FinanceBreakdownItem(BaseModel):
    id: UUID | None = None
    name: str
    value: Decimal


class FinanceBreakdownResponse(BaseModel):
    items: list[FinanceBreakdownItem]


class PatientBalanceItem(BaseModel):
    patient_id: UUID
    patient_name: str
    balance: Decimal


class PatientBalancesResponse(BaseModel):
    items: list[PatientBalanceItem]
