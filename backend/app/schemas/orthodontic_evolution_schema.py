from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CATALOG_TYPES = {"ARCH_MATERIAL", "ARCH_SIZE", "CONTROL_INTERVAL"}
MINI_SCREW_TYPES = {"SELF_TAPPING", "SELF_DRILLING"}
MINI_SCREW_LOCATIONS = {
    "INTERRADICULAR",
    "PALATAL",
    "RETROMOLAR",
    "INFRAZYGOMATIC_OR_ANTERIOR_ALVEOLAR",
}
MINI_SCREW_MATERIALS = {"TITANIUM", "STEEL"}


class OrthodonticCatalogOptionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=160)
    interval_value: int | None = Field(default=None, ge=1, le=120)
    interval_unit: str | None = None

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if "<" in normalized or ">" in normalized:
            raise ValueError("La etiqueta debe ser texto plano.")
        return normalized

    @model_validator(mode="after")
    def validate_interval(self):
        if (self.interval_value is None) != (self.interval_unit is None):
            raise ValueError("El intervalo necesita valor y unidad.")
        if self.interval_unit is not None:
            self.interval_unit = self.interval_unit.upper()
            if self.interval_unit not in {"WEEK", "MONTH"}:
                raise ValueError("La unidad debe ser WEEK o MONTH.")
        return self


class OrthodonticCatalogOptionResponse(BaseModel):
    id: UUID
    catalog_type: str
    scope: str
    code: str
    label: str
    status: str
    sort_order: int
    interval_value: int | None
    interval_unit: str | None


class OrthodonticCatalogResponse(BaseModel):
    catalog_type: str
    can_manage: bool
    items: list[OrthodonticCatalogOptionResponse]


class OrthodonticMiniScrewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screw_type: str
    location: str
    material: str
    measurement: str = Field(min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("screw_type")
    @classmethod
    def valid_type(cls, value: str) -> str:
        value = value.upper()
        if value not in MINI_SCREW_TYPES:
            raise ValueError("Tipo de microtornillo no válido.")
        return value

    @field_validator("location")
    @classmethod
    def valid_location(cls, value: str) -> str:
        value = value.upper()
        if value not in MINI_SCREW_LOCATIONS:
            raise ValueError("Ubicación de microtornillo no válida.")
        return value

    @field_validator("material")
    @classmethod
    def valid_material(cls, value: str) -> str:
        value = value.upper()
        if value not in MINI_SCREW_MATERIALS:
            raise ValueError("Material de microtornillo no válido.")
        return value

    @field_validator("measurement", "notes")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split()) or None


class OrthodonticEvolutionBaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: UUID | None = None
    attended_at: datetime | None = None
    performed_summary: str | None = Field(default=None, max_length=6000)
    notes: str | None = Field(default=None, max_length=12000)
    upper_material_option_id: UUID | None = None
    upper_size_option_id: UUID | None = None
    lower_material_option_id: UUID | None = None
    lower_size_option_id: UUID | None = None
    upper_aligner_note: str | None = Field(default=None, max_length=500)
    lower_aligner_note: str | None = Field(default=None, max_length=500)
    elastic_type: str | None = Field(default=None, max_length=500)
    elastic_configuration: str | None = Field(default=None, max_length=1000)
    mini_screws: list[OrthodonticMiniScrewInput] = Field(default_factory=list, max_length=20)
    next_session_instructions: str | None = Field(default=None, max_length=5000)
    next_control_option_id: UUID | None = None
    alert_text: str | None = Field(default=None, max_length=2000)
    alert_active: bool = False

    @field_validator(
        "performed_summary", "notes", "upper_aligner_note", "lower_aligner_note",
        "elastic_type", "elastic_configuration", "next_session_instructions", "alert_text",
    )
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def alert_requires_text(self):
        if self.alert_active and not self.alert_text:
            raise ValueError("Una alerta activa requiere texto.")
        return self


class OrthodonticEvolutionCreateRequest(OrthodonticEvolutionBaseInput):
    pass


class OrthodonticEvolutionUpdateRequest(OrthodonticEvolutionBaseInput):
    row_version: int = Field(ge=1)
    clinical_evolution_version: int = Field(ge=1)


class OrthodonticEvolutionSignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row_version: int = Field(ge=1)
    clinical_evolution_version: int = Field(ge=1)
    confirm_complete: bool = True


class OrthodonticMiniScrewResponse(BaseModel):
    id: UUID
    screw_type: str
    location: str
    material: str
    measurement: str
    notes: str | None
    sort_order: int


class OrthodonticOptionSnapshot(BaseModel):
    option_id: UUID | None
    code: str | None
    label: str | None


class OrthodonticEvolutionResponse(BaseModel):
    id: UUID
    orthodontic_case_id: UUID
    clinical_evolution_id: UUID
    professional_name: str
    site_id: UUID
    attended_at: datetime
    timezone_name: str
    status: str
    row_version: int
    clinical_evolution_version: int
    signed_at: datetime | None
    schema_version: str
    performed_summary: str | None
    notes: str | None
    upper_material: OrthodonticOptionSnapshot
    upper_size: OrthodonticOptionSnapshot
    lower_material: OrthodonticOptionSnapshot
    lower_size: OrthodonticOptionSnapshot
    upper_aligner_note: str | None
    lower_aligner_note: str | None
    elastic_type: str | None
    elastic_configuration: str | None
    mini_screws: list[OrthodonticMiniScrewResponse]
    next_session_instructions: str | None
    next_control: OrthodonticOptionSnapshot
    next_control_value: int | None
    next_control_unit: str | None
    suggested_next_control_date: date | None
    alert_text: str | None
    alert_active: bool
    orthodontic_payload_hash: str | None
    integrity_status: str


class OrthodonticEvolutionListResponse(BaseModel):
    items: list[OrthodonticEvolutionResponse]
