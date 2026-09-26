from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PeriodontalToothState = Literal["PRESENT", "ABSENT", "IMPLANT"]
PeriodontalSiteCode = Literal[
    "BUCCAL_DISTAL",
    "BUCCAL_MID",
    "BUCCAL_MESIAL",
    "LINGUAL_DISTAL",
    "LINGUAL_MID",
    "LINGUAL_MESIAL",
]


class PeriodontogramPilotCompanyUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool


class PeriodontogramPilotDentistUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    reason: str | None = Field(default=None, max_length=300)


class PeriodontogramPilotDentistResponse(BaseModel):
    authorization_id: UUID | None
    dentist_id: UUID
    user_id: UUID | None
    dentist_name: str
    dentist_status: str
    dentist_is_active: bool
    user_is_active: bool
    authorized: bool
    authorized_at: datetime | None
    authorized_by_user_id: UUID | None
    revoked_at: datetime | None
    revoked_by_user_id: UUID | None


class PeriodontogramPilotResponse(BaseModel):
    company_id: UUID
    enabled: bool
    enabled_at: datetime | None
    enabled_by_user_id: UUID | None
    disabled_at: datetime | None
    disabled_by_user_id: UUID | None
    dentists: list[PeriodontogramPilotDentistResponse]


class PeriodontogramPilotAccessResponse(BaseModel):
    allowed: bool
    code: str
    message: str
    company_id: UUID
    dentist_id: UUID | None
    company_enabled: bool
    dentist_authorized: bool


class PeriodontalExamCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: UUID | None = None
    clinical_date: date


class PeriodontalExamFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)


class PeriodontalExamCorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("El motivo de corrección debe tener al menos 3 caracteres.")
        return normalized


class PeriodontalEvolutionLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evolution_id: UUID
    row_version: int = Field(ge=1)


class PeriodontalToothDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fdi_number: int
    state: PeriodontalToothState | None = None
    mobility_grade: int | None = Field(default=None, ge=0, le=3)
    furcation_mesial: bool | None = None
    furcation_distal: bool | None = None
    clinical_note: str | None = Field(default=None, max_length=1000)
    clear_clinical_data: bool = False


class PeriodontalSiteDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fdi_number: int
    site_code: PeriodontalSiteCode
    probing_depth_mm: int | None = Field(default=None, ge=0, le=50)
    gingival_margin_mm: int | None = Field(default=None, ge=-50, le=50)
    bleeding_on_probing: bool | None = None
    plaque: bool | None = None
    suppuration: bool | None = None


class PeriodontalDraftBatchUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_version: int = Field(ge=1)
    teeth: list[PeriodontalToothDraftUpdate] = Field(default_factory=list, max_length=32)
    sites: list[PeriodontalSiteDraftUpdate] = Field(default_factory=list, max_length=192)

    @model_validator(mode="after")
    def validate_batch(self) -> "PeriodontalDraftBatchUpdateRequest":
        if not self.teeth and not self.sites:
            raise ValueError("Debes enviar al menos un cambio periodontal.")
        tooth_keys = [item.fdi_number for item in self.teeth]
        if len(tooth_keys) != len(set(tooth_keys)):
            raise ValueError("No se puede actualizar dos veces el mismo diente en un lote.")
        site_keys = [(item.fdi_number, item.site_code) for item in self.sites]
        if len(site_keys) != len(set(site_keys)):
            raise ValueError("No se puede actualizar dos veces el mismo sitio en un lote.")
        return self


class PeriodontalSiteResponse(BaseModel):
    site_code: PeriodontalSiteCode
    probing_depth_mm: int | None
    gingival_margin_mm: int | None
    clinical_attachment_level_mm: int | None
    is_periodontal_pocket: bool
    bleeding_on_probing: bool | None
    plaque: bool | None
    suppuration: bool | None


class PeriodontalToothResponse(BaseModel):
    fdi_number: int
    state: PeriodontalToothState
    mobility_grade: int | None
    furcation_mesial: bool | None
    furcation_distal: bool | None
    clinical_note: str | None
    sites: list[PeriodontalSiteResponse]


class PeriodontalCoverageResponse(BaseModel):
    eligible_sites: int
    evaluated_sites: int
    incomplete: bool


class PeriodontalIndexResponse(BaseModel):
    positive_sites: int
    evaluated_sites: int
    percentage: float | None


class PeriodontalIndicesResponse(BaseModel):
    bop: PeriodontalIndexResponse
    plaque: PeriodontalIndexResponse


class PeriodontalExamVersionResponse(BaseModel):
    id: UUID
    exam_id: UUID
    version_number: int
    status: Literal["DRAFT", "FINALIZED"]
    schema_version: str
    row_version: int
    content: dict[str, Any]
    snapshot: dict[str, Any] | None
    snapshot_hash: str | None
    integrity_status: Literal["NOT_APPLICABLE", "PASS", "FAIL"]
    supersedes_version_id: UUID | None
    correction_reason: str | None
    created_by_user_id: UUID
    finalized_by_user_id: UUID | None
    finalized_at: datetime | None
    created_at: datetime


class PeriodontalEvolutionSummaryResponse(BaseModel):
    id: UUID
    attended_at: datetime
    timezone_name: str
    status: Literal["DRAFT", "SIGNED", "VOIDED_BY_COMPENSATING_RECORD"]
    site_id: UUID
    site_name: str
    dentist_id: UUID
    dentist_name: str


class PeriodontalEvolutionCandidateListResponse(BaseModel):
    items: list[PeriodontalEvolutionSummaryResponse]


class PeriodontalExamResponse(BaseModel):
    id: UUID
    company_id: UUID
    patient_id: UUID
    site_id: UUID
    site_name: str
    timezone_name: str
    responsible_dentist_id: UUID
    professional_name: str
    evolution_id: UUID | None
    linked_evolution: PeriodontalEvolutionSummaryResponse | None
    status: Literal["DRAFT", "FINALIZED"]
    clinical_date: date
    finalized_at: datetime | None
    row_version: int
    current_version: PeriodontalExamVersionResponse
    versions: list[PeriodontalExamVersionResponse]
    teeth: list[PeriodontalToothResponse]
    coverage: PeriodontalCoverageResponse
    indices: PeriodontalIndicesResponse
    created_at: datetime
    updated_at: datetime


class PeriodontalExamHistoryItem(BaseModel):
    id: UUID
    clinical_date: date
    professional_name: str
    site_name: str
    status: Literal["DRAFT", "FINALIZED"]
    current_version_number: int
    allowed_actions: list[Literal["VIEW", "FINALIZE", "CORRECT"]]
    created_at: datetime


class PeriodontalExamListResponse(BaseModel):
    items: list[PeriodontalExamHistoryItem]
    total: int


class PeriodontalExamActionResponse(BaseModel):
    success: bool = True
    message: str
    exam: PeriodontalExamResponse
