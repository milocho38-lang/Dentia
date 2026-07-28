from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.clinical_document_schema import (
    ClinicalDocumentCreateRequest,
    ClinicalDocumentListResponse,
    ClinicalDocumentPreviewResponse,
    ClinicalDocumentResponse,
    ClinicalDocumentUpdateRequest,
    ClinicalDocumentVoidRequest,
)
from app.services.auth_service import AuthContext
from app.services.clinical_document_service import (
    ClinicalDocumentError,
    create_document,
    download_document_pdf,
    duplicate_document,
    finalize_document,
    get_document,
    list_documents,
    preview_document,
    update_document,
    void_document,
)


router = APIRouter(tags=["Documentos clínicos"])


def handle_document_error(exc: ClinicalDocumentError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/patients/{patient_id}/clinical-documents", response_model=ClinicalDocumentListResponse)
def list_patient_clinical_documents_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.view"))],
    tipo: str | None = None,
    estado: str | None = None,
    odontologo_id: UUID | None = None,
) -> ClinicalDocumentListResponse:
    try:
        return list_documents(
            session,
            context,
            patient_id,
            document_type=tipo,
            status=estado,
            dentist_id=odontologo_id,
        )
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.post("/api/patients/{patient_id}/clinical-documents", response_model=ClinicalDocumentResponse, status_code=201)
def create_patient_clinical_document_endpoint(
    patient_id: UUID,
    payload: ClinicalDocumentCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.create"))],
) -> ClinicalDocumentResponse:
    try:
        return create_document(session, context, patient_id, payload, get_request_metadata(request))
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.get("/api/clinical-documents/{document_id}", response_model=ClinicalDocumentResponse)
def get_clinical_document_endpoint(
    document_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.view"))],
) -> ClinicalDocumentResponse:
    try:
        return get_document(session, context, document_id)
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.patch("/api/clinical-documents/{document_id}", response_model=ClinicalDocumentResponse)
def update_clinical_document_endpoint(
    document_id: UUID,
    payload: ClinicalDocumentUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.edit_draft"))],
) -> ClinicalDocumentResponse:
    try:
        return update_document(session, context, document_id, payload, get_request_metadata(request))
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.post("/api/clinical-documents/{document_id}/preview", response_model=ClinicalDocumentPreviewResponse)
def preview_clinical_document_endpoint(
    document_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.view"))],
) -> ClinicalDocumentPreviewResponse:
    try:
        return preview_document(session, context, document_id)
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.post("/api/clinical-documents/{document_id}/finalize", response_model=ClinicalDocumentResponse)
def finalize_clinical_document_endpoint(
    document_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.finalize"))],
) -> ClinicalDocumentResponse:
    try:
        return finalize_document(session, context, document_id, get_request_metadata(request))
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.get("/api/clinical-documents/{document_id}/pdf")
def download_clinical_document_pdf_endpoint(
    document_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.download"))],
) -> Response:
    try:
        result = download_document_pdf(session, context, document_id, get_request_metadata(request))
        return Response(
            content=result.content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
        )
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.post("/api/clinical-documents/{document_id}/duplicate", response_model=ClinicalDocumentResponse, status_code=201)
def duplicate_clinical_document_endpoint(
    document_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.create"))],
) -> ClinicalDocumentResponse:
    try:
        return duplicate_document(session, context, document_id, get_request_metadata(request))
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)


@router.post("/api/clinical-documents/{document_id}/void", response_model=ClinicalDocumentResponse)
def void_clinical_document_endpoint(
    document_id: UUID,
    payload: ClinicalDocumentVoidRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical_documents.void"))],
) -> ClinicalDocumentResponse:
    try:
        return void_document(session, context, document_id, payload, get_request_metadata(request))
    except ClinicalDocumentError as exc:
        raise handle_document_error(exc)
