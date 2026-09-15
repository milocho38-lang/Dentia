from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrthodonticsEntitlementUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    seat_limit: int = Field(ge=0, le=10_000)
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    @model_validator(mode="after")
    def validate_effective_range(self):
        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("La fecha final no puede ser anterior a la inicial.")
        if self.enabled and self.seat_limit < 1:
            raise ValueError("Un módulo activo necesita al menos un cupo.")
        return self


class OrthodonticsSeatSummary(BaseModel):
    seat_limit: int
    assigned_active: int
    available: int


class OrthodonticsEntitlementResponse(BaseModel):
    id: UUID | None
    company_id: UUID
    enabled: bool
    status: str
    effective_from: datetime | None
    effective_until: datetime | None
    seats: OrthodonticsSeatSummary
    created_at: datetime | None
    updated_at: datetime | None


class OrthodonticsAssignmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dentist_id: UUID


class OrthodonticsAssignmentRevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=300)


class OrthodonticsDentistAssignmentResponse(BaseModel):
    id: UUID | None
    dentist_id: UUID
    dentist_name: str
    dentist_status: str
    dentist_is_active: bool
    user_id: UUID | None
    user_is_active: bool
    assigned: bool
    assigned_at: datetime | None
    assigned_by_user_id: UUID | None
    revoked_at: datetime | None
    revoked_by_user_id: UUID | None


class OrthodonticsAssignmentListResponse(BaseModel):
    entitlement: OrthodonticsEntitlementResponse
    items: list[OrthodonticsDentistAssignmentResponse]


class OrthodonticsAssignmentActionResponse(BaseModel):
    success: bool = True
    created: bool = False
    message: str
    assignment: OrthodonticsDentistAssignmentResponse
    seats: OrthodonticsSeatSummary


class OrthodonticsAccessResponse(BaseModel):
    allowed: bool
    code: str
    message: str
    company_id: UUID
    dentist_id: UUID | None
    entitlement_enabled: bool
    assignment_active: bool
