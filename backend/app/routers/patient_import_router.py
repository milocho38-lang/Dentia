from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.patient_import_schema import (
    PatientImportConfirmResponse,
    PatientImportPreviewResponse,
    PatientImportSourceCreateRequest,
    PatientImportSourceListResponse,
    PatientImportSourceResponse,
)
from app.services.auth_service import AuthContext
from app.services.dentalink_xlsx_parser import DentalinkWorkbookError, MAX_FILE_BYTES
from app.services.patient_import_service import (
    PatientImportError,
    confirm_dentalink_import,
    create_import_source,
    list_import_sources,
    preview_dentalink_import,
)


router = APIRouter(prefix="/api/patient-imports/dentalink", tags=["Patient imports"])


async def _read_xlsx(file: UploadFile) -> bytes:
    filename = (file.filename or "").casefold()
    if not filename.endswith(".xlsx"):
        raise HTTPException(415, "Selecciona un archivo .xlsx sin macros.")
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, "El archivo supera 8 MB.")
    if not content:
        raise HTTPException(400, "El archivo está vacío.")
    return content


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, PatientImportError):
        return HTTPException(exc.status_code, str(exc))
    return HTTPException(422, str(exc))


@router.get("/sources", response_model=PatientImportSourceListResponse)
def list_sources_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("patients.import"))],
) -> PatientImportSourceListResponse:
    return list_import_sources(session, context)


@router.post("/sources", response_model=PatientImportSourceResponse, status_code=201)
def create_source_endpoint(
    payload: PatientImportSourceCreateRequest,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("patients.import"))],
) -> PatientImportSourceResponse:
    return create_import_source(session, context, label=payload.label)


@router.post("/preview", response_model=PatientImportPreviewResponse)
async def preview_endpoint(
    file: Annotated[UploadFile, File(...)],
    source_id: Annotated[UUID, Form()],
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("patients.import"))],
) -> PatientImportPreviewResponse:
    try:
        return preview_dentalink_import(
            session,
            context,
            source_id=source_id,
            content=await _read_xlsx(file),
        )
    except (DentalinkWorkbookError, PatientImportError) as exc:
        raise _handle(exc)


@router.post("/confirm", response_model=PatientImportConfirmResponse)
async def confirm_endpoint(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    source_id: Annotated[UUID, Form()],
    preview_token: Annotated[str, Form(min_length=20)],
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("patients.import"))],
) -> PatientImportConfirmResponse:
    try:
        return confirm_dentalink_import(
            session,
            context,
            get_request_metadata(request),
            source_id=source_id,
            preview_token=preview_token,
            content=await _read_xlsx(file),
        )
    except (DentalinkWorkbookError, PatientImportError) as exc:
        raise _handle(exc)
