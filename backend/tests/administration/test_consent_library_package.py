from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from app.models.associations import RolePermission
from app.models.audit_event import AuditEvent
from app.models.consent_template import (
    ConsentLibraryDocument,
    ConsentLibraryInstallation,
    ConsentLibraryVersion,
    ConsentTemplate,
    ConsentTemplateVersion,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.consent_library_service import PACKAGE_PATH, ConsentLibraryError, _template_code, import_library_package, load_library_package
from app.services.consent_library_normalization import NORMALIZED_CONTENT_FIELD, assess_electronic_readiness, assess_legacy_patient_content, classify_signer_context, normalize_patient_content_v2, sha256_text, validate_patient_facing_content
from app.services.consent_signer import RESPONSIBLE_ADULT, resolve_signer_snapshot, signer_policy_from_library_version

SOURCE_HASH = "5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c"
PACKAGE = PACKAGE_PATH
V1_PACKAGE = PACKAGE_PATH.parents[1] / "v1" / "documents.json"
V2_PACKAGE = PACKAGE_PATH.parents[1] / "v2" / "documents.json"
V3_PACKAGE = PACKAGE_PATH.parents[1] / "v3" / "documents.json"
REPO_ROOT = PACKAGE_PATH.parents[5]
NORM3_REPORT = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Report.json"
NORM3_HUMAN_REVIEW = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Human-Review.md"
NORM3_HUMAN_REVIEW_HTML = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Human-Review.html"
NORM4_REPORT = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Report.json"
NORM4_HUMAN_REVIEW = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Human-Review.md"
NORM4_HUMAN_REVIEW_HTML = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Human-Review.html"
SOURCE_FRAGMENTS = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-Source-Fragments.json"
HUMAN_REVIEW = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-Human-Equivalence-Review.md"
CHECKLIST = REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-Normalization-Equivalence-Checklist.md"


def _package_payload() -> dict:
    return load_library_package(PACKAGE)


def _import_library(db_session):
    return import_library_package(db_session, path=PACKAGE)


def _approval_payload(**overrides) -> dict:
    payload = {
        "reviewer_name": "Revisor Odontológico Ficticio",
        "reviewed_date": "2026-08-05",
        "review_reference": "CHECKLIST-C019A4-LIB1-FICTICIO",
        "reason": "Aprobación ficticia controlada para prueba automatizada.",
        "clinical_text_faithful": True,
        "risks_preserved": True,
        "warnings_preserved": True,
        "values_preserved": True,
        "variables_correct": True,
        "titles_limits_correct": True,
        "signer_correct": True,
        "classification_correct": True,
        "country_approved": True,
        "odontological_review": True,
        "legal_equivalence_review": True,
    }
    payload.update(overrides)
    return payload


def _approve_version(api_client, token: str, version_id) -> dict:
    response = api_client.post(f"/api/consent-library/versions/{version_id}/approve-equivalence", token=token, json=_approval_payload())
    assert response.status_code == 200, response.text
    return response.json()


def _remove_persisted_library_role_permissions(db_session, company_id):
    permission_ids = list(
        db_session.scalars(
            select(Permission.id).where(Permission.code.like("consent.library.%"))
        )
    )
    role_ids = list(
        db_session.scalars(
            select(Role.id).where(
                Role.company_id == company_id,
                Role.code.in_(["ADMINISTRATOR", "DENTIST_ADMIN", "PLATFORM_ADMIN"]),
            )
        )
    )
    db_session.execute(
        delete(RolePermission).where(
            RolePermission.permission_id.in_(permission_ids),
            RolePermission.role_id.in_(role_ids),
        )
    )
    db_session.commit()


def _published_adult_version(db_session) -> tuple[ConsentLibraryDocument, ConsentLibraryVersion]:
    row = db_session.execute(
        select(ConsentLibraryDocument, ConsentLibraryVersion)
        .join(ConsentLibraryVersion, ConsentLibraryVersion.library_document_id == ConsentLibraryDocument.id)
        .where(
            ConsentLibraryDocument.document_type == "INFORMED_CONSENT",
            ConsentLibraryDocument.signer_scope == "PATIENT_SELF",
            ConsentLibraryVersion.country_code == "CO",
        )
        .order_by(ConsentLibraryDocument.code)
        .limit(1)
    ).first()
    assert row is not None
    return row[0], row[1]


def _procedure(db_session, tenant):
    catalog = ProcedureCatalogItem(company_id=tenant.company.id, name="Procedimiento clínico ficticio", normalized_name=f"procedimiento-{uuid4()}", description="Descripción ficticia", is_active=True, created_by=tenant.dentist_admin.user.id)
    db_session.add(catalog)
    db_session.flush()
    procedure = TreatmentProcedure(company_id=tenant.company.id, treatment_id=tenant.treatment.id, patient_id=tenant.patient.id, catalog_procedure_id=catalog.id, name=catalog.name, status="Pendiente", unit_value=0, quantity=1, total_value=0, scope_type="GENERAL", created_by=tenant.dentist_admin.user.id)
    db_session.add(procedure)
    db_session.commit()
    return catalog, procedure


def _context(tenant, procedure, **changes):
    data = {"patient_id": str(tenant.patient.id), "site_id": str(tenant.site_1.id), "appointment_id": str(tenant.appointment.id), "treatment_id": str(tenant.treatment.id), "treatment_procedure_ids": [str(procedure.id)], "procedure_catalog_ids": [], "dentist_profile_id": str(tenant.dentist_profile.id), "clinical_date": "2026-08-01"}
    data.update(changes)
    return data


def _special_version(db_session, document_type: str) -> tuple[ConsentLibraryDocument, ConsentLibraryVersion]:
    row = db_session.execute(
        select(ConsentLibraryDocument, ConsentLibraryVersion)
        .join(ConsentLibraryVersion, ConsentLibraryVersion.library_document_id == ConsentLibraryDocument.id)
        .where(ConsentLibraryDocument.document_type == document_type, ConsentLibraryVersion.country_code == "CO")
        .order_by(ConsentLibraryDocument.code)
        .limit(1)
    ).first()
    assert row is not None
    return row[0], row[1]


def test_consent_library_package_is_normalized_and_country_independent():
    payload = _package_payload()
    assert payload["package_version"] == "LIB1_NORM_V2_NORM5_ELECTRONIC_READINESS"
    assert payload["normalization_schema_version"] == "LIB1_NORM_V2_ELECTRONIC_READINESS"
    assert payload["patient_facing_content_field"] == "normalized_content_markdown"
    assert payload["source_file_sha256"] == SOURCE_HASH
    assert payload["source_page_count"] == 39
    assert payload["source_pdf_verification"]["checked"] is True
    assert len(payload["documents"]) == 35
    all_versions = [version for document in payload["documents"] for version in document["versions"]]
    assert len(all_versions) == 70
    assert {version["country_code"] for version in all_versions} == {"CO", "CL"}
    assert all(version["legal_review_status"] == "PENDING_EQUIVALENCE_REVIEW" for version in all_versions)
    assert all(version["clinical_review_status"] == "PENDING_EQUIVALENCE_REVIEW" for version in all_versions)
    assert {version["version_number"] for version in all_versions} == {2, 3, 4}
    assert sum(version["version_number"] == 4 for version in all_versions) == 14
    assert all(version["content"] == version["normalized_content_markdown"] for version in all_versions)
    assert all(version["content"].strip() != version["source_text"].strip() for version in all_versions)
    assert all(version["source_text_sha256"] != version["normalized_content_sha256"] for version in all_versions)
    assert all("Texto del documento fuente" not in version["content"] for version in all_versions)
    assert all("[Página" not in version["content"] for version in all_versions)
    assert all("Paciente o responsable: " not in version["content"] for version in all_versions)
    assert all("FIRMA PACIENTE" not in version["content"].upper() for version in all_versions)
    assert all("normalization_schema_version=LIB1_NORM_V2_CONTEXTUAL" in version["transformation_notes"] for version in all_versions)
    assert all("Clínica Dental Seis" not in version["content"] for version in all_versions)
    assert all("DENTAL SEIS" not in version["content"].upper() for version in all_versions)
    assert all("{{company.name}}" in version["content"] for version in all_versions)
    assert all(not version["reviewed_countries"] for version in all_versions)
    adult_published = [document for document in payload["documents"] if document["document_type"] == "INFORMED_CONSENT" and document["signer_scope"] == "PATIENT_SELF"]
    assert adult_published


def test_signer1_fix2_creates_pending_responsible_adult_versions_without_mutating_source():
    payload = load_library_package(V3_PACKAGE)
    revised = [document for document in payload["documents"] if document["versions"][0]["version_number"] == 3]
    patient_or_responsible = [document for document in revised if document["signer_scope"] == "PATIENT_OR_RESPONSIBLE_ADULT"]
    responsible_required = [document for document in revised if document["signer_scope"] == "RESPONSIBLE_ADULT_REQUIRED"]

    assert len(patient_or_responsible) == 13
    assert len(responsible_required) == 2
    for document in revised:
        for version in document["versions"]:
            assert version["publication_status"] == "READY_FOR_REVIEW"
            assert version["legal_review_status"] == "PENDING_EQUIVALENCE_REVIEW"
            assert version["clinical_review_status"] == "PENDING_EQUIVALENCE_REVIEW"
            assert "paciente o tutor legal" not in version["content"].casefold()
            assert "paciente o adulto responsable" in version["content"].casefold()
            assert version["source_text_sha256"] == sha256_text(version["source_text"])
            assert "text_diff=paciente o tutor legal -> paciente o adulto responsable" in version["transformation_notes"]

    pediatric = next(document for document in revised if document["code"] == "CONS_ODONTOPEDIATRIA")
    assert all(version["version_number"] == 3 for version in pediatric["versions"])


def test_norm5_oxido_nitroso_is_patient_or_responsible_and_electronically_ready():
    payload = _package_payload()
    document = next(item for item in payload["documents"] if item["code"] == "CONS_OXIDO_NITROSO")
    assert document["signer_scope"] == "PATIENT_OR_RESPONSIBLE_ADULT"
    assert {version["version_number"] for version in document["versions"]} == {4}
    for version in document["versions"]:
        assert version["signer_compatibility"] == "PATIENT_OR_RESPONSIBLE_ADULT"
        assert "RUT:" not in version["content"]
        assert "tutor legal" not in version["content"].casefold()
        assert "Firma" not in version["content"]
        assert "___" not in version["content"]
        assert version["source_text_sha256"] == sha256_text(version["source_text"])
        assert version["source_text"].strip()
        assert "electronic_readiness_status=READY" in version["transformation_notes"]
        assert "norm5_result=SAFE_NORMALIZED" in version["transformation_notes"]
        assessment = assess_electronic_readiness(version["content"], country_code=version["country_code"], document_type=document["document_type"], signer_compatibility=version["signer_compatibility"])
        assert assessment.status == "READY"


def test_norm5_oxido_signer_rules_allow_adult_and_reject_minor_self_signature():
    payload = _package_payload()
    document = next(item for item in payload["documents"] if item["code"] == "CONS_OXIDO_NITROSO")
    assert document["signer_scope"] == "PATIENT_OR_RESPONSIBLE_ADULT"
    adult_patient = SimpleNamespace(
        id=uuid4(),
        company_id=uuid4(),
        first_names="Paciente",
        last_names="Adulto",
        birth_date=date(1990, 1, 1),
        email="paciente@example.test",
        mobile="3000000000",
        alternate_phone=None,
        document_type="CC",
        document="123",
    )
    signer = resolve_signer_snapshot(None, company_id=adult_patient.company_id, patient=adult_patient, payload_context=SimpleNamespace(responsible_adult=None), policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    assert signer.actor_type == "PATIENT_SELF"

    minor_patient = SimpleNamespace(
        id=uuid4(),
        company_id=uuid4(),
        first_names="Paciente",
        last_names="Menor",
        birth_date=date.today().replace(year=date.today().year - 10),
        email="menor@example.test",
        mobile="3000000001",
        alternate_phone=None,
        document_type="TI",
        document="456",
    )
    with pytest.raises(ValueError, match="menores de edad requieren firma"):
        resolve_signer_snapshot(None, company_id=minor_patient.company_id, patient=minor_patient, payload_context=SimpleNamespace(responsible_adult=None), policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())

    responsible_context = SimpleNamespace(
        responsible_adult=SimpleNamespace(
            patient_responsible_id=None,
            relationship_type="MOTHER",
            relationship_other=None,
            full_name="Adulto Responsable",
            document_type="CC",
            document_number="789",
            email="responsable@example.test",
            phone="3000000002",
            identity_verified=True,
        ),
        minor_participation_status="INFORMED_NO_OBJECTION",
        minor_participation_observation=None,
    )
    responsible = resolve_signer_snapshot(None, company_id=minor_patient.company_id, patient=minor_patient, payload_context=responsible_context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4())
    assert responsible.actor_type == RESPONSIBLE_ADULT


def test_norm5_oxido_library_policy_resolver_uses_latest_signer_metadata(db_session):
    _import_library(db_session)
    row = db_session.execute(
        select(ConsentLibraryDocument, ConsentLibraryVersion)
        .join(ConsentLibraryVersion, ConsentLibraryVersion.library_document_id == ConsentLibraryDocument.id)
        .where(
            ConsentLibraryDocument.code == "CONS_OXIDO_NITROSO",
            ConsentLibraryVersion.country_code == "CO",
            ConsentLibraryVersion.version_number == 4,
        )
    ).first()
    assert row is not None
    document, library_version = row
    assert document.signer_scope == "PATIENT_OR_RESPONSIBLE_ADULT"
    assert any(note == "signer_compatibility=RESPONSIBLE_ADULT_REQUIRED" for note in library_version.transformation_notes)
    assert any(note == "signer_compatibility=PATIENT_OR_RESPONSIBLE_ADULT" for note in library_version.transformation_notes)
    tenant_version = SimpleNamespace(source_library_version_id=library_version.id)
    assert signer_policy_from_library_version(db_session, tenant_version) == "PATIENT_OR_RESPONSIBLE_ADULT"


def test_norm5_oxido_v4_clone_allows_adult_patient_self_draft(api_client, db_session, security_world):
    _import_library(db_session)
    tenant = security_world.tenant_a
    tenant.patient.birth_date = date(1990, 1, 1)
    tenant.patient.email = "adulto.oxido@example.test"
    tenant.patient.mobile = "3000000000"
    db_session.commit()
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_OXIDO_NITROSO"))
    assert document is not None
    assert document.signer_scope == "PATIENT_OR_RESPONSIBLE_ADULT"
    library_version = db_session.scalar(
        select(ConsentLibraryVersion).where(
            ConsentLibraryVersion.library_document_id == document.id,
            ConsentLibraryVersion.country_code == "CO",
            ConsentLibraryVersion.version_number == 4,
        )
    )
    assert library_version is not None
    cloned = api_client.post(f"/api/consent-library/versions/{library_version.id}/clone", token=tenant.dentist_admin.token, json={})
    assert cloned.status_code == 200, cloned.text
    tenant_version = db_session.get(ConsentTemplateVersion, cloned.json()["version_id"])
    assert tenant_version is not None
    assert tenant_version.source_library_version_id == library_version.id
    assert signer_policy_from_library_version(db_session, tenant_version) == "PATIENT_OR_RESPONSIBLE_ADULT"
    published = api_client.post(f"/api/consent-templates/{cloned.json()['template_id']}/versions/{tenant_version.id}/publish", token=tenant.dentist_admin.token)
    assert published.status_code == 200, published.text
    _, procedure = _procedure(db_session, tenant)
    context = _context(tenant, procedure, signer_actor_type="PATIENT_SELF")
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": context, "template_version_ids": [str(tenant_version.id)]})
    assert created.status_code == 201, created.text
    body = created.json()[0]
    assert body["signer_policy"] == "PATIENT_OR_RESPONSIBLE_ADULT"
    assert body["signer_actor_type"] == "PATIENT_SELF"
    assert body["responsible_adult"] is None


def test_signer_policy_matrix_and_age_boundaries():
    company_id = uuid4()
    today = date.today()
    adult_exact_birth_date = today.replace(year=today.year - 18)
    adult = SimpleNamespace(id=uuid4(), company_id=company_id, first_names="Paciente", last_names="Adulto", birth_date=adult_exact_birth_date, email="adulto@example.test", mobile="3000000000", alternate_phone=None, document_type="CC", document="123")
    adult_plus_one = SimpleNamespace(**{**adult.__dict__, "id": uuid4(), "birth_date": adult_exact_birth_date - timedelta(days=1)})
    minor = SimpleNamespace(id=uuid4(), company_id=company_id, first_names="Paciente", last_names="Menor", birth_date=adult_exact_birth_date + timedelta(days=1), email="menor@example.test", mobile="3000000001", alternate_phone=None, document_type="TI", document="456")
    responsible_context = SimpleNamespace(
        responsible_adult=SimpleNamespace(patient_responsible_id=None, relationship_type="MOTHER", relationship_other=None, full_name="Adulto Responsable", document_type="CC", document_number="789", email="responsable@example.test", phone="3000000002", identity_verified=True),
        minor_participation_status="INFORMED_NO_OBJECTION",
        minor_participation_observation=None,
    )
    patient_context = SimpleNamespace(responsible_adult=None, minor_participation_status=None, minor_participation_observation=None)

    assert resolve_signer_snapshot(None, company_id=company_id, patient=adult, payload_context=patient_context, policy="PATIENT_SELF", actor_type="PATIENT_SELF", verified_by_user_id=uuid4()).actor_type == "PATIENT_SELF"
    assert resolve_signer_snapshot(None, company_id=company_id, patient=adult_plus_one, payload_context=patient_context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type="PATIENT_SELF", verified_by_user_id=uuid4()).actor_type == "PATIENT_SELF"
    assert resolve_signer_snapshot(None, company_id=company_id, patient=adult, payload_context=responsible_context, policy="RESPONSIBLE_ADULT_REQUIRED", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4()).actor_type == RESPONSIBLE_ADULT
    assert resolve_signer_snapshot(None, company_id=company_id, patient=minor, payload_context=responsible_context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4()).actor_type == RESPONSIBLE_ADULT
    assert resolve_signer_snapshot(None, company_id=company_id, patient=minor, payload_context=responsible_context, policy="RESPONSIBLE_ADULT_REQUIRED", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4()).actor_type == RESPONSIBLE_ADULT
    with pytest.raises(ValueError, match="menores de edad requieren firma"):
        resolve_signer_snapshot(None, company_id=company_id, patient=minor, payload_context=patient_context, policy="PATIENT_SELF", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    with pytest.raises(ValueError, match="menores de edad requieren firma"):
        resolve_signer_snapshot(None, company_id=company_id, patient=minor, payload_context=patient_context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    with pytest.raises(ValueError, match="requiere firma de adulto responsable"):
        resolve_signer_snapshot(None, company_id=company_id, patient=adult, payload_context=patient_context, policy="RESPONSIBLE_ADULT_REQUIRED", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    with pytest.raises(ValueError, match="no hace parte del flujo estándar"):
        resolve_signer_snapshot(None, company_id=company_id, patient=adult, payload_context=patient_context, policy="SPECIAL_WORKFLOW", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    with pytest.raises(ValueError, match="no hace parte del flujo estándar"):
        resolve_signer_snapshot(None, company_id=company_id, patient=adult, payload_context=patient_context, policy="NO_PATIENT_SIGNATURE", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())


def test_norm5_blocked_variants_and_special_workflows_are_not_electronic_ready():
    payload = _package_payload()
    report = json.loads((REPO_ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM5-Report.json").read_text(encoding="utf-8"))
    assert report["source_file_sha256"] == SOURCE_HASH
    assert report["result_counts"]["SAFE_NORMALIZED"] == 18
    assert report["result_counts"]["NEEDS_STRUCTURED_FIELD"] == 2
    assert report["result_counts"]["NEEDS_HUMAN_REVIEW"] == 2
    assert report["readiness_counts"]["BLOCKED"] == 8
    assert report["readiness_counts"]["READY"] == 62

    rechazo = next(item for item in payload["documents"] if item["code"] == "RECHAZO_TRATAMIENTO")
    for version in rechazo["versions"]:
        assessment = assess_electronic_readiness(version["content"], country_code=version["country_code"], document_type=rechazo["document_type"], signer_compatibility=version.get("signer_compatibility") or rechazo["signer_scope"])
        assert assessment.status == "BLOCKED"
    cert = next(item for item in payload["documents"] if item["code"] == "CERT_ASISTENCIA")
    assert cert["signer_scope"] == "NO_PATIENT_SIGNATURE"
    assert all("signer_compatibility=NO_PATIENT_SIGNATURE" in version["transformation_notes"] for version in cert["versions"] if version["version_number"] == 3)


def test_norm5_v3_package_remains_unchanged_for_oxido_and_hashes_are_deterministic():
    from app.scripts.consent_library_norm5 import build_package

    v3 = json.loads(V3_PACKAGE.read_text(encoding="utf-8"))
    old_oxido = next(item for item in v3["documents"] if item["code"] == "CONS_OXIDO_NITROSO")
    assert old_oxido["signer_scope"] == "RESPONSIBLE_ADULT_REQUIRED"
    assert all(version["version_number"] == 3 for version in old_oxido["versions"])
    assert any("RUT:" in version["content"] for version in old_oxido["versions"])
    assert any("tutor legal" in version["content"].casefold() for version in old_oxido["versions"])

    rebuilt, report = build_package(V3_PACKAGE)
    current = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert rebuilt == current
    assert report["new_versions_count"] == 18


def test_norm3_human_review_report_tracks_source_v1_v2_and_blockers():
    report = json.loads(NORM3_REPORT.read_text(encoding="utf-8"))
    assert report["schema_version"] == "LIB1_NORM_V2"
    assert report["documents"] == 35
    assert report["versions"] == 70
    assert report["countries"] == {"CO": 35, "CL": 35}
    assert report["status_counts"]["BLOCKED"] > 0
    assert report["status_counts"]["NEEDS_REVIEW"] > 0
    target = next(item for item in report["items"] if item["code"] == "CONS_DESTARTRAJE_OPERATORIA" and item["country_code"] == "CO")
    assert "Texto del documento fuente" in target["normalized_content_v1"]
    assert "Texto del documento fuente" not in target["normalized_content_v2"]
    assert "[Página" in target["normalized_content_v1"]
    assert "[Página" not in target["normalized_content_v2"]
    assert target["source_text"].strip()
    assert target["representative_phrases"]
    assert NORM3_HUMAN_REVIEW.exists()
    assert NORM3_HUMAN_REVIEW_HTML.exists()




def test_norm4_contextual_signer_classifier_is_not_word_matching():
    administrative = "# Consentimiento\n\nEl paciente declara ser responsable con las indicaciones y seguirá controles."
    finding = classify_signer_context(administrative, document_type="INFORMED_CONSENT", title="Consentimiento adulto")
    assert finding.scope == "PATIENT_SELF"
    assert finding.category == "término administrativo"
    assert validate_patient_facing_content(administrative, allowed_variables=None, document_type="INFORMED_CONSENT", signer_compatibility=finding.scope, normalized_hash="a" * 64).status != "BLOCKED"

    removed_manual_label = normalize_patient_content_v2("# Consentimiento\n\nAcepto el tratamiento.\n\nPaciente o responsable: __________\nFirma tutor: __________", document_type="INFORMED_CONSENT", signer_scope="ADULT_SELF", title="Consentimiento adulto")
    assert removed_manual_label.signer_compatibility == "PATIENT_SELF"
    assert "Paciente o responsable" not in removed_manual_label.content
    assert removed_manual_label.status != "BLOCKED"

    real = classify_signer_context("# Consentimiento\n\nEl representante legal del paciente autoriza el procedimiento.", document_type="INFORMED_CONSENT", title="Consentimiento")
    assert real.scope == "RESPONSIBLE_ADULT_REQUIRED"
    assert real.category == "representante real"

    pediatric = classify_signer_context("# Consentimiento\n\nTratamiento para niños con recambio dentario.", document_type="INFORMED_CONSENT", title="Consentimiento odontopediatría")
    assert pediatric.scope == "RESPONSIBLE_ADULT_REQUIRED"
    assert pediatric.category == "contenido pediátrico"

    disjunctive = classify_signer_context("# Consentimiento\n\nEntiendo como paciente o tutor legal que debo seguir indicaciones.", document_type="INFORMED_CONSENT", title="Consentimiento")
    assert disjunctive.scope == "PATIENT_OR_RESPONSIBLE_ADULT"
    assert disjunctive.adult_variant_required is True
    assert disjunctive.adult_variant_proposal["legal_approval_required"] is True

    assert classify_signer_context("Rechazo informado", document_type="TREATMENT_REFUSAL").scope == "SPECIAL_WORKFLOW"
    assert classify_signer_context("Indicaciones postoperatorias", document_type="POST_CARE_INSTRUCTIONS").scope == "NO_PATIENT_SIGNATURE"
    assert classify_signer_context("Certificado", document_type="CERTIFICATE").scope == "NO_PATIENT_SIGNATURE"

def test_norm4_report_explains_all_35_documents_and_priority_candidates():
    report = json.loads(NORM4_REPORT.read_text(encoding="utf-8"))
    assert report["schema_version"] == "LIB1_NORM_V2_CONTEXTUAL"
    assert report["documents"] == 35
    assert report["versions"] == 70
    assert len(report["document_inventory"]) == 35
    assert report["status_counts"] == {"BLOCKED": 36, "NEEDS_REVIEW": 34}
    assert report["document_flow_counts"]["PATIENT_SELF"] == 2
    assert report["document_flow_counts"]["PATIENT_OR_RESPONSIBLE_ADULT"] == 13
    assert report["document_flow_counts"]["NO_PATIENT_SIGNATURE"] == 14
    assert report["document_flow_counts"]["SPECIAL_WORKFLOW"] == 4
    assert report["document_flow_counts"]["RESPONSIBLE_ADULT_REQUIRED"] == 2

    inventory = {item["code"]: item for item in report["document_inventory"]}
    assert inventory["CONS_ENDODONCIA"]["flow_classification"] == "PATIENT_SELF"
    assert inventory["CONS_ENDODONCIA"]["blocking_cause"] == "término administrativo"
    assert inventory["CONS_DESTARTRAJE_OPERATORIA"]["flow_classification"] == "PATIENT_OR_RESPONSIBLE_ADULT"
    assert inventory["CONS_DESTARTRAJE_OPERATORIA"]["adult_variant_required"] is True
    assert inventory["CONS_ODONTOPEDIATRIA"]["flow_classification"] == "RESPONSIBLE_ADULT_REQUIRED"
    assert inventory["RECHAZO_TRATAMIENTO"]["flow_classification"] == "SPECIAL_WORKFLOW"
    assert inventory["CERT_ASISTENCIA"]["flow_classification"] == "NO_PATIENT_SIGNATURE"
    assert len(report["priority_review"]) == 8
    assert any(item["code"] == "CONS_ENDODONCIA" and item["flow_classification"] == "PATIENT_SELF" for item in report["priority_review"])
    assert NORM4_HUMAN_REVIEW.exists()
    assert NORM4_HUMAN_REVIEW_HTML.exists()


def test_legacy_content_assessment_quarantines_source_artifacts_without_touching_history():
    legacy = "# Consentimiento\n\nTexto del documento fuente\n\n[Página 1]\nPaciente o responsable: __________\nFirma: __________"
    assessment = assess_legacy_patient_content(legacy)
    assert assessment.is_legacy is True
    assert "source_heading_present" in assessment.reasons
    assert "source_page_marker_present" in assessment.reasons

    clean = "# Consentimiento\n\nPaciente: {{ patient.full_name }}\n\nEl paciente declara haber comprendido el procedimiento."
    assert assess_legacy_patient_content(clean).is_legacy is False

def test_human_equivalence_package_contains_source_fragments_and_diff_material():
    fragments_payload = json.loads(SOURCE_FRAGMENTS.read_text(encoding="utf-8"))
    fragments = fragments_payload["fragments"]
    assert len(fragments) == 35
    assert all(item["pages"] for item in fragments)
    assert all(item["source_text"].strip() for item in fragments)
    assert all(len(item["source_text_sha256"]) == 64 for item in fragments)
    assert fragments[0]["extraction_method"] == "Apple PDFKit via Swift local, sin OCR"

    review = HUMAN_REVIEW.read_text(encoding="utf-8")
    assert "Revisión de variantes Colombia y Chile" in review
    assert "```diff" in review
    assert "{{company.name}}" in review
    assert "`PENDING`" in review

    checklist = CHECKLIST.read_text(encoding="utf-8")
    assert "Texto clínico fiel" in checklist
    assert "Revisión odontológica" in checklist
    assert checklist.count("| `") == 70


def test_special_documents_are_not_common_consent_candidates():
    payload = _package_payload()
    electronic_scopes = {"PATIENT_SELF", "PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}
    special = [document for document in payload["documents"] if document["document_type"] != "INFORMED_CONSENT" or document["signer_scope"] not in electronic_scopes]
    assert special
    for document in special:
        assert document["supports_electronic_signature"] is False or document["signer_scope"] not in electronic_scopes or document["document_type"] != "INFORMED_CONSENT"
        assert all(version["publication_status"] == "READY_FOR_REVIEW" for version in document["versions"])


def test_import_is_idempotent_and_counts_are_real(db_session):
    first = _import_library(db_session)
    assert first["documents_created"] == 35
    assert first["versions_created"] == 70
    assert first["new_versions"] == 70
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryDocument)) == 35
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion)) == 70
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion).where(ConsentLibraryVersion.country_code == "CO")) == 35
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion).where(ConsentLibraryVersion.country_code == "CL")) == 35
    second = _import_library(db_session)
    assert second["documents_created"] == 0
    assert second["versions_created"] == 0
    assert second["unchanged_versions"] == 70
    assert second["conflicts"] == 0
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryDocument)) == 35
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion)) == 70


def test_import_v1_then_norm4_v2_preserves_history_and_api_returns_current(api_client, db_session, security_world):
    legacy = import_library_package(db_session, path=V1_PACKAGE)
    assert legacy["versions_created"] == 70
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    assert document is not None
    legacy_co = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 1))
    assert legacy_co is not None
    legacy_hash = legacy_co.normalized_content_sha256
    legacy_content = legacy_co.content

    norm4 = _import_library(db_session)
    assert norm4["versions_created"] == 70
    assert norm4["new_versions"] == 70
    assert norm4["legacy_versions"] == 70
    assert norm4["conflicts"] == 0
    db_session.refresh(legacy_co)
    db_session.refresh(document)
    assert legacy_co.normalized_content_sha256 == legacy_hash
    assert legacy_co.content == legacy_content
    assert document.signer_scope == "RESPONSIBLE_ADULT_REQUIRED"

    versions = list(db_session.scalars(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO").order_by(ConsentLibraryVersion.version_number)))
    assert [version.version_number for version in versions] == [1, 3]
    assert versions[1].legal_review_status == "PENDING_EQUIVALENCE_REVIEW"
    assert "normalization_schema_version=LIB1_NORM_V2_CONTEXTUAL" in versions[1].transformation_notes
    assert "signer_compatibility=RESPONSIBLE_ADULT_REQUIRED" in versions[1].transformation_notes
    assert "Texto del documento fuente" not in versions[1].content
    assert "FIRMA" not in versions[1].content.upper()

    response = api_client.get("/api/consent-library?q=odontopediatría", token=security_world.tenant_a.admin.token)
    assert response.status_code == 200, response.text
    target = next(item for item in response.json()["items"] if item["code"] == "CONS_ODONTOPEDIATRIA")
    current_co = next(version for version in target["versions"] if version["country_code"] == "CO" and version["is_current"])
    history_co = [version for version in target["versions"] if version["country_code"] == "CO" and version["is_legacy"]]
    assert current_co["version_number"] == 3
    assert current_co["normalization_schema_version"] == "LIB1_NORM_V2_SIGNER1_FIX2"
    assert current_co["signer_compatibility"] == "RESPONSIBLE_ADULT_REQUIRED"
    assert history_co and history_co[0]["version_number"] == 1


def test_signer1_fix2_import_preserves_existing_normalized_version_and_adds_new_pending_version(db_session):
    import_library_package(db_session, path=V2_PACKAGE)
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    previous = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 2))
    previous_content = previous.content
    previous_source_text = previous.source_text
    previous_source_hash = previous.source_text_sha256

    result = _import_library(db_session)
    current = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 3))

    assert result["versions_created"] == 34
    assert result["unchanged_versions"] == 36
    assert previous.content == previous_content
    assert previous.source_text == previous_source_text
    assert previous.source_text_sha256 == previous_source_hash
    assert current is not None
    assert current.legal_review_status == "PENDING_EQUIVALENCE_REVIEW"
    assert "paciente o adulto responsable" in current.content.casefold()


def test_clone_rejects_legacy_v1_and_uses_exact_current_v2(api_client, db_session, security_world):
    import_library_package(db_session, path=V1_PACKAGE)
    _import_library(db_session)
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    assert document is not None
    v1 = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 1))
    current = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 3))
    assert v1 is not None and current is not None
    admin = security_world.tenant_a.admin

    legacy_clone = api_client.post(f"/api/consent-library/versions/{v1.id}/clone", token=admin.token, json={})
    assert legacy_clone.status_code == 409
    assert "versión histórica" in legacy_clone.text

    current_clone = api_client.post(f"/api/consent-library/versions/{current.id}/clone", token=admin.token, json={})
    assert current_clone.status_code == 200, current_clone.text
    installed = db_session.get(ConsentTemplateVersion, current_clone.json()["version_id"])
    assert installed is not None
    assert installed.source_library_version_id == current.id
    assert installed.content == current.content


def test_same_version_number_with_changed_hash_is_conflict(db_session, tmp_path):
    _import_library(db_session)
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    target = payload["documents"][0]["versions"][0]
    conflicting_version_number = target["version_number"]
    target["content"] = target["content"] + "\n\nCambio incompatible sin incrementar versión."
    target[NORMALIZED_CONTENT_FIELD] = target["content"]
    target["normalized_content_sha256"] = sha256_text(target["content"])
    conflict_path = tmp_path / "conflict.json"
    conflict_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    dry_run = import_library_package(db_session, path=conflict_path, dry_run=True)
    assert dry_run["conflicts"] == 1
    assert dry_run["conflict_items"][0]["version_number"] == conflicting_version_number
    with pytest.raises(ConsentLibraryError) as exc:
        import_library_package(db_session, path=conflict_path)
    assert "Conflicto de versionado" in str(exc.value)
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion)) == 70


def test_hash_mismatch_is_rejected(tmp_path):
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    payload["source_file_sha256"] = "0" * 64
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ConsentLibraryError):
        load_library_package(altered)


def test_partial_invalid_package_fails_without_creating_rows(db_session, tmp_path):
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    payload["documents"][0]["versions"][0]["content"] = "# Roto\n\n{{ variable.no_registrada }}"
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ConsentLibraryError):
        import_library_package(db_session, path=broken)
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryDocument)) == 0
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryVersion)) == 0


def test_library_listing_filters_review_and_no_private_install_leak(api_client, db_session, security_world):
    _import_library(db_session)
    admin_a = security_world.tenant_a.dentist_admin
    admin_b = security_world.tenant_b.dentist_admin
    response = api_client.get("/api/consent-library", token=admin_a.token)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 35
    co = api_client.get("/api/consent-library?country=CO", token=admin_a.token)
    assert co.status_code == 200
    assert all(version["country_code"] == "CO" for item in co.json()["items"] for version in item["versions"])
    category = api_client.get("/api/consent-library?category=Indicaciones", token=admin_a.token)
    assert category.status_code == 200
    assert category.json()["total"] > 0
    signer = api_client.get("/api/consent-library?signer_scope=PATIENT_SELF", token=admin_a.token)
    assert signer.status_code == 200
    assert signer.json()["total"] > 0
    assert all(item["signer_scope"] == "PATIENT_SELF" for item in signer.json()["items"])
    assert api_client.get("/api/consent-library", token=security_world.tenant_a.secretary.token).status_code == 403
    assert api_client.get("/api/consent-library", token=security_world.tenant_a.dentist.token).status_code == 403
    assert api_client.get("/api/consent-library", token=security_world.platform_admin.token).status_code == 200

    _, version = _published_adult_version(db_session)
    source_for_tenant = api_client.get(f"/api/consent-library/versions/{version.id}/source", token=admin_a.token)
    assert source_for_tenant.status_code == 403
    source_for_platform = api_client.get(f"/api/consent-library/versions/{version.id}/source", token=security_world.platform_admin.token)
    assert source_for_platform.status_code == 200
    assert "source_text" in source_for_platform.json()
    assert "Texto del documento fuente" not in response.text
    pending = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin_a.token, json={})
    assert pending.status_code == 409
    _approve_version(api_client, security_world.platform_admin.token, version.id)
    installed = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin_a.token, json={})
    assert installed.status_code == 200, installed.text
    list_a = api_client.get("/api/consent-library?country=CO", token=admin_a.token).json()
    assert any(item["installed_exact"] for item in list_a["items"])
    list_b = api_client.get("/api/consent-library?country=CO", token=admin_b.token).json()
    assert not any(item["installed_exact"] for item in list_b["items"])


def test_existing_roles_receive_library_permissions_after_new_session_even_if_role_permissions_are_stale(api_client, db_session, security_world):
    _import_library(db_session)
    _remove_persisted_library_role_permissions(db_session, security_world.tenant_a.company.id)
    _remove_persisted_library_role_permissions(db_session, security_world.platform_admin.user.company_id)

    admin_me = api_client.get("/api/auth/me", token=security_world.tenant_a.admin.token)
    assert admin_me.status_code == 200, admin_me.text
    assert "consent.library.read" in admin_me.json()["permissions"]
    assert "consent.library.install" in admin_me.json()["permissions"]
    assert "consent.library.clone" in admin_me.json()["permissions"]
    assert "consent.library.manage" not in admin_me.json()["permissions"]
    admin_library = api_client.get("/api/consent-library", token=security_world.tenant_a.admin.token)
    assert admin_library.status_code == 200, admin_library.text
    assert admin_library.json()["total"] == 35

    dentist_admin_me = api_client.get("/api/auth/me", token=security_world.tenant_a.dentist_admin.token)
    assert dentist_admin_me.status_code == 200, dentist_admin_me.text
    assert "consent.library.read" in dentist_admin_me.json()["permissions"]
    assert "consent.library.install" in dentist_admin_me.json()["permissions"]
    assert "consent.library.clone" in dentist_admin_me.json()["permissions"]
    assert "consent.library.manage" not in dentist_admin_me.json()["permissions"]
    dentist_admin_library = api_client.get("/api/consent-library", token=security_world.tenant_a.dentist_admin.token)
    assert dentist_admin_library.status_code == 200, dentist_admin_library.text

    secretary_me = api_client.get("/api/auth/me", token=security_world.tenant_a.secretary.token)
    assert secretary_me.status_code == 200, secretary_me.text
    assert "consent.library.read" not in secretary_me.json()["permissions"]
    assert api_client.get("/api/consent-library", token=security_world.tenant_a.secretary.token).status_code == 403

    platform_me = api_client.get("/api/auth/me", token=security_world.platform_admin.token)
    assert platform_me.status_code == 200, platform_me.text
    assert "consent.library.read" in platform_me.json()["permissions"]
    assert "consent.library.manage" in platform_me.json()["permissions"]
    assert "patients.view" not in platform_me.json()["permissions"]


def test_install_official_is_idempotent_tenant_scoped_and_read_only(api_client, db_session, security_world):
    _import_library(db_session)
    document, version = _published_adult_version(db_session)
    admin = security_world.tenant_a.dentist_admin
    blocked = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin.token, json={})
    assert blocked.status_code == 409
    _approve_version(api_client, security_world.platform_admin.token, version.id)
    db_session.refresh(version)
    first = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin.token, json={})
    assert first.status_code == 200, first.text
    second = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin.token, json={})
    assert second.status_code == 200, second.text
    assert second.json()["already_installed"] is True
    template = db_session.get(ConsentTemplate, first.json()["template_id"])
    installed_version = db_session.get(ConsentTemplateVersion, first.json()["version_id"])
    assert template.company_id == security_world.tenant_a.company.id
    assert template.template_origin == "DENTIA_LIBRARY"
    assert template.content_responsibility == "DENTIA"
    assert template.source_library_document_id == document.id
    assert installed_version.status == "PUBLISHED"
    assert installed_version.content == version.content
    assert installed_version.content_sha256 == version.normalized_content_sha256
    assert installed_version.legal_review_status == "APPROVED"
    assert installed_version.clinical_review_status == "APPROVED"
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryInstallation)) == 1
    draft_blocked = api_client.post(f"/api/consent-templates/{template.id}/versions/{installed_version.id}/create-draft", token=admin.token, json={"change_summary": "No debe editar oficial"})
    assert draft_blocked.status_code == 409


def test_approval_requires_platform_permission_complete_checklist_audits_and_preserves_reimport(api_client, db_session, security_world):
    _import_library(db_session)
    _, co_version = _published_adult_version(db_session)
    cl_version = db_session.scalar(
        select(ConsentLibraryVersion).where(
            ConsentLibraryVersion.library_document_id == co_version.library_document_id,
            ConsentLibraryVersion.country_code == "CL",
        )
    )
    assert cl_version is not None

    tenant_attempt = api_client.post(f"/api/consent-library/versions/{co_version.id}/approve-equivalence", token=security_world.tenant_a.dentist_admin.token, json=_approval_payload())
    assert tenant_attempt.status_code == 403

    incomplete = api_client.post(
        f"/api/consent-library/versions/{co_version.id}/approve-equivalence",
        token=security_world.platform_admin.token,
        json=_approval_payload(risks_preserved=False),
    )
    assert incomplete.status_code == 422
    db_session.refresh(co_version)
    assert co_version.legal_review_status == "PENDING_EQUIVALENCE_REVIEW"

    approved = _approve_version(api_client, security_world.platform_admin.token, co_version.id)
    assert approved["legal_review_status"] == "APPROVED"
    assert approved["clinical_review_status"] == "APPROVED"
    assert approved["equivalence_reviewer_name"] == "Revisor Odontológico Ficticio"
    db_session.refresh(co_version)
    db_session.refresh(cl_version)
    assert co_version.reviewed_countries == ["CO"]
    assert cl_version.legal_review_status == "PENDING_EQUIVALENCE_REVIEW"
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.action == "CONSENT_LIBRARY_EQUIVALENCE_APPROVED")) == 1

    _import_library(db_session)
    db_session.refresh(co_version)
    assert co_version.legal_review_status == "APPROVED"
    assert co_version.clinical_review_status == "APPROVED"
    assert co_version.equivalence_review_reason == "Aprobación ficticia controlada para prueba automatizada."


def test_clone_is_editable_and_does_not_modify_official(api_client, db_session, security_world):
    _import_library(db_session)
    _, version = _published_adult_version(db_session)
    admin = security_world.tenant_a.dentist_admin
    cloned = api_client.post(f"/api/consent-library/versions/{version.id}/clone", token=admin.token, json={})
    assert cloned.status_code == 200, cloned.text
    template = db_session.get(ConsentTemplate, cloned.json()["template_id"])
    draft = db_session.get(ConsentTemplateVersion, cloned.json()["version_id"])
    assert template.template_origin == "CLONED_FROM_DENTIA"
    assert template.content_responsibility == "CLINIC"
    assert draft.status == "DRAFT"
    assert draft.legal_review_status == "CLINIC_REVIEW_REQUIRED_AFTER_CLONE"
    original_content = version.content
    updated = api_client.patch(f"/api/consent-templates/{template.id}/versions/{draft.id}", token=admin.token, json={"title": draft.title, "content": draft.content + "\n\nObservación de prueba.", "change_summary": "Edición clínica de prueba", "scope_type": "GENERAL", "priority": 0, "site_ids": [], "procedure_ids": [], "specialties": [], "row_version": draft.row_version})
    assert updated.status_code == 200, updated.text
    db_session.refresh(version)
    assert version.content == original_content


def test_clone_codes_include_library_version_and_allow_multiple_copies(api_client, db_session, security_world):
    import_library_package(db_session, path=V2_PACKAGE)
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    assert document is not None
    v2 = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 2))
    assert v2 is not None
    admin = security_world.tenant_a.dentist_admin

    v2_clone = api_client.post(f"/api/consent-library/versions/{v2.id}/clone", token=admin.token, json={})
    assert v2_clone.status_code == 200, v2_clone.text
    v2_template = db_session.get(ConsentTemplate, v2_clone.json()["template_id"])
    v2_tenant_version = db_session.get(ConsentTemplateVersion, v2_clone.json()["version_id"])
    assert v2_template.code == "DENTIA-CONS_ODONTOPEDIATRIA-CO-V2-COPIA"
    assert v2_template.template_origin == "CLONED_FROM_DENTIA"
    assert v2_tenant_version.source_library_version_id == v2.id
    assert v2_tenant_version.content_sha256 == v2.normalized_content_sha256

    _import_library(db_session)
    v3 = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 3))
    assert v3 is not None
    assert v3.legal_review_status == "PENDING_EQUIVALENCE_REVIEW"
    assert v3.clinical_review_status == "PENDING_EQUIVALENCE_REVIEW"

    first_v3_clone = api_client.post(f"/api/consent-library/versions/{v3.id}/clone", token=admin.token, json={})
    second_v3_clone = api_client.post(f"/api/consent-library/versions/{v3.id}/clone", token=admin.token, json={})
    third_v3_clone = api_client.post(f"/api/consent-library/versions/{v3.id}/clone", token=admin.token, json={})
    assert first_v3_clone.status_code == 200, first_v3_clone.text
    assert second_v3_clone.status_code == 200, second_v3_clone.text
    assert third_v3_clone.status_code == 200, third_v3_clone.text

    v3_templates = [
        db_session.get(ConsentTemplate, first_v3_clone.json()["template_id"]),
        db_session.get(ConsentTemplate, second_v3_clone.json()["template_id"]),
        db_session.get(ConsentTemplate, third_v3_clone.json()["template_id"]),
    ]
    v3_versions = [
        db_session.get(ConsentTemplateVersion, first_v3_clone.json()["version_id"]),
        db_session.get(ConsentTemplateVersion, second_v3_clone.json()["version_id"]),
        db_session.get(ConsentTemplateVersion, third_v3_clone.json()["version_id"]),
    ]
    assert [template.code for template in v3_templates] == [
        "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA",
        "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA-2",
        "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA-3",
    ]
    assert len({template.id for template in [v2_template, *v3_templates]}) == 4
    assert all(version.source_library_version_id == v3.id for version in v3_versions)
    assert v2_tenant_version.source_library_version_id == v2.id

    v3_versions[0].status = "RETIRED"
    db_session.commit()
    fourth_v3_clone = api_client.post(f"/api/consent-library/versions/{v3.id}/clone", token=admin.token, json={})
    assert fourth_v3_clone.status_code == 200, fourth_v3_clone.text
    fourth_template = db_session.get(ConsentTemplate, fourth_v3_clone.json()["template_id"])
    assert fourth_template.code == "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA-4"
    assert db_session.scalar(select(func.count()).select_from(ConsentLibraryInstallation).where(ConsentLibraryInstallation.company_id == security_world.tenant_a.company.id, ConsentLibraryInstallation.library_version_id == v3.id, ConsentLibraryInstallation.installation_mode == "CLONE")) == 4


def test_clone_codes_are_country_and_tenant_scoped(api_client, db_session, security_world):
    _import_library(db_session)
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    assert document is not None
    co_version = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 3))
    cl_version = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CL", ConsentLibraryVersion.version_number == 3))
    assert co_version is not None and cl_version is not None

    tenant_a = security_world.tenant_a.dentist_admin
    tenant_b = security_world.tenant_b.dentist_admin
    tenant_a_co = api_client.post(f"/api/consent-library/versions/{co_version.id}/clone", token=tenant_a.token, json={})
    tenant_a_cl = api_client.post(f"/api/consent-library/versions/{cl_version.id}/clone", token=tenant_a.token, json={})
    tenant_b_co = api_client.post(f"/api/consent-library/versions/{co_version.id}/clone", token=tenant_b.token, json={})
    assert tenant_a_co.status_code == 200, tenant_a_co.text
    assert tenant_a_cl.status_code == 200, tenant_a_cl.text
    assert tenant_b_co.status_code == 200, tenant_b_co.text

    assert db_session.get(ConsentTemplate, tenant_a_co.json()["template_id"]).code == "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA"
    assert db_session.get(ConsentTemplate, tenant_a_cl.json()["template_id"]).code == "DENTIA-CONS_ODONTOPEDIATRIA-CL-V3-COPIA"
    assert db_session.get(ConsentTemplate, tenant_b_co.json()["template_id"]).code == "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA"


def test_clone_concurrent_requests_generate_unique_codes_without_500(api_client, db_session, security_world):
    _import_library(db_session)
    document = db_session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == "CONS_ODONTOPEDIATRIA"))
    assert document is not None
    v3 = db_session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == "CO", ConsentLibraryVersion.version_number == 3))
    assert v3 is not None
    admin = security_world.tenant_a.dentist_admin

    def clone_once():
        return api_client.post(f"/api/consent-library/versions/{v3.id}/clone", token=admin.token, json={})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: clone_once(), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    template_ids = [response.json()["template_id"] for response in responses]
    templates = [db_session.get(ConsentTemplate, template_id) for template_id in template_ids]
    assert sorted(template.code for template in templates) == [
        "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA",
        "DENTIA-CONS_ODONTOPEDIATRIA-CO-V3-COPIA-2",
    ]


def test_clone_code_sanitizes_and_truncates_without_pii():
    document = SimpleNamespace(code="Consentimiento especial con símbolos / áéíóú y nombre paciente no usado " * 2)
    version = SimpleNamespace(country_code="CO", version_number=123)
    code = _template_code(document, version, "CLONE", 12)
    assert len(code) <= 80
    assert re.fullmatch(r"[A-Z0-9_-]+", code)
    assert " " not in code
    assert "/" not in code


def test_special_types_cannot_enter_common_official_flow(api_client, db_session, security_world):
    _import_library(db_session)
    admin = security_world.tenant_a.dentist_admin
    for document_type in ["CERTIFICATE", "POST_CARE_INSTRUCTIONS", "TREATMENT_REFUSAL", "NO_WARRANTY_ACKNOWLEDGEMENT", "AESTHETIC_APPROVAL", "TREATMENT_TERMINATION_ACKNOWLEDGEMENT"]:
        _, version = _special_version(db_session, document_type)
        response = api_client.post(f"/api/consent-library/versions/{version.id}/install", token=admin.token, json={})
        assert response.status_code == 409
    _, special_version = _special_version(db_session, "CERTIFICATE")
    cloned = api_client.post(f"/api/consent-library/versions/{special_version.id}/clone", token=admin.token, json={})
    assert cloned.status_code == 409
