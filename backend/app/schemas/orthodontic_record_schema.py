from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrthodonticRecordOptionResponse(BaseModel):
    code: str
    label: str


class OrthodonticRecordSectionResponse(BaseModel):
    key: str
    label: str
    order: int


class OrthodonticRecordFieldResponse(BaseModel):
    key: str
    label: str
    type: Literal["text", "single", "multi", "boolean"]
    section: str
    order: int
    options: list[OrthodonticRecordOptionResponse]
    clinical_pending_flag: str | None = None
    max_length: int | None = None


class OrthodonticRecordSchemaResponse(BaseModel):
    version: str
    sections: list[OrthodonticRecordSectionResponse]
    fields: list[OrthodonticRecordFieldResponse]


class OrthodonticRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    content: dict[str, Any]


class OrthodonticRecordFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)


class OrthodonticRecordNewVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    based_on_version_id: UUID | None = None


class OrthodonticRecordVersionResponse(BaseModel):
    id: UUID
    record_id: UUID
    version_number: int
    status: Literal["DRAFT", "FINALIZED"]
    schema_version: str
    row_version: int
    content: dict[str, Any]
    schema_snapshot: dict[str, Any]
    content_snapshot: dict[str, Any] | None
    based_on_version_id: UUID | None
    clinical_date: datetime | None
    timezone_name: str | None
    content_hash: str | None
    integrity_status: Literal["NOT_APPLICABLE", "PASS", "FAIL"]
    created_by_user_id: UUID
    updated_by_user_id: UUID
    finalized_by_user_id: UUID | None
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime
    section_progress: dict[str, str]


class OrthodonticRecordResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    company_id: UUID
    patient_id: UUID
    orthodontic_case_id: UUID
    label: str
    case_status: str
    can_edit: bool
    read_only_reason: str | None
    record_schema: OrthodonticRecordSchemaResponse = Field(alias="schema")
    current_version: OrthodonticRecordVersionResponse | None
    versions: list[OrthodonticRecordVersionResponse]
    created_at: datetime
    updated_at: datetime


class OrthodonticRecordActionResponse(BaseModel):
    success: bool = True
    message: str
    record: OrthodonticRecordResponse
