from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.consent_library_schema import ConsentLibraryEquivalenceApprovalRequest, ConsentLibraryInstallRequest, ConsentLibraryInstallResponse, ConsentLibraryListResponse, ConsentLibrarySourceResponse, ConsentLibraryVersionResponse
from app.services.auth_service import AuthContext
from app.services.consent_library_service import ConsentLibraryError, approve_library_equivalence, get_library_source_for_review, install_library_version, list_library

router = APIRouter(tags=["Biblioteca oficial de documentos odontológicos"])


def _http_error(exc: ConsentLibraryError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/consent-library", response_model=ConsentLibraryListResponse)
def list_library_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.library.read"))],
    q: str | None = None,
    country: str | None = None,
    document_type: str | None = None,
    specialty: str | None = None,
    category: str | None = None,
    signer_scope: str | None = None,
    publication_status: str | None = None,
) -> ConsentLibraryListResponse:
    try:
        return list_library(session, context, text_query=q, country=country, document_type=document_type, specialty=specialty, category=category, signer_scope=signer_scope, publication_status=publication_status)
    except ConsentLibraryError as exc:
        raise _http_error(exc)


@router.get("/api/consent-library/versions/{version_id}/source", response_model=ConsentLibrarySourceResponse)
def get_library_source_endpoint(
    version_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.library.manage"))],
) -> ConsentLibrarySourceResponse:
    return get_library_source_for_review(session, version_id)


@router.post("/api/consent-library/versions/{version_id}/install", response_model=ConsentLibraryInstallResponse)
def install_library_endpoint(
    version_id: UUID,
    payload: ConsentLibraryInstallRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.library.install"))],
) -> ConsentLibraryInstallResponse:
    try:
        return install_library_version(session, context, version_id, payload, get_request_metadata(request), mode="EXACT")
    except ConsentLibraryError as exc:
        raise _http_error(exc)


@router.post("/api/consent-library/versions/{version_id}/clone", response_model=ConsentLibraryInstallResponse)
def clone_library_endpoint(
    version_id: UUID,
    payload: ConsentLibraryInstallRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.library.clone"))],
) -> ConsentLibraryInstallResponse:
    try:
        return install_library_version(session, context, version_id, payload, get_request_metadata(request), mode="CLONE")
    except ConsentLibraryError as exc:
        raise _http_error(exc)


@router.post("/api/consent-library/versions/{version_id}/approve-equivalence", response_model=ConsentLibraryVersionResponse)
def approve_equivalence_endpoint(
    version_id: UUID,
    payload: ConsentLibraryEquivalenceApprovalRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.library.manage"))],
) -> ConsentLibraryVersionResponse:
    try:
        return approve_library_equivalence(session, context, version_id, payload, get_request_metadata(request))
    except ConsentLibraryError as exc:
        raise _http_error(exc)
