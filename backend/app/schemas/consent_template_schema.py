import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


DOCUMENT_KINDS = {
    "GENERAL_CLINICAL_CONSENT",
    "PROCEDURE_CONSENT",
    "TREATMENT_AUTHORIZATION",
    "IMAGE_USE_AUTHORIZATION",
    "DATA_PROCESSING_AUTHORIZATION",
    "COMMUNICATIONS_AUTHORIZATION",
    "REPRESENTATIVE_CONSENT",
    "TREATMENT_REJECTION",
    "CONSENT_REVOCATION",
    "INFORMATION_ACKNOWLEDGEMENT",
    "OTHER",
}
SUPPORTED_COUNTRIES = {"CL", "CO"}
SUPPORTED_LANGUAGES = {"es-CL", "es-CO"}
VERSION_STATUSES = {"DRAFT", "PUBLISHED", "SUPERSEDED", "RETIRED", "VOIDED"}
SCOPE_TYPES = {"GENERAL", "SPECIFIC"}
CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{1,79}$")
SPECIALTY_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{1,79}$")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class SpecialtyInput(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)

    @field_validator("code")
    @classmethod
    def valid_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not SPECIALTY_CODE_PATTERN.fullmatch(normalized):
            raise ValueError("Código de especialidad no válido.")
        return normalized

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()


class ConsentVersionDraftInput(BaseModel):
    title: str = Field(min_length=2, max_length=250)
    content: str = Field(min_length=1, max_length=50000)
    change_summary: str | None = Field(default=None, max_length=1000)
    scope_type: str = "GENERAL"
    priority: int = Field(default=0, ge=0, le=1000)
    site_ids: list[UUID] = Field(default_factory=list, max_length=100)
    procedure_ids: list[UUID] = Field(default_factory=list, max_length=100)
    specialties: list[SpecialtyInput] = Field(default_factory=list, max_length=50)

    @field_validator("title", "content")
    @classmethod
    def required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("change_summary")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("scope_type")
    @classmethod
    def valid_scope(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SCOPE_TYPES:
            raise ValueError("Ámbito no válido.")
        return normalized

    @model_validator(mode="after")
    def specific_has_criteria(self):
        if self.scope_type == "GENERAL" and (self.site_ids or self.procedure_ids or self.specialties):
            raise ValueError("Una versión general no puede declarar criterios específicos.")
        if self.scope_type == "SPECIFIC" and not (self.site_ids or self.procedure_ids or self.specialties):
            raise ValueError("Una versión específica requiere al menos una sede, procedimiento o especialidad.")
        if len(set(self.site_ids)) != len(self.site_ids) or len(set(self.procedure_ids)) != len(self.procedure_ids):
            raise ValueError("Las asociaciones no pueden repetirse.")
        specialty_codes = [item.code for item in self.specialties]
        if len(set(specialty_codes)) != len(specialty_codes):
            raise ValueError("Las especialidades no pueden repetirse.")
        return self


class ConsentTemplateCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    document_kind: str
    country_code: str
    language_code: str
    initial_version: ConsentVersionDraftInput

    @field_validator("code")
    @classmethod
    def valid_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not CODE_PATTERN.fullmatch(normalized):
            raise ValueError("El código solo admite letras, números, punto, guion y guion bajo.")
        return normalized

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("document_kind")
    @classmethod
    def valid_kind(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in DOCUMENT_KINDS:
            raise ValueError("Tipo documental no válido.")
        return normalized

    @field_validator("country_code")
    @classmethod
    def valid_country(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_COUNTRIES:
            raise ValueError("País no soportado. C019A.1 habilita CL y CO.")
        return normalized

    @field_validator("language_code")
    @classmethod
    def valid_language(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Idioma no soportado. C019A.1 habilita es-CL y es-CO.")
        return normalized

    @model_validator(mode="after")
    def language_matches_country(self):
        if self.language_code != f"es-{self.country_code}":
            raise ValueError("El idioma debe corresponder al país de la plantilla.")
        return self


class ConsentTemplateUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    document_kind: str | None = None
    country_code: str | None = None
    language_code: str | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def valid_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not CODE_PATTERN.fullmatch(normalized):
            raise ValueError("Código no válido.")
        return normalized

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("document_kind")
    @classmethod
    def valid_kind(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in DOCUMENT_KINDS:
            raise ValueError("Tipo documental no válido.")
        return normalized

    @field_validator("country_code")
    @classmethod
    def valid_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_COUNTRIES:
            raise ValueError("País no soportado.")
        return normalized

    @field_validator("language_code")
    @classmethod
    def valid_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Idioma no soportado.")
        return normalized


class ConsentVersionUpdateRequest(ConsentVersionDraftInput):
    row_version: int = Field(ge=1)


class ConsentReasonRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return value.strip()


class ConsentVersionCreateFromRequest(BaseModel):
    change_summary: str = Field(min_length=3, max_length=1000)

    @field_validator("change_summary")
    @classmethod
    def clean_summary(cls, value: str) -> str:
        return value.strip()


class CatalogItemResponse(BaseModel):
    code: str
    label: str
    description: str
    category: str | None = None
    sample_value: str | None = None


class VariableValidationResponse(BaseModel):
    valid: bool
    used_variables: list[str]
    invalid_variables: list[str]
    syntax_errors: list[str]


class ConsentVersionResponse(BaseModel):
    id: UUID
    template_id: UUID
    version_number: int
    status: str
    title: str
    content: str
    content_format: str
    used_variables: list[str]
    variable_schema_snapshot: dict | None
    content_sha256: str | None
    based_on_version_id: UUID | None
    change_summary: str | None
    scope_type: str
    priority: int
    site_ids: list[UUID]
    procedure_ids: list[UUID]
    specialties: list[SpecialtyInput]
    row_version: int
    published_at: datetime | None
    published_by: UUID | None
    retired_at: datetime | None
    retire_reason: str | None
    voided_at: datetime | None
    void_reason: str | None
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class ConsentTemplateResponse(BaseModel):
    id: UUID
    company_id: UUID
    code: str
    name: str
    description: str | None
    document_kind: str
    country_code: str
    language_code: str
    is_active: bool
    published_version: ConsentVersionResponse | None
    draft_versions: list[ConsentVersionResponse]
    versions_count: int
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime


class ConsentTemplateListResponse(BaseModel):
    items: list[ConsentTemplateResponse]
    total: int


class ConsentPreviewResponse(BaseModel):
    warning: str
    title: str
    rendered_content: str
    used_variables: list[str]
    validation: VariableValidationResponse


class ApplicableTemplateCandidate(BaseModel):
    template_id: UUID
    version_id: UUID
    template_code: str
    template_name: str
    version_number: int
    country_code: str
    language_code: str
    scope_type: str
    priority: int
    content: str
    content_sha256: str
    variable_schema_snapshot: dict
    site_ids: list[UUID]
    procedure_ids: list[UUID]
    specialties: list[SpecialtyInput]


class ConsentTemplateAuditResponse(BaseModel):
    id: UUID
    action: str
    result: str
    user_id: UUID | None
    occurred_at: datetime
    detail: dict | None
