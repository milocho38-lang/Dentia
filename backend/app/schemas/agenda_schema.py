from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


CONFIRMATION_METHODS = {"WhatsApp", "Llamada", "Presencial"}


class DentistOptionResponse(BaseModel):
    id: UUID
    name: str
    site_ids: list[UUID]


class SiteOptionResponse(BaseModel):
    id: UUID
    name: str
    address: str
    timezone: str


class AppointmentTypeOptionResponse(BaseModel):
    id: UUID
    name: str
    suggested_duration_minutes: int


class AgendaOptionsResponse(BaseModel):
    timezone: str = "America/Bogota"
    active_site_id: UUID | None = None
    dentists: list[DentistOptionResponse]
    sites: list[SiteOptionResponse]
    appointment_types: list[AppointmentTypeOptionResponse]


class AppointmentCreateRequest(BaseModel):
    patient_id: UUID
    dentist_id: UUID
    site_id: UUID
    appointment_type_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=1, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    is_overbook: bool = False
    overbook_reason: str | None = Field(default=None, max_length=300)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()

    @field_validator("notes", "overbook_reason")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria.")
        if self.ends_at <= self.starts_at:
            raise ValueError("La hora de fin debe ser posterior al inicio.")
        if self.is_overbook and not self.overbook_reason:
            raise ValueError("Debes justificar el sobrecupo.")
        return self


class AppointmentUpdateRequest(BaseModel):
    appointment_type_id: UUID | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class AppointmentConfirmRequest(BaseModel):
    method: str

    @field_validator("method")
    @classmethod
    def valid_method(cls, value: str) -> str:
        if value not in CONFIRMATION_METHODS:
            raise ValueError("Medio de confirmación no válido.")
        return value


class AppointmentCancelRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=300)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class AppointmentRescheduleRequest(BaseModel):
    site_id: UUID
    dentist_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=2, max_length=300)
    is_overbook: bool = False
    overbook_reason: str | None = Field(default=None, max_length=300)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()

    @field_validator("overbook_reason")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria.")
        if self.ends_at <= self.starts_at:
            raise ValueError("La hora de fin debe ser posterior al inicio.")
        if self.is_overbook and not self.overbook_reason:
            raise ValueError("Debes justificar el sobrecupo.")
        return self


class AppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    patient_mobile: str
    dentist_id: UUID
    dentist_name: str
    site_id: UUID
    site_name: str
    appointment_type_id: UUID
    appointment_type_name: str
    origin_appointment_id: UUID | None
    starts_at: datetime
    ends_at: datetime
    starts_at_local: str
    ends_at_local: str
    timezone: str
    reason: str
    notes: str | None
    status: str
    is_overbook: bool
    overbook_reason: str | None
    confirmation_method: str | None
    confirmed_at: datetime | None


class AgendaEventsResponse(BaseModel):
    items: list[AppointmentResponse]


class AppointmentWhatsAppLinkResponse(BaseModel):
    url: str
    phone: str
    message: str
