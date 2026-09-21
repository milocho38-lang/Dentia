from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security_catalog import ROLES
from app.models.audit_event import AuditEvent
from app.models.demo_request import DemoRequest, DemoRequestNote
from app.services.demo_request_service import reset_demo_request_throttle_for_tests
from app.services.email_service import (
    EmailDeliveryError,
    EmailProvider,
    get_test_email_outbox,
)


@pytest.fixture(autouse=True)
def reset_public_demo_request_state(monkeypatch):
    reset_demo_request_throttle_for_tests()
    get_test_email_outbox().clear()
    monkeypatch.setattr(settings, "demo_request_notification_emails", "")
    monkeypatch.setattr(settings, "demo_request_from_email", None)


def _payload(**overrides):
    payload = {
        "first_name": "Ana",
        "last_name": "Demo",
        "email": "ANA.DEMO@example.test",
        "phone": "+56900000000",
        "country": "CL",
        "city": "Santiago",
        "practice_type": "DENTAL_CLINIC",
        "dentist_count": 3,
        "message": "Quiero conocer el flujo para mi clínica.",
        "privacy_consent": True,
        "company_website": None,
    }
    payload.update(overrides)
    return payload


def _create(api_client, **overrides):
    return api_client.post(
        "/api/public/demo-requests",
        json=_payload(**overrides),
        headers={"x-forwarded-for": "203.0.113.20", "user-agent": "dentia-web-test"},
    )


def test_public_request_requires_consent_validates_and_sanitizes(
    api_client, db_session
) -> None:
    denied = _create(api_client, privacy_consent=False)
    assert denied.status_code == 422
    assert denied.json()["detail"]["code"] == "DEMO_REQUEST_INVALID"
    assert db_session.scalar(select(DemoRequest)) is None

    invalid = _create(api_client, dentist_count=0)
    assert invalid.status_code == 422

    created = _create(
        api_client,
        first_name="  Ana <strong>Demo</strong>  ",
        message="Consulta <script>alert(1)</script>\n sin datos clínicos",
    )
    assert created.status_code == 201, created.text
    assert created.headers["cache-control"] == "no-store, max-age=0"
    assert set(created.json()) == {"accepted", "message"}
    db_session.expire_all()
    item = db_session.scalar(select(DemoRequest))
    assert item is not None
    assert item.first_name == "Ana Demo"
    assert item.normalized_email == "ana.demo@example.test"
    assert "<script>" not in (item.message or "")
    assert item.consent_at is not None
    assert item.consent_version == "DENTIA_PRIVACY_POLICY_V1"
    assert item.status == "NEW"
    assert item.notification_status == "NOT_CONFIGURED"


def test_honeypot_and_immediate_duplicate_do_not_create_extra_leads(
    api_client, db_session
) -> None:
    honeypot = _create(api_client, company_website="https://spam.example")
    assert honeypot.status_code == 201
    assert db_session.scalar(select(DemoRequest)) is None

    first = _create(api_client)
    second = _create(api_client)
    assert first.status_code == second.status_code == 201
    db_session.expire_all()
    assert len(db_session.scalars(select(DemoRequest)).all()) == 1


def test_public_rate_limit_is_backend_enforced_without_persisting_ip(
    api_client, db_session, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "demo_request_rate_limit_max", 2)
    for index in range(2):
        response = _create(
            api_client,
            email=f"lead-{index}@example.test",
            first_name=f"Ana {index}",
        )
        assert response.status_code == 201
    limited = _create(api_client, email="lead-3@example.test", first_name="Ana 3")
    assert limited.status_code == 429
    assert limited.json()["detail"]["code"] == "DEMO_REQUEST_RATE_LIMITED"
    db_session.expire_all()
    assert len(db_session.scalars(select(DemoRequest)).all()) == 2
    public_audit = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "DEMO_REQUEST_CREATED")
    ).all()
    assert public_audit
    assert all(event.ip_address is None and event.user_agent is None for event in public_audit)


def test_internal_notification_is_configurable_and_failure_never_loses_lead(
    api_client, db_session, monkeypatch
) -> None:
    monkeypatch.setattr(
        settings,
        "demo_request_notification_emails",
        "ventas@example.test, socia@example.test",
    )
    sent = _create(api_client)
    assert sent.status_code == 201
    outbox = get_test_email_outbox()
    assert [delivery.recipient for delivery in outbox] == [
        "ventas@example.test",
        "socia@example.test",
    ]
    assert all("Ana Demo" in delivery.body for delivery in outbox)
    db_session.expire_all()
    item = db_session.scalar(select(DemoRequest))
    assert item is not None and item.notification_status == "SENT"

    class FailingProvider(EmailProvider):
        def send(self, delivery):
            raise EmailDeliveryError("simulated")

    monkeypatch.setattr(
        "app.services.demo_request_service.get_email_provider",
        lambda: FailingProvider(),
    )
    failed = _create(
        api_client,
        email="carlos.demo@example.test",
        first_name="Carlos",
        country="CO",
        city="Bogotá",
        practice_type="INDEPENDENT_DENTIST",
        dentist_count=1,
    )
    assert failed.status_code == 201
    db_session.expire_all()
    failed_item = db_session.scalar(
        select(DemoRequest).where(
            DemoRequest.normalized_email == "carlos.demo@example.test"
        )
    )
    assert failed_item is not None
    assert failed_item.notification_status == "FAILED"
    assert failed_item.notification_error_code == "DELIVERY_FAILED"


def test_platform_list_detail_assignment_schedule_notes_and_conversion(
    api_client, db_session, security_world
) -> None:
    assert _create(api_client).status_code == 201
    db_session.expire_all()
    item = db_session.scalar(select(DemoRequest))
    assert item is not None

    unauthenticated = api_client.get("/api/platform/demo-requests")
    assert unauthenticated.status_code == 401
    tenant_denied = api_client.get(
        "/api/platform/demo-requests", token=security_world.tenant_a.admin.token
    )
    assert tenant_denied.status_code == 403

    listing = api_client.get(
        "/api/platform/demo-requests?status=NEW&country=CL&search=ana",
        token=security_world.platform_admin.token,
    )
    assert listing.status_code == 200, listing.text
    assert listing.headers["cache-control"] == "no-store, max-age=0"
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == str(item.id)

    detail = api_client.get(
        f"/api/platform/demo-requests/{item.id}",
        token=security_world.platform_admin.token,
    )
    assert detail.status_code == 200
    row_version = detail.json()["row_version"]

    invalid_owner = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/assignment",
        token=security_world.platform_admin.token,
        json={
            "assigned_to_user_id": str(security_world.tenant_a.admin.user.id),
            "row_version": row_version,
        },
    )
    assert invalid_owner.status_code == 422

    assigned = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/assignment",
        token=security_world.platform_admin.token,
        json={
            "assigned_to_user_id": str(security_world.platform_admin.user.id),
            "row_version": row_version,
        },
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["assigned_to"]["id"] == str(
        security_world.platform_admin.user.id
    )

    contacted = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "CONTACTED",
            "reason": "Contacto inicial por correo.",
            "row_version": assigned.json()["row_version"],
        },
    )
    assert contacted.status_code == 200, contacted.text
    assert contacted.json()["contacted_at"] is not None

    scheduled_at = datetime.now(timezone.utc) + timedelta(days=2)
    scheduled_local = scheduled_at.astimezone(ZoneInfo("America/Santiago")).replace(
        tzinfo=None, microsecond=0
    )
    scheduled = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/schedule",
        token=security_world.platform_admin.token,
        json={
            "scheduled_at": scheduled_local.isoformat(),
            "timezone": "America/Santiago",
            "meeting_url": "https://meet.example.test/demo",
            "assigned_to_user_id": str(security_world.platform_admin.user.id),
            "note": "Demo coordinada con datos sintéticos.",
            "row_version": contacted.json()["row_version"],
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    assert scheduled.json()["status"] == "DEMO_SCHEDULED"
    assert scheduled.json()["timezone"] == "America/Santiago"
    persisted_schedule = datetime.fromisoformat(
        scheduled.json()["scheduled_at"].replace("Z", "+00:00")
    )
    assert persisted_schedule == scheduled_local.replace(
        tzinfo=ZoneInfo("America/Santiago")
    )

    noted = api_client.post(
        f"/api/platform/demo-requests/{item.id}/notes",
        token=security_world.platform_admin.token,
        json={
            "text": "Próximo paso: revisar usuarios y sedes.",
            "row_version": scheduled.json()["row_version"],
        },
    )
    assert noted.status_code == 200, noted.text
    assert len(noted.json()["notes"]) == 3
    assert noted.json()["notes"][0]["author"]["id"] == str(
        security_world.platform_admin.user.id
    )

    completed = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "DEMO_COMPLETED",
            "row_version": noted.json()["row_version"],
        },
    )
    assert completed.status_code == 200
    converted = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "CONVERTED",
            "reason": "Decisión comercial registrada.",
            "row_version": completed.json()["row_version"],
        },
    )
    assert converted.status_code == 200, converted.text
    assert converted.json()["converted_at"] is not None

    stale = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/assignment",
        token=security_world.platform_admin.token,
        json={"assigned_to_user_id": None, "row_version": row_version},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "DEMO_REQUEST_VERSION_CONFLICT"

    db_session.expire_all()
    assert len(
        db_session.scalars(
            select(DemoRequestNote).where(DemoRequestNote.demo_request_id == item.id)
        ).all()
    ) == 4
    actions = {
        event.action
        for event in db_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == item.id)
        )
    }
    assert {
        "DEMO_REQUEST_CREATED",
        "DEMO_REQUEST_ASSIGNED",
        "DEMO_REQUEST_STATUS_CHANGED",
        "DEMO_REQUEST_SCHEDULED",
        "DEMO_REQUEST_NOTE_ADDED",
        "DEMO_REQUEST_CONVERTED",
    } <= actions
    for event in db_session.scalars(
        select(AuditEvent).where(AuditEvent.entity_id == item.id)
    ):
        serialized = str(event.detail or {})
        assert "ana.demo@example.test" not in serialized
        assert "+56900000000" not in serialized


def test_platform_exact_contact_schedule_note_and_close_workflow(
    api_client, db_session, security_world
) -> None:
    assert _create(
        api_client,
        email="ana.web4c1@example.test",
        message="Solicitud sintética WEB-4C.1",
    ).status_code == 201
    db_session.expire_all()
    item = db_session.scalar(
        select(DemoRequest).where(
            DemoRequest.normalized_email == "ana.web4c1@example.test"
        )
    )
    assert item is not None and item.status == "NEW"

    detail = api_client.get(
        f"/api/platform/demo-requests/{item.id}",
        token=security_world.platform_admin.token,
    )
    assigned = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/assignment",
        token=security_world.platform_admin.token,
        json={
            "assigned_to_user_id": str(security_world.platform_admin.user.id),
            "row_version": detail.json()["row_version"],
        },
    )
    assert assigned.status_code == 200, assigned.text

    contacted = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "CONTACTED",
            "reason": None,
            "row_version": assigned.json()["row_version"],
        },
    )
    assert contacted.status_code == 200, contacted.text
    assert contacted.json()["status"] == "CONTACTED"
    contacted_at = contacted.json()["contacted_at"]
    assert contacted_at is not None

    scheduled_local = (
        datetime.now(timezone.utc) + timedelta(days=2)
    ).astimezone(ZoneInfo("America/Santiago")).replace(tzinfo=None, microsecond=0)
    scheduled = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/schedule",
        token=security_world.platform_admin.token,
        json={
            "scheduled_at": scheduled_local.isoformat(),
            "timezone": "America/Santiago",
            "meeting_url": None,
            "assigned_to_user_id": str(security_world.platform_admin.user.id),
            "note": None,
            "row_version": contacted.json()["row_version"],
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    assert scheduled.json()["status"] == "DEMO_SCHEDULED"
    assert scheduled.json()["contacted_at"] == contacted_at

    noted = api_client.post(
        f"/api/platform/demo-requests/{item.id}/notes",
        token=security_world.platform_admin.token,
        json={
            "text": "Prueba sintética WEB-4C",
            "row_version": scheduled.json()["row_version"],
        },
    )
    assert noted.status_code == 200, noted.text
    assert [note["text"] for note in noted.json()["notes"]] == [
        "Prueba sintética WEB-4C"
    ]

    completed = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "DEMO_COMPLETED",
            "reason": None,
            "row_version": noted.json()["row_version"],
        },
    )
    assert completed.status_code == 200, completed.text

    closed = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "NOT_CONTINUING",
            "reason": "Lead sintético de validación WEB-4C",
            "row_version": completed.json()["row_version"],
        },
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "NOT_CONTINUING"
    assert closed.json()["contacted_at"] == contacted_at
    assert closed.json()["assigned_to"]["id"] == str(
        security_world.platform_admin.user.id
    )
    assert closed.json()["timezone"] == "America/Santiago"

    db_session.expire_all()
    persisted = db_session.get(DemoRequest, item.id)
    assert persisted is not None
    assert persisted.status == "NOT_CONTINUING"
    assert persisted.contacted_at is not None
    assert persisted.assigned_to_user_id == security_world.platform_admin.user.id
    assert persisted.timezone == "America/Santiago"

    notes = db_session.scalars(
        select(DemoRequestNote)
        .where(DemoRequestNote.demo_request_id == item.id)
        .order_by(DemoRequestNote.created_at, DemoRequestNote.id)
    ).all()
    assert {note.text for note in notes} == {
        "Prueba sintética WEB-4C",
        "Lead sintético de validación WEB-4C",
    }
    assert len(notes) == 2
    assert all(
        note.author_user_id == security_world.platform_admin.user.id
        and note.created_at is not None
        for note in notes
    )

    events = db_session.scalars(
        select(AuditEvent).where(AuditEvent.entity_id == item.id)
    ).all()
    actions = {event.action for event in events}
    assert {
        "DEMO_REQUEST_CREATED",
        "DEMO_REQUEST_ASSIGNED",
        "DEMO_REQUEST_STATUS_CHANGED",
        "DEMO_REQUEST_SCHEDULED",
        "DEMO_REQUEST_NOTE_ADDED",
        "DEMO_REQUEST_CLOSED",
    } <= actions
    transitions = {
        (
            (event.detail or {}).get("previous_status"),
            (event.detail or {}).get("new_status"),
        )
        for event in events
        if event.action in {
            "DEMO_REQUEST_STATUS_CHANGED",
            "DEMO_REQUEST_SCHEDULED",
            "DEMO_REQUEST_CLOSED",
        }
    }
    assert {
        ("NEW", "CONTACTED"),
        ("CONTACTED", "DEMO_SCHEDULED"),
        ("DEMO_SCHEDULED", "DEMO_COMPLETED"),
        ("DEMO_COMPLETED", "NOT_CONTINUING"),
    } <= transitions


def test_not_continuing_and_rbac_catalog_are_platform_only(
    api_client, db_session, security_world
) -> None:
    role_permissions = {
        role.code: set(role.permission_codes)
        for role in ROLES
    }
    expected = {"platform.demo_requests.view", "platform.demo_requests.manage"}
    assert expected <= role_permissions["PLATFORM_ADMIN"]
    for role in ("ADMINISTRATOR", "DENTIST_ADMIN", "DENTIST", "SECRETARY"):
        assert not expected.intersection(role_permissions[role])

    assert _create(
        api_client,
        first_name="Carlos",
        last_name="Demo",
        email="carlos.demo@example.test",
        country="CO",
        city="Bogotá",
        practice_type="INDEPENDENT_DENTIST",
        dentist_count=1,
    ).status_code == 201
    db_session.expire_all()
    item = db_session.scalar(
        select(DemoRequest).where(
            DemoRequest.normalized_email == "carlos.demo@example.test"
        )
    )
    closed = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.platform_admin.token,
        json={
            "status": "NOT_CONTINUING",
            "reason": "No es el momento.",
            "row_version": item.row_version,
        },
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "NOT_CONTINUING"
    assert closed.json()["notes"][0]["text"] == "No es el momento."

    tenant_manage_denied = api_client.patch(
        f"/api/platform/demo-requests/{item.id}/status",
        token=security_world.tenant_a.dentist_admin.token,
        json={
            "status": "CONTACTED",
            "row_version": closed.json()["row_version"],
        },
    )
    assert tenant_manage_denied.status_code == 403
