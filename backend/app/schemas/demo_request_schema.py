from datetime import datetime
from urllib.parse import urlsplit
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.demo_request import DEMO_PRACTICE_TYPES, DEMO_REQUEST_STATUSES


def _strip_required(value: str) -> str:
    return value.strip()


def _strip_optional(value: str | None) -> str | None:
    return value.strip() or None if value else None


class PublicDemoRequestCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=320)
    phone: str = Field(min_length=7, max_length=50)
    country: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=120)
    practice_type: str
    dentist_count: int = Field(ge=1, le=10_000)
    message: str | None = Field(default=None, max_length=2_000)
    privacy_consent: bool
    consent_version: str | None = Field(default=None, max_length=80)
    company_website: str | None = Field(default=None, max_length=500)

    @field_validator(
        "first_name",
        "last_name",
        "email",
        "phone",
        "country",
        "city",
        "practice_type",
    )
    @classmethod
    def strip_required(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("message", "consent_version", "company_website")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.casefold()
        if (
            normalized.count("@") != 1
            or any(character.isspace() for character in normalized)
            or "." not in normalized.rsplit("@", 1)[-1]
        ):
            raise ValueError("Correo electrónico no válido.")
        return normalized

    @field_validator("practice_type")
    @classmethod
    def validate_practice_type(cls, value: str) -> str:
        if value not in DEMO_PRACTICE_TYPES:
            raise ValueError("Tipo de práctica no válido.")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        labels = {
            "CO": "CO",
            "COLOMBIA": "CO",
            "CL": "CL",
            "CHILE": "CL",
            "OTHER": "OTHER",
            "OTRO": "OTHER",
        }
        return labels.get(value.upper(), value)

    @model_validator(mode="after")
    def require_privacy_consent(self):
        if not self.privacy_consent:
            raise ValueError("Debes autorizar el contacto para enviar la solicitud.")
        return self


class PublicDemoRequestResponse(BaseModel):
    accepted: bool = True
    message: str


class DemoRequestOwner(BaseModel):
    id: UUID
    name: str
    email: str


class DemoRequestListItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    country: str
    city: str
    practice_type: str
    dentist_count: int
    source: str
    status: str
    assigned_to: DemoRequestOwner | None
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    row_version: int


class DemoRequestNoteResponse(BaseModel):
    id: UUID
    text: str
    author: DemoRequestOwner
    created_at: datetime


class DemoRequestDetail(DemoRequestListItem):
    phone: str
    message: str | None
    timezone: str | None
    meeting_url: str | None
    contacted_at: datetime | None
    converted_at: datetime | None
    consent_at: datetime
    consent_version: str
    notification_status: str
    notes: list[DemoRequestNoteResponse]


class DemoRequestListResponse(BaseModel):
    items: list[DemoRequestListItem]
    total: int
    page: int
    page_size: int


class DemoRequestOwnersResponse(BaseModel):
    items: list[DemoRequestOwner]


class DemoRequestAssignmentUpdate(BaseModel):
    assigned_to_user_id: UUID | None = None
    row_version: int = Field(ge=1)


class DemoRequestStatusUpdate(BaseModel):
    status: str
    reason: str | None = Field(default=None, max_length=1_000)
    row_version: int = Field(ge=1)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in DEMO_REQUEST_STATUSES:
            raise ValueError("Estado no válido.")
        return value

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class DemoRequestScheduleUpdate(BaseModel):
    scheduled_at: datetime
    timezone: str = Field(min_length=1, max_length=80)
    meeting_url: str | None = Field(default=None, max_length=500)
    assigned_to_user_id: UUID | None = None
    note: str | None = Field(default=None, max_length=1_000)
    row_version: int = Field(ge=1)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        value = value.strip()
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Zona horaria no válida.") from exc
        return value

    @field_validator("meeting_url")
    @classmethod
    def validate_meeting_url(cls, value: str | None) -> str | None:
        value = _strip_optional(value)
        if value:
            parsed = urlsplit(value)
            if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
                raise ValueError("El enlace de reunión debe usar una URL HTTP o HTTPS válida.")
        return value

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @model_validator(mode="after")
    def apply_selected_timezone(self):
        if self.scheduled_at.tzinfo is None:
            self.scheduled_at = self.scheduled_at.replace(tzinfo=ZoneInfo(self.timezone))
        return self


class DemoRequestNoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    row_version: int = Field(ge=1)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()
