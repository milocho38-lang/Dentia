from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.organization_schema import (
    CompanyResponse,
    CompanyUpdateRequest,
    DentistSiteListResponse,
    DentistSiteManagementResponse,
    DentistSiteUpdateRequest,
    SiteActionRequest,
    SiteActionResponse,
    SiteCreateRequest,
    SiteImpactResponse,
    SiteListResponse,
    SiteResponse,
    SiteUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.organization_service import (
    OrganizationError,
    create_site,
    deactivate_site,
    get_company,
    get_site,
    list_dentists_for_site_management,
    list_sites,
    reactivate_site,
    site_impact,
    update_company,
    update_dentist_sites,
    update_site,
)


router = APIRouter(tags=["Organization"])


def handle(exc: OrganizationError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/company", response_model=CompanyResponse)
def company_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("company.view"))],
):
    return get_company(session, context)


@router.patch("/api/company", response_model=CompanyResponse)
def update_company_endpoint(
    payload: CompanyUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("company.update"))],
):
    try:
        return update_company(
            session, context, payload, get_request_metadata(request)
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.get("/api/sites", response_model=SiteListResponse)
def sites_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.view"))],
    search: str | None = Query(default=None, max_length=150),
    status: str | None = Query(default=None, max_length=20),
):
    try:
        return list_sites(
            session, context, search=search, status=status
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.post("/api/sites", response_model=SiteResponse, status_code=201)
def create_site_endpoint(
    payload: SiteCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.manage"))],
):
    try:
        return create_site(
            session, context, payload, get_request_metadata(request)
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.get("/api/sites/{site_id}", response_model=SiteResponse)
def site_endpoint(
    site_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.view"))],
):
    try:
        return get_site(session, context, site_id)
    except OrganizationError as exc:
        raise handle(exc)


@router.patch("/api/sites/{site_id}", response_model=SiteResponse)
def update_site_endpoint(
    site_id: UUID,
    payload: SiteUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.manage"))],
):
    try:
        return update_site(
            session, context, site_id, payload, get_request_metadata(request)
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.get("/api/sites/{site_id}/impact", response_model=SiteImpactResponse)
def impact_endpoint(
    site_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.view"))],
):
    try:
        return site_impact(session, context, site_id)
    except OrganizationError as exc:
        raise handle(exc)


@router.post("/api/sites/{site_id}/deactivate", response_model=SiteActionResponse)
def deactivate_endpoint(
    site_id: UUID,
    payload: SiteActionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.manage"))],
):
    try:
        return deactivate_site(
            session,
            context,
            site_id,
            payload.reason,
            get_request_metadata(request),
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.post("/api/sites/{site_id}/reactivate", response_model=SiteActionResponse)
def reactivate_endpoint(
    site_id: UUID,
    payload: SiteActionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.manage"))],
):
    try:
        return reactivate_site(
            session,
            context,
            site_id,
            payload.reason,
            get_request_metadata(request),
        )
    except OrganizationError as exc:
        raise handle(exc)


@router.get("/api/dentists", response_model=DentistSiteListResponse)
def dentists_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.view"))],
) -> DentistSiteListResponse:
    try:
        return list_dentists_for_site_management(session, context)
    except OrganizationError as exc:
        raise handle(exc)


@router.patch(
    "/api/dentists/{dentist_id}/sites",
    response_model=DentistSiteManagementResponse,
)
def update_dentist_sites_endpoint(
    dentist_id: UUID,
    payload: DentistSiteUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("sites.manage"))],
) -> DentistSiteManagementResponse:
    try:
        return update_dentist_sites(
            session,
            context,
            dentist_id,
            payload,
            get_request_metadata(request),
        )
    except OrganizationError as exc:
        raise handle(exc)
