from __future__ import annotations

import hashlib

from sqlalchemy import select

from app.models.clinical_document import ClinicalDocument
from app.models.prescription import Prescription


def assert_denied(response) -> None:
    assert response.status_code in {403, 404}, response.text


def test_company_a_can_download_own_prescription(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/prescriptions/{security_world.tenant_a.prescription.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert response.status_code == 200, response.text
    assert response.content == security_world.tenant_a.prescription_content
    assert response.headers["content-type"].startswith("application/pdf")


def test_company_a_cannot_download_company_b_prescription(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/prescriptions/{security_world.tenant_b.prescription.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert_denied(response)
    assert security_world.tenant_b.prescription_content not in response.content
    assert str(security_world.tenant_b.prescription.pdf_storage_path) not in response.text


def test_prescription_hash_mismatch_is_not_delivered(api_client, db_session, security_world) -> None:
    prescription = db_session.scalar(select(Prescription).where(Prescription.id == security_world.tenant_a.prescription.id))
    prescription.pdf_sha256 = hashlib.sha256(b"different").hexdigest()
    db_session.commit()
    response = api_client.get(
        f"/api/prescriptions/{prescription.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert response.status_code == 409, response.text
    assert security_world.tenant_a.prescription_content not in response.content


def test_company_a_can_download_own_clinical_document(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/clinical-documents/{security_world.tenant_a.clinical_document.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert response.status_code == 200, response.text
    assert response.content == security_world.tenant_a.clinical_document_content
    assert response.headers["content-type"].startswith("application/pdf")


def test_company_a_cannot_download_company_b_clinical_document(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/clinical-documents/{security_world.tenant_b.clinical_document.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert_denied(response)
    assert security_world.tenant_b.clinical_document_content not in response.content
    assert str(security_world.tenant_b.clinical_document.pdf_storage_path) not in response.text


def test_clinical_document_path_traversal_record_is_not_delivered(api_client, db_session, security_world) -> None:
    document = db_session.scalar(select(ClinicalDocument).where(ClinicalDocument.id == security_world.tenant_a.clinical_document.id))
    document.pdf_storage_path = "../outside.pdf"
    db_session.commit()
    response = api_client.get(
        f"/api/clinical-documents/{document.id}/pdf",
        token=security_world.tenant_a.dentist_admin.token,
    )
    assert response.status_code == 400, response.text
    assert b"outside" not in response.content
