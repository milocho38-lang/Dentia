from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.orthodontics_schema import OrthodonticsAccessResponse


class OrthodonticCaseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    responsible_dentist_id: UUID | None = None
    treatment_plan: str | None = Field(default=None, max_length=10_000)
    current_appliance_summary: str | None = Field(default=None, max_length=4_000)


class OrthodonticCaseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    treatment_plan: str | None = Field(default=None, max_length=10_000)
    current_appliance_summary: str | None = Field(default=None, max_length=4_000)


class OrthodonticCaseTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1_000)


class OrthodonticResponsibleChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    responsible_dentist_id: UUID


class OrthodonticDentistOption(BaseModel):
    id: UUID
    name: str


class OrthodonticNextAppointment(BaseModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime
    site_id: UUID
    dentist_id: UUID
    reason: str
    status: str


class OrthodonticCaseResponse(BaseModel):
    id: UUID
    company_id: UUID
    patient_id: UUID
    clinical_record_id: UUID
    primary_site_id: UUID
    responsible_dentist_id: UUID
    responsible_dentist_name: str
    status: str
    display_status: str
    started_at: datetime | None
    completed_at: datetime | None
    closure_reason_code: str | None
    closure_notes: str | None
    treatment_plan: str | None
    current_appliance_summary: str | None
    row_version: int
    created_at: datetime
    updated_at: datetime


class OrthodonticSummaryResponse(BaseModel):
    case: OrthodonticCaseResponse
    last_visit: None = None
    what_was_done: None = None
    next_session_instructions: None = None
    next_clinical_control: None = None
    active_alerts: list[dict[str, object]] = Field(default_factory=list)
    next_appointment: OrthodonticNextAppointment | None = None


class OrthodonticPatientWorkspaceResponse(BaseModel):
    access: OrthodonticsAccessResponse
    active_case: OrthodonticCaseResponse | None
    historical_cases: list[OrthodonticCaseResponse]
    summary: OrthodonticSummaryResponse | None
    eligible_responsibles: list[OrthodonticDentistOption]
    record_label: str


class OrthodonticCaseActionResponse(BaseModel):
    success: bool = True
    message: str
    case: OrthodonticCaseResponse
