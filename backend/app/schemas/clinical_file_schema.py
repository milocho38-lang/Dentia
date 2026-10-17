from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ClinicalFileResponse(BaseModel):
    id: UUID
    patient_id: UUID
    treatment_id: UUID | None
    appointment_id: UUID | None
    file_type: str
    category: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    description: str | None
    uploaded_at: datetime
    uploaded_by: UUID


class ClinicalFileListResponse(BaseModel):
    items: list[ClinicalFileResponse]
    total: int


class ClinicalFileDeactivateRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value
