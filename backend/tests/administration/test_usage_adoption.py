from datetime import date, datetime, timedelta, timezone

from sqlalchemy import event

from app.core.security_catalog import ROLES
from app.models.agenda import Appointment, AppointmentHistory
from app.models.audit_event import AuditEvent
from app.models.orthodontics import OrthodonticCase, OrthodonticEvolution
from app.services.usage_adoption_service import (
    get_user_usage_adoption,
    resolve_usage_dates,
)


def _url(company_id, user_id, **params) -> str:
    query = {
        "company_id": company_id,
        "start_date": "2026-08-01",
        "end_date": "2026-09-30",
        **params,
    }
    return "/api/platform/usage/users/{}?{}".format(
        user_id,
        "&".join(f"{key}={value}" for key, value in query.items()),
    )


def test_usage_permission_is_platform_only() -> None:
    role_permissions = {
        definition.code: definition.permission_codes for definition in ROLES
    }
    assert "platform.usage.view" in role_permissions["PLATFORM_ADMIN"]
    for role_code in (
        "ADMINISTRATOR",
        "DENTIST_ADMIN",
        "DENTIST",
        "SECRETARY",
    ):
        assert "platform.usage.view" not in role_permissions[role_code]


def test_platform_usage_endpoint_rbac_cross_company_and_no_store(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    url = _url(tenant.company.id, tenant.dentist_admin.user.id)

    assert api_client.get(url).status_code == 401
    for actor in (
        tenant.admin,
        tenant.dentist_admin,
        tenant.dentist,
        tenant.secretary,
    ):
        assert api_client.get(url, token=actor.token).status_code == 403

    allowed = api_client.get(url, token=security_world.platform_admin.token)
    assert allowed.status_code == 200, allowed.text
    assert allowed.headers["cache-control"] == "no-store, max-age=0"
    assert allowed.json()["company_id"] == str(tenant.company.id)
    assert allowed.json()["user_id"] == str(tenant.dentist_admin.user.id)

    crossed = api_client.get(
        _url(tenant.company.id, security_world.tenant_b.dentist_admin.user.id),
        token=security_world.platform_admin.token,
    )
    assert crossed.status_code == 404


def test_usage_context_is_platform_only_minimal_and_no_store(
    api_client, security_world
) -> None:
    url = (
        "/api/platform/usage/context?company_id="
        f"{security_world.tenant_a.company.id}"
    )
    assert api_client.get(url).status_code == 401
    for actor in (
        security_world.tenant_a.admin,
        security_world.tenant_a.dentist_admin,
        security_world.tenant_a.dentist,
        security_world.tenant_a.secretary,
    ):
        assert api_client.get(url, token=actor.token).status_code == 403

    response = api_client.get(url, token=security_world.platform_admin.token)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store, max-age=0"
    payload = response.json()
    company = next(
        item
        for item in payload["companies"]
        if item["id"] == str(security_world.tenant_a.company.id)
    )
    assert company["timezone"] == security_world.tenant_a.company.timezone
    user = next(
        item
        for item in company["users"]
        if item["id"] == str(security_world.tenant_a.dentist_admin.user.id)
    )
    assert user["dentist"]["id"] == str(
        security_world.tenant_a.dentist_profile.id
    )
    assert user["role_names"]
    assert {item["id"] for item in company["sites"]} >= {
        str(security_world.tenant_a.site_1.id)
    }

    forbidden_keys = {
        "email",
        "phone",
        "document",
        "patient_id",
        "diagnosis",
        "clinical_text",
        "amount",
        "ip_address",
        "user_agent",
    }

    def walk(value):
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    assert security_world.tenant_a.dentist_admin.user.email not in response.text


def test_appointment_attribution_uses_actor_not_assigned_dentist(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    secretary = tenant.secretary.user
    assigned_dentist = tenant.dentist_profile
    base = datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)
    for index in range(10):
        appointment = Appointment(
            company_id=tenant.company.id,
            patient_id=tenant.patient.id,
            dentist_id=assigned_dentist.id,
            site_id=tenant.site_1.id,
            appointment_type_id=tenant.appointment_type.id,
            starts_at=base + timedelta(days=index),
            ends_at=base + timedelta(days=index, minutes=30),
            reason="Cita sintética de atribución",
            status="Confirmada",
            created_by=secretary.id,
            updated_by=secretary.id,
            created_at=base + timedelta(days=index),
            updated_at=base + timedelta(days=index),
        )
        db_session.add(appointment)
        db_session.flush()
        db_session.add(
            AppointmentHistory(
                company_id=tenant.company.id,
                appointment_id=appointment.id,
                previous_status="Programada",
                new_status="Confirmada",
                user_id=secretary.id,
                created_at=base + timedelta(days=index, minutes=1),
                updated_at=base + timedelta(days=index, minutes=1),
            )
        )
    db_session.commit()

    secretary_result = api_client.get(
        _url(tenant.company.id, secretary.id),
        token=security_world.platform_admin.token,
    )
    assert secretary_result.status_code == 200, secretary_result.text
    assert secretary_result.json()["agenda"]["appointments_created"] == 10
    assert (
        secretary_result.json()["agenda"]["appointments_confirmed_by_actor"] == 10
    )
    assert (
        secretary_result.json()["agenda"][
            "unique_patients_with_appointment_activity"
        ]
        == 1
    )

    dentist_result = api_client.get(
        _url(tenant.company.id, tenant.dentist_admin.user.id),
        token=security_world.platform_admin.token,
    )
    assert dentist_result.status_code == 200, dentist_result.text
    assert dentist_result.json()["agenda"]["appointments_created"] == 1
    assert dentist_result.json()["agenda"]["appointments_confirmed_by_actor"] == 0


def test_clinical_financial_orthodontic_counts_and_privacy(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    actor = tenant.dentist_admin.user
    orthodontic_case = OrthodonticCase(
        company_id=tenant.company.id,
        patient_id=tenant.patient.id,
        clinical_record_id=tenant.clinical_record.id,
        primary_site_id=tenant.site_1.id,
        responsible_dentist_id=tenant.dentist_profile.id,
        status="DRAFT",
        created_by_user_id=actor.id,
        created_at=datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(orthodontic_case)
    db_session.flush()
    db_session.add(
        OrthodonticEvolution(
            company_id=tenant.company.id,
            orthodontic_case_id=orthodontic_case.id,
            clinical_evolution_id=tenant.evolution.id,
            created_at=datetime(2026, 9, 12, 12, 5, tzinfo=timezone.utc),
            updated_at=datetime(2026, 9, 12, 12, 5, tzinfo=timezone.utc),
        )
    )
    db_session.add(
        AuditEvent(
            company_id=tenant.company.id,
            user_id=actor.id,
            entity="clinical_evolution",
            entity_id=tenant.evolution.id,
            action="CLINICAL_EVOLUTION_SIGNED",
            result="SUCCESS",
            detail={"patient_name": "Paciente privado", "clinical_text": "Secreto"},
            ip_address="203.0.113.10",
            user_agent="sensitive-test-agent",
            occurred_at=datetime(2026, 9, 12, 12, 10, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    response = api_client.get(
        _url(tenant.company.id, actor.id),
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["clinical"]["clinical_evolutions_signed"] == 1
    assert payload["administrative_activity"]["payments_registered"] == 1
    assert payload["orthodontics"]["orthodontic_cases_created"] == 1
    assert payload["orthodontics"]["orthodontic_evolutions_created"] == 1
    assert payload["patients"]["unique_patients_with_actor_activity"] == 1
    assert payload["general"]["active_days"] == 1

    serialized = response.text
    forbidden_keys = {
        "patient_id",
        "patient_name",
        "document",
        "diagnosis",
        "evolution_text",
        "consent_content",
        "amount",
        "ip_address",
        "user_agent",
    }

    def walk(value):
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    assert tenant.patient.first_names not in serialized
    assert tenant.patient.last_names not in serialized
    assert (tenant.patient.document or "SENSITIVE-DOCUMENT") not in serialized
    assert "25000" not in serialized
    assert "Paciente privado" not in serialized
    assert "sensitive-test-agent" not in serialized


def test_payment_is_attributed_to_registering_admin_not_assigned_dentist(
    db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.payment.registered_by = tenant.admin.user.id
    tenant.payment.paid_at = datetime(2026, 9, 14, 14, 0, tzinfo=timezone.utc)
    db_session.commit()

    admin_metrics = get_user_usage_adoption(
        db_session,
        company_id=tenant.company.id,
        user_id=tenant.admin.user.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )
    dentist_metrics = get_user_usage_adoption(
        db_session,
        company_id=tenant.company.id,
        user_id=tenant.dentist_admin.user.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )
    assert admin_metrics.administrative_activity.payments_registered == 1
    assert dentist_metrics.administrative_activity.payments_registered == 0


def test_date_boundaries_presets_and_query_count(db_session, security_world) -> None:
    tenant = security_world.tenant_a
    actor = tenant.secretary.user
    before_local_day = datetime(2026, 9, 1, 4, 30, tzinfo=timezone.utc)
    inside_local_day = datetime(2026, 9, 1, 5, 30, tzinfo=timezone.utc)
    for timestamp in (before_local_day, inside_local_day):
        db_session.add(
            Appointment(
                company_id=tenant.company.id,
                patient_id=tenant.patient.id,
                dentist_id=tenant.dentist_profile.id,
                site_id=tenant.site_1.id,
                appointment_type_id=tenant.appointment_type.id,
                starts_at=timestamp + timedelta(days=1),
                ends_at=timestamp + timedelta(days=1, minutes=30),
                reason="Límite horario sintético",
                status="Programada",
                created_by=actor.id,
                updated_by=actor.id,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
    db_session.commit()

    assert resolve_usage_dates(
        start_date=None,
        end_date=None,
        preset="last_7_days",
        today=date(2026, 9, 21),
    )[:2] == (date(2026, 9, 15), date(2026, 9, 21))
    assert resolve_usage_dates(
        start_date=None,
        end_date=None,
        preset="last_30_days",
        today=date(2026, 9, 21),
    )[:2] == (date(2026, 8, 23), date(2026, 9, 21))

    statements = 0

    def count_queries(*_args, **_kwargs):
        nonlocal statements
        statements += 1

    connection = db_session.get_bind()
    event.listen(connection, "before_cursor_execute", count_queries)
    try:
        result = get_user_usage_adoption(
            db_session,
            company_id=tenant.company.id,
            user_id=actor.id,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 1),
        )
    finally:
        event.remove(connection, "before_cursor_execute", count_queries)
    assert result.agenda.appointments_created == 1
    assert result.period.start_at == datetime(2026, 9, 1, 5, 0, tzinfo=timezone.utc)
    assert statements <= 32
