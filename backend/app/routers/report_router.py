from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.report_schema import (
    ActionItemsResponse,
    AppointmentReportsResponse,
    ExecutiveSummaryResponse,
    FinanceReportsResponse,
    FollowupReportsResponse,
    PatientReportsResponse,
    TreatmentReportsResponse,
)
from app.services.auth_service import AuthContext
from app.services.report_service import ReportError, executive_summary


router = APIRouter(tags=["Reports"])


def handle_report_error(exc: ReportError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/reports/executive-summary", response_model=ExecutiveSummaryResponse)
def executive_summary_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
    page_size: int = Query(default=10, ge=1, le=50),
) -> ExecutiveSummaryResponse:
    try:
        return executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            page_size=page_size,
        )
    except ReportError as exc:
        raise handle_report_error(exc)


@router.get("/api/reports/appointments", response_model=AppointmentReportsResponse)
def appointments_report_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
) -> AppointmentReportsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    if summary.appointments is None:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportes operativos.")
    return summary.appointments


@router.get("/api/reports/patients", response_model=PatientReportsResponse)
def patients_report_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
) -> PatientReportsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    if summary.patients is None:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportes operativos.")
    return summary.patients


@router.get("/api/reports/treatments", response_model=TreatmentReportsResponse)
def treatments_report_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
) -> TreatmentReportsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    if summary.treatments is None:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportes operativos.")
    return summary.treatments


@router.get("/api/reports/finance", response_model=FinanceReportsResponse)
def finance_report_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
) -> FinanceReportsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    if summary.finance is None:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportes financieros.")
    return summary.finance


@router.get("/api/reports/followups", response_model=FollowupReportsResponse)
def followups_report_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
) -> FollowupReportsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    if summary.followups is None:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportes operativos.")
    return summary.followups


@router.get("/api/reports/action-items", response_model=ActionItemsResponse)
def action_items_endpoint(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
    preset: str | None = Query(default="month_current"),
    date_from: date | None = None,
    date_to: date | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
    page_size: int = Query(default=10, ge=1, le=50),
) -> ActionItemsResponse:
    try:
        summary = executive_summary(
            session,
            context,
            get_request_metadata(request),
            preset=preset,
            date_from=date_from,
            date_to=date_to,
            site_id=site_id,
            dentist_id=dentist_id,
            page_size=page_size,
            audit=False,
        )
    except ReportError as exc:
        raise handle_report_error(exc)
    return summary.action_items or ActionItemsResponse()
