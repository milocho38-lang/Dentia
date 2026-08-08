from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsentLibraryVersionResponse(BaseModel):
    id: UUID
    library_document_id: UUID
    country_code: str
    language_code: str
    version_number: int
    publication_status: str
    legal_review_status: str
    clinical_review_status: str
    reviewed_countries: list[str]
    reviewed_at: datetime | None
    review_reference: str | None
    content_format: str
    content: str
    source_text_sha256: str
    normalized_content_sha256: str
    variable_schema_snapshot: list[str]
    source_pages: list[int]
    transformation_notes: list[str]
    review_notes: str | None
    equivalence_reviewer_name: str | None
    equivalence_review_reason: str | None
    equivalence_checklist_snapshot: dict | None
    normalization_schema_version: str | None = None
    normalization_status: str = "UNKNOWN"
    signer_compatibility: str = "UNKNOWN"
    signer_blocking_category: str | None = None
    signer_blocking_reason: str | None = None
    signer_blocking_term: str | None = None
    signer_blocking_line: int | None = None
    signer_blocking_context: str | None = None
    adult_variant_required: bool = False
    normalization_alerts: list[str] = Field(default_factory=list)
    electronic_readiness_status: str = "UNKNOWN"
    electronic_readiness_findings: list[str] = Field(default_factory=list)
    norm5_result: str | None = None
    is_current: bool = False
    is_legacy: bool = False
    historical_message: str | None = None
    imported_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentLibraryDocumentResponse(BaseModel):
    id: UUID
    code: str
    title: str
    summary: str | None
    document_type: str
    category: str
    specialty_code: str | None
    specialty_name: str | None
    signer_scope: str
    requires_patient_signature: bool
    supports_electronic_signature: bool
    source_package_version: str
    source_document_hash: str
    source_page_start: int
    source_page_end: int
    source_title_exact: str | None
    source_origin_note: str
    source_reference: str
    is_active: bool
    versions: list[ConsentLibraryVersionResponse] = Field(default_factory=list)
    installed_exact: bool = False
    installed_clone: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentLibraryListResponse(BaseModel):
    items: list[ConsentLibraryDocumentResponse]
    total: int


class ConsentLibrarySourceResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    document_code: str
    title: str
    country_code: str
    language_code: str
    source_text: str
    normalized_content: str
    source_text_sha256: str
    normalized_content_sha256: str
    source_pages: list[int]
    source_reference: str


class ConsentLibraryInstallRequest(BaseModel):
    change_summary: str | None = Field(default=None, max_length=1000)

    @field_validator("change_summary")
    @classmethod
    def clean_summary(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ConsentLibraryInstallResponse(BaseModel):
    mode: str
    template_id: UUID
    version_id: UUID
    already_installed: bool
    content_responsibility: str
    message: str


class ConsentLibraryEquivalenceApprovalRequest(BaseModel):
    reviewer_name: str = Field(min_length=3, max_length=200)
    reviewed_date: date
    review_reference: str = Field(min_length=3, max_length=250)
    reason: str = Field(min_length=5, max_length=2000)
    clinical_text_faithful: bool = False
    risks_preserved: bool = False
    warnings_preserved: bool = False
    values_preserved: bool = False
    variables_correct: bool = False
    titles_limits_correct: bool = False
    signer_correct: bool = False
    classification_correct: bool = False
    country_approved: bool = False
    odontological_review: bool = False
    legal_equivalence_review: bool = False

    @field_validator("reviewer_name", "review_reference", "reason")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El campo es obligatorio.")
        return cleaned
