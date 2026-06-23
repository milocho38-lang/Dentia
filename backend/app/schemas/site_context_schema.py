from uuid import UUID

from pydantic import BaseModel


class AuthSiteResponse(BaseModel):
    id: UUID
    name: str
    city: str
    timezone: str


class SwitchSiteRequest(BaseModel):
    site_id: UUID
