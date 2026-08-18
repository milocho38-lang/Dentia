from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
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
    ConsentPaperPacketResponse,
    ConsentPaperReorderRequest,
    ConsentPaperSignedRequest,
    ConsentPaperVerificationRequest,
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
from app.services.consent_paper_service import (
    MAX_FILE_BYTES,
    ConsentPaperError,
    document_bytes,
    finalize as finalize_paper,
    get_packet as get_paper_packet,
    page_preview,
    prepare_packet,
    record_signed,
    remove_page,
    reorder_pages,
    upload_pages,
)


router = APIRouter(prefix="/api/consent-instances", tags=["Instancias de consentimiento"])


def _error(exc: ConsentInstanceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def _paper_error(exc: ConsentPaperError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def _creation_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No fue posible crear el consentimiento. Intenta nuevamente.",
    )


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
    except Exception as exc: raise _creation_error() from exc


@router.post("/batch", response_model=list[ConsentInstanceResponse], status_code=201)
def batch(payload: ConsentInstanceBatchCreateRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.instance.create"))]):
    try: return create_batch(session, context, payload, get_request_metadata(request))
    except ConsentInstanceError as exc: raise _error(exc)
    except Exception as exc: raise _creation_error() from exc


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


@router.get("/{instance_id}/paper", response_model=ConsentPaperPacketResponse)
def paper_detail(instance_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.read"))]):
    try: return get_paper_packet(session, context, instance_id)
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.post("/{instance_id}/paper", response_model=ConsentPaperPacketResponse)
def paper_prepare(instance_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.prepare"))]):
    try: return prepare_packet(session, context, instance_id, get_request_metadata(request))
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.get("/{instance_id}/paper/print-document")
def paper_print_document(instance_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.read"))]):
    try:
        raw, filename = document_bytes(session, context, instance_id, final=False, metadata=get_request_metadata(request))
        return Response(raw, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{filename}"', "Cache-Control": "no-store"})
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.post("/{instance_id}/paper/record-signed", response_model=ConsentPaperPacketResponse)
def paper_record_signed(instance_id: UUID, payload: ConsentPaperSignedRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.record_signed"))]):
    try: return record_signed(session, context, instance_id, get_request_metadata(request), payload.confirmed)
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.post("/{instance_id}/paper/pages", response_model=ConsentPaperPacketResponse)
async def paper_upload(instance_id: UUID, request: Request, file: Annotated[UploadFile, File(...)], session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.upload"))]):
    try:
        raw = await file.read(MAX_FILE_BYTES + 1)
        return upload_pages(session, context, instance_id, get_request_metadata(request), raw)
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)
    finally: await file.close()


@router.get("/{instance_id}/paper/pages/{page_id}/preview")
def paper_page_preview(instance_id: UUID, page_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.read"))]):
    try: return Response(page_preview(session, context, instance_id, page_id), media_type="image/png", headers={"Cache-Control":"no-store"})
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.delete("/{instance_id}/paper/pages/{page_id}", response_model=ConsentPaperPacketResponse)
def paper_remove(instance_id: UUID, page_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.upload"))]):
    try: return remove_page(session, context, instance_id, page_id, get_request_metadata(request))
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.patch("/{instance_id}/paper/pages/order", response_model=ConsentPaperPacketResponse)
def paper_reorder(instance_id: UUID, payload: ConsentPaperReorderRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.upload"))]):
    try: return reorder_pages(session, context, instance_id, payload.page_ids, get_request_metadata(request))
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.post("/{instance_id}/paper/finalize", response_model=ConsentPaperPacketResponse)
def paper_finalize(instance_id: UUID, payload: ConsentPaperVerificationRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.finalize"))]):
    try: return finalize_paper(session, context, instance_id, payload, get_request_metadata(request))
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)


@router.get("/{instance_id}/paper/final-document")
def paper_final_document(instance_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_consent_permission("consent.paper.read"))], download: bool = False):
    try:
        raw, filename = document_bytes(session, context, instance_id, final=True, metadata=get_request_metadata(request), download=download)
        disposition = "attachment" if download else "inline"
        return Response(raw, media_type="application/pdf", headers={"Content-Disposition": f'{disposition}; filename="{filename}"', "Cache-Control":"no-store"})
    except (ConsentPaperError, ConsentInstanceError) as exc: raise _paper_error(exc) if isinstance(exc, ConsentPaperError) else _error(exc)
