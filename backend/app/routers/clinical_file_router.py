from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.clinical_file_schema import ClinicalFileDeactivateRequest, ClinicalFileListResponse, ClinicalFileResponse
from app.services.auth_service import AuthContext
from app.services.clinical_file_service import ClinicalFileError, deactivate_file, download_file, list_files, upload_file

router = APIRouter(tags=["Archivos clínicos"])


def _error(exc: ClinicalFileError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/patients/{patient_id}/clinical-files", response_model=ClinicalFileListResponse)
def list_endpoint(patient_id: UUID, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("clinical_files.view"))], tipo: str | None = None, categoria: str | None = None):
    try:
        return list_files(session, context, patient_id, tipo, categoria)
    except ClinicalFileError as exc:
        raise _error(exc)


@router.post("/api/patients/{patient_id}/clinical-files", response_model=ClinicalFileResponse, status_code=201)
async def upload_endpoint(patient_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("clinical_files.create"))], archivo: Annotated[UploadFile, File()], tipo: Annotated[str, Form()], categoria: Annotated[str, Form()] = "GENERAL", descripcion: Annotated[str | None, Form()] = None, tratamiento_id: Annotated[UUID | None, Form()] = None, cita_id: Annotated[UUID | None, Form()] = None):
    try:
        return await upload_file(session, context, patient_id, archivo, tipo, categoria, descripcion, tratamiento_id, cita_id, get_request_metadata(request))
    except ClinicalFileError as exc:
        raise _error(exc)


@router.get("/api/clinical-files/{file_id}/download")
def download_endpoint(file_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("clinical_files.view"))]):
    try:
        path, item = download_file(session, context, file_id, get_request_metadata(request))
        return FileResponse(path, media_type=item.mime_type, filename=item.original_name, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
    except ClinicalFileError as exc:
        raise _error(exc)


@router.post("/api/clinical-files/{file_id}/deactivate", status_code=204)
def deactivate_endpoint(file_id: UUID, payload: ClinicalFileDeactivateRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("clinical_files.manage"))]):
    try:
        deactivate_file(session, context, file_id, payload.reason, get_request_metadata(request))
        return Response(status_code=204)
    except ClinicalFileError as exc:
        raise _error(exc)
