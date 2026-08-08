from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ConsentResponsibleAdultInput(BaseModel):
    patient_responsible_id: UUID | None = None
    full_name: str | None = Field(default=None, max_length=250)
    document_type: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=80)
    relationship_type: str = Field(max_length=40)
    relationship_other: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=220)
    phone: str | None = Field(default=None, max_length=80)
    identity_verified: bool = False

    @field_validator("relationship_type")
    @classmethod
    def normalize_relationship(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("full_name", "document_type", "document_number", "relationship_other", "phone", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class ConsentResponsibleAdultResponse(BaseModel):
    id: UUID | None = None
    patient_responsible_id: UUID | None = None
    full_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    relationship_type: str | None = None
    relationship_other: str | None = None
    relationship_label: str | None = None
    email_masked: str | None = None
    phone: str | None = None
    identity_verified_at: datetime | None = None
    identity_verified_by: UUID | None = None


class ConsentContextInput(BaseModel):
    patient_id: UUID
    site_id: UUID
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    treatment_procedure_ids: list[UUID] = Field(default_factory=list, max_length=50)
    procedure_catalog_ids: list[UUID] = Field(default_factory=list, max_length=50)
    dentist_profile_id: UUID
    clinical_date: date | None = None
    signer_actor_type: str | None = Field(default=None, max_length=40)
    responsible_adult: ConsentResponsibleAdultInput | None = None
    minor_participation_status: str | None = Field(default=None, max_length=80)
    minor_participation_observation: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def no_duplicates(self):
        if len(set(self.treatment_procedure_ids)) != len(self.treatment_procedure_ids):
            raise ValueError("Los procedimientos del tratamiento no pueden repetirse.")
        if len(set(self.procedure_catalog_ids)) != len(self.procedure_catalog_ids):
            raise ValueError("Los procedimientos de catálogo no pueden repetirse.")
        return self


class ApplicableTemplatesRequest(ConsentContextInput):
    pass


class ApplicableConsentTemplateResponse(BaseModel):
    template_id: UUID
    version_id: UUID
    template_name: str
    title: str
    document_kind: str
    country_code: str
    language_code: str
    version_number: int
    applicability_reason_codes: list[str]
    applicability_reasons: list[str]
    covered_procedure_ids: list[UUID]
    required_variables: list[str]
    required_variable_labels: list[str]
    missing_variables: list[str]
    missing_variable_labels: list[str]
    rendered_preview: str
    signer_policy: str = "PATIENT_SELF"


class ApplicableTemplatesResponse(BaseModel):
    items: list[ApplicableConsentTemplateResponse]
    total: int


class ConsentInstanceBatchCreateRequest(BaseModel):
    context: ConsentContextInput
    template_version_ids: list[UUID] = Field(min_length=1, max_length=20)

    @field_validator("template_version_ids")
    @classmethod
    def unique_versions(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Las plantillas seleccionadas no pueden repetirse.")
        return value


class ConsentInstanceCreateRequest(BaseModel):
    context: ConsentContextInput
    template_version_id: UUID


class ConsentInstanceUpdateRequest(ConsentContextInput):
    row_version: int = Field(ge=1)


class ConsentInstanceVoidRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return value.strip()


class ConsentInstanceConfirmRequest(BaseModel):
    confirmed: bool
    row_version: int = Field(ge=1)


class ConsentInstanceProcedureResponse(BaseModel):
    id: UUID
    procedure_catalog_id: UUID | None
    treatment_procedure_id: UUID | None
    code: str | None
    name: str
    description: str | None
    order: int


class ConsentInstanceResponse(BaseModel):
    id: UUID
    visible_number: str
    patient_id: UUID
    site_id: UUID
    template_id: UUID
    template_version_id: UUID
    appointment_id: UUID | None
    treatment_id: UUID | None
    professional_user_id: UUID
    dentist_profile_id: UUID | None
    status: str
    document_kind: str
    country_code: str
    language_code: str
    clinical_date: date
    timezone: str
    display_title: str
    signer_policy: str
    signer_actor_type: str
    signer_name: str | None
    signer_email_masked: str | None
    responsible_adult: ConsentResponsibleAdultResponse | None
    minor_participation_status: str | None
    minor_participation_observation: str | None
    rendered_content: str | None
    template_version_number: int
    template_content_sha256: str
    instance_content_sha256: str | None
    context_sha256: str | None
    integrity_hash: str | None
    variable_values: dict
    missing_variables: list[str]
    missing_variable_labels: list[str]
    context_snapshot: dict
    acceptance_compatible: bool
    acceptance_block_code: str | None
    acceptance_block_message: str | None
    is_test_document: bool
    test_notice: str | None
    legal_review_status: str | None
    declaration_set_code: str | None
    declaration_set_version: str | None
    procedures: list[ConsentInstanceProcedureResponse]
    professional_confirmed_at: datetime | None
    professional_confirmed_by: UUID | None
    ready_at: datetime | None
    voided_at: datetime | None
    voided_by: UUID | None
    void_reason: str | None
    row_version: int
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class ConsentInstanceListResponse(BaseModel):
    items: list[ConsentInstanceResponse]
    total: int


class ConsentInstancePreviewResponse(BaseModel):
    warning: str
    instance: ConsentInstanceResponse


class ConsentInstanceAuditResponse(BaseModel):
    id: UUID
    action: str
    result: str
    user_id: UUID | None
    occurred_at: datetime
    detail: dict | None


class ReservedTransitionResponse(BaseModel):
    detail: str
