from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.orthodontic_record_schema import (
    OrthodonticRecordActionResponse,
    OrthodonticRecordFinalizeRequest,
    OrthodonticRecordNewVersionRequest,
    OrthodonticRecordResponse,
    OrthodonticRecordUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.orthodontic_record_service import (
    create_orthodontic_record,
    create_orthodontic_record_version,
    finalize_orthodontic_record_version,
    get_orthodontic_record,
    update_orthodontic_record_version,
)
from app.services.orthodontics_entitlement_service import OrthodonticsError


router = APIRouter(tags=["Orthodontics clinical record"])


def _handle(exc: OrthodonticsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get(
    "/api/orthodontics/cases/{case_id}/record",
    response_model=OrthodonticRecordResponse,
)
def get_record_endpoint(
    case_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.view"))],
    version_id: UUID | None = None,
) -> OrthodonticRecordResponse:
    try:
        return get_orthodontic_record(
            session, context, case_id, version_id=version_id
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/cases/{case_id}/record",
    response_model=OrthodonticRecordActionResponse,
    status_code=201,
)
def create_record_endpoint(
    case_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticRecordActionResponse:
    try:
        return create_orthodontic_record(
            session, context, case_id, get_request_metadata(request)
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.patch(
    "/api/orthodontics/cases/{case_id}/record/versions/{version_id}",
    response_model=OrthodonticRecordActionResponse,
)
def update_record_version_endpoint(
    case_id: UUID,
    version_id: UUID,
    payload: OrthodonticRecordUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticRecordActionResponse:
    try:
        return update_orthodontic_record_version(
            session,
            context,
            case_id,
            version_id,
            payload,
            get_request_metadata(request),
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/cases/{case_id}/record/versions/{version_id}/finalize",
    response_model=OrthodonticRecordActionResponse,
)
def finalize_record_version_endpoint(
    case_id: UUID,
    version_id: UUID,
    payload: OrthodonticRecordFinalizeRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.sign"))
    ],
) -> OrthodonticRecordActionResponse:
    try:
        return finalize_orthodontic_record_version(
            session,
            context,
            case_id,
            version_id,
            payload,
            get_request_metadata(request),
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/cases/{case_id}/record/versions",
    response_model=OrthodonticRecordActionResponse,
    status_code=201,
)
def create_record_version_endpoint(
    case_id: UUID,
    payload: OrthodonticRecordNewVersionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticRecordActionResponse:
    try:
        return create_orthodontic_record_version(
            session,
            context,
            case_id,
            payload,
            get_request_metadata(request),
        )
    except OrthodonticsError as exc:
        raise _handle(exc)
