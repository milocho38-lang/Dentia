from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.security import normalize_username

from app.schemas.site_context_schema import AuthSiteResponse


class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3, max_length=320)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_identifier(self):
        if self.identifier is None and self.email is None:
            raise ValueError("Ingresa tu nombre de usuario.")
        if (
            self.identifier is not None
            and self.email is not None
            and normalize_username(self.identifier) != normalize_username(self.email)
        ):
            raise ValueError("Los identificadores de acceso no coinciden.")
        return self

    @property
    def login_identifier(self) -> str:
        return self.identifier if self.identifier is not None else str(self.email)


class AuthUserResponse(BaseModel):
    id: UUID
    name: str
    username: str
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
