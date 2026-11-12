from __future__ import annotations


def test_odontogram_readiness_is_authenticated_tenant_and_site_scoped(
    api_client, db_session, security_world
) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    treatment = tenant_a.treatment
    treatment.main_site_id = tenant_a.site_2.id
    db_session.commit()
    endpoint = f"/api/treatments/{treatment.id}/odontogram-readiness"

    allowed = api_client.get(endpoint, token=tenant_a.admin.token)
    assert allowed.status_code == 200, allowed.text
    assert set(allowed.json()) == {"clinical_record_exists", "odontogram_exists"}

    unauthenticated = api_client.get(endpoint)
    assert unauthenticated.status_code == 401
    assert str(tenant_a.patient.id) not in unauthenticated.text

    cross_tenant = api_client.get(endpoint, token=tenant_b.admin.token)
    assert cross_tenant.status_code == 404
    assert str(tenant_a.patient.id) not in cross_tenant.text

    wrong_site = api_client.get(endpoint, token=tenant_a.restricted_site_1.token)
    assert wrong_site.status_code == 403
    assert str(tenant_a.patient.id) not in wrong_site.text

    platform_only = api_client.get(endpoint, token=security_world.platform_admin.token)
    assert platform_only.status_code == 403
    assert str(tenant_a.patient.id) not in platform_only.text
