from datetime import datetime
import re
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


COMPANY_TYPES = {"Profesional independiente", "Consultorio", "Clínica"}
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


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


class BrandingResponse(BaseModel):
    id: UUID
    name: str
    legal_name: str | None
    company_type: str | None
    tax_id: str | None
    address: str | None
    city: str | None
    department: str | None
    country: str | None
    phone: str | None
    mobile: str | None
    email: str | None
    website: str | None
    social_media: dict[str, str] | None
    logo_filename: str | None
    logo_url: str | None
    signature_filename: str | None
    signature_url: str | None
    primary_dentist_name: str | None
    professional_specialty: str | None
    professional_license: str | None
    university: str | None
    experience_years: int | None
    header_text: str | None
    footer_text: str | None
    legal_observations: str | None
    cancellation_policy: str | None
    thank_you_message: str | None
    primary_color: str
    secondary_color: str
    button_color: str
    heading_color: str
    updated_at: datetime


class BrandingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)
    company_type: str | None = Field(default=None, max_length=50)
    tax_id: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    mobile: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    social_media: dict[str, str] | None = None
    primary_dentist_name: str | None = Field(default=None, max_length=200)
    professional_specialty: str | None = Field(default=None, max_length=150)
    professional_license: str | None = Field(default=None, max_length=100)
    university: str | None = Field(default=None, max_length=200)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    header_text: str | None = Field(default=None, max_length=1000)
    footer_text: str | None = Field(default=None, max_length=1000)
    legal_observations: str | None = Field(default=None, max_length=2000)
    cancellation_policy: str | None = Field(default=None, max_length=2000)
    thank_you_message: str | None = Field(default=None, max_length=1000)
    primary_color: str = "#16a34a"
    secondary_color: str = "#0f766e"
    button_color: str = "#16a34a"
    heading_color: str = "#0f172a"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "legal_name",
        "company_type",
        "tax_id",
        "address",
        "city",
        "department",
        "country",
        "phone",
        "mobile",
        "email",
        "website",
        "primary_dentist_name",
        "professional_specialty",
        "professional_license",
        "university",
        "header_text",
        "footer_text",
        "legal_observations",
        "cancellation_policy",
        "thank_you_message",
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

    @field_validator("website")
    @classmethod
    def valid_website(cls, value: str | None) -> str | None:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("El sitio web debe iniciar con http:// o https://.")
        return value

    @field_validator("social_media")
    @classmethod
    def clean_social_media(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if not value:
            return None
        cleaned = {
            str(key).strip()[:50]: str(item).strip()[:300]
            for key, item in value.items()
            if str(key).strip() and str(item).strip()
        }
        return cleaned or None

    @field_validator("primary_color", "secondary_color", "button_color", "heading_color")
    @classmethod
    def valid_color(cls, value: str) -> str:
        value = value.strip()
        if not HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError("Color institucional no válido.")
        return value


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
