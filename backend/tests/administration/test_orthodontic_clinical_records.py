from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution, ClinicalTimelineEvent
from app.models.orthodontics import (
    OrthodonticClinicalRecord,
    OrthodonticClinicalRecordVersion,
)
from app.services.orthodontic_record_schema_service import (
    ORTHODONTIC_RECORD_FIELD_KEYS,
    ORTHODONTIC_RECORD_SCHEMA_VERSION,
    ORTHODONTIC_RECORD_SECTIONS,
    ORTHODONTIC_RECORD_FIELDS,
    OrthodonticRecordSchemaError,
    validate_orthodontic_record_content,
)


def _prepare_active_case(api_client, world, tenant=None):
    tenant = tenant or world.tenant_a
    enabled = api_client.put(
        f"/api/platform/companies/{tenant.company.id}/orthodontics-entitlement",
        token=world.platform_admin.token,
        json={"enabled": True, "seat_limit": 1},
    )
    assert enabled.status_code == 200, enabled.text
    assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(tenant.dentist_profile.id)},
    )
    assert assigned.status_code == 200, assigned.text
    created = api_client.post(
        f"/api/patients/{tenant.patient.id}/orthodontics/cases",
        token=tenant.dentist_admin.token,
        json={},
    )
    assert created.status_code == 201, created.text
    draft = created.json()["case"]
    activated = api_client.post(
        f"/api/orthodontics/cases/{draft['id']}/activate",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    )
    assert activated.status_code == 200, activated.text
    return tenant, activated.json()["case"]


def _create_record(api_client, tenant, case):
    response = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert response.status_code == 201, response.text
    return response.json()["record"]


def _save(api_client, tenant, case, record, content):
    version = record["current_version"]
    response = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{version['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": version["row_version"], "content": content},
    )
    assert response.status_code == 200, response.text
    return response.json()["record"]


def _finalize(api_client, tenant, case, record):
    version = record["current_version"]
    response = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{version['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": version["row_version"]},
    )
    assert response.status_code == 200, response.text
    return response.json()["record"]


def test_schema_preserves_source_structure_and_all_fields_are_optional() -> None:
    assert ORTHODONTIC_RECORD_SCHEMA_VERSION == "ORTHODONTIC_RECORD_V1"
    assert [section["key"] for section in ORTHODONTIC_RECORD_SECTIONS] == [
        "general", "facial", "occlusal", "dentoalveolar", "articulator",
        "periodontal", "tmj_muscular", "studies", "airway", "cephalometric",
        "other_factors",
    ]
    expected_fields = set("""
        chief_complaint habits hand_radiograph_stage williams_asymmetry
        mandibular_deviation gingival_exposure lip_seal sagittal_facial_class
        lower_facial_third upper_lip lower_lip chin dentition upper_midline
        lower_midline left_molar_class right_molar_class left_canine_class
        right_canine_class overjet spee_curve overbite occlusal_plane
        transverse_bite wilson_curve upper_arch_shape lower_arch_shape
        upper_dental_discrepancy lower_dental_discrepancy posterior_discrepancy
        bolton_index supernumerary_or_agenesis absent_or_retained_teeth
        second_molars third_molars occlusal_trauma wear_facets
        panoramic_radiograph_findings rc_oc_discrepancy premature_contact
        molar_rotation molar_torque cpi_right cpi_left cpi_transverse oral_hygiene
        periodontal_biotype recessions gingival_hyperplasia root_prominence
        lingual_frenum upper_median_frenum lower_median_frenum lateral_frena
        periodontal_others mandibular_manipulation right_tmj left_tmj
        muscle_palpation opening_pattern cbct_diagnosis other_studies
        mri_diagnosis breathing_type sleep airway_others ricketts_type
        ricketts_level jarabak_type jarabak_level jarabak_percentage
        upper_incisor_inclination lower_incisor_inclination anb_angle wits
        skeletal_class maxillary_vertical_excess lower_incisor_to_upper_stomion
        upper_incisor_to_stomion penn_analysis symphysis_width_group_v
        determining_factors
    """.split())
    assert set(ORTHODONTIC_RECORD_FIELD_KEYS) == expected_fields
    assert len(ORTHODONTIC_RECORD_FIELD_KEYS) == 82
    for section in ORTHODONTIC_RECORD_SECTIONS:
        orders = [
            field["order"] for field in ORTHODONTIC_RECORD_FIELDS
            if field["section"] == section["key"]
        ]
        assert orders == list(range(1, len(orders) + 1))
    assert validate_orthodontic_record_content({}) == {}
    assert {"chief_complaint", "habits", "right_tmj", "cbct_diagnosis", "wits", "determining_factors"}.issubset(ORTHODONTIC_RECORD_FIELD_KEYS)


def test_schema_validates_single_multi_text_and_boolean_without_required_fields() -> None:
    assert validate_orthodontic_record_content({
        "hand_radiograph_stage": "MP3_CAP",
        "habits": ["ONYCHOPHAGIA", "MOUTH_BREATHING"],
        "chief_complaint": "  Control de alineación  ",
        "posterior_discrepancy": False,
    }) == {
        "hand_radiograph_stage": "MP3_CAP",
        "habits": ["ONYCHOPHAGIA", "MOUTH_BREATHING"],
        "chief_complaint": "Control de alineación",
        "posterior_discrepancy": False,
    }
    with pytest.raises(OrthodonticRecordSchemaError):
        validate_orthodontic_record_content({"hand_radiograph_stage": "INVENTED"})
    with pytest.raises(OrthodonticRecordSchemaError):
        validate_orthodontic_record_content({"habits": ["INVENTED"]})
    with pytest.raises(OrthodonticRecordSchemaError):
        validate_orthodontic_record_content({"posterior_discrepancy": "yes"})
    with pytest.raises(OrthodonticRecordSchemaError):
        validate_orthodontic_record_content({"chief_complaint": 123})


def test_record_lifecycle_schema_snapshot_hash_timeline_and_audit(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    clinical_evolutions_before = len(list(db_session.scalars(select(ClinicalEvolution))))
    record = _create_record(api_client, tenant, case)
    assert record["orthodontic_case_id"] == case["id"]
    assert record["label"] == "Historia clínica de Ortodoncia"
    assert record["current_version"]["status"] == "DRAFT"
    assert record["schema"]["version"] == ORTHODONTIC_RECORD_SCHEMA_VERSION

    duplicate = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert duplicate.status_code == 409

    invalid = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{record['current_version']['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": record["current_version"]["row_version"], "content": {"invented_field": "x"}},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "ORTHODONTIC_RECORD_SCHEMA_INVALID"

    content = {
        "chief_complaint": "  Consulta por alineación dental  ",
        "habits": ["ONYCHOPHAGIA", "MOUTH_BREATHING"],
        "posterior_discrepancy": False,
        "right_tmj": ["OPENING_CLICK"],
        "wits": "-2 mm",
    }
    record = _save(api_client, tenant, case, record, content)
    assert record["current_version"]["content"]["chief_complaint"] == "Consulta por alineación dental"
    stale = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{record['current_version']['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": 1, "content": {}},
    )
    assert stale.status_code == 409

    record = _finalize(api_client, tenant, case, record)
    finalized = record["current_version"]
    assert finalized["status"] == "FINALIZED"
    assert len(finalized["content_hash"]) == 64
    assert finalized["content_snapshot"]["habits"]["display_value"] == ["Onicofagia", "Respiración bucal"]
    assert finalized["schema_snapshot"]["version"] == ORTHODONTIC_RECORD_SCHEMA_VERSION
    assert finalized["clinical_date"] and finalized["timezone_name"]

    immutable = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{finalized['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": finalized["row_version"], "content": {}},
    )
    assert immutable.status_code == 409
    assert immutable.json()["detail"]["code"] == "ORTHODONTIC_RECORD_VERSION_IMMUTABLE"

    db_session.expire_all()
    assert len(list(db_session.scalars(select(ClinicalEvolution)))) == clinical_evolutions_before
    timeline = db_session.scalar(select(ClinicalTimelineEvent).where(
        ClinicalTimelineEvent.entity_id == finalized["id"],
        ClinicalTimelineEvent.event_type == "ORTHODONTIC_RECORD_FINALIZED",
    ))
    assert timeline is not None
    actions = set(db_session.scalars(select(AuditEvent.action).where(
        AuditEvent.entity_id == record["id"]
    )))
    assert {
        "ORTHODONTIC_RECORD_CREATED",
        "ORTHODONTIC_RECORD_DRAFT_UPDATED",
        "ORTHODONTIC_RECORD_FINALIZED",
    }.issubset(actions)


def test_new_version_clones_finalized_and_concurrency_allows_one_draft(
    api_client, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    record = _save(api_client, tenant, case, _create_record(api_client, tenant, case), {"chief_complaint": "Control"})
    record = _finalize(api_client, tenant, case, record)
    source_id = record["current_version"]["id"]
    source_hash = record["current_version"]["content_hash"]

    def create_version():
        return api_client.post(
            f"/api/orthodontics/cases/{case['id']}/record/versions",
            token=tenant.dentist_admin.token,
            json={"based_on_version_id": source_id},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: create_version(), range(2)))
    assert sorted(response.status_code for response in responses) == [201, 409]
    created = next(response for response in responses if response.status_code == 201).json()["record"]
    draft = created["current_version"]
    assert draft["version_number"] == 2
    assert draft["based_on_version_id"] == source_id
    assert draft["content"] == {"chief_complaint": "Control"}
    assert created["versions"][1]["content_hash"] is not None

    updated = _save(
        api_client,
        tenant,
        case,
        created,
        {"chief_complaint": "Control actualizado", "posterior_discrepancy": True},
    )
    finalized_v2 = _finalize(api_client, tenant, case, updated)
    assert finalized_v2["current_version"]["version_number"] == 2
    historical_v1 = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record?version_id={source_id}",
        token=tenant.dentist_admin.token,
    )
    assert historical_v1.status_code == 200
    assert historical_v1.json()["current_version"]["content"] == {"chief_complaint": "Control"}
    assert historical_v1.json()["current_version"]["content_hash"] == source_hash


def test_suspended_completed_and_revoked_entitlement_preserve_read_only_history(
    api_client, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    record = _finalize(api_client, tenant, case, _create_record(api_client, tenant, case))
    suspended = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/suspend",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"], "reason": "Pausa clínica"},
    )
    assert suspended.status_code == 200, suspended.text
    read = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert read.status_code == 200 and read.json()["can_edit"] is False
    assert "suspendido" in read.json()["read_only_reason"]
    blocked = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record/versions",
        token=tenant.dentist_admin.token,
        json={"based_on_version_id": record["current_version"]["id"]},
    )
    assert blocked.status_code == 409

    resumed = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/resume",
        token=tenant.dentist_admin.token,
        json={"row_version": suspended.json()["case"]["row_version"]},
    )
    assert resumed.status_code == 200, resumed.text
    completed = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/complete",
        token=tenant.dentist_admin.token,
        json={"row_version": resumed.json()["case"]["row_version"]},
    )
    assert completed.status_code == 200, completed.text
    completed_read = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert completed_read.status_code == 200
    assert "finalizado" in completed_read.json()["read_only_reason"]

    disabled = api_client.put(
        f"/api/platform/companies/{tenant.company.id}/orthodontics-entitlement",
        token=security_world.platform_admin.token,
        json={"enabled": False, "seat_limit": 1},
    )
    assert disabled.status_code == 200, disabled.text
    historical = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert historical.status_code == 200, historical.text
    workspace = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist_admin.token,
    )
    assert workspace.status_code == 200
    assert workspace.json()["access"]["allowed"] is False


def test_revoked_assignment_preserves_history_and_blocks_new_writes(
    api_client, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    record = _finalize(api_client, tenant, case, _create_record(api_client, tenant, case))
    assignments = api_client.get(
        "/api/orthodontics/assignments", token=tenant.admin.token
    )
    assert assignments.status_code == 200
    assignment = next(
        item for item in assignments.json()["items"]
        if item["dentist_id"] == str(tenant.dentist_profile.id) and item["assigned"]
    )
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assignment['id']}/revoke",
        token=tenant.admin.token,
        json={"reason": "Prueba de conservación histórica"},
    )
    assert revoked.status_code == 200, revoked.text

    historical = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert historical.status_code == 200, historical.text
    assert historical.json()["can_edit"] is False
    blocked = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record/versions",
        token=tenant.dentist_admin.token,
        json={"based_on_version_id": record["current_version"]["id"]},
    )
    assert blocked.status_code == 403


def test_record_rbac_and_cross_tenant_are_enforced(api_client, security_world) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    _create_record(api_client, tenant, case)
    path = f"/api/orthodontics/cases/{case['id']}/record"
    assert api_client.get(path, token=tenant.admin.token).status_code == 403
    assert api_client.get(path, token=tenant.secretary.token).status_code == 403
    assert api_client.get(path, token=security_world.platform_admin.token).status_code == 403

    other, _ = _prepare_active_case(api_client, security_world, security_world.tenant_b)
    wrong_tenant = api_client.get(path, token=other.dentist_admin.token)
    assert wrong_tenant.status_code == 404
    assert wrong_tenant.json()["detail"]["code"] == "ORTHODONTIC_RECORD_CASE_NOT_FOUND"


def test_country_label_is_chile_specific(api_client, db_session, security_world) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    tenant.company.country = "CL"
    db_session.commit()
    record = _create_record(api_client, tenant, case)
    assert record["label"] == "Ficha clínica de Ortodoncia"

    root = db_session.scalar(select(OrthodonticClinicalRecord).where(
        OrthodonticClinicalRecord.id == record["id"]
    ))
    versions = list(db_session.scalars(select(OrthodonticClinicalRecordVersion).where(
        OrthodonticClinicalRecordVersion.record_id == root.id
    )))
    assert len(versions) == 1
