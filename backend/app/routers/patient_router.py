from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.patient_schema import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    PatientActionResponse,
    PatientAppointmentsResponse,
    PatientCreateRequest,
    PatientListResponse,
    PatientQuickCreateRequest,
    PatientResponse,
    PatientSummaryResponse,
    PatientUpdateRequest,
    ResponsibleCreateRequest,
    ResponsibleListResponse,
    ResponsibleResponse,
    ResponsibleUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.patient_service import (
    PatientManagementError,
    change_patient_status,
    check_duplicates,
    create_patient,
    create_quick_patient,
    create_responsible,
    delete_responsible,
    get_patient_appointments,
    get_patient_detail,
    get_patient_summary,
    list_patients,
    list_responsibles,
    update_patient,
    update_responsible,
)


router = APIRouter(prefix="/api/patients", tags=["Patients"])


def handle_patient_error(exc: PatientManagementError) -> HTTPException:
    if exc.duplicates is not None:
        return HTTPException(
            status_code=exc.status_code,
            detail={
                "message": str(exc),
                "duplicates": exc.duplicates.model_dump(mode="json"),
            },
        )
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("", response_model=PatientListResponse)
def list_patients_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
    search: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default=None, pattern="^(Activo|Inactivo)$"),
    incomplete: bool | None = None,
    minor: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PatientListResponse:
    return list_patients(
        session,
        context,
        search=search,
        status=status,
        incomplete=incomplete,
        minor=minor,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient_endpoint(
    payload: PatientCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.create"))
    ],
) -> PatientResponse:
    try:
        return create_patient(
            session, context, payload, get_request_metadata(request)
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.post(
    "/quick",
    response_model=PatientResponse,
    status_code=201,
)
def quick_patient_endpoint(
    payload: PatientQuickCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.create"))
    ],
) -> PatientResponse:
    try:
        return create_quick_patient(
            session, context, payload, get_request_metadata(request)
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.post("/check-duplicates", response_model=DuplicateCheckResponse)
def check_duplicates_endpoint(
    payload: DuplicateCheckRequest,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
) -> DuplicateCheckResponse:
    return check_duplicates(session, context, payload)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
) -> PatientResponse:
    try:
        return get_patient_detail(session, context, patient_id)
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient_endpoint(
    patient_id: UUID,
    payload: PatientUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.update"))
    ],
) -> PatientResponse:
    try:
        return update_patient(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.post("/{patient_id}/deactivate", response_model=PatientActionResponse)
def deactivate_patient_endpoint(
    patient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.deactivate"))
    ],
) -> PatientActionResponse:
    try:
        return change_patient_status(
            session,
            context,
            patient_id,
            active=False,
            metadata=get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.post("/{patient_id}/reactivate", response_model=PatientActionResponse)
def reactivate_patient_endpoint(
    patient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.deactivate"))
    ],
) -> PatientActionResponse:
    try:
        return change_patient_status(
            session,
            context,
            patient_id,
            active=True,
            metadata=get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.get(
    "/{patient_id}/appointments",
    response_model=PatientAppointmentsResponse,
)
def patient_appointments_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PatientAppointmentsResponse:
    try:
        return get_patient_appointments(
            session,
            context,
            patient_id,
            page=page,
            page_size=page_size,
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.get("/{patient_id}/summary", response_model=PatientSummaryResponse)
def patient_summary_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
) -> PatientSummaryResponse:
    try:
        return get_patient_summary(session, context, patient_id)
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.get(
    "/{patient_id}/responsibles",
    response_model=ResponsibleListResponse,
)
def list_responsibles_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.view"))
    ],
) -> ResponsibleListResponse:
    try:
        return list_responsibles(session, context, patient_id)
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.post(
    "/{patient_id}/responsibles",
    response_model=ResponsibleResponse,
    status_code=201,
)
def create_responsible_endpoint(
    patient_id: UUID,
    payload: ResponsibleCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.update"))
    ],
) -> ResponsibleResponse:
    try:
        return create_responsible(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.patch(
    "/{patient_id}/responsibles/{responsible_id}",
    response_model=ResponsibleResponse,
)
def update_responsible_endpoint(
    patient_id: UUID,
    responsible_id: UUID,
    payload: ResponsibleUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.update"))
    ],
) -> ResponsibleResponse:
    try:
        return update_responsible(
            session,
            context,
            patient_id,
            responsible_id,
            payload,
            get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)


@router.delete(
    "/{patient_id}/responsibles/{responsible_id}",
    response_model=ResponsibleListResponse,
)
def delete_responsible_endpoint(
    patient_id: UUID,
    responsible_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("patients.update"))
    ],
) -> ResponsibleListResponse:
    try:
        return delete_responsible(
            session,
            context,
            patient_id,
            responsible_id,
            get_request_metadata(request),
        )
    except PatientManagementError as exc:
        raise handle_patient_error(exc)
