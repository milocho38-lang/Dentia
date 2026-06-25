from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.followup_schema import (
    CompleteAppointmentRequest, CompleteAppointmentResponse,
    FollowupActionResponse, FollowupAppointmentRequest,
    FollowupCloseRequest, FollowupContactRequest,
    FollowupDashboardResponse, FollowupListResponse, FollowupResponse,
    WhatsAppLinkResponse,
)
from app.services.auth_service import AuthContext
from app.services.followup_service import (
    FollowupError, close_followup, complete_appointment, dashboard,
    get_followup, get_followup_by_patient_appointment, list_followups,
    register_contact, reopen_followup, schedule_followup_appointment,
    whatsapp_link,
)


router = APIRouter(tags=["Followups"])


def handle(exc: FollowupError):
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/api/appointments/{appointment_id}/complete", response_model=CompleteAppointmentResponse)
def complete_endpoint(
    appointment_id: UUID, payload: CompleteAppointmentRequest, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("appointments.complete"))],
):
    try:
        return complete_appointment(session, context, appointment_id, payload, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)


@router.get("/api/followups", response_model=FollowupListResponse)
def list_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.view"))],
    classification: str | None = None, status: str | None = None,
    search: str | None = Query(default=None, max_length=200),
    site_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    try:
        return list_followups(
            session, context, classification, status, search, site_id,
            page, page_size
        )
    except FollowupError as exc:
        raise handle(exc)


@router.get("/api/followups/dashboard", response_model=FollowupDashboardResponse)
def dashboard_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.view"))],
    site_id: UUID | None = None,
):
    try:
        return dashboard(session, context, site_id)
    except FollowupError as exc:
        raise handle(exc)


@router.get("/api/followups/{followup_id}", response_model=FollowupResponse)
def detail_endpoint(
    followup_id: UUID, session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.view"))],
):
    try:
        return get_followup(session, context, followup_id)
    except FollowupError as exc:
        raise handle(exc)


@router.get(
    "/api/patients/{patient_id}/appointments/{appointment_id}/followup",
    response_model=FollowupResponse,
)
def patient_appointment_followup_endpoint(
    patient_id: UUID,
    appointment_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.view"))],
):
    try:
        return get_followup_by_patient_appointment(
            session, context, patient_id, appointment_id
        )
    except FollowupError as exc:
        raise handle(exc)


@router.post("/api/followups/{followup_id}/contact", response_model=FollowupActionResponse)
def contact_endpoint(
    followup_id: UUID, payload: FollowupContactRequest, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.contact"))],
):
    try:
        return register_contact(session, context, followup_id, payload, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)


@router.post("/api/followups/{followup_id}/whatsapp-link", response_model=WhatsAppLinkResponse)
def whatsapp_endpoint(
    followup_id: UUID, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.contact"))],
):
    try:
        return whatsapp_link(session, context, followup_id, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)


@router.post("/api/followups/{followup_id}/appointments", response_model=FollowupActionResponse)
def appointment_endpoint(
    followup_id: UUID, payload: FollowupAppointmentRequest, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.manage"))],
):
    try:
        return schedule_followup_appointment(session, context, followup_id, payload, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)


@router.post("/api/followups/{followup_id}/close", response_model=FollowupActionResponse)
def close_endpoint(
    followup_id: UUID, payload: FollowupCloseRequest, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.manage"))],
):
    try:
        return close_followup(session, context, followup_id, payload, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)


@router.post("/api/followups/{followup_id}/reopen", response_model=FollowupActionResponse)
def reopen_endpoint(
    followup_id: UUID, request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("followups.manage"))],
):
    try:
        return reopen_followup(session, context, followup_id, get_request_metadata(request))
    except FollowupError as exc:
        raise handle(exc)
