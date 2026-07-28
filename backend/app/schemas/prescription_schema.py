from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


PRESCRIPTION_STATUSES = {"DRAFT", "FINALIZED", "VOIDED"}


class PrescriptionItemInput(BaseModel):
    generic_name: str = Field(min_length=1, max_length=240)
    brand_name: str | None = Field(default=None, max_length=200)
    pharmaceutical_form: str = Field(min_length=1, max_length=160)
    concentration: str = Field(min_length=1, max_length=160)
    dose: str = Field(min_length=1, max_length=180)
    route: str = Field(min_length=1, max_length=120)
    frequency: str = Field(min_length=1, max_length=180)
    duration: str = Field(min_length=1, max_length=160)
    total_quantity: str = Field(min_length=1, max_length=120)
    quantity_unit: str | None = Field(default=None, max_length=120)
    instructions: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "generic_name",
        "brand_name",
        "pharmaceutical_form",
        "concentration",
        "dose",
        "route",
        "frequency",
        "duration",
        "total_quantity",
        "quantity_unit",
        "instructions",
    )
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        required = {
            "generic_name",
            "pharmaceutical_form",
            "concentration",
            "dose",
            "route",
            "frequency",
            "duration",
            "total_quantity",
        }
        if not normalized and info.field_name in required:
            raise ValueError("Campo obligatorio.")
        return normalized or None


class PrescriptionBase(BaseModel):
    site_id: UUID
    dentist_profile_id: UUID | None = None
    clinical_date: date
    related_treatment_id: UUID | None = None
    related_evolution_id: UUID | None = None
    related_appointment_id: UUID | None = None
    general_instructions: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[PrescriptionItemInput] = Field(default_factory=list)

    @field_validator("general_instructions", "notes")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class PrescriptionCreateRequest(PrescriptionBase):
    pass


class PrescriptionUpdateRequest(BaseModel):
    site_id: UUID | None = None
    dentist_profile_id: UUID | None = None
    clinical_date: date | None = None
    related_treatment_id: UUID | None = None
    related_evolution_id: UUID | None = None
    related_appointment_id: UUID | None = None
    general_instructions: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[PrescriptionItemInput] | None = None
    version: int = Field(ge=1)

    @field_validator("general_instructions", "notes")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class PrescriptionFinalizeRequest(BaseModel):
    allergies_reviewed: bool

    @model_validator(mode="after")
    def require_review(self):
        if not self.allergies_reviewed:
            raise ValueError("Debe confirmar que revisó alergias y medicamentos actuales.")
        return self


class PrescriptionVoidRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class PrescriptionItemResponse(BaseModel):
    id: UUID
    position: int
    generic_name: str
    brand_name: str | None
    pharmaceutical_form: str
    concentration: str
    dose: str
    route: str
    frequency: str
    duration: str
    total_quantity: str
    quantity_unit: str | None
    instructions: str | None


class PrescriptionResponse(BaseModel):
    id: UUID
    company_id: UUID
    site_id: UUID
    site_name: str | None
    patient_id: UUID
    patient_name: str
    professional_user_id: UUID | None
    dentist_profile_id: UUID | None
    professional_name: str | None
    status: str
    prescription_number: str | None
    clinical_date: date
    related_treatment_id: UUID | None
    related_evolution_id: UUID | None
    related_appointment_id: UUID | None
    previous_prescription_id: UUID | None
    general_instructions: str | None
    notes: str | None
    allergies_reviewed: bool
    finalized_at: datetime | None
    voided_at: datetime | None
    void_reason: str | None
    pdf_sha256: str | None
    integrity_hash: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    items: list[PrescriptionItemResponse]
    clinical_alerts: dict | None = None


class PrescriptionListResponse(BaseModel):
    items: list[PrescriptionResponse]
    total: int


class PrescriptionPreviewResponse(BaseModel):
    content_base64: str
    filename: str
