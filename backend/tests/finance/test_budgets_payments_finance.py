from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from app.models.treatment import Budget, TreatmentPayment
from tests.security_assertions import assert_denied, assert_no_tenant_b_leak, assert_payload_has_no_tenant_b_items


def _payment_payload(security_world, *, site_id=None, value="10000.00") -> dict:
    tenant = security_world.tenant_a
    return {
        "site_id": str(site_id or tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id),
        "procedure_ids": [],
        "paid_at": "2026-08-02T15:00:00+00:00",
        "value": value,
        "payment_method": "Efectivo",
        "reference": "TEST-AUTHORIZED",
        "observation": "Pago ficticio autorizado A",
    }


def test_budget_list_detail_and_cross_tenant_access_are_isolated(api_client, security_world) -> None:
    own_list = api_client.get("/api/budgets", token=security_world.tenant_a.admin.token)
    assert own_list.status_code == 200, own_list.text
    assert str(security_world.tenant_a.budget.id) in own_list.text
    assert_payload_has_no_tenant_b_items(own_list.json(), security_world.tenant_b)

    own_detail = api_client.get(
        f"/api/budgets/{security_world.tenant_a.budget.id}",
        token=security_world.tenant_a.admin.token,
    )
    assert own_detail.status_code == 200, own_detail.text
    assert own_detail.json()["id"] == str(security_world.tenant_a.budget.id)

    denied = api_client.get(
        f"/api/budgets/{security_world.tenant_b.budget.id}",
        token=security_world.tenant_a.admin.token,
    )
    assert_denied(denied, allowed={404})
    assert_no_tenant_b_leak(denied, security_world.tenant_b)


def test_budget_cross_tenant_mutations_are_denied_and_atomic(api_client, db_session, security_world) -> None:
    before = db_session.scalar(select(Budget).where(Budget.id == security_world.tenant_b.budget.id))
    before_status = before.status
    before_final = before.final_value
    before_version = before.version
    before_count = db_session.scalar(select(func.count(Budget.id)))

    mutation_calls = [
        ("post", f"/api/treatments/{security_world.tenant_b.treatment.id}/budget", {"procedure_ids": [], "discount_value": "0"}),
        ("patch", f"/api/budgets/{security_world.tenant_b.budget.id}", {"procedure_ids": [], "discount_value": "0"}),
        ("post", f"/api/budgets/{security_world.tenant_b.budget.id}/submit", None),
        ("post", f"/api/budgets/{security_world.tenant_b.budget.id}/approve", None),
        ("post", f"/api/budgets/{security_world.tenant_b.budget.id}/reject", None),
        (
            "post",
            f"/api/budgets/{security_world.tenant_b.budget.id}/duplicate-version",
            {"reason": "Intento cruzado ficticio", "idempotency_key": "cross-budget-b"},
        ),
    ]
    for method, url, body in mutation_calls:
        response = getattr(api_client, method)(
            url,
            token=security_world.tenant_a.admin.token,
            json=body,
        )
        assert_denied(response)
        assert_no_tenant_b_leak(response, security_world.tenant_b)

    db_session.expire_all()
    after = db_session.scalar(select(Budget).where(Budget.id == security_world.tenant_b.budget.id))
    assert after.status == before_status
    assert after.final_value == before_final
    assert after.version == before_version
    assert db_session.scalar(select(func.count(Budget.id))) == before_count


def test_budget_pdf_authorized_and_cross_tenant_denied(api_client, security_world) -> None:
    own = api_client.get(
        f"/api/budgets/{security_world.tenant_a.budget.id}/pdf",
        token=security_world.tenant_a.admin.token,
    )
    assert own.status_code == 200, own.text
    assert own.headers["content-type"].startswith("application/pdf")
    assert b"%PDF" in own.content[:20]

    denied = api_client.get(
        f"/api/budgets/{security_world.tenant_b.budget.id}/pdf",
        token=security_world.tenant_a.admin.token,
    )
    assert_denied(denied, allowed={404})
    assert b"%PDF" not in denied.content[:20]
    assert_no_tenant_b_leak(denied, security_world.tenant_b)


def test_payment_list_detail_create_and_cross_tenant_create_are_isolated(api_client, db_session, security_world) -> None:
    own_list = api_client.get("/api/payments", token=security_world.tenant_a.admin.token)
    assert own_list.status_code == 200, own_list.text
    assert str(security_world.tenant_a.payment.id) in own_list.text
    assert_payload_has_no_tenant_b_items(own_list.json(), security_world.tenant_b)

    own_detail = api_client.get(
        f"/api/payments/{security_world.tenant_a.payment.id}",
        token=security_world.tenant_a.admin.token,
    )
    assert own_detail.status_code == 200, own_detail.text
    assert own_detail.json()["receipt_number"] == security_world.tenant_a.payment.receipt_number

    before_count = db_session.scalar(select(func.count(TreatmentPayment.id)))
    created = api_client.post(
        f"/api/treatments/{security_world.tenant_a.treatment.id}/payments",
        token=security_world.tenant_a.admin.token,
        json=_payment_payload(security_world),
    )
    assert created.status_code == 201, created.text
    assert created.json()["treatment_id"] == str(security_world.tenant_a.treatment.id)
    assert Decimal(created.json()["value"]) == Decimal("10000.00")

    denied_treatment = api_client.post(
        f"/api/treatments/{security_world.tenant_b.treatment.id}/payments",
        token=security_world.tenant_a.admin.token,
        json=_payment_payload(security_world),
    )
    assert_denied(denied_treatment)
    assert_no_tenant_b_leak(denied_treatment, security_world.tenant_b)

    denied_site = api_client.post(
        f"/api/treatments/{security_world.tenant_a.treatment.id}/payments",
        token=security_world.tenant_a.admin.token,
        json=_payment_payload(security_world, site_id=security_world.tenant_b.site_1.id),
    )
    assert_denied(denied_site)
    assert_no_tenant_b_leak(denied_site, security_world.tenant_b)

    db_session.expire_all()
    assert db_session.scalar(select(func.count(TreatmentPayment.id))) == before_count + 1


def test_payment_receipt_authorized_cross_tenant_and_role_denied(api_client, security_world) -> None:
    own = api_client.get(
        f"/api/payments/{security_world.tenant_a.payment.id}/receipt",
        token=security_world.tenant_a.admin.token,
    )
    assert own.status_code == 200, own.text
    assert own.headers["content-type"].startswith("application/pdf")
    assert b"%PDF" in own.content[:20]

    denied = api_client.get(
        f"/api/payments/{security_world.tenant_b.payment.id}/receipt",
        token=security_world.tenant_a.admin.token,
    )
    assert_denied(denied, allowed={404})
    assert b"%PDF" not in denied.content[:20]
    assert_no_tenant_b_leak(denied, security_world.tenant_b)

    role_denied = api_client.get(
        f"/api/payments/{security_world.tenant_a.payment.id}/receipt",
        token=security_world.tenant_a.dentist.token,
    )
    assert role_denied.status_code == 403, role_denied.text


def test_payment_reverse_cross_tenant_denied_and_authorized_reverse_is_scoped(api_client, db_session, security_world) -> None:
    b_payment = db_session.scalar(select(TreatmentPayment).where(TreatmentPayment.id == security_world.tenant_b.payment.id))
    before_status = b_payment.status
    before_reason = b_payment.reversal_reason

    denied = api_client.post(
        f"/api/payments/{security_world.tenant_b.payment.id}/reverse",
        token=security_world.tenant_a.admin.token,
        json={"reason": "Intento reverso cruzado"},
    )
    assert_denied(denied, allowed={404})
    assert_no_tenant_b_leak(denied, security_world.tenant_b)
    db_session.expire_all()
    b_after = db_session.scalar(select(TreatmentPayment).where(TreatmentPayment.id == security_world.tenant_b.payment.id))
    assert b_after.status == before_status
    assert b_after.reversal_reason == before_reason

    own = api_client.post(
        f"/api/payments/{security_world.tenant_a.payment.id}/reverse",
        token=security_world.tenant_a.admin.token,
        json={"reason": "Reverso autorizado ficticio"},
    )
    assert own.status_code == 200, own.text
    assert own.json()["status"] == "reversado"


def test_finance_endpoints_are_tenant_scoped_and_financially_restricted(api_client, security_world) -> None:
    for path in [
        "/api/finance/dashboard",
        "/api/finance/income",
        "/api/finance/receivables",
        "/api/finance/by-site",
        "/api/finance/by-dentist",
        "/api/finance/by-procedure",
    ]:
        response = api_client.get(path, token=security_world.tenant_a.admin.token)
        assert response.status_code == 200, f"{path}: {response.text}"
        assert_no_tenant_b_leak(response, security_world.tenant_b)

    denied = api_client.get("/api/finance/dashboard", token=security_world.tenant_a.dentist.token)
    assert denied.status_code == 403, denied.text

    platform_denied = api_client.get("/api/finance/dashboard", token=security_world.platform_admin.token)
    assert platform_denied.status_code == 403, platform_denied.text
