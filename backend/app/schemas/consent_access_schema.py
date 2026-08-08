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
    public_path: str


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
    signer_actor_type: str = "PATIENT_SELF"
    signer_name: str | None = None
    signer_relationship: str | None = None
    professional_name: str
    clinical_date: str
    procedures: list[str]
    content: str
    template_version: int
    status_label: str = "Revisado, aún no firmado"
    test_document: bool = False
    is_test_document: bool = False
    test_notice: str | None = None
    legal_review_status: str | None = None
    declaration_set_code: str | None = None
    declaration_set_version: str | None = None
    acceptance_compatible: bool = True
    acceptance_block_message: str | None = None


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


class AcceptanceDeclarationResponse(BaseModel):
    code: str
    text: str
    order: int


class AcceptanceRequirementsResponse(BaseModel):
    enabled: bool
    declaration_set_code: str
    declarations_country_code: str
    declarations_locale: str
    declarations_version: str
    declarations_legal_status: str
    declarations_set_sha256: str
    declarations: list[AcceptanceDeclarationResponse]
    patient_name: str
    signer_actor_type: str = "PATIENT_SELF"
    signer_name: str | None = None
    signer_relationship: str | None = None
    signature_required: bool
    legal_review_pending: bool = True
    test_document: bool = True
    test_notice: str | None = None


class AcceptanceDeclarationInput(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    accepted: bool


class AcceptanceSubmitRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=100)
    acting_on_own_behalf: bool
    declarations_version: str = Field(min_length=2, max_length=60)
    declaration_set_code: str = Field(min_length=2, max_length=80)
    declarations_set_sha256: str = Field(min_length=64, max_length=64)
    declarations: list[AcceptanceDeclarationInput]
    typed_full_name: str = Field(min_length=2, max_length=250)
    signature_data_url: str = Field(min_length=50, max_length=600_000)


class AcceptanceSubmitResponse(BaseModel):
    acceptance_id: UUID
    status: str
    accepted_at: datetime
    final_document_sha256: str
    verification_id: UUID
    download_url: str
    copy_delivery_status: str
    test_document: bool
    test_notice: str | None


class AcceptanceSummaryResponse(BaseModel):
    acceptance_id: UUID
    status: str
    accepted_at: datetime
    actor_type: str
    patient_name: str
    signer_name: str | None = None
    signer_relationship: str | None = None
    declarations_version: str
    declaration_set_code: str
    declarations_country_code: str
    declarations_locale: str
    declarations_legal_status: str
    declarations_set_sha256: str
    test_document: bool
    test_notice: str | None
    final_document_sha256: str
    copy_delivery_status: str | None


class AcceptanceEvidenceResponse(BaseModel):
    acceptance_id: UUID
    schema_version: str
    manifest_sha256: str
    manifest: dict
