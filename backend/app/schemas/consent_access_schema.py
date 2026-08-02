from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class AccessIssueRequest(BaseModel):
    expires_in_hours: int | None = Field(default=None, ge=1, le=168)


class AccessRevokeRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)

    @field_validator("reason")
    @classmethod
    def clean(cls, value: str) -> str:
        return value.strip()


class AccessSessionResponse(BaseModel):
    id: UUID
    status: str
    recipient_masked: str
    issued_at: datetime
    expires_at: datetime
    verified_at: datetime | None
    viewed_at: datetime | None
    clarification_requested_at: datetime | None
    last_activity_at: datetime
    row_version: int


class AccessIssuedResponse(AccessSessionResponse):
    public_url: str


class PublicLinkResponse(BaseModel):
    status: str
    recipient_masked: str | None = None
    expires_at: datetime | None = None
    message: str


class OtpRequestResponse(BaseModel):
    detail: str
    recipient_masked: str
    retry_after_seconds: int


class OtpVerifyRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class OtpVerifyResponse(BaseModel):
    detail: str
    expires_at: datetime


class PublicConsentDocumentResponse(BaseModel):
    title: str
    clinic_name: str
    patient_name: str
    professional_name: str
    clinical_date: str
    procedures: list[str]
    content: str
    template_version: int
    status_label: str = "Revisado, aún no firmado"


class ClarificationCreateRequest(BaseModel):
    message: str | None = Field(default=None, max_length=500)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class ClarificationResponse(BaseModel):
    id: UUID
    status: str
    message: str | None
    requested_at: datetime
    resolved_at: datetime | None


class AccessAuditResponse(BaseModel):
    id: UUID
    action: str
    result: str
    user_id: UUID | None
    occurred_at: datetime
    detail: dict | None
