from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select, text

from app.models.audit_event import AuditEvent
from app.models.commercial_control import CommercialObligation, CommercialReconciliation, CommercialTransfer


def _configure(api_client, world, *, start="2026-11-01"):
    return api_client.put(
        f"/api/platform/commercial/accounts/{world.tenant_a.company.id}",
        token=world.platform_admin.token,
        json={"plan_type":"FOUNDER","monthly_fee":"100.00","currency":"USD","service_start_date":start,"last_contact_at":None,"agreement":"Tarifa fundadora","owner":"Camilo","next_contact_date":"2026-11-15"},
    )


def test_only_platform_admin_can_access_commercial_control(api_client, security_world) -> None:
    allowed = api_client.get("/api/platform/commercial/accounts", token=security_world.platform_admin.token)
    denied = api_client.get("/api/platform/commercial/accounts", token=security_world.tenant_a.admin.token)
    assert allowed.status_code == 200
    assert denied.status_code == 403


def test_unconfigured_clinic_can_open_initial_form_without_read_side_effect(api_client, security_world, db_session) -> None:
    response = api_client.get(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}", token=security_world.platform_admin.token)
    assert response.status_code == 200
    assert Decimal(response.json()["monthly_fee"]) == 0
    from app.models.commercial_control import CommercialAccount
    assert db_session.scalar(select(CommercialAccount).where(CommercialAccount.company_id == security_world.tenant_a.company.id)) is None


def test_pending_verify_credit_year_and_idempotency(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    payload = {"transfer_date":"2026-10-12","received_amount":"1100.00","agreed_amount":"1000.00","discount_amount":"200.00","months_covered":12,"reference":"TEST-YEAR-1","receipt_reference":None,"idempotency_key":"test-year-unique"}
    first = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers", token=security_world.platform_admin.token, json=payload)
    second = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers", token=security_world.platform_admin.token, json=payload)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["coverage_through"] is None
    transfers = list(db_session.scalars(select(CommercialTransfer).where(CommercialTransfer.company_id == security_world.tenant_a.company.id)))
    assert len(transfers) == 1
    verified = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers/{transfers[0].id}/verify", token=security_world.platform_admin.token)
    body = verified.json()
    assert verified.status_code == 200
    assert body["coverage_through"] == "2027-10-31"
    assert body["next_due_date"] == "2027-11-01"
    assert Decimal(body["credit_balance"]) == Decimal("100.00")


def test_reversal_restores_account_without_deleting_history(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    created = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers", token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"50.00","agreed_amount":"0","months_covered":0,"reference":"TEST-CREDIT","receipt_reference":None,"idempotency_key":"test-credit-unique"})
    transfer_id = created.json()["transfers"][0]["id"]
    api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers/{transfer_id}/verify", token=security_world.platform_admin.token)
    reversed_response = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers/{transfer_id}/reverse", token=security_world.platform_admin.token, json={"reason":"Transferencia devuelta"})
    assert reversed_response.status_code == 200
    assert Decimal(reversed_response.json()["credit_balance"]) == 0
    stored = db_session.get(CommercialTransfer, transfer_id)
    assert stored is not None and stored.status == "REVERSED"
    assert stored.reversal_reason == "Transferencia devuelta"


def test_partial_payment_does_not_grant_coverage_and_credit_completes_later(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    base = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    partial = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"50","agreed_amount":"100","months_covered":1,"reference":"PARTIAL","idempotency_key":"partial-one"})
    transfer_id = partial.json()["transfers"][0]["id"]
    refused = api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    assert refused.status_code == 409
    assert refused.json()["detail"].startswith("El importe recibido")
    assert db_session.scalar(select(CommercialObligation).where(CommercialObligation.transfer_id == transfer_id)) is None
    credit = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"50","agreed_amount":"0","months_covered":0,"reference":"CREDIT","idempotency_key":"credit-before-partial"})
    credit_id = credit.json()["transfers"][0]["id"]
    assert api_client.post(f"{base}/{credit_id}/verify", token=security_world.platform_admin.token).status_code == 200
    verified = api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    assert verified.status_code == 200
    assert verified.json()["coverage_through"] == "2026-11-30"
    assert Decimal(verified.json()["credit_balance"]) == 0


def test_anchor_is_preserved_across_two_monthly_payments(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world, start="2027-01-31").status_code == 200
    base = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    for index in (1, 2):
        created = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":f"M{index}","idempotency_key":f"anchor-payment-{index}"})
        transfer_id = created.json()["transfers"][0]["id"]
        response = api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    assert response.json()["coverage_through"] == "2027-03-30"
    obligations = list(db_session.scalars(select(CommercialObligation).order_by(CommercialObligation.period_index)))
    assert [(item.period_start.isoformat(), item.period_end.isoformat()) for item in obligations] == [("2027-01-31", "2027-02-27"), ("2027-02-28", "2027-03-30")]


def test_idempotency_conflict_currency_lock_and_reconciliation(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    base = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    payload = {"transfer_date":"2026-10-12","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":"ONE","idempotency_key":"stable-attempt-key"}
    assert api_client.post(base, token=security_world.platform_admin.token, json=payload).status_code == 201
    changed = dict(payload, received_amount="101")
    assert api_client.post(base, token=security_world.platform_admin.token, json=changed).status_code == 409
    currency_change = api_client.put(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}", token=security_world.platform_admin.token, json={"plan_type":"FOUNDER","monthly_fee":"100","currency":"COP","service_start_date":"2026-11-01","last_contact_at":None,"agreement":None,"owner":None,"next_contact_date":None})
    assert currency_change.status_code == 409
    assert db_session.scalar(select(CommercialReconciliation)) is not None


def test_pending_balance_accumulates_and_credit_never_becomes_negative(api_client, security_world) -> None:
    assert _configure(api_client, security_world, start="2026-07-01").status_code == 200
    detail = api_client.get(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}", token=security_world.platform_admin.token)
    assert Decimal(detail.json()["pending_balance"]) == Decimal("400")
    base = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    credit = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"50","agreed_amount":"0","months_covered":0,"reference":"CREDIT","idempotency_key":"accrued-credit"})
    transfer_id = credit.json()["transfers"][0]["id"]
    verified = api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    assert Decimal(verified.json()["pending_balance"]) == Decimal("350")
    assert Decimal(verified.json()["credit_balance"]) == Decimal("50")


def test_reversing_earlier_period_creates_traced_gap_without_rewriting_later_fact(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world, start="2026-09-01").status_code == 200
    base = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    ids = []
    for index in (1, 2):
        created = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":f"P{index}","idempotency_key":f"gap-payment-{index}"})
        transfer_id = created.json()["transfers"][0]["id"]; ids.append(transfer_id)
        api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    later_before = db_session.get(CommercialTransfer, ids[1]).coverage_end
    reversed_response = api_client.post(f"{base}/{ids[0]}/reverse", token=security_world.platform_admin.token, json={"reason":"Corrección del primer período"})
    db_session.expire_all()
    assert reversed_response.json()["coverage_through"] is None
    assert Decimal(reversed_response.json()["pending_balance"]) == Decimal("100")
    assert db_session.get(CommercialTransfer, ids[1]).coverage_end == later_before
    assert db_session.scalar(select(CommercialReconciliation).where(CommercialReconciliation.action == "TRANSFER_REVERSED")) is not None


def test_gap_payment_reports_non_contiguous_periods_without_revaluing_old_debt(api_client, security_world) -> None:
    assert _configure(api_client, security_world, start="2026-07-01").status_code == 200
    company_id = security_world.tenant_a.company.id
    base = f"/api/platform/commercial/accounts/{company_id}/transfers"
    ids = []
    for index in (1, 2):
        created = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":f"OLD-{index}","idempotency_key":f"old-rate-{index}"})
        transfer_id = created.json()["transfers"][0]["id"]
        ids.append(transfer_id)
        assert api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token).status_code == 200
    assert api_client.post(f"{base}/{ids[0]}/reverse", token=security_world.platform_admin.token, json={"reason":"Abrir hueco inicial"}).status_code == 200
    changed = api_client.put(f"/api/platform/commercial/accounts/{company_id}", token=security_world.platform_admin.token, json={"plan_type":"FOUNDER","monthly_fee":"200","currency":"USD","service_start_date":"2026-07-01","last_contact_at":None,"agreement":None,"owner":None,"next_contact_date":None})
    assert changed.status_code == 200
    # July, September and October remain unpaid at their historical USD 100 rate.
    assert Decimal(changed.json()["pending_balance"]) == Decimal("300")
    created = api_client.post(base, token=security_world.platform_admin.token, json={"transfer_date":"2026-10-12","received_amount":"200","agreed_amount":"200","months_covered":2,"reference":"FILL-1-3","idempotency_key":"fill-non-contiguous"})
    transfer_id = created.json()["transfers"][0]["id"]
    verified = api_client.post(f"{base}/{transfer_id}/verify", token=security_world.platform_admin.token)
    assert verified.status_code == 200
    transfer = next(item for item in verified.json()["transfers"] if item["id"] == transfer_id)
    assert [item["period_index"] for item in transfer["covered_periods"]] == [1, 3]
    assert [(item["period_start"], item["period_end"]) for item in transfer["covered_periods"]] == [("2026-07-01", "2026-07-31"), ("2026-09-01", "2026-09-30")]
    assert Decimal(verified.json()["pending_balance"]) == Decimal("100")


def test_concurrent_duplicate_submission_creates_one_transfer_and_audit_snapshot(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    url = f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers"
    payload = {"transfer_date":"2026-10-12","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":"RACE","idempotency_key":"concurrent-stable-key"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: api_client.post(url, token=security_world.platform_admin.token, json=payload), range(2)))
    assert [response.status_code for response in responses] == [201, 201]
    rows = list(db_session.scalars(select(CommercialTransfer).where(CommercialTransfer.idempotency_key == "concurrent-stable-key")))
    assert len(rows) == 1
    audit = db_session.scalar(select(AuditEvent).where(AuditEvent.entity_id == rows[0].id, AuditEvent.action == "COMMERCIAL_TRANSFER_RECORDED"))
    assert audit.detail["currency"] == "USD"
    assert Decimal(audit.detail["received_amount"]) == Decimal("100.00")
    assert audit.detail["months"] == 1
    assert audit.detail["reference"] == "RACE"


def test_future_transfer_rejected_and_database_checks_are_installed(api_client, security_world, db_session) -> None:
    assert _configure(api_client, security_world).status_code == 200
    response = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers", token=security_world.platform_admin.token, json={"transfer_date":"2026-10-13","received_amount":"100","agreed_amount":"100","months_covered":1,"reference":"FUTURE","idempotency_key":"future-transfer"})
    assert response.status_code == 422
    constraints = " ".join(db_session.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'platform_commercial_transfers'::regclass")).scalars())
    assert "received_amount >" in constraints
    assert "months_covered >= 0" in constraints and "months_covered <= 120" in constraints
    assert "UNIQUE (company_id, idempotency_key)" in constraints
