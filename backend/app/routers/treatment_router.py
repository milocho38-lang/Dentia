from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.treatment_schema import (
    BudgetCreateRequest,
    BudgetListResponse,
    BudgetResponse,
    FinanceBreakdownResponse,
    FinanceDashboardResponse,
    LinkProcedureAppointmentRequest,
    PatientBalancesResponse,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
    PaymentReverseRequest,
    ProcedureCatalogCreateRequest,
    ProcedureCatalogItemResponse,
    ProcedureCatalogListResponse,
    ProcedureCatalogUpdateRequest,
    ProcedureCreateRequest,
    ProcedureResponse,
    ProcedureUpdateRequest,
    StatusReasonRequest,
    TreatmentCreateRequest,
    TreatmentListResponse,
    TreatmentResponse,
    TreatmentUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.treatment_service import (
    TreatmentError,
    cancel_procedure,
    change_procedure_catalog_status,
    change_budget_status,
    change_treatment_status,
    create_budget,
    create_payment,
    create_procedure,
    create_procedure_catalog_item,
    create_treatment,
    delete_procedure,
    finance_by_dentist,
    finance_by_procedure,
    finance_by_site,
    finance_dashboard,
    generate_budget_pdf,
    generate_payment_receipt_pdf,
    get_budget,
    get_payment,
    get_treatment,
    link_appointment_treatment_procedure,
    link_procedure_appointment,
    list_budgets,
    list_payments,
    list_procedure_catalog,
    list_procedures,
    list_treatments,
    mark_procedure_done,
    patient_balances,
    reverse_payment,
    update_budget,
    update_procedure,
    update_procedure_catalog_item,
    update_treatment,
)


router = APIRouter(tags=["Tratamientos y finanzas"])


def handle_treatment_error(exc: TreatmentError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/procedure-catalog", response_model=ProcedureCatalogListResponse)
def list_procedure_catalog_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("procedure_catalog.view"))],
    busqueda: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    categoria: str | None = Query(default=None),
) -> ProcedureCatalogListResponse:
    try:
        return list_procedure_catalog(
            session,
            context,
            search=busqueda,
            active=activo,
            category=categoria,
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/procedure-catalog", response_model=ProcedureCatalogItemResponse, status_code=201)
def create_procedure_catalog_endpoint(
    payload: ProcedureCatalogCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("procedure_catalog.manage"))],
) -> ProcedureCatalogItemResponse:
    try:
        return create_procedure_catalog_item(
            session,
            context,
            payload,
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.patch("/api/procedure-catalog/{item_id}", response_model=ProcedureCatalogItemResponse)
def update_procedure_catalog_endpoint(
    item_id: UUID,
    payload: ProcedureCatalogUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("procedure_catalog.manage"))],
) -> ProcedureCatalogItemResponse:
    try:
        return update_procedure_catalog_item(
            session,
            context,
            item_id,
            payload,
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/procedure-catalog/{item_id}/activate", response_model=ProcedureCatalogItemResponse)
def activate_procedure_catalog_endpoint(
    item_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("procedure_catalog.manage"))],
) -> ProcedureCatalogItemResponse:
    try:
        return change_procedure_catalog_status(
            session,
            context,
            item_id,
            True,
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/procedure-catalog/{item_id}/deactivate", response_model=ProcedureCatalogItemResponse)
def deactivate_procedure_catalog_endpoint(
    item_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("procedure_catalog.manage"))],
) -> ProcedureCatalogItemResponse:
    try:
        return change_procedure_catalog_status(
            session,
            context,
            item_id,
            False,
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/treatments", response_model=TreatmentListResponse)
def list_treatments_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.view"))],
    patient_id: UUID | None = None,
    estado: str | None = Query(default=None),
    sede_id: UUID | None = Query(default=None),
    odontologo_id: UUID | None = Query(default=None),
    con_saldo: bool | None = Query(default=None),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
) -> TreatmentListResponse:
    try:
        return list_treatments(
            session,
            context,
            patient_id=patient_id,
            status=estado,
            site_id=sede_id,
            dentist_id=odontologo_id,
            has_balance=con_saldo,
            date_from=fecha_desde,
            date_to=fecha_hasta,
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments", response_model=TreatmentResponse, status_code=201)
def create_treatment_endpoint(
    payload: TreatmentCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.create"))],
) -> TreatmentResponse:
    try:
        return create_treatment(session, context, payload, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/treatments/{treatment_id}", response_model=TreatmentResponse)
def get_treatment_endpoint(
    treatment_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.view"))],
) -> TreatmentResponse:
    try:
        return get_treatment(session, context, treatment_id)
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.patch("/api/treatments/{treatment_id}", response_model=TreatmentResponse)
def update_treatment_endpoint(
    treatment_id: UUID,
    payload: TreatmentUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> TreatmentResponse:
    try:
        return update_treatment(
            session, context, treatment_id, payload, get_request_metadata(request)
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/approve", response_model=TreatmentResponse)
def approve_treatment_endpoint(
    treatment_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> TreatmentResponse:
    try:
        return change_treatment_status(
            session,
            context,
            treatment_id,
            "Aprobado",
            "TREATMENT_APPROVED",
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/pause", response_model=TreatmentResponse)
def pause_treatment_endpoint(
    treatment_id: UUID,
    payload: StatusReasonRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> TreatmentResponse:
    try:
        return change_treatment_status(
            session,
            context,
            treatment_id,
            "Pausado",
            "TREATMENT_PAUSED",
            get_request_metadata(request),
            payload.reason,
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/resume", response_model=TreatmentResponse)
def resume_treatment_endpoint(
    treatment_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> TreatmentResponse:
    try:
        return change_treatment_status(
            session,
            context,
            treatment_id,
            "En ejecución",
            "TREATMENT_RESUMED",
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/cancel", response_model=TreatmentResponse)
def cancel_treatment_endpoint(
    treatment_id: UUID,
    payload: StatusReasonRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.cancel"))],
) -> TreatmentResponse:
    try:
        return change_treatment_status(
            session,
            context,
            treatment_id,
            "Cancelado",
            "TREATMENT_CANCELLED",
            get_request_metadata(request),
            payload.reason,
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/close", response_model=TreatmentResponse)
def close_treatment_endpoint(
    treatment_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.close"))],
) -> TreatmentResponse:
    try:
        return change_treatment_status(
            session,
            context,
            treatment_id,
            "Finalizado",
            "TREATMENT_CLOSED",
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/treatments/{treatment_id}/procedures", response_model=list[ProcedureResponse])
def list_procedures_endpoint(
    treatment_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.view"))],
) -> list[ProcedureResponse]:
    try:
        return list_procedures(session, context, treatment_id)
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/procedures", response_model=ProcedureResponse, status_code=201)
def create_procedure_endpoint(
    treatment_id: UUID,
    payload: ProcedureCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> ProcedureResponse:
    try:
        return create_procedure(session, context, treatment_id, payload, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.patch("/api/treatments/{treatment_id}/procedures/{procedure_id}", response_model=ProcedureResponse)
def update_procedure_endpoint(
    treatment_id: UUID,
    procedure_id: UUID,
    payload: ProcedureUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> ProcedureResponse:
    try:
        return update_procedure(
            session, context, treatment_id, procedure_id, payload, get_request_metadata(request)
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.delete("/api/treatments/{treatment_id}/procedures/{procedure_id}", status_code=204)
def delete_procedure_endpoint(
    treatment_id: UUID,
    procedure_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> Response:
    try:
        delete_procedure(
            session,
            context,
            treatment_id,
            procedure_id,
            get_request_metadata(request),
        )
        return Response(status_code=204)
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/procedures/{procedure_id}/mark-done", response_model=ProcedureResponse)
def mark_procedure_done_endpoint(
    treatment_id: UUID,
    procedure_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> ProcedureResponse:
    try:
        return mark_procedure_done(session, context, treatment_id, procedure_id, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/procedures/{procedure_id}/cancel", response_model=ProcedureResponse)
def cancel_procedure_endpoint(
    treatment_id: UUID,
    procedure_id: UUID,
    payload: StatusReasonRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> ProcedureResponse:
    try:
        return cancel_procedure(
            session, context, treatment_id, procedure_id, get_request_metadata(request), payload.reason
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/treatments/{treatment_id}/procedures/{procedure_id}/link-appointment", response_model=ProcedureResponse)
def link_procedure_appointment_endpoint(
    treatment_id: UUID,
    procedure_id: UUID,
    payload: LinkProcedureAppointmentRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("treatments.update"))],
) -> ProcedureResponse:
    try:
        return link_procedure_appointment(
            session, context, treatment_id, procedure_id, payload.appointment_id, get_request_metadata(request)
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/budgets", response_model=BudgetListResponse)
def list_budgets_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.view"))],
) -> BudgetListResponse:
    items = list_budgets(session, context)
    return BudgetListResponse(items=items, total=len(items))


@router.post("/api/treatments/{treatment_id}/budget", response_model=BudgetResponse, status_code=201)
def create_budget_endpoint(
    treatment_id: UUID,
    payload: BudgetCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.create"))],
) -> BudgetResponse:
    try:
        return create_budget(session, context, treatment_id, payload, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget_endpoint(
    budget_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.view"))],
) -> BudgetResponse:
    try:
        return get_budget(session, context, budget_id)
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/budgets/{budget_id}/pdf")
def get_budget_pdf_endpoint(
    budget_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.view"))],
) -> Response:
    try:
        result = generate_budget_pdf(session, context, budget_id)
        return Response(
            content=result.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{result.filename}"'
            },
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.patch("/api/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget_endpoint(
    budget_id: UUID,
    payload: BudgetCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.update"))],
) -> BudgetResponse:
    try:
        return update_budget(session, context, budget_id, payload, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/budgets/{budget_id}/submit", response_model=BudgetResponse)
def submit_budget_endpoint(
    budget_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.update"))],
) -> BudgetResponse:
    try:
        return change_budget_status(session, context, budget_id, "Pendiente de aprobación", "BUDGET_SUBMITTED", get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/budgets/{budget_id}/approve", response_model=BudgetResponse)
def approve_budget_endpoint(
    budget_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.update"))],
) -> BudgetResponse:
    try:
        return change_budget_status(session, context, budget_id, "Aprobado", "BUDGET_APPROVED", get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/budgets/{budget_id}/reject", response_model=BudgetResponse)
def reject_budget_endpoint(
    budget_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.update"))],
) -> BudgetResponse:
    try:
        return change_budget_status(session, context, budget_id, "Rechazado", "BUDGET_REJECTED", get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/budgets/{budget_id}/duplicate-version", response_model=BudgetResponse, status_code=201)
def duplicate_budget_endpoint(
    budget_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("budgets.create"))],
) -> BudgetResponse:
    try:
        budget = get_budget(session, context, budget_id)
        return create_budget(
            session,
            context,
            budget.treatment_id,
            BudgetCreateRequest(
                discount_type=budget.discount_type,
                discount_value=budget.discount_value,
                observations=budget.observations,
                expires_on=budget.expires_on,
            ),
            get_request_metadata(request),
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/payments", response_model=PaymentListResponse)
def list_payments_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("payments.view"))],
) -> PaymentListResponse:
    items = list_payments(session, context)
    return PaymentListResponse(items=items, total=len(items))


@router.post("/api/treatments/{treatment_id}/payments", response_model=PaymentResponse, status_code=201)
def create_payment_endpoint(
    treatment_id: UUID,
    payload: PaymentCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("payments.create"))],
) -> PaymentResponse:
    try:
        return create_payment(session, context, treatment_id, payload, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/payments/{payment_id}", response_model=PaymentResponse)
def get_payment_endpoint(
    payment_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("payments.view"))],
) -> PaymentResponse:
    try:
        return get_payment(session, context, payment_id)
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/payments/{payment_id}/receipt")
def get_payment_receipt_endpoint(
    payment_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("payments.view"))],
) -> Response:
    try:
        result = generate_payment_receipt_pdf(
            session,
            context,
            payment_id,
            get_request_metadata(request),
        )
        return Response(
            content=result.content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
        )
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.post("/api/payments/{payment_id}/reverse", response_model=PaymentResponse)
def reverse_payment_endpoint(
    payment_id: UUID,
    payload: PaymentReverseRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("payments.reverse"))],
) -> PaymentResponse:
    try:
        return reverse_payment(session, context, payment_id, payload.reason, get_request_metadata(request))
    except TreatmentError as exc:
        raise handle_treatment_error(exc)


@router.get("/api/finance/dashboard", response_model=FinanceDashboardResponse)
def finance_dashboard_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("finance.dashboard.view"))],
) -> FinanceDashboardResponse:
    return finance_dashboard(session, context)


@router.get("/api/finance/income", response_model=FinanceBreakdownResponse)
def finance_income_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> FinanceBreakdownResponse:
    return finance_by_site(session, context)


@router.get("/api/finance/receivables", response_model=PatientBalancesResponse)
def finance_receivables_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> PatientBalancesResponse:
    return patient_balances(session, context)


@router.get("/api/finance/by-site", response_model=FinanceBreakdownResponse)
def finance_by_site_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> FinanceBreakdownResponse:
    return finance_by_site(session, context)


@router.get("/api/finance/by-dentist", response_model=FinanceBreakdownResponse)
def finance_by_dentist_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> FinanceBreakdownResponse:
    return finance_by_dentist(session, context)


@router.get("/api/finance/by-procedure", response_model=FinanceBreakdownResponse)
def finance_by_procedure_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> FinanceBreakdownResponse:
    return finance_by_procedure(session, context)


@router.get("/api/finance/patient-balances", response_model=PatientBalancesResponse)
def patient_balances_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("reports.view"))],
) -> PatientBalancesResponse:
    return patient_balances(session, context)


@router.post("/api/appointments/{appointment_id}/link-treatment-procedure", status_code=204)
def link_appointment_treatment_endpoint(
    appointment_id: UUID,
    payload: dict,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("appointments.update"))],
) -> None:
    try:
        link_appointment_treatment_procedure(
            session,
            context,
            appointment_id,
            UUID(payload["treatment_id"]),
            UUID(payload["procedure_id"]) if payload.get("procedure_id") else None,
            get_request_metadata(request),
        )
    except (KeyError, ValueError):
        raise HTTPException(status_code=422, detail="Datos de vinculación inválidos.")
    except TreatmentError as exc:
        raise handle_treatment_error(exc)
