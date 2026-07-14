from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


USER_STATUSES = {"Pendiente", "Activo", "Suspendido", "Inactivo"}


class RoleOptionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None


class SiteOptionResponse(BaseModel):
    id: UUID
    name: str


class AccessOptionsResponse(BaseModel):
    roles: list[RoleOptionResponse]
    sites: list[SiteOptionResponse]


class UserRoleResponse(BaseModel):
    id: UUID
    code: str
    name: str


class UserSiteResponse(BaseModel):
    id: UUID
    name: str
    is_default: bool


class UserSummaryResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str | None
    status: str
    is_active: bool
    is_locked: bool
    locked_until: datetime | None
    must_change_password: bool
    last_login_at: datetime | None
    default_site_id: UUID | None
    default_site_name: str | None
    roles: list[UserRoleResponse]
    sites: list[UserSiteResponse]
    active_sessions: int
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    role_ids: list[UUID] = Field(min_length=1)
    site_ids: list[UUID] = Field(min_length=1)
    default_site_id: UUID

    @field_validator("name", "email")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_default_site(self):
        if self.default_site_id not in self.site_ids:
            raise ValueError("La sede predeterminada debe estar asignada.")
        return self


class UserUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("name", "email")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class UserRolesRequest(BaseModel):
    role_ids: list[UUID] = Field(min_length=1)


class UserSitesRequest(BaseModel):
    site_ids: list[UUID] = Field(min_length=1)
    default_site_id: UUID

    @model_validator(mode="after")
    def validate_default_site(self):
        if self.default_site_id not in self.site_ids:
            raise ValueError("La sede predeterminada debe estar asignada.")
        return self


class EnableClinicalRoleRequest(BaseModel):
    role_code: str = "DENTIST_ADMIN"

    @field_validator("role_code")
    @classmethod
    def validate_role_code(cls, value: str) -> str:
        if value not in {"DENTIST", "DENTIST_ADMIN"}:
            raise ValueError("Rol clínico no válido.")
        return value


class TemporaryPasswordResponse(BaseModel):
    user: UserSummaryResponse
    temporary_password: str


class ActionResponse(BaseModel):
    success: bool = True
    message: str
    user: UserSummaryResponse | None = None


class UserSessionResponse(BaseModel):
    id: UUID
    active_site_id: UUID | None
    active_site_name: str | None
    ip_address: str | None
    user_agent: str | None
    device_name: str | None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revoke_reason: str | None
    is_active: bool


class UserSessionsResponse(BaseModel):
    items: list[UserSessionResponse]


class AuditEventResponse(BaseModel):
    id: UUID
    action: str
    result: str
    detail: dict | None
    ip_address: str | None
    user_agent: str | None
    occurred_at: datetime
    actor_user_id: UUID | None


class UserAuditResponse(BaseModel):
    items: list[AuditEventResponse]


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden.")
        if self.current_password == self.new_password:
            raise ValueError("La nueva contraseña debe ser diferente.")
        return self
