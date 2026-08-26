from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator


COMPANY_TYPES = {"Profesional independiente", "Consultorio", "Clínica"}
COUNTRIES = {"Colombia", "Chile"}


def validate_timezone(value: str) -> str:
    value = value.strip()
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Zona horaria no válida.") from exc
    if value not in {"America/Bogota", "America/Santiago"}:
        raise ValueError("Zona horaria no habilitada para C011A.")
    return value


class PlatformCompanyCreateRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    company_type: str
    tax_id: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    address: str = Field(min_length=3, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    country: str
    timezone: str
    admin_name: str = Field(min_length=2, max_length=200)
    admin_email: str = Field(min_length=3, max_length=320)
    admin_password: str | None = Field(default=None, min_length=12, max_length=256)

    @field_validator(
        "company_name",
        "company_type",
        "address",
        "city",
        "country",
        "timezone",
        "admin_name",
        "admin_email",
    )
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("tax_id", "phone", "email", "admin_password")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("company_type")
    @classmethod
    def valid_type(cls, value: str) -> str:
        if value not in COMPANY_TYPES:
            raise ValueError("Tipo de empresa no válido.")
        return value

    @field_validator("country")
    @classmethod
    def valid_country(cls, value: str) -> str:
        if value not in COUNTRIES:
            raise ValueError("País no válido.")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return validate_timezone(value)

    @field_validator("email", "admin_email")
    @classmethod
    def valid_email(cls, value: str | None) -> str | None:
        if value and ("@" not in value or "." not in value.rsplit("@", 1)[-1]):
            raise ValueError("Correo electrónico no válido.")
        return value

    @model_validator(mode="after")
    def validate_country_timezone(self):
        expected = {
            "Colombia": "America/Bogota",
            "Chile": "America/Santiago",
        }
        if expected[self.country] != self.timezone:
            raise ValueError("La zona horaria no corresponde al país seleccionado.")
        return self


class PlatformCompanyListItem(BaseModel):
    id: UUID
    name: str
    company_type: str | None
    tax_id: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    country: str | None
    timezone: str
    status: str
    is_active: bool
    site_count: int
    user_count: int
    active_dentist_count: int
    max_active_dentists: int
    created_at: datetime
    updated_at: datetime


class PlatformCompanyListResponse(BaseModel):
    items: list[PlatformCompanyListItem]


class PlatformSiteSummary(BaseModel):
    id: UUID
    name: str
    city: str
    timezone: str | None
    effective_timezone: str
    status: str


class PlatformRoleOption(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None


class PlatformUserSiteSummary(BaseModel):
    id: UUID
    name: str
    is_default: bool


class PlatformDentistProfileSummary(BaseModel):
    id: UUID
    name: str
    status: str
    is_active: bool
    sites: list[PlatformUserSiteSummary]


class PlatformUserSummary(BaseModel):
    id: UUID
    name: str
    email: str
    status: str
    is_active: bool
    role_ids: list[UUID]
    roles: list[str]
    role_names: list[str]
    sites: list[PlatformUserSiteSummary]
    dentist_profile: PlatformDentistProfileSummary | None = None
    needs_dentist_profile: bool = False


class PlatformCompanyDetail(PlatformCompanyListItem):
    sites: list[PlatformSiteSummary]
    users: list[PlatformUserSummary]
    role_options: list[PlatformRoleOption]


class PlatformCompanyCreateResponse(BaseModel):
    company: PlatformCompanyDetail
    admin_user: PlatformUserSummary
    temporary_password: str


class PlatformCompanyActionResponse(BaseModel):
    success: bool = True
    message: str
    company: PlatformCompanyDetail


class PlatformCompanyUserRoleUpdateRequest(BaseModel):
    role_ids: list[UUID] = Field(min_length=1)
    site_ids: list[UUID] = Field(min_length=1)
    default_site_id: UUID
    status: str
    ensure_dentist_profile: bool = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip()
        if value not in {"Activo", "Inactivo"}:
            raise ValueError("Estado no válido.")
        return value

    @model_validator(mode="after")
    def validate_default_site(self):
        if self.default_site_id not in self.site_ids:
            raise ValueError("La sede predeterminada debe estar asignada.")
        return self


class PlatformCompanyUserRoleUpdateResponse(BaseModel):
    success: bool = True
    message: str
    user: PlatformUserSummary


class PlatformCompanyDentistLimitUpdateRequest(BaseModel):
    max_active_dentists: int

    @field_validator("max_active_dentists")
    @classmethod
    def validate_dentist_limit(cls, value: int) -> int:
        if value not in {1, 3, 5, 10}:
            raise ValueError("El límite debe ser 1, 3, 5 o 10 odontólogos.")
        return value


class PlatformCompanyDentistLimitUpdateResponse(BaseModel):
    success: bool = True
    message: str
    company: PlatformCompanyDetail
