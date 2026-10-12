from decimal import Decimal

from sqlalchemy import select

from app.models.commercial_control import CommercialTransfer


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
    payload = {"transfer_date":"2026-10-30","received_amount":"1100.00","agreed_amount":"1000.00","months_covered":12,"reference":"TEST-YEAR-1","receipt_reference":None,"idempotency_key":"test-year-unique"}
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
    created = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers", token=security_world.platform_admin.token, json={"transfer_date":"2026-11-01","received_amount":"50.00","agreed_amount":"0","months_covered":0,"reference":"TEST-CREDIT","receipt_reference":None,"idempotency_key":"test-credit-unique"})
    transfer_id = created.json()["transfers"][0]["id"]
    api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers/{transfer_id}/verify", token=security_world.platform_admin.token)
    reversed_response = api_client.post(f"/api/platform/commercial/accounts/{security_world.tenant_a.company.id}/transfers/{transfer_id}/reverse", token=security_world.platform_admin.token, json={"reason":"Transferencia devuelta"})
    assert reversed_response.status_code == 200
    assert Decimal(reversed_response.json()["credit_balance"]) == 0
    stored = db_session.get(CommercialTransfer, transfer_id)
    assert stored is not None and stored.status == "REVERSED"
    assert stored.reversal_reason == "Transferencia devuelta"
