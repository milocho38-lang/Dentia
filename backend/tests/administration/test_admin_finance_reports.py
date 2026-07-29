from __future__ import annotations

from sqlalchemy import select

from app.models.company import Company
from app.models.role import Role
from app.models.site import Site
from app.models.user import User
from tests.security_assertions import assert_denied, assert_no_tenant_b_leak, assert_payload_has_no_tenant_b_items


def _role_id(db_session, company_id, code: str) -> str:
    role = db_session.scalar(select(Role).where(Role.company_id == company_id, Role.code == code))
    assert role is not None
    return str(role.id)


def _site_payload(label: str) -> dict:
    return {
        "name": f"Sede Nueva {label}",
        "address": f"Calle Nueva {label}",
        "city": "Bogotá",
        "phone": "+5710000000",
        "timezone": "America/Bogota",
    }


def test_company_admin_user_management_is_tenant_scoped(api_client, db_session, security_world) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    admin_role_id = _role_id(db_session, tenant_a.company.id, "ADMINISTRATOR")
    secretary_role_id = _role_id(db_session, tenant_a.company.id, "SECRETARY")

    users = api_client.get("/api/users", token=tenant_a.admin.token)
    assert users.status_code == 200, users.text
    assert str(tenant_a.secretary.user.id) in users.text
    assert_payload_has_no_tenant_b_items(users.json(), tenant_b)

    own = api_client.get(f"/api/users/{tenant_a.secretary.user.id}", token=tenant_a.admin.token)
    assert own.status_code == 200, own.text

    cross = api_client.get(f"/api/users/{tenant_b.admin.user.id}", token=tenant_a.admin.token)
    assert_denied(cross, allowed={404})
    assert_no_tenant_b_leak(cross, tenant_b)

    assigned = api_client.put(
        f"/api/users/{tenant_a.secretary.user.id}/roles",
        token=tenant_a.admin.token,
        json={"role_ids": [admin_role_id, secretary_role_id]},
    )
    assert assigned.status_code == 200, assigned.text
    role_codes = {role["code"] for role in assigned.json()["roles"]}
    assert {"ADMINISTRATOR", "SECRETARY"} <= role_codes

    b_before = db_session.scalar(select(User).where(User.id == tenant_b.admin.user.id))
    before_updated_at = b_before.updated_at
    denied = api_client.put(
        f"/api/users/{tenant_b.admin.user.id}/roles",
        token=tenant_a.admin.token,
        json={"role_ids": [admin_role_id]},
    )
    assert_denied(denied, allowed={404})
    assert_no_tenant_b_leak(denied, tenant_b)
    db_session.expire_all()
    b_after = db_session.scalar(select(User).where(User.id == tenant_b.admin.user.id))
    assert b_after.updated_at == before_updated_at


def test_user_site_management_rejects_cross_tenant_site_and_insufficient_role(api_client, db_session, security_world) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b

    assigned = api_client.put(
        f"/api/users/{tenant_a.secretary.user.id}/sites",
        token=tenant_a.admin.token,
        json={"site_ids": [str(tenant_a.site_1.id), str(tenant_a.site_2.id)], "default_site_id": str(tenant_a.site_1.id)},
    )
    assert assigned.status_code == 200, assigned.text
    assert str(tenant_a.site_2.id) in assigned.text

    denied_site = api_client.put(
        f"/api/users/{tenant_a.secretary.user.id}/sites",
        token=tenant_a.admin.token,
        json={"site_ids": [str(tenant_b.site_1.id)], "default_site_id": str(tenant_b.site_1.id)},
    )
    assert_denied(denied_site)
    assert_no_tenant_b_leak(denied_site, tenant_b)

    denied_role = api_client.put(
        f"/api/users/{tenant_a.secretary.user.id}/roles",
        token=tenant_a.secretary.token,
        json={"role_ids": [_role_id(db_session, tenant_a.company.id, "ADMINISTRATOR")]},
    )
    assert denied_role.status_code == 403, denied_role.text

    self_escalation = api_client.put(
        f"/api/users/{tenant_a.secretary.user.id}/roles",
        token=tenant_a.secretary.token,
        json={"role_ids": [_role_id(db_session, tenant_a.company.id, "ADMINISTRATOR")]},
    )
    assert self_escalation.status_code == 403, self_escalation.text


def test_sites_company_and_branding_are_scoped_and_role_protected(api_client, db_session, security_world) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b

    sites = api_client.get("/api/sites", token=tenant_a.admin.token)
    assert sites.status_code == 200, sites.text
    assert str(tenant_a.site_1.id) in sites.text
    assert_payload_has_no_tenant_b_items(sites.json(), tenant_b)

    created = api_client.post("/api/sites", token=tenant_a.admin.token, json=_site_payload("A"))
    assert created.status_code == 201, created.text
    assert created.json()["name"] == "Sede Nueva A"

    denied_get_b_site = api_client.get(f"/api/sites/{tenant_b.site_1.id}", token=tenant_a.admin.token)
    assert_denied(denied_get_b_site, allowed={404})
    assert_no_tenant_b_leak(denied_get_b_site, tenant_b)

    b_site_before = db_session.scalar(select(Site).where(Site.id == tenant_b.site_1.id))
    before_name = b_site_before.name
    denied_patch_b_site = api_client.patch(
        f"/api/sites/{tenant_b.site_1.id}",
        token=tenant_a.admin.token,
        json=_site_payload("B Invadida"),
    )
    assert_denied(denied_patch_b_site, allowed={404})
    assert_no_tenant_b_leak(denied_patch_b_site, tenant_b)
    db_session.expire_all()
    b_site_after = db_session.scalar(select(Site).where(Site.id == tenant_b.site_1.id))
    assert b_site_after.name == before_name

    company = api_client.get("/api/company", token=tenant_a.admin.token)
    assert company.status_code == 200, company.text
    assert company.json()["id"] == str(tenant_a.company.id)
    assert_no_tenant_b_leak(company, tenant_b)

    updated_company = api_client.patch(
        "/api/company",
        token=tenant_a.admin.token,
        json={
            "name": "Clínica Ficticia A Actualizada",
            "company_type": "Clínica",
            "tax_id": "TEST-A",
            "phone": "+571111111",
            "email": "contacto-a@example.test",
            "address": "Calle A Actualizada",
            "city": "Bogotá",
            "country": "Colombia",
            "timezone": "America/Bogota",
        },
    )
    assert updated_company.status_code == 200, updated_company.text
    assert updated_company.json()["name"] == "Clínica Ficticia A Actualizada"

    insufficient = api_client.patch(
        "/api/company",
        token=tenant_a.secretary.token,
        json=updated_company.json() | {"name": "No autorizado"},
    )
    assert insufficient.status_code == 403, insufficient.text


def test_branding_authorized_update_assets_and_insufficient_role_denied(api_client, db_session, security_world) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b

    branding = api_client.get("/api/company/branding", token=tenant_a.admin.token)
    assert branding.status_code == 200, branding.text
    assert_no_tenant_b_leak(branding, tenant_b)

    updated = api_client.patch(
        "/api/company/branding",
        token=tenant_a.admin.token,
        json={
            "name": "Marca A",
            "legal_name": "Marca A SAS",
            "company_type": "Clínica",
            "tax_id": "TEST-A",
            "address": "Calle Branding A",
            "city": "Bogotá",
            "department": "Bogotá",
            "country": "Colombia",
            "phone": "+571111111",
            "mobile": "+573111111111",
            "email": "branding-a@example.test",
            "website": "https://example.test",
            "social_media": {"instagram": "@dentia_a"},
            "primary_dentist_name": "Dra. A",
            "professional_specialty": "Odontología",
            "professional_license": "A-123",
            "university": "Universidad Test",
            "experience_years": 5,
            "header_text": "Encabezado A",
            "footer_text": "Pie A",
            "legal_observations": "Legal A",
            "cancellation_policy": "Política A",
            "thank_you_message": "Gracias A",
            "payment_receipt_title": "COMPROBANTE DE PAGO",
            "primary_color": "#16a34a",
            "secondary_color": "#0f766e",
            "button_color": "#16a34a",
            "heading_color": "#0f172a",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Marca A"

    upload = api_client.post(
        "/api/company/branding/logo",
        token=tenant_a.admin.token,
        files={"file": ("logo-a.png", b"fake-png-a", "image/png")},
    )
    assert upload.status_code == 200, upload.text
    assert "logo-a.png" in upload.text
    assert "/Users/" not in upload.text
    assert "/tmp/" not in upload.text

    asset = api_client.get("/api/company/branding/logo", token=tenant_a.admin.token)
    assert asset.status_code == 200, asset.text
    assert asset.content == b"fake-png-a"

    insufficient = api_client.post(
        "/api/company/branding/signature",
        token=tenant_a.secretary.token,
        files={"file": ("signature-a.png", b"fake-signature-a", "image/png")},
    )
    assert insufficient.status_code == 403, insufficient.text

    b_company = db_session.scalar(select(Company).where(Company.id == tenant_b.company.id))
    assert b_company.logo_path is None
    assert b_company.signature_path is None


def test_platform_role_management_contract_and_vertical_escalation(api_client, db_session, security_world) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b

    detail = api_client.get(
        f"/api/platform/companies/{tenant_a.company.id}",
        token=security_world.platform_admin.token,
    )
    assert detail.status_code == 200, detail.text
    role_options = detail.json()["role_options"]
    role_codes = {role["code"] for role in role_options}
    assert "PLATFORM_ADMIN" not in role_codes
    admin_role = next(role for role in role_options if role["code"] == "ADMINISTRATOR")
    dentist_role = next(role for role in role_options if role["code"] == "DENTIST")
    dentist_admin_role = next(role for role in role_options if role["code"] == "DENTIST_ADMIN")

    updated = api_client.patch(
        f"/api/platform/companies/{tenant_a.company.id}/users/{tenant_a.secretary.user.id}/roles",
        token=security_world.platform_admin.token,
        json={
            "role_ids": [admin_role["id"], dentist_role["id"], dentist_admin_role["id"]],
            "site_ids": [str(tenant_a.site_1.id), str(tenant_a.site_2.id)],
            "default_site_id": str(tenant_a.site_1.id),
            "status": "Activo",
            "ensure_dentist_profile": False,
        },
    )
    assert updated.status_code == 200, updated.text
    assert {"ADMINISTRATOR", "DENTIST", "DENTIST_ADMIN"} <= set(updated.json()["user"]["roles"])

    denied_cross_company = api_client.patch(
        f"/api/platform/companies/{tenant_a.company.id}/users/{tenant_b.admin.user.id}/roles",
        token=security_world.platform_admin.token,
        json={
            "role_ids": [admin_role["id"]],
            "site_ids": [str(tenant_a.site_1.id)],
            "default_site_id": str(tenant_a.site_1.id),
            "status": "Activo",
            "ensure_dentist_profile": False,
        },
    )
    assert_denied(denied_cross_company)
    assert_no_tenant_b_leak(denied_cross_company, tenant_b)

    platform_role_id = _role_id(db_session, tenant_a.company.id, "PLATFORM_ADMIN")
    denied_platform_role = api_client.patch(
        f"/api/platform/companies/{tenant_a.company.id}/users/{tenant_a.secretary.user.id}/roles",
        token=security_world.platform_admin.token,
        json={
            "role_ids": [platform_role_id],
            "site_ids": [str(tenant_a.site_1.id)],
            "default_site_id": str(tenant_a.site_1.id),
            "status": "Activo",
            "ensure_dentist_profile": False,
        },
    )
    assert_denied(denied_platform_role)


def test_reports_are_tenant_scoped_financially_restricted_and_platform_denied(api_client, security_world) -> None:
    report_paths = [
        "/api/reports/executive-summary",
        "/api/reports/appointments",
        "/api/reports/patients",
        "/api/reports/treatments",
        "/api/reports/finance",
        "/api/reports/followups",
        "/api/reports/action-items",
    ]
    for path in report_paths:
        response = api_client.get(path, token=security_world.tenant_a.admin.token)
        assert response.status_code == 200, f"{path}: {response.text}"
        assert_no_tenant_b_leak(response, security_world.tenant_b)

        filtered = api_client.get(
            f"{path}?site_id={security_world.tenant_b.site_1.id}",
            token=security_world.tenant_a.admin.token,
        )
        assert filtered.status_code in {400, 403}, f"{path}: {filtered.text}"
        assert_no_tenant_b_leak(filtered, security_world.tenant_b)

    dentist_finance = api_client.get("/api/reports/finance", token=security_world.tenant_a.dentist.token)
    assert dentist_finance.status_code == 403, dentist_finance.text

    platform_finance = api_client.get("/api/reports/finance", token=security_world.platform_admin.token)
    assert platform_finance.status_code == 403, platform_finance.text
