from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models.agenda import Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.associations import RolePermission
from app.models.clinical_record import ClinicalEvolution, ClinicalRecord
from app.models.permission import Permission
from app.models.periodontogram import (
    PeriodontalExam,
    PeriodontalExamVersion,
    PeriodontalSite,
    PeriodontalTooth,
    PeriodontogramPilotCompanyGate,
    PeriodontogramPilotDentistAuthorization,
)
from app.models.role import Role
from app.services.periodontal_clinical import (
    calculate_cal,
    calculate_periodontal_aggregates,
    is_periodontal_pocket,
)
from app.services import periodontogram_service


@pytest.fixture(autouse=True)
def _enable_default_periodontogram_pilots(db_session, security_world) -> None:
    """Keep the accumulated PERIO regression suite inside an explicit pilot."""
    for tenant in (security_world.tenant_a, security_world.tenant_b):
        db_session.add(
            PeriodontogramPilotCompanyGate(
                company_id=tenant.company.id,
                is_enabled=True,
                enabled_at=datetime.now(timezone.utc),
                enabled_by_user_id=security_world.platform_admin.user.id,
            )
        )
        db_session.add(
            PeriodontogramPilotDentistAuthorization(
                company_id=tenant.company.id,
                dentist_id=tenant.dentist_profile.id,
                authorized_at=datetime.now(timezone.utc),
                authorized_by_user_id=security_world.platform_admin.user.id,
            )
        )
    db_session.commit()


def _path(tenant) -> str:
    return f"/api/patients/{tenant.patient.id}/periodontograms"


def _create(api_client, tenant, *, token=None, site_id=None):
    payload = {"clinical_date": date.today().isoformat()}
    if site_id:
        payload["site_id"] = str(site_id)
    return api_client.post(
        _path(tenant),
        token=token or tenant.dentist_admin.token,
        json=payload,
    )


def _enable_dentist_profile(db_session, tenant) -> Dentist:
    dentist = Dentist(
        company_id=tenant.company.id,
        user_id=tenant.dentist.user.id,
        name=tenant.dentist.user.name,
        status="Activo",
        is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(dentist)
    db_session.flush()
    db_session.add(
        DentistSite(
            company_id=tenant.company.id,
            dentist_id=dentist.id,
            site_id=tenant.site_1.id,
            is_active=True,
            created_by=tenant.admin.user.id,
        )
    )
    db_session.commit()
    return dentist


def _update(api_client, tenant, exam, *, teeth=None, sites=None):
    return api_client.patch(
        f"/api/periodontograms/{exam['id']}/draft",
        token=tenant.dentist_admin.token,
        json={
            "row_version": exam["row_version"],
            "teeth": teeth or [],
            "sites": sites or [],
        },
    )


def _finalize(api_client, tenant, exam):
    return api_client.post(
        f"/api/periodontograms/{exam['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": exam["row_version"]},
    )


def _evolution(
    db_session,
    tenant,
    *,
    patient_id=None,
    clinical_record_id=None,
    site_id=None,
    text_value="Evolución sintética compatible",
):
    item = ClinicalEvolution(
        company_id=tenant.company.id,
        patient_id=patient_id or tenant.patient.id,
        clinical_record_id=clinical_record_id or tenant.clinical_record.id,
        appointment_id=None,
        site_id=site_id or tenant.site_1.id,
        dentist_id=tenant.dentist_profile.id,
        attended_at=datetime.now(timezone.utc),
        timezone_name="America/Bogota",
        evolution_text=text_value,
        status="SIGNED",
        signed_at=datetime.now(timezone.utc),
        signed_by=tenant.dentist_admin.user.id,
        created_by=tenant.dentist_admin.user.id,
        updated_by=tenant.dentist_admin.user.id,
    )
    db_session.add(item)
    db_session.commit()
    return item


def test_periodontal_cal_pocket_and_index_semantics() -> None:
    assert calculate_cal(4, -2) == 6
    assert calculate_cal(4, 2) == 2
    assert calculate_cal(None, 2) is None
    assert calculate_cal(4, None) is None
    assert is_periodontal_pocket(4) is True
    assert is_periodontal_pocket(3) is False
    aggregates = calculate_periodontal_aggregates(
        [
            {
                "state": "PRESENT",
                "sites": [
                    {"site_code": "BUCCAL_DISTAL", "probing_depth_mm": 0, "gingival_margin_mm": 0, "bleeding_on_probing": True, "plaque": None},
                    {"site_code": "BUCCAL_MID", "probing_depth_mm": None, "gingival_margin_mm": None, "bleeding_on_probing": False, "plaque": True},
                ],
            },
            {
                "state": "IMPLANT",
                "sites": [
                    {"site_code": "BUCCAL_DISTAL", "probing_depth_mm": 4, "gingival_margin_mm": -1, "bleeding_on_probing": True, "plaque": False},
                ],
            },
            {"state": "ABSENT", "sites": []},
        ]
    )
    assert aggregates["coverage"] == {
        "eligible_sites": 12,
        "evaluated_sites": 2,
        "incomplete": True,
    }
    assert aggregates["indices"]["bop"] == {
        "positive_sites": 2,
        "evaluated_sites": 3,
        "percentage": 66.67,
    }
    assert aggregates["indices"]["plaque"] == {
        "positive_sites": 1,
        "evaluated_sites": 2,
        "percentage": 50.0,
    }


def test_periodontogram_permission_matrix_is_clinical_only(
    db_session, security_world
) -> None:
    rows = db_session.execute(
        select(Role.code, Permission.code)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            Permission.code.like("periodontogram.%"),
            RolePermission.is_active.is_(True),
        )
    ).all()
    by_role: dict[str, set[str]] = {}
    for role_code, permission_code in rows:
        by_role.setdefault(role_code, set()).add(permission_code)
    clinical = {
        "periodontogram.view",
        "periodontogram.create",
        "periodontogram.update_draft",
        "periodontogram.finalize",
        "periodontogram.correct",
    }
    pilot = {
        "periodontogram.pilot.view",
        "periodontogram.pilot.manage",
    }
    assert by_role["DENTIST"] == clinical
    assert by_role["DENTIST_ADMIN"] == clinical
    assert by_role.get("ADMINISTRATOR", set()) == set()
    assert by_role.get("SECRETARY", set()) == set()
    assert by_role["PLATFORM_ADMIN"] == pilot


def test_periodontogram_pilot_company_dentist_platform_and_history_gates(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other = security_world.tenant_b
    platform_token = security_world.platform_admin.token
    pilot_path = f"/api/platform/companies/{tenant.company.id}/periodontogram-pilot"
    access_path = "/api/periodontograms/access"

    current = api_client.get(pilot_path, token=platform_token)
    assert current.status_code == 200, current.text
    assert current.json()["enabled"] is True
    authorized = {
        item["dentist_id"]: item["authorized"] for item in current.json()["dentists"]
    }
    assert authorized[str(tenant.dentist_profile.id)] is True

    access = api_client.get(access_path, token=tenant.dentist_admin.token)
    assert access.status_code == 200, access.text
    assert access.json()["allowed"] is True

    unassigned_dentist = _enable_dentist_profile(db_session, tenant)
    unassigned_access = api_client.get(access_path, token=tenant.dentist.token)
    assert unassigned_access.status_code == 200
    assert unassigned_access.json()["allowed"] is False
    assert (
        unassigned_access.json()["code"]
        == "PERIODONTOGRAM_PILOT_DENTIST_NOT_AUTHORIZED"
    )
    assert api_client.get(_path(tenant), token=tenant.dentist.token).status_code == 403

    exam = _create(api_client, tenant)
    assert exam.status_code == 201, exam.text
    exam_id = exam.json()["exam"]["id"]

    disabled = api_client.put(
        pilot_path,
        token=platform_token,
        json={"enabled": False},
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["enabled"] is False
    denied = api_client.get(access_path, token=tenant.dentist_admin.token)
    assert denied.status_code == 200
    assert denied.json()["allowed"] is False
    assert denied.json()["code"] == "PERIODONTOGRAM_PILOT_DISABLED"
    assert api_client.get(_path(tenant), token=tenant.dentist_admin.token).status_code == 403
    assert api_client.get(
        f"/api/periodontograms/{exam_id}",
        token=tenant.dentist_admin.token,
    ).status_code == 403
    assert db_session.get(PeriodontalExam, exam_id) is not None

    enabled = api_client.put(
        pilot_path,
        token=platform_token,
        json={"enabled": True},
    )
    assert enabled.status_code == 200, enabled.text
    dentist_path = (
        f"{pilot_path}/dentists/{tenant.dentist_profile.id}"
    )
    revoked = api_client.put(
        dentist_path,
        token=platform_token,
        json={"enabled": False, "reason": "Fin temporal del piloto"},
    )
    assert revoked.status_code == 200, revoked.text
    assert api_client.get(_path(tenant), token=tenant.dentist_admin.token).status_code == 403
    assert db_session.get(PeriodontalExam, exam_id) is not None

    repeated_revoke = api_client.put(
        dentist_path,
        token=platform_token,
        json={"enabled": False},
    )
    assert repeated_revoke.status_code == 200
    reauthorized = api_client.put(
        dentist_path,
        token=platform_token,
        json={"enabled": True},
    )
    assert reauthorized.status_code == 200, reauthorized.text
    assert api_client.get(_path(tenant), token=tenant.dentist_admin.token).status_code == 200

    cross_tenant = api_client.put(
        f"{pilot_path}/dentists/{other.dentist_profile.id}",
        token=platform_token,
        json={"enabled": True},
    )
    assert cross_tenant.status_code == 404
    assert api_client.put(
        pilot_path,
        token=tenant.admin.token,
        json={"enabled": False},
    ).status_code == 403
    assert api_client.get(_path(tenant), token=platform_token).status_code == 403

    actions = set(
        db_session.scalars(
            select(AuditEvent.action).where(
                AuditEvent.company_id == tenant.company.id,
                AuditEvent.action.in_(
                    (
                        "PERIODONTOGRAM_PILOT_DISABLED",
                        "PERIODONTOGRAM_PILOT_ENABLED",
                        "PERIODONTOGRAM_PILOT_DENTIST_REVOKED",
                        "PERIODONTOGRAM_PILOT_DENTIST_AUTHORIZED",
                    )
                ),
            )
        )
    )
    assert actions == {
        "PERIODONTOGRAM_PILOT_DISABLED",
        "PERIODONTOGRAM_PILOT_ENABLED",
        "PERIODONTOGRAM_PILOT_DENTIST_REVOKED",
        "PERIODONTOGRAM_PILOT_DENTIST_AUTHORIZED",
    }


def test_periodontogram_rbac_identity_site_and_tenant_boundaries(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    assert api_client.get(_path(tenant), token=tenant.dentist_admin.token).status_code == 200
    assert api_client.get(_path(tenant), token=tenant.dentist.token).status_code == 403
    assert api_client.get(_path(tenant), token=tenant.admin.token).status_code == 403
    assert api_client.get(_path(tenant), token=tenant.secretary.token).status_code == 403
    assert api_client.get(_path(tenant), token=security_world.platform_admin.token).status_code == 403

    no_identity = _create(api_client, tenant, token=tenant.dentist.token)
    assert no_identity.status_code == 403
    assert no_identity.json()["detail"]["code"] == "PERIODONTAL_DENTIST_IDENTITY_REQUIRED"
    dentist = _enable_dentist_profile(db_session, tenant)
    db_session.add(
        PeriodontogramPilotDentistAuthorization(
            company_id=tenant.company.id,
            dentist_id=dentist.id,
            authorized_at=datetime.now(timezone.utc),
            authorized_by_user_id=security_world.platform_admin.user.id,
        )
    )
    db_session.commit()
    assert _create(api_client, tenant, token=tenant.dentist.token).status_code == 201

    wrong_site = _create(api_client, tenant, site_id=tenant.site_2.id)
    assert wrong_site.status_code == 403
    assert wrong_site.json()["detail"]["code"] == "PERIODONTAL_DENTIST_SITE_DENIED"

    other = security_world.tenant_b
    assert api_client.get(_path(tenant), token=other.dentist_admin.token).status_code == 404
    exam_id = _create(api_client, tenant).json()["exam"]["id"]
    cross_tenant_detail = api_client.get(
        f"/api/periodontograms/{exam_id}", token=other.dentist_admin.token
    )
    assert cross_tenant_detail.status_code == 404
    assert exam_id not in cross_tenant_detail.text


def test_multiple_controls_are_independent_and_history_has_no_n_plus_one_contract(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    first = _create(api_client, tenant)
    second = _create(api_client, tenant)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["exam"]["id"] != second.json()["exam"]["id"]

    history = api_client.get(_path(tenant), token=tenant.dentist_admin.token)
    assert history.status_code == 200, history.text
    body = history.json()
    assert body["total"] == 2
    assert all(item["current_version_number"] == 1 for item in body["items"])
    assert all(item["professional_name"] and item["site_name"] for item in body["items"])


def test_finalize_freezes_deterministic_snapshot_hash_and_audits_identifiers_only(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    finalized = api_client.post(
        f"/api/periodontograms/{draft['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    )
    assert finalized.status_code == 200, finalized.text
    exam = finalized.json()["exam"]
    version = exam["current_version"]
    assert exam["status"] == "FINALIZED"
    assert version["status"] == "FINALIZED"
    assert version["integrity_status"] == "PASS"
    assert len(version["snapshot_hash"]) == 64
    assert version["snapshot"]["clinical_contract"] == {
        "calculation": "PD_MINUS_GM",
        "dentition": "PERMANENT",
        "gm_sign": "APICAL_NEGATIVE_CORONAL_POSITIVE",
        "pocket_visual_threshold_mm": 4,
        "sites_per_tooth": 6,
    }
    actions = list(
        db_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == draft["id"])
        )
    )
    assert {item.action for item in actions} >= {
        "PERIODONTAL_EXAM_CREATED",
        "PERIODONTAL_EXAM_FINALIZED",
        "PERIODONTAL_EXAM_VERSION_FINALIZED",
    }
    assert all("clinical_data" not in (item.detail or {}) for item in actions)


def test_correction_creates_v2_without_rewriting_finalized_v1(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    v1 = api_client.post(
        f"/api/periodontograms/{draft['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    ).json()["exam"]
    original = v1["current_version"]

    corrected = api_client.post(
        f"/api/periodontograms/{draft['id']}/correct",
        token=tenant.dentist_admin.token,
        json={"row_version": v1["row_version"], "reason": "Corrección clínica trazable"},
    )
    assert corrected.status_code == 201, corrected.text
    exam = corrected.json()["exam"]
    assert exam["status"] == "DRAFT"
    assert exam["current_version"]["version_number"] == 2
    assert exam["current_version"]["supersedes_version_id"] == original["id"]
    assert exam["current_version"]["correction_reason"] == "Corrección clínica trazable"
    assert len(exam["versions"]) == 2

    persisted_v1 = db_session.get(PeriodontalExamVersion, original["id"])
    db_session.refresh(persisted_v1)
    assert persisted_v1.status == "FINALIZED"
    assert persisted_v1.snapshot_hash == original["snapshot_hash"]
    assert persisted_v1.row_version == original["row_version"]

    finalized_v2 = api_client.post(
        f"/api/periodontograms/{draft['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": exam["row_version"]},
    )
    assert finalized_v2.status_code == 200, finalized_v2.text
    current = finalized_v2.json()["exam"]
    assert current["current_version"]["version_number"] == 2
    assert current["current_version"]["integrity_status"] == "PASS"

    persisted_exam = db_session.get(PeriodontalExam, draft["id"])
    db_session.refresh(persisted_exam)
    db_session.refresh(persisted_v1)
    immutable_before_read = {
        "snapshot_hash": persisted_v1.snapshot_hash,
        "updated_at": persisted_v1.updated_at,
        "row_version": persisted_v1.row_version,
        "current_version_id": persisted_exam.current_version_id,
        "exam_updated_at": persisted_exam.updated_at,
        "exam_row_version": persisted_exam.row_version,
    }
    audit_count_before = db_session.scalar(
        select(func.count()).select_from(AuditEvent).where(AuditEvent.entity_id == draft["id"])
    )

    historical_read = api_client.get(
        f"/api/periodontograms/{draft['id']}", token=tenant.dentist_admin.token
    )
    assert historical_read.status_code == 200, historical_read.text
    historical_versions = historical_read.json()["versions"]
    assert [item["version_number"] for item in historical_versions] == [2, 1]
    historical_v1 = next(item for item in historical_versions if item["version_number"] == 1)
    assert historical_v1["snapshot_hash"] == original["snapshot_hash"]
    assert historical_v1["snapshot"] == original["snapshot"]

    db_session.refresh(persisted_exam)
    db_session.refresh(persisted_v1)
    assert persisted_v1.snapshot_hash == immutable_before_read["snapshot_hash"]
    assert persisted_v1.updated_at == immutable_before_read["updated_at"]
    assert persisted_v1.row_version == immutable_before_read["row_version"]
    assert persisted_exam.current_version_id == immutable_before_read["current_version_id"]
    assert persisted_exam.updated_at == immutable_before_read["exam_updated_at"]
    assert persisted_exam.row_version == immutable_before_read["exam_row_version"]
    assert db_session.scalar(
        select(func.count()).select_from(AuditEvent).where(AuditEvent.entity_id == draft["id"])
    ) == audit_count_before

    second_correction = api_client.post(
        f"/api/periodontograms/{draft['id']}/correct",
        token=tenant.dentist_admin.token,
        json={"row_version": exam["row_version"], "reason": "Versión obsoleta"},
    )
    assert second_correction.status_code == 409
    assert second_correction.json()["detail"]["code"] == "PERIODONTAL_STALE_VERSION"


def test_finalized_version_is_immutable_at_database_level(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    finalized = api_client.post(
        f"/api/periodontograms/{draft['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    ).json()["exam"]
    version_id = finalized["current_version"]["id"]

    with pytest.raises(DBAPIError):
        db_session.execute(
            text(
                "UPDATE periodontal_exam_versions "
                "SET content = '{\"forbidden\": true}'::jsonb WHERE id = :id"
            ),
            {"id": version_id},
        )
        db_session.commit()
    db_session.rollback()
    version = db_session.get(PeriodontalExamVersion, version_id)
    assert version.content == {}


def test_stale_and_concurrent_finalize_allow_exactly_one_winner(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    path = f"/api/periodontograms/{draft['id']}/finalize"

    def finalize():
        return api_client.post(
            path,
            token=tenant.dentist_admin.token,
            json={"row_version": draft["row_version"]},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: finalize(), range(2)))
    assert sorted(statuses) == [200, 409]

    stale = api_client.post(
        path,
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "PERIODONTAL_STALE_VERSION"


def test_concurrent_correction_keeps_single_draft(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    finalized = api_client.post(
        f"/api/periodontograms/{draft['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    ).json()["exam"]
    path = f"/api/periodontograms/{draft['id']}/correct"

    def correct(index: int):
        return api_client.post(
            path,
            token=tenant.dentist_admin.token,
            json={
                "row_version": finalized["row_version"],
                "reason": f"Corrección concurrente {index}",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(correct, range(2)))
    assert sorted(statuses) == [201, 409]

    count = db_session.scalar(
        select(func.count()).where(
            PeriodontalExamVersion.exam_id == draft["id"],
            PeriodontalExamVersion.status == "DRAFT",
        )
    )
    assert count == 1


def test_no_destructive_delete_route_and_root_state_remains_versioned(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    assert api_client.delete(
        f"/api/periodontograms/{draft['id']}", token=tenant.dentist_admin.token
    ).status_code == 405
    assert db_session.get(PeriodontalExam, draft["id"]) is not None


def test_create_seeds_permanent_dentition_and_six_unmeasured_sites(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    exam = _create(api_client, tenant).json()["exam"]
    assert len(exam["teeth"]) == 32
    assert [item["fdi_number"] for item in exam["teeth"]][:9] == [18, 17, 16, 15, 14, 13, 12, 11, 21]
    assert all(len(item["sites"]) == 6 for item in exam["teeth"])
    assert exam["coverage"] == {"eligible_sites": 192, "evaluated_sites": 0, "incomplete": True}
    assert exam["indices"]["bop"]["percentage"] is None
    version_id = exam["current_version"]["id"]
    assert db_session.scalar(
        select(func.count()).select_from(PeriodontalTooth).where(PeriodontalTooth.version_id == version_id)
    ) == 32
    assert db_session.scalar(
        select(func.count()).select_from(PeriodontalSite).where(PeriodontalSite.version_id == version_id)
    ) == 192


def test_batch_update_persists_partial_measurements_and_rejects_stale_or_invalid_fdi(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    exam = _create(api_client, tenant).json()["exam"]
    saved = _update(
        api_client,
        tenant,
        exam,
        teeth=[{
            "fdi_number": 16,
            "mobility_grade": 1,
            "furcation_mesial": True,
            "clinical_note": "Nota periodontal breve",
        }],
        sites=[
            {
                "fdi_number": 16,
                "site_code": "BUCCAL_DISTAL",
                "probing_depth_mm": 4,
                "gingival_margin_mm": -2,
                "bleeding_on_probing": True,
                "plaque": False,
            }
        ],
    )
    assert saved.status_code == 200, saved.text
    current = saved.json()["exam"]
    tooth = next(item for item in current["teeth"] if item["fdi_number"] == 16)
    site = next(item for item in tooth["sites"] if item["site_code"] == "BUCCAL_DISTAL")
    assert tooth["mobility_grade"] == 1
    assert tooth["furcation_mesial"] is True
    assert tooth["clinical_note"] == "Nota periodontal breve"
    assert site["clinical_attachment_level_mm"] == 6
    assert site["is_periodontal_pocket"] is True
    assert current["coverage"]["evaluated_sites"] == 1
    audit = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == exam["id"],
            AuditEvent.action == "PERIODONTAL_EXAM_DRAFT_UPDATED",
        )
    )
    assert audit.detail["changed_teeth"] == 1
    assert "Nota periodontal breve" not in str(audit.detail)

    stale = _update(api_client, tenant, exam, teeth=[{"fdi_number": 16, "mobility_grade": 2}])
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "PERIODONTAL_STALE_VERSION"
    invalid = _update(
        api_client,
        tenant,
        current,
        sites=[{"fdi_number": 55, "site_code": "BUCCAL_DISTAL", "probing_depth_mm": 3}],
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "PERIODONTAL_INVALID_FDI"


def test_tooth_state_mobility_furcation_and_implant_rules(api_client, security_world) -> None:
    tenant = security_world.tenant_a
    exam = _create(api_client, tenant).json()["exam"]
    measured = _update(
        api_client,
        tenant,
        exam,
        sites=[{"fdi_number": 11, "site_code": "BUCCAL_MID", "probing_depth_mm": 3}],
    ).json()["exam"]
    guarded = _update(api_client, tenant, measured, teeth=[{"fdi_number": 11, "state": "ABSENT"}])
    assert guarded.status_code == 409
    assert guarded.json()["detail"]["code"] == "PERIODONTAL_STATE_CHANGE_REQUIRES_CLEAR"
    absent = _update(
        api_client,
        tenant,
        measured,
        teeth=[{"fdi_number": 11, "state": "ABSENT", "clear_clinical_data": True}],
    ).json()["exam"]
    assert next(item for item in absent["teeth"] if item["fdi_number"] == 11)["state"] == "ABSENT"
    no_absent_site = _update(
        api_client,
        tenant,
        absent,
        sites=[{"fdi_number": 11, "site_code": "BUCCAL_MID", "probing_depth_mm": 2}],
    )
    assert no_absent_site.status_code == 422

    implant = _update(
        api_client,
        tenant,
        absent,
        teeth=[{"fdi_number": 12, "state": "IMPLANT"}],
    ).json()["exam"]
    mobility = _update(
        api_client,
        tenant,
        implant,
        teeth=[{"fdi_number": 12, "mobility_grade": 1}],
    )
    assert mobility.status_code == 422
    suppuration = _update(
        api_client,
        tenant,
        implant,
        sites=[{"fdi_number": 12, "site_code": "BUCCAL_MID", "suppuration": True}],
    )
    assert suppuration.status_code == 200
    natural_suppuration = _update(
        api_client,
        tenant,
        suppuration.json()["exam"],
        sites=[{"fdi_number": 13, "site_code": "BUCCAL_MID", "suppuration": False}],
    )
    assert natural_suppuration.status_code == 422

    non_molar = _update(
        api_client,
        tenant,
        suppuration.json()["exam"],
        teeth=[{"fdi_number": 14, "furcation_mesial": True}],
    )
    assert non_molar.status_code == 422
    invalid_mobility = _update(
        api_client,
        tenant,
        suppuration.json()["exam"],
        teeth=[{"fdi_number": 16, "mobility_grade": 4}],
    )
    assert invalid_mobility.status_code == 422


def test_partial_finalize_snapshot_correction_and_child_immutability(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    exam = _create(api_client, tenant).json()["exam"]
    v1_draft = _update(
        api_client,
        tenant,
        exam,
        sites=[
            {
                "fdi_number": 18,
                "site_code": "BUCCAL_DISTAL",
                "probing_depth_mm": 5,
                "gingival_margin_mm": 1,
                "bleeding_on_probing": True,
            }
        ],
    ).json()["exam"]
    v1 = api_client.post(
        f"/api/periodontograms/{exam['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": v1_draft["row_version"]},
    ).json()["exam"]
    v1_hash = v1["current_version"]["snapshot_hash"]
    assert v1["current_version"]["snapshot"]["coverage"]["evaluated_sites"] == 1
    assert v1["current_version"]["snapshot"]["teeth"][0]["fdi_number"] == 18

    tooth_id = db_session.scalar(
        select(PeriodontalTooth.id).where(
            PeriodontalTooth.version_id == v1["current_version"]["id"],
            PeriodontalTooth.fdi_number == 18,
        )
    )
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE periodontal_teeth SET mobility_grade = 2 WHERE id = :id"),
            {"id": tooth_id},
        )
        db_session.commit()
    db_session.rollback()

    v2_draft = api_client.post(
        f"/api/periodontograms/{exam['id']}/correct",
        token=tenant.dentist_admin.token,
        json={"row_version": v1["row_version"], "reason": "Nueva medición clínica"},
    ).json()["exam"]
    inherited = next(item for item in v2_draft["teeth"] if item["fdi_number"] == 18)
    assert inherited["sites"][0]["probing_depth_mm"] == 5
    changed = _update(
        api_client,
        tenant,
        v2_draft,
        sites=[{"fdi_number": 18, "site_code": "BUCCAL_DISTAL", "probing_depth_mm": 6}],
    ).json()["exam"]
    v2 = api_client.post(
        f"/api/periodontograms/{exam['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": changed["row_version"]},
    ).json()["exam"]
    assert v2["current_version"]["snapshot_hash"] != v1_hash
    old_version = next(item for item in v2["versions"] if item["version_number"] == 1)
    assert old_version["snapshot_hash"] == v1_hash

    audit = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == exam["id"],
            AuditEvent.action == "PERIODONTAL_EXAM_DRAFT_UPDATED",
        )
    )
    assert audit.detail["changed_sites"] == 1
    assert "probing_depth_mm" not in audit.detail


def test_0044_evolution_link_schema_has_nullable_fk_and_tenant_patient_index(
    db_session,
) -> None:
    schema = inspect(db_session.bind)
    columns = {item["name"]: item for item in schema.get_columns("periodontal_exams")}
    assert columns["evolucion_id"]["nullable"] is True
    foreign_keys = {
        item["name"]: item for item in schema.get_foreign_keys("periodontal_exams")
    }
    link_fk = foreign_keys["fk_periodontal_exams_evolution"]
    assert link_fk["constrained_columns"] == ["evolucion_id"]
    assert link_fk["referred_table"] == "evoluciones_clinicas"
    assert link_fk["referred_columns"] == ["id"]
    assert link_fk["options"]["ondelete"] == "RESTRICT"
    indexes = {item["name"]: item for item in schema.get_indexes("periodontal_exams")}
    assert indexes["ix_periodontal_exams_evolution_link"]["column_names"] == [
        "empresa_id",
        "paciente_id",
        "evolucion_id",
    ]


def test_history_orders_independent_exams_and_distinguishes_draft_from_finalized(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    older = api_client.post(
        _path(tenant),
        token=tenant.dentist_admin.token,
        json={"clinical_date": "2026-01-15"},
    ).json()["exam"]
    finalized = _finalize(api_client, tenant, older)
    assert finalized.status_code == 200, finalized.text
    newer = api_client.post(
        _path(tenant),
        token=tenant.dentist_admin.token,
        json={"clinical_date": "2026-09-23"},
    ).json()["exam"]

    history = api_client.get(_path(tenant), token=tenant.dentist_admin.token)
    assert history.status_code == 200, history.text
    items = history.json()["items"]
    assert [item["id"] for item in items] == [newer["id"], older["id"]]
    assert items[0]["status"] == "DRAFT"
    assert "FINALIZE" in items[0]["allowed_actions"]
    assert items[1]["status"] == "FINALIZED"
    assert "CORRECT" in items[1]["allowed_actions"]
    assert all(item["current_version_number"] == 1 for item in items)


def test_finalized_exam_links_to_compatible_evolution_idempotently_without_touching_snapshot(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    finalized = _finalize(api_client, tenant, _create(api_client, tenant).json()["exam"])
    assert finalized.status_code == 200, finalized.text
    exam = finalized.json()["exam"]
    original_hash = exam["current_version"]["snapshot_hash"]
    candidates = api_client.get(
        f"/api/periodontograms/{exam['id']}/evolution-candidates",
        token=tenant.dentist_admin.token,
    )
    assert candidates.status_code == 200, candidates.text
    candidate = next(
        item for item in candidates.json()["items"] if item["id"] == str(tenant.evolution.id)
    )
    assert set(candidate) == {
        "id",
        "attended_at",
        "timezone_name",
        "status",
        "site_id",
        "site_name",
        "dentist_id",
        "dentist_name",
    }
    assert "Evolución ficticia" not in candidates.text

    payload = {
        "evolution_id": str(tenant.evolution.id),
        "row_version": exam["row_version"],
    }
    linked = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json=payload,
    )
    assert linked.status_code == 200, linked.text
    linked_exam = linked.json()["exam"]
    assert linked_exam["evolution_id"] == str(tenant.evolution.id)
    assert linked_exam["linked_evolution"]["id"] == str(tenant.evolution.id)
    assert linked_exam["current_version"]["snapshot_hash"] == original_hash
    assert linked_exam["current_version"]["integrity_status"] == "PASS"

    repeated = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json=payload,
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["exam"]["row_version"] == linked_exam["row_version"]

    audit_rows = list(
        db_session.scalars(
            select(AuditEvent).where(
                AuditEvent.entity_id == exam["id"],
                AuditEvent.action == "PERIODONTAL_EXAM_EVOLUTION_LINKED",
            )
        )
    )
    assert len(audit_rows) == 1
    assert audit_rows[0].detail == {
        "evolution_id": str(tenant.evolution.id),
        "site_id": str(tenant.site_1.id),
    }
    assert audit_rows[0].user_id == tenant.dentist_admin.user.id

    replacement = _evolution(db_session, tenant, text_value="No debe copiarse")
    conflict = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={
            "evolution_id": str(replacement.id),
            "row_version": linked_exam["row_version"],
        },
    )
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["detail"]["code"] == "PERIODONTAL_EVOLUTION_LINK_CONFLICT"

    db_session.expire_all()
    with pytest.raises(IntegrityError):
        db_session.delete(db_session.get(ClinicalEvolution, tenant.evolution.id))
        db_session.commit()
    db_session.rollback()


def test_evolution_link_rejects_draft_cross_tenant_patient_site_and_stale_requests(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    draft = _create(api_client, tenant).json()["exam"]
    draft_link = api_client.post(
        f"/api/periodontograms/{draft['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={"evolution_id": str(tenant.evolution.id), "row_version": draft["row_version"]},
    )
    assert draft_link.status_code == 409
    assert draft_link.json()["detail"]["code"] == "PERIODONTAL_EVOLUTION_LINK_REQUIRES_FINALIZED"

    exam = _finalize(api_client, tenant, draft).json()["exam"]
    stale = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={"evolution_id": str(tenant.evolution.id), "row_version": exam["row_version"] - 1},
    )
    assert stale.status_code == 409
    assert "otra sesión" in stale.json()["detail"]["message"]

    cross_tenant = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={
            "evolution_id": str(security_world.tenant_b.evolution.id),
            "row_version": exam["row_version"],
        },
    )
    assert cross_tenant.status_code == 404
    assert str(security_world.tenant_b.evolution.id) not in cross_tenant.text

    wrong_site = _evolution(db_session, tenant, site_id=tenant.site_2.id)
    cross_site = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={"evolution_id": str(wrong_site.id), "row_version": exam["row_version"]},
    )
    assert cross_site.status_code == 404

    other_patient = Patient(
        company_id=tenant.company.id,
        first_names="Paciente",
        last_names="Sintético alterno",
        document_type="Sin documento",
        mobile="+57000000999",
        normalized_mobile="+57000000999",
        status="Activo",
        search_text="paciente sintetico alterno",
        created_by=tenant.dentist_admin.user.id,
    )
    db_session.add(other_patient)
    db_session.flush()
    other_record = ClinicalRecord(
        company_id=tenant.company.id,
        patient_id=other_patient.id,
        opening_site_id=tenant.site_1.id,
        opening_dentist_id=tenant.dentist_profile.id,
        created_by=tenant.dentist_admin.user.id,
        updated_by=tenant.dentist_admin.user.id,
    )
    db_session.add(other_record)
    db_session.commit()
    wrong_patient = _evolution(
        db_session,
        tenant,
        patient_id=other_patient.id,
        clinical_record_id=other_record.id,
    )
    cross_patient = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={"evolution_id": str(wrong_patient.id), "row_version": exam["row_version"]},
    )
    assert cross_patient.status_code == 404


def test_evolution_link_rejects_finalized_snapshot_with_failed_integrity(
    api_client, db_session, monkeypatch, security_world
) -> None:
    tenant = security_world.tenant_a
    exam = _finalize(api_client, tenant, _create(api_client, tenant).json()["exam"]).json()["exam"]
    monkeypatch.setattr(periodontogram_service, "_integrity", lambda _version: "FAIL")

    response = api_client.post(
        f"/api/periodontograms/{exam['id']}/evolution-link",
        token=tenant.dentist_admin.token,
        json={"evolution_id": str(tenant.evolution.id), "row_version": exam["row_version"]},
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "PERIODONTAL_EVOLUTION_LINK_INTEGRITY_FAILED"
    assert db_session.get(PeriodontalExam, exam["id"]).evolution_id is None


def test_evolution_link_routes_preserve_periodontogram_rbac_and_site_scope(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    exam = _finalize(api_client, tenant, _create(api_client, tenant).json()["exam"]).json()["exam"]
    candidates_path = f"/api/periodontograms/{exam['id']}/evolution-candidates"
    link_path = f"/api/periodontograms/{exam['id']}/evolution-link"
    payload = {"evolution_id": str(tenant.evolution.id), "row_version": exam["row_version"]}

    for actor in (tenant.admin, tenant.secretary, security_world.platform_admin):
        assert api_client.get(candidates_path, token=actor.token).status_code == 403
        assert api_client.post(link_path, token=actor.token, json=payload).status_code == 403

    other = security_world.tenant_b
    assert api_client.get(candidates_path, token=other.dentist_admin.token).status_code == 404
    denied = api_client.post(link_path, token=other.dentist_admin.token, json=payload)
    assert denied.status_code == 404
    assert exam["id"] not in denied.text
