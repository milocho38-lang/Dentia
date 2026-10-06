from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PatientImportSourceCreateRequest(BaseModel):
    label: str = Field(min_length=3, max_length=100)

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        return value.strip()


class PatientImportSourceResponse(BaseModel):
    id: UUID
    code: str
    label: str
    source_system: str


class PatientImportSourceListResponse(BaseModel):
    items: list[PatientImportSourceResponse]


class PatientImportPreviewRow(BaseModel):
    row_number: int
    source_patient_id: str
    display_name: str
    status: str
    issues: list[str] = Field(default_factory=list)
    pending_fields: list[str] = Field(default_factory=list)


class PatientImportCounts(BaseModel):
    ready: int = 0
    incomplete: int = 0
    review: int = 0
    rejected: int = 0
    already_imported: int = 0


class PatientImportPreviewResponse(BaseModel):
    preview_token: str
    file_sha256: str
    source: PatientImportSourceResponse
    sheet_name: str
    total_rows: int
    counts: PatientImportCounts
    extra_headers: list[str] = Field(default_factory=list)
    missing_headers: list[str] = Field(default_factory=list)
    rows: list[PatientImportPreviewRow]


class PatientImportConfirmResponse(BaseModel):
    batch_id: str
    imported: int
    skipped_already_imported: int
    skipped_review: int
    rejected: int
    rows: list[PatientImportPreviewRow]
