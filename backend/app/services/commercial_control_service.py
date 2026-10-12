import calendar
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.commercial_control import CommercialAccount, CommercialTransfer
from app.models.company import Company
from app.schemas.commercial_control_schema import CommercialAccountSummary, CommercialAccountUpdate, TransferCreate, TransferSummary
from app.services.auth_service import AuthContext, RequestMetadata
from app.core.security import utc_now


class CommercialControlError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def add_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def coverage_end(start: date, months: int) -> date:
    if months <= 0:
        raise ValueError("months must be positive")
    return add_months(start, months) - timedelta(days=1)


def _account(session: Session, company_id: UUID, *, create: bool = False, actor: UUID | None = None) -> tuple[Company, CommercialAccount]:
    company = session.get(Company, company_id)
    if company is None:
        raise CommercialControlError("Clínica no encontrada.", 404)
    account = session.scalar(select(CommercialAccount).where(CommercialAccount.company_id == company_id))
    if account is None and create:
        account = CommercialAccount(company_id=company_id, created_by=actor)
        session.add(account)
        session.flush()
    if account is None:
        raise CommercialControlError("Configura primero la tarifa comercial.", 409)
    return company, account


def _active_verified(session: Session, account: CommercialAccount) -> list[CommercialTransfer]:
    return list(session.scalars(select(CommercialTransfer).where(
        CommercialTransfer.account_id == account.id,
        CommercialTransfer.status == "VERIFIED",
    ).order_by(CommercialTransfer.verified_at, CommercialTransfer.created_at)))


def _recalculate(session: Session, account: CommercialAccount) -> None:
    transfers = _active_verified(session, account)
    total_months = sum(item.months_covered for item in transfers)
    account.credit_balance = sum((item.received_amount - item.agreed_amount for item in transfers), Decimal("0"))
    if account.plan_type == "FREE":
        account.coverage_through = None
    elif account.service_start_date and total_months:
        account.coverage_through = coverage_end(account.service_start_date, total_months)
    else:
        account.coverage_through = None


def _summary(session: Session, company: Company, account: CommercialAccount, *, with_transfers: bool) -> CommercialAccountSummary:
    verified = _active_verified(session, account)
    all_transfers = list(session.scalars(select(CommercialTransfer).where(CommercialTransfer.account_id == account.id).order_by(CommercialTransfer.created_at.desc()))) if with_transfers else []
    next_due = None if account.plan_type == "FREE" else ((account.coverage_through + timedelta(days=1)) if account.coverage_through else account.service_start_date)
    pending = Decimal("0")
    if next_due and next_due <= date.today():
        pending = max(account.monthly_fee - account.credit_balance, Decimal("0"))
    return CommercialAccountSummary(
        company_id=company.id, company_name=company.name, plan_type=account.plan_type,
        monthly_fee=account.monthly_fee, currency=account.currency,
        service_start_date=account.service_start_date,
        last_verified_payment_date=max((item.transfer_date for item in verified), default=None),
        total_months_covered=sum(item.months_covered for item in verified), coverage_through=account.coverage_through,
        next_due_date=next_due, pending_balance=pending, credit_balance=account.credit_balance,
        last_contact_at=account.last_contact_at, agreement=account.agreement, owner=account.owner,
        next_contact_date=account.next_contact_date,
        transfers=[TransferSummary.model_validate(item, from_attributes=True) for item in all_transfers],
    )


def list_accounts(session: Session) -> list[CommercialAccountSummary]:
    rows = session.execute(select(Company, CommercialAccount).join(CommercialAccount, CommercialAccount.company_id == Company.id, isouter=True).order_by(Company.name))
    result = []
    for company, account in rows:
        if account is None:
            account = CommercialAccount(company_id=company.id, plan_type="STANDARD", monthly_fee=Decimal("0"), currency="COP", credit_balance=Decimal("0"))
        result.append(_summary(session, company, account, with_transfers=False))
    return result


def get_account(session: Session, company_id: UUID) -> CommercialAccountSummary:
    company = session.get(Company, company_id)
    if company is None:
        raise CommercialControlError("Clínica no encontrada.", 404)
    account = session.scalar(select(CommercialAccount).where(CommercialAccount.company_id == company_id))
    if account is None:
        account = CommercialAccount(company_id=company.id, plan_type="STANDARD", monthly_fee=Decimal("0"), currency="COP", credit_balance=Decimal("0"))
    return _summary(session, company, account, with_transfers=True)


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, company_id: UUID, entity_id: UUID, action: str, detail: dict | None = None) -> None:
    session.add(AuditEvent(company_id=company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="platform_commercial", entity_id=entity_id, action=action, result="SUCCESS", detail=detail, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


def update_account(session: Session, context: AuthContext, company_id: UUID, payload: CommercialAccountUpdate, metadata: RequestMetadata) -> CommercialAccountSummary:
    company, account = _account(session, company_id, create=True, actor=context.user.id)
    for key, value in payload.model_dump().items():
        setattr(account, key, value)
    _recalculate(session, account)
    _audit(session, context, metadata, company_id, account.id, "COMMERCIAL_ACCOUNT_UPDATED", payload.model_dump(mode="json"))
    session.commit()
    return _summary(session, company, account, with_transfers=True)


def create_transfer(session: Session, context: AuthContext, company_id: UUID, payload: TransferCreate, metadata: RequestMetadata) -> CommercialAccountSummary:
    company, account = _account(session, company_id)
    existing = session.scalar(select(CommercialTransfer).where(CommercialTransfer.company_id == company_id, CommercialTransfer.idempotency_key == payload.idempotency_key))
    if existing:
        return _summary(session, company, account, with_transfers=True)
    transfer = CommercialTransfer(company_id=company_id, account_id=account.id, created_by=context.user.id, **payload.model_dump())
    session.add(transfer)
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_RECORDED")
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    return _summary(session, company, account, with_transfers=True)


def verify_transfer(session: Session, context: AuthContext, company_id: UUID, transfer_id: UUID, metadata: RequestMetadata) -> CommercialAccountSummary:
    company, account = _account(session, company_id)
    transfer = session.scalar(select(CommercialTransfer).where(CommercialTransfer.id == transfer_id, CommercialTransfer.company_id == company_id).with_for_update())
    if transfer is None:
        raise CommercialControlError("Transferencia no encontrada.", 404)
    if transfer.status == "REVERSED":
        raise CommercialControlError("Una transferencia reversada no puede verificarse.", 409)
    if transfer.status == "VERIFIED":
        return _summary(session, company, account, with_transfers=True)
    if transfer.months_covered and not account.service_start_date:
        raise CommercialControlError("Define la fecha de inicio del servicio antes de verificar.", 409)
    prior_months = sum(item.months_covered for item in _active_verified(session, account))
    if transfer.months_covered:
        transfer.coverage_start = add_months(account.service_start_date, prior_months)
        transfer.coverage_end = coverage_end(transfer.coverage_start, transfer.months_covered)
    transfer.status = "VERIFIED"
    transfer.verified_at = utc_now()
    transfer.verified_by = context.user.id
    session.flush()
    _recalculate(session, account)
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_VERIFIED")
    session.commit()
    return _summary(session, company, account, with_transfers=True)


def reverse_transfer(session: Session, context: AuthContext, company_id: UUID, transfer_id: UUID, reason: str, metadata: RequestMetadata) -> CommercialAccountSummary:
    company, account = _account(session, company_id)
    transfer = session.scalar(select(CommercialTransfer).where(CommercialTransfer.id == transfer_id, CommercialTransfer.company_id == company_id).with_for_update())
    if transfer is None:
        raise CommercialControlError("Transferencia no encontrada.", 404)
    if transfer.status == "REVERSED":
        return _summary(session, company, account, with_transfers=True)
    transfer.status = "REVERSED"
    transfer.reversed_at = utc_now()
    transfer.reversed_by = context.user.id
    transfer.reversal_reason = reason.strip()
    session.flush()
    _recalculate(session, account)
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_REVERSED", {"reason": transfer.reversal_reason})
    session.commit()
    return _summary(session, company, account, with_transfers=True)
