from __future__ import annotations

from argparse import Namespace
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, Patient
from app.models.company import Company
from app.models.followup import PatientFollowup
from app.models.associations import UserRole
from app.models.role import Role
from app.cli.demo_tenant import _require_apply_confirmation
from app.services.demo_tenant_service import (
    BOGOTA,
    DATASET_VERSION,
    DEMO_COMPANY_NAME,
    DEMO_COMPANY_SLUG,
    DemoStorageTransaction,
    DemoTenantError,
    DemoTenantOrchestrator,
    audit_invariants,
    database_target,
    deterministic_id,
    require_demo_identity,
    require_platform_actor,
)
from app.services.email_service import (
    DemoEmailSink,
    EmailDelivery,
    EmailDeliveryError,
    get_email_provider,
    use_email_company,
    use_company_email_provider,
)


def test_demo_email_sink_is_exactly_company_scoped_and_redacts_secrets(monkeypatch):
    company_id = uuid4()
    other_company_id = uuid4()
    sink = DemoEmailSink("controlled@example.test")
    with use_company_email_provider(company_id, sink):
        assert get_email_provider(company_id) is sink
        assert isinstance(get_email_provider(other_company_id), type(get_email_provider()))
        with use_email_company(company_id):
            assert get_email_provider() is sink
        with use_email_company(other_company_id):
            assert get_email_provider() is not sink
        sink.send(
            EmailDelivery(
                recipient="controlled@example.test",
                subject="Código de seguridad",
                body="Código 123456 en /consentimiento/sensitive-token-value",
            )
        )
        assert sink.consume_latest_otp() == "123456"
        assert "123456" not in sink.records[0].body_redacted
        assert "sensitive-token-value" not in sink.records[0].body_redacted
    assert get_email_provider(company_id) is not sink
    with pytest.raises(EmailDeliveryError):
        sink.send(EmailDelivery("outside@example.test", "No", "No"))


def test_demo_identity_requires_uuid_slug_and_name(db_session, security_world, monkeypatch):
    company = security_world.tenant_a.company
    orchestrator = DemoTenantOrchestrator(db_session)
    assert orchestrator.status(company.id).counts == {}
    assert orchestrator.plan("reset", company.id, apply=False).counts == {}
    monkeypatch.setenv("DENTIA_DEMO_TENANT_IDS", str(company.id))
    with pytest.raises(DemoTenantError, match="Identidad demo inválida"):
        require_demo_identity(db_session, company.id)
    company.name = DEMO_COMPANY_NAME
    company.slug = DEMO_COMPANY_SLUG
    db_session.commit()
    assert require_demo_identity(db_session, company.id).id == company.id
    monkeypatch.setenv("DENTIA_DEMO_TENANT_IDS", str(uuid4()))
    with pytest.raises(DemoTenantError, match="allowlist"):
        require_demo_identity(db_session, company.id)


def test_apply_requires_database_and_production_specific_confirmations(monkeypatch):
    company_id = uuid4()
    args = Namespace(
        command="update",
        company_id=company_id,
        confirm_database_target=None,
        confirm_environment=None,
        confirm_tenant=None,
        confirm_reset=None,
        backup_reference=None,
    )
    with pytest.raises(DemoTenantError, match="confirm-database-target"):
        _require_apply_confirmation(args)

    args.confirm_database_target = database_target()
    monkeypatch.setattr("app.cli.demo_tenant.is_production_target", lambda: True)
    with pytest.raises(DemoTenantError, match="confirm-environment"):
        _require_apply_confirmation(args)
    args.confirm_environment = "PRODUCTION"
    args.confirm_tenant = str(company_id)
    _require_apply_confirmation(args)

    args.command = "reset"
    args.confirm_reset = f"RESET CLINICA DENTAL AURORA {company_id}"
    with pytest.raises(DemoTenantError, match="backup-reference"):
        _require_apply_confirmation(args)
    args.backup_reference = "verified-backup-reference"
    _require_apply_confirmation(args)


def test_deterministic_ids_are_stable_and_tenant_specific():
    first = uuid4()
    second = uuid4()
    assert deterministic_id(first, "patient", "mariana") == deterministic_id(first, "patient", "mariana")
    assert deterministic_id(first, "patient", "mariana") != deterministic_id(second, "patient", "mariana")
    assert DATASET_VERSION == "aurora-v1"


def test_storage_transaction_only_touches_exact_tenant_directory(tmp_path, monkeypatch):
    company_id = uuid4()
    other_id = uuid4()
    monkeypatch.setattr("app.services.demo_tenant_service.settings.branding_storage_dir", str(tmp_path / "branding"))
    monkeypatch.setattr("app.services.demo_tenant_service.settings.consent_final_storage_dir", str(tmp_path / "consents"))
    own = tmp_path / "branding" / str(company_id)
    other = tmp_path / "branding" / str(other_id)
    own.mkdir(parents=True)
    other.mkdir(parents=True)
    (own / "own.txt").write_text("demo")
    (other / "other.txt").write_text("tenant")
    storage = DemoStorageTransaction(company_id)
    storage.snapshot()
    storage.quarantine()
    assert not own.exists()
    assert other.exists()
    storage.rollback()
    assert (own / "own.txt").read_text() == "demo"
    assert (other / "other.txt").read_text() == "tenant"

    storage = DemoStorageTransaction(company_id)
    storage.snapshot()
    (own / "generated.pdf").write_bytes(b"synthetic")
    storage.rollback()
    assert (own / "own.txt").read_text() == "demo"
    assert not (own / "generated.pdf").exists()
    assert (other / "other.txt").read_text() == "tenant"


def test_aurora_create_update_and_reset_are_idempotent(
    db_session,
    security_world,
    monkeypatch,
):
    actor = require_platform_actor(db_session, security_world.platform_admin.user.id)
    orchestrator = DemoTenantOrchestrator(db_session)
    anchor = date(2026, 8, 3)
    planned_counts = orchestrator.plan("create", None, apply=False).counts
    created = orchestrator.create(
        actor,
        admin_email="valentina.aurora@example.test",
        admin_password="Aurora-Test-Password-Only-2026!",
        sink_recipient="controlled-demo@example.test",
        anchor=anchor,
    )
    assert created.found and created.name == DEMO_COMPANY_NAME
    assert created.counts == planned_counts
    assert created.counts["users"] == 3
    assert created.counts["patients"] == 14
    assert created.counts["followups"] == 17
    assert created.counts["consents"] == 4
    assert created.counts["payments"] == 2
    assert created.counts["documents"] == 1
    assert db_session.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.company_id == created.company_id, Role.code == "PLATFORM_ADMIN")
    ) == 0

    monkeypatch.setenv("DENTIA_DEMO_TENANT_IDS", str(created.company_id))
    before = dict(created.counts)
    second_create = orchestrator.create(
        actor,
        admin_email="valentina.aurora@example.test",
        admin_password="Aurora-Test-Password-Only-2026!",
        sink_recipient="controlled-demo@example.test",
        anchor=anchor,
    )
    assert second_create.company_id == created.company_id
    assert second_create.counts == before
    updated = orchestrator.update(
        actor,
        created.company_id,
        admin_password=None,
        sink_recipient="controlled-demo@example.test",
        anchor=anchor,
    )
    assert updated.counts == before
    assert orchestrator.status(created.company_id).counts == before
    company = db_session.get(Company, created.company_id)
    assert audit_invariants(db_session, company)

    followups = list(
        db_session.scalars(
            select(PatientFollowup).where(PatientFollowup.company_id == company.id)
        )
    )
    assert sum(item.followup_date < anchor and item.status == "Pendiente" for item in followups) == 2
    assert sum(
        item.status == "Cita programada" and item.scheduled_appointment_id is not None
        for item in followups
    ) == 5
    week_start = anchor - timedelta(days=anchor.weekday())
    week_end = week_start + timedelta(days=5)
    weekly = list(
        db_session.scalars(
            select(Appointment).where(
                Appointment.company_id == company.id,
                Appointment.starts_at >= datetime.combine(week_start, datetime.min.time(), BOGOTA),
                Appointment.starts_at < datetime.combine(week_end, datetime.min.time(), BOGOTA),
            )
        )
    )
    assert len(weekly) >= 20

    reset_status, deleted = orchestrator.reset(
        actor,
        company.id,
        sink_recipient="controlled-demo@example.test",
        anchor=anchor + timedelta(days=7),
    )
    assert deleted["pacientes"] == 14
    assert reset_status.counts == before
    assert db_session.scalar(select(func.count()).select_from(Patient).where(Patient.company_id == company.id)) == 14


def test_demo_cross_tenant_reference_is_detected(db_session, security_world, monkeypatch):
    actor = require_platform_actor(db_session, security_world.platform_admin.user.id)
    status = DemoTenantOrchestrator(db_session).create(
        actor,
        admin_email="valentina.isolation@example.test",
        admin_password="Aurora-Isolation-Test-Only-2026!",
        sink_recipient="controlled-isolation@example.test",
        anchor=date(2026, 8, 3),
    )
    company = db_session.get(Company, status.company_id)
    monkeypatch.setenv("DENTIA_DEMO_TENANT_IDS", str(company.id))
    appointment = db_session.scalar(
        select(Appointment).where(Appointment.company_id == company.id)
    )
    appointment.patient_id = security_world.tenant_b.patient.id
    db_session.commit()
    with pytest.raises(DemoTenantError, match="cross-tenant"):
        audit_invariants(db_session, company)


def test_failed_create_rolls_back_database_and_generated_storage(
    db_session,
    security_world,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        "app.services.demo_tenant_service.settings.branding_storage_dir",
        str(tmp_path / "branding"),
    )
    monkeypatch.setattr(
        "app.services.demo_tenant_service.settings.consent_final_storage_dir",
        str(tmp_path / "consents"),
    )

    def fail_after_artifacts(*_args, **_kwargs):
        raise DemoTenantError("fallo inducido")

    monkeypatch.setattr(
        "app.services.demo_tenant_service._reconcile_document",
        fail_after_artifacts,
    )
    connection = db_session.get_bind().connect()
    transaction = connection.begin()
    isolated = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    orchestrator = DemoTenantOrchestrator(isolated)
    try:
        actor = require_platform_actor(isolated, security_world.platform_admin.user.id)
        with pytest.raises(DemoTenantError, match="fallo inducido"):
            orchestrator.create(
                actor,
                admin_email="valentina.rollback@example.test",
                admin_password="Aurora-Rollback-Test-Only-2026!",
                sink_recipient="controlled-rollback@example.test",
                anchor=date(2026, 8, 3),
            )
        transaction.rollback()
        assert orchestrator.storage_transaction is not None
        roots = orchestrator.storage_transaction.roots()
        orchestrator.storage_transaction.rollback()
    finally:
        isolated.close()
        connection.close()

    db_session.expire_all()
    assert db_session.scalar(
        select(func.count()).select_from(Company).where(Company.slug == DEMO_COMPANY_SLUG)
    ) == 0
    assert all(not root.exists() for root in roots)
