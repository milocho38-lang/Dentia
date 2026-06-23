from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.agenda_schema import (
    AgendaEventsResponse,
    AgendaOptionsResponse,
    AppointmentCancelRequest,
    AppointmentConfirmRequest,
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentRescheduleRequest,
    AppointmentUpdateRequest,
)
from app.services.agenda_service import (
    AgendaError,
    cancel_appointment,
    confirm_appointment,
    create_appointment,
    get_events,
    get_options,
    reschedule_appointment,
    update_appointment,
)
from app.services.auth_service import AuthContext


router = APIRouter(tags=["Agenda"])


def handle_agenda_error(exc: AgendaError) -> HTTPException:
    if exc.conflicts is not None:
        return HTTPException(
            status_code=exc.status_code,
            detail={
                "message": str(exc),
                "conflicts": [
                    conflict.model_dump(mode="json")
                    for conflict in exc.conflicts
                ],
                "can_overbook": exc.can_overbook,
            },
        )
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/agenda/events", response_model=AgendaEventsResponse)
def agenda_events_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.view"))
    ],
    starts_at: datetime = Query(),
    ends_at: datetime = Query(),
    dentist_id: UUID | None = None,
    site_id: UUID | None = None,
) -> AgendaEventsResponse:
    try:
        return get_events(
            session,
            context,
            starts_at=starts_at,
            ends_at=ends_at,
            dentist_id=dentist_id,
            site_id=site_id,
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)


@router.get("/api/agenda/options", response_model=AgendaOptionsResponse)
def agenda_options_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.view"))
    ],
) -> AgendaOptionsResponse:
    return get_options(session, context)


@router.post(
    "/api/appointments",
    response_model=AppointmentResponse,
    status_code=201,
)
def create_appointment_endpoint(
    payload: AppointmentCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.create"))
    ],
) -> AppointmentResponse:
    try:
        return create_appointment(
            session, context, payload, get_request_metadata(request)
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)


@router.patch(
    "/api/appointments/{appointment_id}",
    response_model=AppointmentResponse,
)
def update_appointment_endpoint(
    appointment_id: UUID,
    payload: AppointmentUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.update"))
    ],
) -> AppointmentResponse:
    try:
        return update_appointment(
            session,
            context,
            appointment_id,
            payload,
            get_request_metadata(request),
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)


@router.post(
    "/api/appointments/{appointment_id}/confirm",
    response_model=AppointmentResponse,
)
def confirm_appointment_endpoint(
    appointment_id: UUID,
    payload: AppointmentConfirmRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.update"))
    ],
) -> AppointmentResponse:
    try:
        return confirm_appointment(
            session,
            context,
            appointment_id,
            payload.method,
            get_request_metadata(request),
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)


@router.post(
    "/api/appointments/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment_endpoint(
    appointment_id: UUID,
    payload: AppointmentCancelRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.cancel"))
    ],
) -> AppointmentResponse:
    try:
        return cancel_appointment(
            session,
            context,
            appointment_id,
            payload.reason,
            get_request_metadata(request),
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)


@router.post(
    "/api/appointments/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
)
def reschedule_appointment_endpoint(
    appointment_id: UUID,
    payload: AppointmentRescheduleRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("appointments.update"))
    ],
) -> AppointmentResponse:
    try:
        return reschedule_appointment(
            session,
            context,
            appointment_id,
            payload,
            get_request_metadata(request),
        )
    except AgendaError as exc:
        raise handle_agenda_error(exc)
