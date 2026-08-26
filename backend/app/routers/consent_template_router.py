from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.consent_template_schema import (
    CatalogItemResponse,
    ConsentContentReviewRequest,
    ConsentPreviewResponse,
    ConsentReasonRequest,
    ConsentTemplateCreateRequest,
    ConsentTemplateAuditResponse,
    ConsentTemplateListResponse,
    ConsentTemplateResponse,
    ConsentTemplateUpdateRequest,
    ConsentVersionCreateFromRequest,
    ConsentVersionDraftInput,
    ConsentVersionResponse,
    ConsentVersionUpdateRequest,
    VariableValidationResponse,
)
from app.services.auth_service import AuthContext
from app.services.consent_template_service import (
    ConsentTemplateError,
    confirm_content_review,
    create_draft,
    create_draft_from_version,
    create_template,
    document_kind_catalog,
    get_template,
    get_version,
    list_templates,
    list_template_audit,
    list_versions,
    preview_version,
    publish_version,
    retire_version,
    update_draft,
    update_template,
    validate_version,
    variable_catalog,
    void_draft,
)


router = APIRouter(tags=["Plantillas de consentimiento"])


def _http_error(exc: ConsentTemplateError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/consent-template-catalog/document-kinds", response_model=list[CatalogItemResponse])
def document_kinds_endpoint(
    _: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> list[CatalogItemResponse]:
    return document_kind_catalog()


@router.get("/api/consent-template-catalog/variables", response_model=list[CatalogItemResponse])
def variables_endpoint(
    _: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> list[CatalogItemResponse]:
    return variable_catalog()


@router.get("/api/consent-templates", response_model=ConsentTemplateListResponse)
def list_templates_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
    q: str | None = None,
    status: str | None = None,
    country: str | None = None,
    document_kind: str | None = None,
    site_id: UUID | None = None,
    procedure_id: UUID | None = None,
    specialty: str | None = None,
) -> ConsentTemplateListResponse:
    return list_templates(session, context, text_query=q, status=status, country=country, document_kind=document_kind, site_id=site_id, procedure_id=procedure_id, specialty=specialty)


@router.post("/api/consent-templates", response_model=ConsentTemplateResponse, status_code=201)
def create_template_endpoint(
    payload: ConsentTemplateCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.create"))],
) -> ConsentTemplateResponse:
    try:
        return create_template(session, context, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.get("/api/consent-templates/{template_id}", response_model=ConsentTemplateResponse)
def get_template_endpoint(
    template_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> ConsentTemplateResponse:
    try:
        return get_template(session, context, template_id)
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.patch("/api/consent-templates/{template_id}", response_model=ConsentTemplateResponse)
def update_template_endpoint(
    template_id: UUID,
    payload: ConsentTemplateUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.edit_draft"))],
) -> ConsentTemplateResponse:
    try:
        return update_template(session, context, template_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.get("/api/consent-templates/{template_id}/audit", response_model=list[ConsentTemplateAuditResponse])
def template_audit_endpoint(
    template_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.view_audit"))],
) -> list[ConsentTemplateAuditResponse]:
    try:
        return list_template_audit(session, context, template_id)
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.get("/api/consent-templates/{template_id}/versions", response_model=list[ConsentVersionResponse])
def list_versions_endpoint(
    template_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> list[ConsentVersionResponse]:
    try:
        return list_versions(session, context, template_id)
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions", response_model=ConsentVersionResponse, status_code=201)
def create_version_endpoint(
    template_id: UUID,
    payload: ConsentVersionDraftInput,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.create"))],
) -> ConsentVersionResponse:
    try:
        return create_draft(session, context, template_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.get("/api/consent-templates/{template_id}/versions/{version_id}", response_model=ConsentVersionResponse)
def get_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> ConsentVersionResponse:
    try:
        return get_version(session, context, template_id, version_id)
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.patch("/api/consent-templates/{template_id}/versions/{version_id}", response_model=ConsentVersionResponse)
def update_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    payload: ConsentVersionUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.edit_draft"))],
) -> ConsentVersionResponse:
    try:
        return update_draft(session, context, template_id, version_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/validate", response_model=VariableValidationResponse)
def validate_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> VariableValidationResponse:
    try:
        return validate_version(session, context, template_id, version_id)
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/preview", response_model=ConsentPreviewResponse)
def preview_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.read"))],
) -> ConsentPreviewResponse:
    try:
        return preview_version(session, context, template_id, version_id, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/publish", response_model=ConsentVersionResponse)
def publish_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.publish"))],
) -> ConsentVersionResponse:
    try:
        return publish_version(session, context, template_id, version_id, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/review-content", response_model=ConsentVersionResponse)
def review_content_endpoint(
    template_id: UUID,
    version_id: UUID,
    payload: ConsentContentReviewRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.review_content"))],
) -> ConsentVersionResponse:
    try:
        return confirm_content_review(session, context, template_id, version_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/retire", response_model=ConsentVersionResponse)
def retire_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    payload: ConsentReasonRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.retire"))],
) -> ConsentVersionResponse:
    try:
        return retire_version(session, context, template_id, version_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/void", response_model=ConsentVersionResponse)
def void_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    payload: ConsentReasonRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.void_draft"))],
) -> ConsentVersionResponse:
    try:
        return void_draft(session, context, template_id, version_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)


@router.post("/api/consent-templates/{template_id}/versions/{version_id}/create-draft", response_model=ConsentVersionResponse, status_code=201)
def create_draft_from_version_endpoint(
    template_id: UUID,
    version_id: UUID,
    payload: ConsentVersionCreateFromRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("consent.template.create"))],
) -> ConsentVersionResponse:
    try:
        return create_draft_from_version(session, context, template_id, version_id, payload, get_request_metadata(request))
    except ConsentTemplateError as exc:
        raise _http_error(exc)
