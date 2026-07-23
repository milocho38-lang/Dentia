from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.odontogram_schema import (
    OdontogramCatalogItemResponse,
    OdontogramCreateRequest,
    OdontogramCurrentStateResponse,
    OdontogramEnvelope,
    OdontogramEventConfirmRequest,
    OdontogramEventCorrectRequest,
    OdontogramEventCreateRequest,
    OdontogramEventListResponse,
    OdontogramEventResponse,
    OdontogramEventUpdateRequest,
    OdontogramResponse,
    OdontogramToothHistoryResponse,
)
from app.schemas.treatment_schema import (
    OdontogramLinkedProcedureListResponse,
    OdontogramPlannedProcedureCreateRequest,
    OdontogramPlannedProcedureCreateResponse,
)
from app.services.auth_service import AuthContext
from app.services.odontogram_service import (
    OdontogramError,
    confirm_event,
    correct_event,
    create_event,
    create_odontogram,
    current_state,
    get_event,
    get_odontogram,
    list_catalog,
    list_events,
    tooth_history,
    update_event_draft,
)
from app.services.treatment_service import (
    TreatmentError,
    create_planned_procedure_from_odontogram_event,
    list_odontogram_planned_procedure_links,
)


router = APIRouter(prefix="/api/patients", tags=["Odontogram"])
odontogram_router = APIRouter(prefix="/api/odontogram", tags=["Odontogram"])


def handle_odontogram_error(exc: OdontogramError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def handle_treatment_error(exc: TreatmentError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{patient_id}/odontogram", response_model=OdontogramEnvelope)
def get_patient_odontogram_endpoint(
    patient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
) -> OdontogramEnvelope:
    try:
        return get_odontogram(
            session,
            context,
            patient_id,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.post(
    "/{patient_id}/odontogram",
    response_model=OdontogramResponse,
    status_code=201,
)
def create_patient_odontogram_endpoint(
    patient_id: UUID,
    payload: OdontogramCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.create"))],
) -> OdontogramResponse:
    try:
        return create_odontogram(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.get(
    "/{patient_id}/odontogram/current",
    response_model=OdontogramCurrentStateResponse,
)
def get_patient_odontogram_current_endpoint(
    patient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
) -> OdontogramCurrentStateResponse:
    try:
        return current_state(
            session,
            context,
            patient_id,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.get(
    "/{patient_id}/odontogram/events",
    response_model=OdontogramEventListResponse,
)
def list_patient_odontogram_events_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
    status: str | None = None,
) -> OdontogramEventListResponse:
    try:
        return list_events(session, context, patient_id, status=status)
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.post(
    "/{patient_id}/odontogram/events",
    response_model=OdontogramEventResponse,
    status_code=201,
)
def create_patient_odontogram_event_endpoint(
    patient_id: UUID,
    payload: OdontogramEventCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("odontogram.update_draft"))
    ],
) -> OdontogramEventResponse:
    try:
        return create_event(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.get(
    "/{patient_id}/odontogram/teeth/{tooth_code}/history",
    response_model=OdontogramToothHistoryResponse,
)
def patient_odontogram_tooth_history_endpoint(
    patient_id: UUID,
    tooth_code: str,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.history"))],
    status: str | None = None,
    surface: str | None = None,
    event_type: str | None = None,
) -> OdontogramToothHistoryResponse:
    try:
        return tooth_history(
            session,
            context,
            patient_id,
            tooth_code,
            get_request_metadata(request),
            status=status,
            surface=surface,
            event_type=event_type,
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@router.get(
    "/{patient_id}/odontogram/planned-procedure-links",
    response_model=OdontogramLinkedProcedureListResponse,
)
def patient_odontogram_planned_procedure_links_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
    tooth_code: str | None = None,
) -> OdontogramLinkedProcedureListResponse:
    try:
        return list_odontogram_planned_procedure_links(
            session,
            context,
            patient_id,
            tooth_code=tooth_code,
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@odontogram_router.get(
    "/catalog",
    response_model=list[OdontogramCatalogItemResponse],
)
def odontogram_catalog_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
) -> list[OdontogramCatalogItemResponse]:
    try:
        return list_catalog(session, context)
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@odontogram_router.get(
    "/events/{event_id}",
    response_model=OdontogramEventResponse,
)
def get_odontogram_event_endpoint(
    event_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
) -> OdontogramEventResponse:
    try:
        return get_event(session, context, event_id, get_request_metadata(request))
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@odontogram_router.patch(
    "/events/{event_id}/draft",
    response_model=OdontogramEventResponse,
)
def update_odontogram_event_draft_endpoint(
    event_id: UUID,
    payload: OdontogramEventUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("odontogram.update_draft"))
    ],
) -> OdontogramEventResponse:
    try:
        return update_event_draft(
            session,
            context,
            event_id,
            payload,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@odontogram_router.post(
    "/events/{event_id}/confirm",
    response_model=OdontogramEventResponse,
)
def confirm_odontogram_event_endpoint(
    event_id: UUID,
    payload: OdontogramEventConfirmRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.confirm"))],
) -> OdontogramEventResponse:
    try:
        return confirm_event(
            session,
            context,
            event_id,
            payload,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@odontogram_router.post(
    "/events/{event_id}/correct",
    response_model=OdontogramEventResponse,
)
def correct_odontogram_event_endpoint(
    event_id: UUID,
    payload: OdontogramEventCorrectRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.correct"))],
) -> OdontogramEventResponse:
    try:
        return correct_event(
            session,
            context,
            event_id,
            payload,
            get_request_metadata(request),
        )
    except OdontogramError as exc:
        raise handle_odontogram_error(exc)


@odontogram_router.post(
    "/events/{event_id}/planned-procedures",
    response_model=OdontogramPlannedProcedureCreateResponse,
)
def create_planned_procedure_from_odontogram_event_endpoint(
    event_id: UUID,
    payload: OdontogramPlannedProcedureCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("odontogram.view"))],
) -> OdontogramPlannedProcedureCreateResponse:
    try:
        return create_planned_procedure_from_odontogram_event(
            session,
            context,
            event_id,
            payload,
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)
