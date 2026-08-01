from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_auth_context, get_request_metadata
from app.database.session import get_db
from app.models.audit_event import AuditEvent
from app.schemas.consent_instance_schema import (
    ApplicableTemplatesRequest,
    ApplicableTemplatesResponse,
    ConsentInstanceAuditResponse,
    ConsentInstanceBatchCreateRequest,
    ConsentInstanceConfirmRequest,
    ConsentInstanceCreateRequest,
    ConsentInstanceListResponse,
    ConsentInstancePreviewResponse,
    ConsentInstanceResponse,
    ConsentInstanceUpdateRequest,
    ConsentInstanceVoidRequest,
)
from app.services.auth_service import AuthContext
from app.services.consent_instance_service import (
    ConsentInstanceError,
    applicable_templates,
    confirm_professionally,
    create_batch,
    get_instance,
    list_audit,
    list_instances,
    mark_pending_signature,
    preview_instance,
    resolve_instance,
    update_instance,
    void_instance,
)


router = APIRouter(prefix="/api/consent-instances", tags=["Instancias de consentimiento"])


def _error(exc: ConsentInstanceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def require_consent_permission(permission: str):
    def permission_dependency(
        request: Request,
        session: Annotated[Session, Depends(get_db)],
        context: Annotated[AuthContext, Depends(get_current_auth_context)],
    ) -> AuthContext:
        if context.user.must_change_password or permission not in context.permissions:
            metadata = get_request_metadata(request)
            session.add(AuditEvent(
                company_id=context.user.company_id,
                user_id=context.user.id,
                session_id=context.auth_session.id,
                entity="consent_instance",
                action="CONSENT_INSTANCE_ACCESS_DENIED",
                result="FAILURE",
                detail={"permission": permission, "path": request.url.path, "method": request.method},
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            ))
            session.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para realizar esta acción.")
        return context

    return permission_dependency


@router.post("/applicable-templates", response_model=ApplicableTemplatesResponse)
def candidates(payload: ApplicableTemplatesRequest, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.create"))]):
    try: return applicable_templates(session, context, payload)
    except ConsentInstanceError as exc: raise _error(exc)


@router.get("", response_model=ConsentInstanceListResponse)
def instances(session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.read"))], patient_id: UUID | None = None):
    return list_instances(session, context, patient_id)


@router.post("", response_model=ConsentInstanceResponse, status_code=201)
def create(payload: ConsentInstanceCreateRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.create"))]):
    try: return create_batch(session, context, ConsentInstanceBatchCreateRequest(context=payload.context, template_version_ids=[payload.template_version_id]), get_request_metadata(request))[0]
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/batch", response_model=list[ConsentInstanceResponse], status_code=201)
def batch(payload: ConsentInstanceBatchCreateRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.create"))]):
    try: return create_batch(session, context, payload, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.get("/{instance_id}", response_model=ConsentInstanceResponse)
def detail(instance_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.read"))]):
    try: return get_instance(session, context, instance_id)
    except ConsentInstanceError as exc: raise _error(exc)


@router.patch("/{instance_id}", response_model=ConsentInstanceResponse)
def update(instance_id: UUID, payload: ConsentInstanceUpdateRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.edit_draft"))]):
    try: return update_instance(session, context, instance_id, payload, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/{instance_id}/resolve", response_model=ConsentInstanceResponse)
def resolve(instance_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.edit_draft"))]):
    try: return resolve_instance(session, context, instance_id, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/{instance_id}/preview", response_model=ConsentInstancePreviewResponse)
def preview(instance_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.read"))]):
    try: return preview_instance(session, context, instance_id, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/{instance_id}/professional-confirm", response_model=ConsentInstanceResponse)
@router.post("/{instance_id}/ready-for-review", response_model=ConsentInstanceResponse, include_in_schema=False)
def confirm(instance_id: UUID, payload: ConsentInstanceConfirmRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.review"))]):
    try: return confirm_professionally(session, context, instance_id, payload, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/{instance_id}/mark-pending-signature", status_code=409)
def pending(instance_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.mark_pending_signature"))]):
    try: mark_pending_signature(session, context, instance_id)
    except ConsentInstanceError as exc: raise _error(exc)


@router.post("/{instance_id}/void", response_model=ConsentInstanceResponse)
def void(instance_id: UUID, payload: ConsentInstanceVoidRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.void"))]):
    try: return void_instance(session, context, instance_id, payload, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)


@router.get("/{instance_id}/audit", response_model=list[ConsentInstanceAuditResponse])
def audit(instance_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.view_audit"))]):
    try: return list_audit(session, context, instance_id)
    except ConsentInstanceError as exc: raise _error(exc)
