from __future__ import annotations


def test_restricted_site_user_sees_only_authorized_site_in_agenda_options(api_client, security_world) -> None:
    response = api_client.get("/api/agenda/options", token=security_world.tenant_a.restricted_site_1.token)
    assert response.status_code == 200, response.text
    payload = response.json()
    site_ids = {item["id"] for item in payload["sites"]}
    assert str(security_world.tenant_a.site_1.id) in site_ids
    assert str(security_world.tenant_a.site_2.id) not in site_ids
    assert str(security_world.tenant_b.site_1.id) not in site_ids


def test_secretary_cannot_access_clinical_sensitive_record(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/patients/{security_world.tenant_a.patient.id}/clinical-record",
        token=security_world.tenant_a.secretary.token,
    )
    assert response.status_code == 403, response.text
