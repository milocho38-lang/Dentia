from __future__ import annotations

from sqlalchemy import select

from app.models.agenda import Patient


def assert_denied(response) -> None:
    assert response.status_code in {403, 404}, response.text


def test_company_a_cannot_read_company_b_patient(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/patients/{security_world.tenant_b.patient.id}",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert_denied(response)
    assert str(security_world.tenant_b.patient.id) not in response.text
    assert "Paciente B" not in response.text


def test_company_a_patient_list_does_not_contain_company_b_data(api_client, security_world) -> None:
    response = api_client.get("/api/patients", token=security_world.tenant_a.dentist_admin.token)
    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = response.text
    assert str(security_world.tenant_a.patient.id) in serialized
    assert str(security_world.tenant_b.patient.id) not in serialized
    assert all("Paciente B" not in item["full_name"] for item in payload["items"])


def test_company_a_cannot_update_company_b_patient(api_client, db_session, security_world) -> None:
    before = db_session.scalar(select(Patient).where(Patient.id == security_world.tenant_b.patient.id))
    before_updated_at = before.updated_at
    before_mobile = before.mobile

    response = api_client.patch(
        f"/api/patients/{security_world.tenant_b.patient.id}",
        token=security_world.tenant_a.dentist_admin.token,
        json={
            "first_names": "Paciente B Modificado",
            "last_names": "Seguridad",
            "document_type": "CC",
            "document": "B0001",
            "mobile": "+573111111111",
            "birth_date": "1990-01-01",
            "sex": "no informa",
            "acknowledge_duplicate_warning": True,
        },
    )
    assert_denied(response)
    db_session.expire_all()
    after = db_session.scalar(select(Patient).where(Patient.id == security_world.tenant_b.patient.id))
    assert after.mobile == before_mobile
    assert after.updated_at == before_updated_at


def test_secretary_without_deactivate_permission_cannot_deactivate_patient(api_client, security_world) -> None:
    response = api_client.post(
        f"/api/patients/{security_world.tenant_a.patient.id}/deactivate",
        token=security_world.tenant_a.secretary.token,
    )
    assert response.status_code == 403, response.text
