from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ConsentContextInput(BaseModel):
    patient_id: UUID
    site_id: UUID
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    treatment_procedure_ids: list[UUID] = Field(default_factory=list, max_length=50)
    procedure_catalog_ids: list[UUID] = Field(default_factory=list, max_length=50)
    dentist_profile_id: UUID
    clinical_date: date | None = None

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
