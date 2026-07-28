from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator


CLINICAL_DOCUMENT_TYPES = {"REFERRAL", "CLINICAL_REPORT", "CERTIFICATE", "GENERAL_LETTER"}
CLINICAL_DOCUMENT_STATUSES = {"DRAFT", "FINALIZED", "VOIDED"}


class ClinicalDocumentBase(BaseModel):
    site_id: UUID
    dentist_profile_id: UUID | None = None
    document_type: str
    title: str | None = Field(default=None, max_length=200)
    recipient_name: str | None = Field(default=None, max_length=200)
    recipient_entity: str | None = Field(default=None, max_length=200)
    recipient_specialty: str | None = Field(default=None, max_length=160)
    subject: str | None = Field(default=None, max_length=250)
    body: str = Field(min_length=1, max_length=12000)
    clinical_date: date
    related_treatment_id: UUID | None = None
    related_evolution_id: UUID | None = None
    related_appointment_id: UUID | None = None

    @field_validator("document_type")
    @classmethod
    def valid_document_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in CLINICAL_DOCUMENT_TYPES:
            raise ValueError("Tipo de documento no válido.")
        return normalized

    @field_validator(
        "title",
        "recipient_name",
        "recipient_entity",
        "recipient_specialty",
        "subject",
        "body",
    )
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized and info.field_name == "body":
            raise ValueError("El contenido del documento es obligatorio.")
        return normalized or None


class ClinicalDocumentCreateRequest(ClinicalDocumentBase):
    pass


class ClinicalDocumentUpdateRequest(BaseModel):
    site_id: UUID | None = None
    dentist_profile_id: UUID | None = None
    document_type: str | None = None
    title: str | None = Field(default=None, max_length=200)
    recipient_name: str | None = Field(default=None, max_length=200)
    recipient_entity: str | None = Field(default=None, max_length=200)
    recipient_specialty: str | None = Field(default=None, max_length=160)
    subject: str | None = Field(default=None, max_length=250)
    body: str | None = Field(default=None, min_length=1, max_length=12000)
    clinical_date: date | None = None
    related_treatment_id: UUID | None = None
    related_evolution_id: UUID | None = None
    related_appointment_id: UUID | None = None
    version: int = Field(ge=1)

    @field_validator("document_type")
    @classmethod
    def valid_document_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in CLINICAL_DOCUMENT_TYPES:
            raise ValueError("Tipo de documento no válido.")
        return normalized

    @field_validator(
        "title",
        "recipient_name",
        "recipient_entity",
        "recipient_specialty",
        "subject",
        "body",
    )
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized and info.field_name == "body":
            raise ValueError("El contenido del documento es obligatorio.")
        return normalized or None


class ClinicalDocumentVoidRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class ClinicalDocumentResponse(BaseModel):
    id: UUID
    company_id: UUID
    site_id: UUID
    site_name: str | None = None
    patient_id: UUID
    patient_name: str
    professional_user_id: UUID | None
    dentist_profile_id: UUID | None
    professional_name: str | None
    document_type: str
    status: str
    document_number: str | None
    title: str | None
    recipient_name: str | None
    recipient_entity: str | None
    recipient_specialty: str | None
    subject: str | None
    body: str
    clinical_date: date
    finalized_at: datetime | None
    voided_at: datetime | None
    void_reason: str | None
    related_treatment_id: UUID | None
    related_evolution_id: UUID | None
    related_appointment_id: UUID | None
    previous_document_id: UUID | None
    pdf_sha256: str | None
    integrity_hash: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class ClinicalDocumentListResponse(BaseModel):
    items: list[ClinicalDocumentResponse]
    total: int


class ClinicalDocumentPreviewResponse(BaseModel):
    content_base64: str
    filename: str
