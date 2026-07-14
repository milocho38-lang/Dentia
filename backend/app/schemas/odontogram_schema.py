from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class OdontogramCatalogItemResponse(BaseModel):
    id: UUID
    company_id: UUID | None
    code: str
    name: str
    type: str
    category: str | None = None
    description: str | None = None
    color: str | None = None
    pattern: str | None = None
    symbol: str | None = None
    allowed_scopes: list[str] = Field(default_factory=list)
    allowed_surfaces: list[str] | None = None
    is_active: bool


class OdontogramResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinical_record_id: UUID
    status: str
    preferred_dentition: str
    created_on: datetime
    version: int


class OdontogramEnvelope(BaseModel):
    exists: bool
    odontogram: OdontogramResponse | None = None
    clinical_record_exists: bool


class OdontogramCreateRequest(BaseModel):
    preferred_dentition: str = "PERMANENT"


class OdontogramEventDetailInput(BaseModel):
    catalog_item_id: UUID
    scope_type: str
    zone: str | None = None
    tooth_code: str | None = None
    dentition: str | None = None
    surfaces: list[str] | None = None
    layer: str
    status_after: str | None = None
    metadata: dict | None = None


class OdontogramEventCreateRequest(BaseModel):
    event_type: str
    status: str = "DRAFT"
    evolution_id: UUID | None = None
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    procedure_id: UUID | None = None
    clinical_date: datetime | None = None
    site_id: UUID | None = None
    dentist_id: UUID | None = None
    observation: str | None = None
    details: list[OdontogramEventDetailInput]

    @model_validator(mode="after")
    def validate_details(self):
        if not self.details:
            raise ValueError("Debe registrar al menos un detalle odontográfico.")
        return self


class OdontogramEventUpdateRequest(BaseModel):
    version: int
    event_type: str
    evolution_id: UUID | None = None
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    procedure_id: UUID | None = None
    clinical_date: datetime | None = None
    site_id: UUID | None = None
    dentist_id: UUID | None = None
    observation: str | None = None
    details: list[OdontogramEventDetailInput]

    @model_validator(mode="after")
    def validate_details(self):
        if not self.details:
            raise ValueError("Debe registrar al menos un detalle odontográfico.")
        return self


class OdontogramEventConfirmRequest(BaseModel):
    version: int


class OdontogramEventCorrectRequest(BaseModel):
    reason: str
    replacement_event: OdontogramEventCreateRequest | None = None


class OdontogramEventDetailResponse(BaseModel):
    id: UUID
    catalog_item_id: UUID
    catalog_code: str
    catalog_name: str
    catalog_type: str
    color: str | None = None
    pattern: str | None = None
    symbol: str | None = None
    scope_type: str
    zone: str | None = None
    tooth_code: str | None = None
    dentition: str | None = None
    surfaces: list[str] | None = None
    layer: str
    status_after: str | None = None
    metadata: dict | None = None


class OdontogramEventResponse(BaseModel):
    id: UUID
    patient_id: UUID
    odontogram_id: UUID
    evolution_id: UUID | None = None
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    procedure_id: UUID | None = None
    event_type: str
    status: str
    clinical_date: datetime
    timezone: str
    observation: str | None = None
    correction_reason: str | None = None
    parent_event_id: UUID | None = None
    version: int
    content_hash: str | None = None
    confirmed_at: datetime | None = None
    confirmed_by: UUID | None = None
    site_id: UUID
    site_name: str | None = None
    dentist_id: UUID
    dentist_name: str | None = None
    created_by: UUID
    details: list[OdontogramEventDetailResponse] = Field(default_factory=list)


class OdontogramEventListResponse(BaseModel):
    items: list[OdontogramEventResponse] = Field(default_factory=list)


class OdontogramToothState(BaseModel):
    tooth_code: str
    dentition: str
    layers: dict[str, list[OdontogramEventDetailResponse]] = Field(default_factory=dict)
    event_count: int = 0


class OdontogramCurrentStateResponse(BaseModel):
    odontogram: OdontogramResponse
    preferred_dentition: str
    teeth: list[OdontogramToothState] = Field(default_factory=list)
    general_events: list[OdontogramEventResponse] = Field(default_factory=list)
    legend: list[OdontogramCatalogItemResponse] = Field(default_factory=list)


class OdontogramToothHistoryResponse(BaseModel):
    tooth_code: str
    items: list[OdontogramEventResponse] = Field(default_factory=list)
