from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


COMPANY_TYPES = {"Profesional independiente", "Consultorio", "Clínica"}


def validate_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Zona horaria no válida.") from exc
    return value


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    company_type: str | None
    tax_id: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    country: str | None
    timezone: str
    status: str
    profile_complete: bool
    created_at: datetime
    updated_at: datetime


class CompanyUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    company_type: str | None = Field(default=None, max_length=50)
    tax_id: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="America/Bogota", max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "company_type", "tax_id", "phone", "email", "address", "city", "country"
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("company_type")
    @classmethod
    def valid_company_type(cls, value: str | None) -> str | None:
        if value is not None and value not in COMPANY_TYPES:
            raise ValueError("Tipo de empresa no válido.")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str | None) -> str | None:
        if value and ("@" not in value or "." not in value.rsplit("@", 1)[-1]):
            raise ValueError("Correo electrónico no válido.")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return validate_timezone(value) or "America/Bogota"


class SiteResponse(BaseModel):
    id: UUID
    name: str
    address: str
    city: str
    phone: str | None
    timezone: str | None
    effective_timezone: str
    status: str
    is_active: bool
    assigned_users: int = 0
    dentists: int = 0
    future_appointments: int = 0
    open_followups: int = 0
    created_at: datetime
    updated_at: datetime


class SiteListResponse(BaseModel):
    items: list[SiteResponse]


class SiteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=3, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    timezone: str | None = Field(default=None, max_length=100)

    @field_validator("name", "address", "city")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        return validate_timezone(value)


class SiteUpdateRequest(SiteCreateRequest):
    pass


class SiteImpactResponse(BaseModel):
    future_appointments: int
    assigned_users: int
    default_for_users: int
    users_without_alternative: int
    active_sessions: int
    dentists: int
    open_followups: int
    active_sites_after: int
    can_deactivate: bool
    blocking_reasons: list[str]


class SiteActionRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class SiteActionResponse(BaseModel):
    success: bool = True
    message: str
    site: SiteResponse
    sessions_revoked: int = 0
    defaults_reassigned: int = 0


class DentistSiteOptionResponse(BaseModel):
    id: UUID
    name: str
    address: str
    timezone: str
    assigned: bool


class DentistSiteManagementResponse(BaseModel):
    id: UUID
    name: str
    status: str
    user_id: UUID | None
    site_ids: list[UUID]
    sites: list[DentistSiteOptionResponse]


class DentistSiteListResponse(BaseModel):
    items: list[DentistSiteManagementResponse]


class DentistSiteUpdateRequest(BaseModel):
    site_ids: list[UUID]
