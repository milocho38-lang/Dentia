from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models.agenda import Appointment


def assert_denied(response) -> None:
    assert response.status_code in {400, 403, 404}, response.text


def test_company_a_cannot_create_appointment_for_company_b_patient(api_client, db_session, security_world) -> None:
    starts = datetime(2026, 8, 2, 14, 0, tzinfo=timezone.utc)
    before_count = db_session.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.company_id == security_world.tenant_a.company.id)
    )
    response = api_client.post(
        "/api/appointments",
        token=security_world.tenant_a.dentist_admin.token,
        json={
            "patient_id": str(security_world.tenant_b.patient.id),
            "dentist_id": str(security_world.tenant_a.dentist_profile.id),
            "site_id": str(security_world.tenant_a.site_1.id),
            "appointment_type_id": str(security_world.tenant_a.appointment_type.id),
            "starts_at": starts.isoformat(),
            "ends_at": (starts + timedelta(minutes=30)).isoformat(),
            "reason": "Intento IDOR paciente externo",
        },
    )
    assert_denied(response)
    after_count = db_session.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.company_id == security_world.tenant_a.company.id)
    )
    assert after_count == before_count


def test_company_a_cannot_create_appointment_in_company_b_site(api_client, db_session, security_world) -> None:
    starts = datetime(2026, 8, 2, 15, 0, tzinfo=timezone.utc)
    before_count = db_session.scalar(select(func.count()).select_from(Appointment))
    response = api_client.post(
        "/api/appointments",
        token=security_world.tenant_a.dentist_admin.token,
        json={
            "patient_id": str(security_world.tenant_a.patient.id),
            "dentist_id": str(security_world.tenant_a.dentist_profile.id),
            "site_id": str(security_world.tenant_b.site_1.id),
            "appointment_type_id": str(security_world.tenant_a.appointment_type.id),
            "starts_at": starts.isoformat(),
            "ends_at": (starts + timedelta(minutes=30)).isoformat(),
            "reason": "Intento IDOR sede externa",
        },
    )
    assert_denied(response)
    after_count = db_session.scalar(select(func.count()).select_from(Appointment))
    assert after_count == before_count


def test_restricted_site_user_cannot_query_unassigned_site(api_client, security_world) -> None:
    response = api_client.get(
        "/api/agenda/events",
        token=security_world.tenant_a.restricted_site_1.token,
        params={
            "starts_at": "2026-08-01T00:00:00+00:00",
            "ends_at": "2026-08-03T00:00:00+00:00",
            "site_id": str(security_world.tenant_a.site_2.id),
        },
    )
    assert_denied(response)
