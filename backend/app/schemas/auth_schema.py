from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.site_context_schema import AuthSiteResponse


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class AuthUserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    company_id: UUID
    active_site_id: UUID | None
    active_site_name: str | None
    sites: list[AuthSiteResponse]
    roles: list[str]
    permissions: list[str]
    must_change_password: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Sesión cerrada."


class MeResponse(AuthUserResponse):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
