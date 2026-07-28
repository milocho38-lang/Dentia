from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.prescription_schema import (
    PrescriptionCreateRequest,
    PrescriptionFinalizeRequest,
    PrescriptionListResponse,
    PrescriptionPreviewResponse,
    PrescriptionResponse,
    PrescriptionUpdateRequest,
    PrescriptionVoidRequest,
)
from app.services.auth_service import AuthContext
from app.services.prescription_service import (
    PrescriptionError,
    create_prescription,
    download_prescription_pdf,
    duplicate_prescription,
    finalize_prescription,
    get_prescription,
    list_prescriptions,
    preview_prescription,
    update_prescription,
    void_prescription,
)


router = APIRouter(tags=["Recetas"])


def handle_prescription_error(exc: PrescriptionError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/patients/{patient_id}/prescriptions", response_model=PrescriptionListResponse)
def list_patient_prescriptions_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.view"))],
    estado: str | None = None,
    odontologo_id: UUID | None = None,
    medicamento: str | None = None,
) -> PrescriptionListResponse:
    try:
        return list_prescriptions(session, context, patient_id, status=estado, dentist_id=odontologo_id, medication=medicamento)
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.post("/api/patients/{patient_id}/prescriptions", response_model=PrescriptionResponse, status_code=201)
def create_patient_prescription_endpoint(
    patient_id: UUID,
    payload: PrescriptionCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.create"))],
) -> PrescriptionResponse:
    try:
        return create_prescription(session, context, patient_id, payload, get_request_metadata(request))
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.get("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription_endpoint(
    prescription_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.view"))],
) -> PrescriptionResponse:
    try:
        return get_prescription(session, context, prescription_id)
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.patch("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription_endpoint(
    prescription_id: UUID,
    payload: PrescriptionUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.edit_draft"))],
) -> PrescriptionResponse:
    try:
        return update_prescription(session, context, prescription_id, payload, get_request_metadata(request))
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.post("/api/prescriptions/{prescription_id}/preview", response_model=PrescriptionPreviewResponse)
def preview_prescription_endpoint(
    prescription_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.view"))],
) -> PrescriptionPreviewResponse:
    try:
        return preview_prescription(session, context, prescription_id)
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.post("/api/prescriptions/{prescription_id}/finalize", response_model=PrescriptionResponse)
def finalize_prescription_endpoint(
    prescription_id: UUID,
    payload: PrescriptionFinalizeRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.finalize"))],
) -> PrescriptionResponse:
    try:
        return finalize_prescription(session, context, prescription_id, payload, get_request_metadata(request))
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.get("/api/prescriptions/{prescription_id}/pdf")
def download_prescription_pdf_endpoint(
    prescription_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.download"))],
) -> Response:
    try:
        result = download_prescription_pdf(session, context, prescription_id, get_request_metadata(request))
        return Response(
            content=result.content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
        )
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.post("/api/prescriptions/{prescription_id}/duplicate", response_model=PrescriptionResponse, status_code=201)
def duplicate_prescription_endpoint(
    prescription_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.create"))],
) -> PrescriptionResponse:
    try:
        return duplicate_prescription(session, context, prescription_id, get_request_metadata(request))
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)


@router.post("/api/prescriptions/{prescription_id}/void", response_model=PrescriptionResponse)
def void_prescription_endpoint(
    prescription_id: UUID,
    payload: PrescriptionVoidRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("prescriptions.void"))],
) -> PrescriptionResponse:
    try:
        return void_prescription(session, context, prescription_id, payload, get_request_metadata(request))
    except PrescriptionError as exc:
        raise handle_prescription_error(exc)
