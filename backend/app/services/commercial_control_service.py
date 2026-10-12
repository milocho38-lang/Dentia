import calendar, hashlib, json
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import utc_now
from app.models.audit_event import AuditEvent
from app.models.commercial_control import CommercialAccount, CommercialObligation, CommercialRate, CommercialReconciliation, CommercialTransfer
from app.models.company import Company
from app.schemas.commercial_control_schema import CommercialAccountSummary, CommercialAccountUpdate, CoveredPeriod, TransferCreate, TransferSummary
from app.services.auth_service import AuthContext, RequestMetadata

ZERO = Decimal("0.00")

class CommercialControlError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message); self.status_code = status_code

def add_months(value: date, months: int) -> date:
    index = value.month - 1 + months; year = value.year + index // 12; month = index % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))

def anchored_period(start: date, period_index: int) -> tuple[date, date]:
    return add_months(start, period_index - 1), add_months(start, period_index) - timedelta(days=1)

def coverage_end(start: date, months: int) -> date:
    if months <= 0: raise ValueError("months must be positive")
    return add_months(start, months) - timedelta(days=1)

def _account(session: Session, company_id: UUID, *, create=False, actor=None):
    company = session.get(Company, company_id)
    if company is None: raise CommercialControlError("Clínica no encontrada.", 404)
    account = session.scalar(select(CommercialAccount).where(CommercialAccount.company_id == company_id).with_for_update())
    if account is None and create:
        account = CommercialAccount(company_id=company_id, plan_type="STANDARD", monthly_fee=ZERO, currency="COP", credit_balance=ZERO, created_by=actor); session.add(account); session.flush()
    if account is None: raise CommercialControlError("Configura primero la tarifa comercial.", 409)
    return company, account

def _verified(session, account):
    return list(session.scalars(select(CommercialTransfer).where(CommercialTransfer.account_id == account.id, CommercialTransfer.status == "VERIFIED").order_by(CommercialTransfer.verified_at, CommercialTransfer.created_at)))

def _obligations(session, account):
    return list(session.scalars(select(CommercialObligation).where(CommercialObligation.account_id == account.id, CommercialObligation.status == "PAID").order_by(CommercialObligation.period_index)))

def _consecutive(items):
    expected = 1
    for item in items:
        if item.period_index != expected: break
        expected += 1
    return expected - 1

def _months_due(start, through):
    if not start or through < start: return 0
    count = 0
    while add_months(start, count) <= through: count += 1
    return count

def _rate_for(session, account, period_index):
    rate = session.scalar(select(CommercialRate).where(CommercialRate.account_id == account.id, CommercialRate.effective_period_index <= period_index).order_by(CommercialRate.effective_period_index.desc()))
    return rate.monthly_fee if rate else account.monthly_fee

def _missing_indexes(session, account, count, *, due_only=False):
    occupied = {item.period_index for item in _obligations(session, account)}; result=[]; candidate=1
    limit = _months_due(account.service_start_date, date.today()) if due_only else 10_000
    while len(result) < count and candidate <= limit:
        if candidate not in occupied: result.append(candidate)
        candidate += 1
    return result

def _state(session, account):
    paid = _consecutive(_obligations(session, account)); coverage = coverage_end(account.service_start_date, paid) if account.service_start_date and paid else None
    next_due = None if account.plan_type == "FREE" else (add_months(account.service_start_date, paid) if account.service_start_date else None)
    credit = sum((item.credit_generated - item.credit_applied for item in _verified(session, account)), ZERO)
    if credit < ZERO: raise CommercialControlError("La conciliación produciría saldo a favor negativo.", 409)
    due_count = 0 if account.plan_type == "FREE" else _months_due(account.service_start_date, date.today())
    occupied = {item.period_index for item in _obligations(session, account)}
    debt = sum((_rate_for(session, account, index) for index in range(1, due_count + 1) if index not in occupied), ZERO)
    return paid, coverage, next_due, credit, max(debt - credit, ZERO)

def _reconcile(session, account, *, action, actor, transfer_id=None, detail=None):
    state = _state(session, account); account.coverage_through = state[1]; account.credit_balance = state[3]
    session.add(CommercialReconciliation(company_id=account.company_id, account_id=account.id, trigger_transfer_id=transfer_id, action=action, coverage_through=state[1], credit_balance=state[3], pending_balance=state[4], detail=detail, created_by=actor)); return state

def _summary(session, company, account, *, with_transfers):
    paid, coverage, next_due, credit, pending = _state(session, account)
    verified = _verified(session, account)
    transfers = list(session.scalars(select(CommercialTransfer).where(CommercialTransfer.account_id == account.id).order_by(CommercialTransfer.created_at.desc()))) if with_transfers and account.id else []
    summaries=[]
    for transfer in transfers:
        item=TransferSummary.model_validate(transfer, from_attributes=True)
        item.covered_periods=[CoveredPeriod(period_index=o.period_index,period_start=o.period_start,period_end=o.period_end,status=o.status) for o in session.scalars(select(CommercialObligation).where(CommercialObligation.transfer_id==transfer.id).order_by(CommercialObligation.period_index))]
        summaries.append(item)
    return CommercialAccountSummary(company_id=company.id, company_name=company.name, plan_type=account.plan_type, monthly_fee=account.monthly_fee, currency=account.currency, service_start_date=account.service_start_date, last_verified_payment_date=max((x.transfer_date for x in verified), default=None), total_months_covered=paid, coverage_through=coverage, next_due_date=next_due, pending_balance=pending, credit_balance=credit, last_contact_at=account.last_contact_at, agreement=account.agreement, owner=account.owner, next_contact_date=account.next_contact_date, transfers=summaries)

def _transient(company): return CommercialAccount(company_id=company.id, plan_type="STANDARD", monthly_fee=ZERO, currency="COP", credit_balance=ZERO)

def list_accounts(session):
    rows = session.execute(select(Company, CommercialAccount).join(CommercialAccount, CommercialAccount.company_id == Company.id, isouter=True).order_by(Company.name))
    return [_summary(session, c, a or _transient(c), with_transfers=False) for c, a in rows]

def get_account(session, company_id):
    company = session.get(Company, company_id)
    if company is None: raise CommercialControlError("Clínica no encontrada.", 404)
    account = session.scalar(select(CommercialAccount).where(CommercialAccount.company_id == company_id))
    return _summary(session, company, account or _transient(company), with_transfers=True)

def _audit(session, context, metadata, company_id, entity_id, action, detail):
    session.add(AuditEvent(company_id=company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="platform_commercial", entity_id=entity_id, action=action, result="SUCCESS", detail=detail, ip_address=metadata.ip_address, user_agent=metadata.user_agent))

def update_account(session, context, company_id, payload, metadata):
    company, account = _account(session, company_id, create=True, actor=context.user.id)
    has_history = bool(session.scalar(select(func.count()).select_from(CommercialTransfer).where(CommercialTransfer.account_id == account.id)))
    if has_history and payload.currency != account.currency: raise CommercialControlError("No se puede cambiar la moneda de una cuenta con historial.", 409)
    if has_history and payload.service_start_date != account.service_start_date: raise CommercialControlError("No se puede cambiar la fecha inicial de una cuenta con historial.", 409)
    before = {"plan_type": account.plan_type, "monthly_fee": str(account.monthly_fee), "currency": account.currency, "service_start_date": account.service_start_date.isoformat() if account.service_start_date else None}
    fee_changed = payload.monthly_fee != account.monthly_fee
    for key, value in payload.model_dump().items(): setattr(account, key, value)
    session.flush()
    existing_rate = session.scalar(select(CommercialRate.id).where(CommercialRate.account_id == account.id))
    if existing_rate is None:
        session.add(CommercialRate(company_id=company_id, account_id=account.id, effective_period_index=1, monthly_fee=account.monthly_fee, currency=account.currency, created_by=context.user.id))
    elif fee_changed:
        effective = max(_months_due(account.service_start_date, date.today()) + 1, int(session.scalar(select(func.max(CommercialObligation.period_index)).where(CommercialObligation.account_id == account.id)) or 0) + 1)
        prior = session.scalar(select(CommercialRate).where(CommercialRate.account_id == account.id, CommercialRate.effective_period_index == effective))
        if prior: prior.monthly_fee = account.monthly_fee
        else: session.add(CommercialRate(company_id=company_id, account_id=account.id, effective_period_index=effective, monthly_fee=account.monthly_fee, currency=account.currency, created_by=context.user.id))
    session.flush(); state = _reconcile(session, account, action="ACCOUNT_UPDATED", actor=context.user.id, detail=json.dumps({"before": before, "after": payload.model_dump(mode="json")}, ensure_ascii=False))
    _audit(session, context, metadata, company_id, account.id, "COMMERCIAL_ACCOUNT_UPDATED", {"before": before, "after": payload.model_dump(mode="json"), "coverage_through": str(state[1]), "credit_balance": str(state[3]), "pending_balance": str(state[4])}); session.commit()
    return _summary(session, company, account, with_transfers=True)

def _payload_hash(payload):
    raw = json.dumps(payload.model_dump(mode="json", exclude={"idempotency_key"}), sort_keys=True, separators=(",", ":")); return hashlib.sha256(raw.encode()).hexdigest()

def create_transfer(session, context, company_id, payload, metadata):
    company, account = _account(session, company_id); digest = _payload_hash(payload)
    existing = session.scalar(select(CommercialTransfer).where(CommercialTransfer.company_id == company_id, CommercialTransfer.idempotency_key == payload.idempotency_key))
    if existing:
        if existing.payload_hash != digest: raise CommercialControlError("La clave de idempotencia ya fue usada con otros datos.", 409)
        return _summary(session, company, account, with_transfers=True)
    indexes = _missing_indexes(session, account, payload.months_covered)
    list_amount = sum((_rate_for(session, account, index) for index in indexes), ZERO).quantize(Decimal("0.01"))
    if payload.months_covered and payload.agreed_amount + payload.discount_amount != list_amount: raise CommercialControlError("Importe acordado más descuento debe coincidir con la tarifa de los meses.", 422)
    transfer = CommercialTransfer(company_id=company_id, account_id=account.id, created_by=context.user.id, transfer_date=payload.transfer_date, received_amount=payload.received_amount, agreed_amount=payload.agreed_amount, list_amount=list_amount, discount_amount=payload.discount_amount, currency_snapshot=account.currency, monthly_fee_snapshot=(_rate_for(session, account, indexes[0]) if indexes else account.monthly_fee), months_covered=payload.months_covered, reference=payload.reference, receipt_reference=payload.receipt_reference, idempotency_key=payload.idempotency_key, payload_hash=digest, credit_applied=ZERO, credit_generated=ZERO)
    session.add(transfer); session.flush()
    snap = {"received_amount": str(transfer.received_amount), "agreed_amount": str(transfer.agreed_amount), "list_amount": str(transfer.list_amount), "discount_amount": str(transfer.discount_amount), "currency": transfer.currency_snapshot, "monthly_fee": str(transfer.monthly_fee_snapshot), "months": transfer.months_covered, "reference": transfer.reference, "receipt_reference": transfer.receipt_reference}
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_RECORDED", snap)
    try: session.commit()
    except IntegrityError:
        session.rollback(); existing = session.scalar(select(CommercialTransfer).where(CommercialTransfer.company_id == company_id, CommercialTransfer.idempotency_key == payload.idempotency_key))
        if existing is None or existing.payload_hash != digest: raise CommercialControlError("Conflicto de idempotencia.", 409)
    return _summary(session, company, account, with_transfers=True)

def _split(total, count):
    if not count: return []
    base = (total / count).quantize(Decimal("0.01"), rounding=ROUND_DOWN); values = [base] * count; values[-1] += total - sum(values, ZERO); return values

def verify_transfer(session, context, company_id, transfer_id, metadata):
    company, account = _account(session, company_id); transfer = session.scalar(select(CommercialTransfer).where(CommercialTransfer.id == transfer_id, CommercialTransfer.company_id == company_id).with_for_update())
    if transfer is None: raise CommercialControlError("Transferencia no encontrada.", 404)
    if transfer.status == "REVERSED": raise CommercialControlError("Una transferencia reversada no puede verificarse.", 409)
    if transfer.status == "VERIFIED": return _summary(session, company, account, with_transfers=True)
    if transfer.months_covered and not account.service_start_date: raise CommercialControlError("Define la fecha de inicio del servicio antes de verificar.", 409)
    credit = _state(session, account)[3]
    if transfer.received_amount + credit < transfer.agreed_amount: raise CommercialControlError("El importe recibido y el saldo a favor no cubren el importe acordado.", 409)
    transfer.credit_applied = min(credit, transfer.agreed_amount); cash_applied = transfer.agreed_amount - transfer.credit_applied; transfer.credit_generated = transfer.received_amount - cash_applied
    period_indexes = _missing_indexes(session, account, transfer.months_covered)
    if transfer.months_covered:
        transfer.coverage_start = anchored_period(account.service_start_date, period_indexes[0])[0]; transfer.coverage_end = anchored_period(account.service_start_date, period_indexes[-1])[1]
        discounts, dues, lists = _split(transfer.discount_amount, transfer.months_covered), _split(transfer.agreed_amount, transfer.months_covered), [_rate_for(session, account, index) for index in period_indexes]
        for offset, index in enumerate(period_indexes):
            start, end = anchored_period(account.service_start_date, index)
            session.add(CommercialObligation(company_id=company_id, account_id=account.id, transfer_id=transfer.id, period_index=index, period_start=start, period_end=end, currency=transfer.currency_snapshot, list_amount=lists[offset], discount_amount=discounts[offset], amount_due=dues[offset], status="PAID", created_by=context.user.id))
    transfer.status = "VERIFIED"; transfer.verified_at = utc_now(); transfer.verified_by = context.user.id; session.flush()
    state = _reconcile(session, account, action="TRANSFER_VERIFIED", actor=context.user.id, transfer_id=transfer.id)
    snap = {"received_amount": str(transfer.received_amount), "agreed_amount": str(transfer.agreed_amount), "list_amount": str(transfer.list_amount), "discount_amount": str(transfer.discount_amount), "currency": transfer.currency_snapshot, "monthly_fee": str(transfer.monthly_fee_snapshot), "months": transfer.months_covered, "reference": transfer.reference, "credit_applied": str(transfer.credit_applied), "credit_generated": str(transfer.credit_generated), "coverage_start": str(transfer.coverage_start), "coverage_end": str(transfer.coverage_end), "account_coverage_through": str(state[1])}
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_VERIFIED", snap); session.commit(); return _summary(session, company, account, with_transfers=True)

def reverse_transfer(session, context, company_id, transfer_id, reason, metadata):
    company, account = _account(session, company_id); transfer = session.scalar(select(CommercialTransfer).where(CommercialTransfer.id == transfer_id, CommercialTransfer.company_id == company_id).with_for_update())
    if transfer is None: raise CommercialControlError("Transferencia no encontrada.", 404)
    if transfer.status == "REVERSED": return _summary(session, company, account, with_transfers=True)
    if transfer.status == "VERIFIED":
        later_use = session.scalar(select(func.count()).select_from(CommercialTransfer).where(CommercialTransfer.account_id == account.id, CommercialTransfer.status == "VERIFIED", CommercialTransfer.verified_at > transfer.verified_at, CommercialTransfer.credit_applied > ZERO)) or 0
        if transfer.credit_generated and later_use: raise CommercialControlError("Reversa primero los movimientos posteriores que consumieron este saldo a favor.", 409)
        for obligation in session.scalars(select(CommercialObligation).where(CommercialObligation.transfer_id == transfer.id, CommercialObligation.status == "PAID")):
            obligation.status = "VOID"; obligation.is_active = False; obligation.voided_at = utc_now(); obligation.void_reason = reason.strip()
    transfer.status = "REVERSED"; transfer.reversed_at = utc_now(); transfer.reversed_by = context.user.id; transfer.reversal_reason = reason.strip(); session.flush()
    state = _reconcile(session, account, action="TRANSFER_REVERSED", actor=context.user.id, transfer_id=transfer.id, detail=transfer.reversal_reason)
    _audit(session, context, metadata, company_id, transfer.id, "COMMERCIAL_TRANSFER_REVERSED", {"reason": transfer.reversal_reason, "received_amount": str(transfer.received_amount), "agreed_amount": str(transfer.agreed_amount), "discount_amount": str(transfer.discount_amount), "currency": transfer.currency_snapshot, "months": transfer.months_covered, "reference": transfer.reference, "coverage_through": str(state[1]), "credit_balance": str(state[3]), "pending_balance": str(state[4])}); session.commit(); return _summary(session, company, account, with_transfers=True)
