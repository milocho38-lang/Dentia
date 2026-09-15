from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.orthodontic_case_schema import (
    OrthodonticCaseActionResponse,
    OrthodonticCaseCreateRequest,
    OrthodonticCaseTransitionRequest,
    OrthodonticCaseUpdateRequest,
    OrthodonticPatientWorkspaceResponse,
    OrthodonticResponsibleChangeRequest,
    OrthodonticSummaryResponse,
)
from app.services.auth_service import AuthContext
from app.services.orthodontics_entitlement_service import OrthodonticsError
from app.services.orthodontic_case_service import (
    activate_orthodontic_case,
    change_responsible_orthodontist,
    complete_orthodontic_case,
    create_orthodontic_case,
    discontinue_orthodontic_case,
    get_orthodontic_case,
    get_patient_orthodontics,
    resume_orthodontic_case,
    suspend_orthodontic_case,
    update_orthodontic_case,
)


router = APIRouter(tags=["Orthodontics"])


def _handle(exc: OrthodonticsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get(
    "/api/patients/{patient_id}/orthodontics",
    response_model=OrthodonticPatientWorkspaceResponse,
)
def patient_orthodontics_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.view"))],
) -> OrthodonticPatientWorkspaceResponse:
    try:
        return get_patient_orthodontics(session, context, patient_id)
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/api/patients/{patient_id}/orthodontics/cases",
    response_model=OrthodonticCaseActionResponse,
    status_code=201,
)
def create_case_endpoint(
    patient_id: UUID,
    payload: OrthodonticCaseCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    try:
        return create_orthodontic_case(
            session, context, patient_id, payload, get_request_metadata(request)
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.get(
    "/api/orthodontics/cases/{case_id}",
    response_model=OrthodonticSummaryResponse,
)
def case_detail_endpoint(
    case_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.view"))],
) -> OrthodonticSummaryResponse:
    try:
        return get_orthodontic_case(session, context, case_id)
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.patch(
    "/api/orthodontics/cases/{case_id}",
    response_model=OrthodonticCaseActionResponse,
)
def update_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    try:
        return update_orthodontic_case(
            session, context, case_id, payload, get_request_metadata(request)
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


def _transition(
    action: Callable[..., OrthodonticCaseActionResponse],
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Session,
    context: AuthContext,
) -> OrthodonticCaseActionResponse:
    try:
        return action(
            session, context, case_id, payload, get_request_metadata(request)
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/cases/{case_id}/activate",
    response_model=OrthodonticCaseActionResponse,
)
def activate_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    return _transition(activate_orthodontic_case, case_id, payload, request, session, context)


@router.post(
    "/api/orthodontics/cases/{case_id}/complete",
    response_model=OrthodonticCaseActionResponse,
)
def complete_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    return _transition(complete_orthodontic_case, case_id, payload, request, session, context)


@router.post(
    "/api/orthodontics/cases/{case_id}/suspend",
    response_model=OrthodonticCaseActionResponse,
)
def suspend_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    return _transition(suspend_orthodontic_case, case_id, payload, request, session, context)


@router.post(
    "/api/orthodontics/cases/{case_id}/resume",
    response_model=OrthodonticCaseActionResponse,
)
def resume_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    return _transition(resume_orthodontic_case, case_id, payload, request, session, context)


@router.post(
    "/api/orthodontics/cases/{case_id}/discontinue",
    response_model=OrthodonticCaseActionResponse,
)
def discontinue_case_endpoint(
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    return _transition(discontinue_orthodontic_case, case_id, payload, request, session, context)


@router.post(
    "/api/orthodontics/cases/{case_id}/change-responsible",
    response_model=OrthodonticCaseActionResponse,
)
def change_responsible_endpoint(
    case_id: UUID,
    payload: OrthodonticResponsibleChangeRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.update"))],
) -> OrthodonticCaseActionResponse:
    try:
        return change_responsible_orthodontist(
            session, context, case_id, payload, get_request_metadata(request)
        )
    except OrthodonticsError as exc:
        raise _handle(exc)
