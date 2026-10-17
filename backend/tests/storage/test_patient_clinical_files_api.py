from uuid import UUID
from io import BytesIO
import os

from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.clinical_file import ClinicalFile
from app.services import clinical_file_service


def synthetic_pdf() -> bytes:
    output = BytesIO(); document = canvas.Canvas(output); document.drawString(72, 720, "Synthetic clinical file"); document.save(); return output.getvalue()


PDF = synthetic_pdf()


def upload(api_client, tenant, *, content=PDF, name="synthetic-xray.pdf", token=None, idempotency_key="12345678-1234-4234-9234-123456789abc"):
    return api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-files",
        token=token or tenant.dentist_admin.token,
        data={"tipo": "RADIOGRAPH", "categoria": "INITIAL", "descripcion": "Radiografía sintética", "idempotency_key": idempotency_key},
        files={"archivo": (name, content, "application/pdf")},
    )


def test_upload_list_download_and_soft_deactivate_are_audited(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    created = upload(api_client, tenant)
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["original_name"] == "synthetic-xray.pdf"
    assert item["sha256"]

    listed = api_client.get(f"/api/patients/{tenant.patient.id}/clinical-files", token=tenant.dentist_admin.token)
    assert listed.status_code == 200
    assert [entry["id"] for entry in listed.json()["items"]] == [item["id"]]

    downloaded = api_client.get(f"/api/clinical-files/{item['id']}/download", token=tenant.dentist_admin.token)
    assert downloaded.status_code == 200
    assert downloaded.content == PDF
    assert downloaded.headers["cache-control"] == "private, no-store"

    retired = api_client.post(f"/api/clinical-files/{item['id']}/deactivate", token=tenant.dentist_admin.token, json={"reason": "Carga duplicada sintética"})
    assert retired.status_code == 204, retired.text
    assert api_client.get(f"/api/clinical-files/{item['id']}/download", token=tenant.dentist_admin.token).status_code == 404
    record = db_session.get(ClinicalFile, UUID(item["id"])); db_session.refresh(record)
    assert record is not None and record.is_active is False and record.deactivated_at is not None
    actions = set(db_session.scalars(select(AuditEvent.action).where(AuditEvent.entity_id == record.id)))
    assert {"CLINICAL_FILE_UPLOADED", "CLINICAL_FILE_DOWNLOAD_AUTHORIZED", "CLINICAL_FILE_DEACTIVATED"} <= actions


def test_tenant_isolation_permissions_and_authentication(api_client, security_world):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    item = upload(api_client, tenant_a).json()
    assert api_client.get(f"/api/patients/{tenant_a.patient.id}/clinical-files").status_code == 401
    assert upload(api_client, tenant_a, token=tenant_a.secretary.token).status_code == 403
    assert api_client.get(f"/api/patients/{tenant_a.patient.id}/clinical-files", token=tenant_a.secretary.token).status_code == 403
    assert api_client.get(f"/api/clinical-files/{item['id']}/download", token=tenant_b.dentist_admin.token).status_code == 404
    assert api_client.get(f"/api/patients/{tenant_a.patient.id}/clinical-files", token=tenant_b.dentist_admin.token).status_code == 404
    assert upload(api_client, tenant_a, token=tenant_b.dentist_admin.token).status_code == 404
    assert upload(api_client, tenant_a, token=tenant_a.dentist.token, idempotency_key="22345678-1234-4234-9234-123456789abc").status_code == 201
    assert api_client.post(f"/api/clinical-files/{item['id']}/deactivate", token=tenant_a.dentist.token, json={"reason": "No autorizado"}).status_code == 403


def test_rejects_invalid_empty_and_oversized_content(api_client, monkeypatch, security_world):
    tenant = security_world.tenant_a
    assert upload(api_client, tenant, content=b"<svg>not allowed</svg>", name="xray.pdf").status_code == 415
    assert upload(api_client, tenant, content=b"").status_code == 422
    monkeypatch.setattr(clinical_file_service, "MAX_SIZE", 16)
    oversized = upload(api_client, tenant, content=b"%PDF-1.7" + b"x" * 20)
    assert oversized.status_code == 413


def test_rejects_cross_patient_relationships_and_sanitizes_name(api_client, security_world):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    response = api_client.post(
        f"/api/patients/{tenant_a.patient.id}/clinical-files",
        token=tenant_a.dentist_admin.token,
        data={"tipo": "EXAM", "categoria": "GENERAL", "tratamiento_id": str(tenant_b.treatment.id), "idempotency_key": "32345678-1234-4234-9234-123456789abc"},
        files={"archivo": ("../../patient-name.pdf", PDF, "application/pdf")},
    )
    assert response.status_code == 422
    safe = upload(api_client, tenant_a, name="../../patient-name.pdf", idempotency_key="42345678-1234-4234-9234-123456789abc")
    assert safe.status_code == 201
    assert safe.json()["original_name"] == "patient-name.pdf"


def test_idempotency_private_modes_integrity_audit_and_blank_reason(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    key = "52345678-1234-4234-9234-123456789abc"
    first = upload(api_client, tenant, idempotency_key=key); second = upload(api_client, tenant, idempotency_key=key)
    assert first.status_code == second.status_code == 201 and first.json()["id"] == second.json()["id"]
    record = db_session.get(ClinicalFile, UUID(first.json()["id"])); db_session.refresh(record)
    path = clinical_file_service.resolve_storage_key(record.storage_key)
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert os.stat(path.parent).st_mode & 0o777 == 0o700
    assert api_client.post(f"/api/clinical-files/{record.id}/deactivate", token=tenant.dentist_admin.token, json={"reason": "     "}).status_code == 422
    path.write_bytes(b"tampered")
    response = api_client.get(f"/api/clinical-files/{record.id}/download", token=tenant.dentist_admin.token)
    assert response.status_code == 410
    event = db_session.scalar(select(AuditEvent).where(AuditEvent.entity_id == record.id, AuditEvent.action == "CLINICAL_FILE_INTEGRITY_FAILED"))
    assert event is not None and event.result == "FAILURE"
