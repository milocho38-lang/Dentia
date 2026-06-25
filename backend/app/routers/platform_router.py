from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.platform_schema import (
    PlatformCompanyActionResponse,
    PlatformCompanyCreateRequest,
    PlatformCompanyCreateResponse,
    PlatformCompanyDetail,
    PlatformCompanyListResponse,
)
from app.services.auth_service import AuthContext
from app.services.platform_service import (
    PlatformError,
    change_company_status,
    create_platform_company,
    get_platform_company,
    list_platform_companies,
)


router = APIRouter(prefix="/api/platform", tags=["Platform"])


def handle(exc: PlatformError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/companies", response_model=PlatformCompanyListResponse)
def list_companies_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.companies.view"))
    ],
    search: str | None = Query(default=None, max_length=200),
) -> PlatformCompanyListResponse:
    return list_platform_companies(session, search)


@router.post(
    "/companies",
    response_model=PlatformCompanyCreateResponse,
    status_code=201,
)
def create_company_endpoint(
    payload: PlatformCompanyCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.companies.manage"))
    ],
) -> PlatformCompanyCreateResponse:
    try:
        return create_platform_company(
            session, context, payload, get_request_metadata(request)
        )
    except PlatformError as exc:
        raise handle(exc)


@router.get("/companies/{company_id}", response_model=PlatformCompanyDetail)
def company_detail_endpoint(
    company_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.companies.view"))
    ],
) -> PlatformCompanyDetail:
    try:
        return get_platform_company(session, company_id)
    except PlatformError as exc:
        raise handle(exc)


@router.post(
    "/companies/{company_id}/deactivate",
    response_model=PlatformCompanyActionResponse,
)
def deactivate_company_endpoint(
    company_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.companies.manage"))
    ],
) -> PlatformCompanyActionResponse:
    try:
        return change_company_status(
            session,
            context,
            company_id,
            active=False,
            metadata=get_request_metadata(request),
        )
    except PlatformError as exc:
        raise handle(exc)


@router.post(
    "/companies/{company_id}/reactivate",
    response_model=PlatformCompanyActionResponse,
)
def reactivate_company_endpoint(
    company_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.companies.manage"))
    ],
) -> PlatformCompanyActionResponse:
    try:
        return change_company_status(
            session,
            context,
            company_id,
            active=True,
            metadata=get_request_metadata(request),
        )
    except PlatformError as exc:
        raise handle(exc)
