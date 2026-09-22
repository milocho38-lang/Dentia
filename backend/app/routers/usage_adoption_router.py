from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_permission
from app.database.session import get_db
from app.schemas.usage_adoption_schema import (
    UsageAdoptionResponse,
    UsageContextResponse,
)
from app.services.auth_service import AuthContext
from app.services.usage_adoption_service import (
    UsageAdoptionError,
    get_usage_context,
    get_user_usage_adoption,
)


router = APIRouter(prefix="/api/platform/usage", tags=["Platform usage adoption"])


@router.get("/context", response_model=UsageContextResponse)
def usage_context_endpoint(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _context: Annotated[
        AuthContext, Depends(require_permission("platform.usage.view"))
    ],
    company_id: UUID | None = Query(default=None),
) -> UsageContextResponse:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    try:
        return get_usage_context(session, company_id=company_id)
    except UsageAdoptionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": "USAGE_CONTEXT_INVALID", "message": str(exc)},
        ) from exc


@router.get("/users/{user_id}", response_model=UsageAdoptionResponse)
def user_usage_adoption_endpoint(
    user_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _context: Annotated[
        AuthContext, Depends(require_permission("platform.usage.view"))
    ],
    company_id: UUID = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    preset: str | None = Query(default=None, max_length=30),
    dentist_id: UUID | None = Query(default=None),
    site_id: UUID | None = Query(default=None),
) -> UsageAdoptionResponse:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    try:
        return get_user_usage_adoption(
            session,
            company_id=company_id,
            user_id=user_id,
            dentist_id=dentist_id,
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            preset=preset,
        )
    except UsageAdoptionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": "USAGE_ADOPTION_INVALID", "message": str(exc)},
        ) from exc
