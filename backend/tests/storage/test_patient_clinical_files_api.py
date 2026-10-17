from uuid import UUID
from io import BytesIO
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor

from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.agenda import Patient
from app.models.clinical_file import ClinicalFile
from app.services import clinical_file_service


def synthetic_pdf(text="Synthetic clinical file") -> bytes:
    output = BytesIO(); document = canvas.Canvas(output); document.drawString(72, 720, text); document.save(); return output.getvalue()


PDF = synthetic_pdf()
PDF_B = synthetic_pdf("Different synthetic file")


def upload(api_client, tenant, *, content=PDF, name="synthetic-xray.pdf", token=None, idempotency_key="12345678-1234-4234-9234-123456789abc", file_type="RADIOGRAPH", patient_id=None):
    return api_client.post(
        f"/api/patients/{patient_id or tenant.patient.id}/clinical-files",
        token=token or tenant.dentist_admin.token,
        data={"tipo": file_type, "categoria": "INITIAL", "descripcion": "Radiografía sintética", "idempotency_key": idempotency_key},
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
    assert upload(api_client, tenant, content=b"%PDF-1.7 fake %%EOF", idempotency_key="62345678-1234-4234-9234-123456789abc").status_code == 415
    structural_fake = b"%PDF-1.7 /Type /Pages /Type /Page startxref\n10\n%%EOF"
    assert upload(api_client, tenant, content=structural_fake, idempotency_key="72345678-1234-4234-9234-123456789abc").status_code == 415
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
    conflict = upload(api_client, tenant, content=PDF + b"different", idempotency_key=key)
    assert conflict.status_code == 409
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


def test_concurrent_idempotent_uploads_create_one_record(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    key = "82345678-1234-4234-9234-123456789abc"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: upload(api_client, tenant, idempotency_key=key), range(2)))
    assert [response.status_code for response in responses] == [201, 201]
    assert len({response.json()["id"] for response in responses}) == 1
    count = len(list(db_session.scalars(select(ClinicalFile).where(ClinicalFile.company_id == tenant.company.id, ClinicalFile.idempotency_key == UUID(key)))))
    assert count == 1
    record = db_session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == tenant.company.id, ClinicalFile.idempotency_key == UUID(key)))
    path = clinical_file_service.resolve_storage_key(record.storage_key)
    assert path.read_bytes() == PDF
    assert api_client.get(f"/api/clinical-files/{record.id}/download", token=tenant.dentist_admin.token).content == PDF


def test_concurrent_conflicting_payload_never_overwrites_winner(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    key = "92345678-1234-4234-9234-123456789abc"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda content: upload(api_client, tenant, content=content, idempotency_key=key), (PDF, PDF_B)))
    assert sorted(response.status_code for response in responses) == [201, 409]
    record = db_session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == tenant.company.id, ClinicalFile.idempotency_key == UUID(key)))
    db_session.refresh(record)
    path = clinical_file_service.resolve_storage_key(record.storage_key)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record.sha256
    assert api_client.get(f"/api/clinical-files/{record.id}/download", token=tenant.dentist_admin.token).content == path.read_bytes()


def test_same_key_conflicts_across_type_and_patient_without_extra_candidates(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    other = Patient(company_id=tenant.company.id, first_names="Paciente", last_names="Sintético Dos", document_type="CC", document="SYNTH-2", normalized_document="SYNTH-2", mobile="+573000000001", normalized_mobile="573000000001", status="Activo", search_text="paciente sintetico dos", profile_complete=True, created_by=tenant.dentist_admin.user.id, updated_by=tenant.dentist_admin.user.id)
    db_session.add(other); db_session.commit()
    key = "a2345678-1234-4234-9234-123456789abc"
    assert upload(api_client, tenant, idempotency_key=key).status_code == 201
    assert upload(api_client, tenant, idempotency_key=key, file_type="EXAM").status_code == 409
    assert upload(api_client, tenant, idempotency_key=key, patient_id=other.id).status_code == 409
    records = list(db_session.scalars(select(ClinicalFile).where(ClinicalFile.company_id == tenant.company.id, ClinicalFile.idempotency_key == UUID(key))))
    assert len(records) == 1
    upload_dir = clinical_file_service.resolve_storage_key(f"company_{tenant.company.id}/uploads")
    assert len([path for path in upload_dir.iterdir() if path.name == str(records[0].id)]) == 1


def test_interrupted_promotion_is_inventoried_and_retry_recovers(api_client, db_session, monkeypatch, security_world):
    tenant = security_world.tenant_a
    key = "b2345678-1234-4234-9234-123456789abc"
    original = clinical_file_service._private_directory
    monkeypatch.setattr(clinical_file_service, "_private_directory", lambda _: (_ for _ in ()).throw(OSError("synthetic crash")))
    interrupted = upload(api_client, tenant, idempotency_key=key)
    assert interrupted.status_code == 500
    record = db_session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == tenant.company.id, ClinicalFile.idempotency_key == UUID(key)))
    db_session.refresh(record)
    assert record.storage_status == "PENDING"
    assert db_session.scalar(select(AuditEvent).where(AuditEvent.entity_id == record.id, AuditEvent.action == "CLINICAL_FILE_UPLOAD_REGISTERED")) is not None
    monkeypatch.setattr(clinical_file_service, "_private_directory", original)
    recovered = upload(api_client, tenant, idempotency_key=key)
    assert recovered.status_code == 201
    db_session.refresh(record)
    assert record.storage_status == "AVAILABLE"
    assert api_client.get(f"/api/clinical-files/{record.id}/download", token=tenant.dentist_admin.token).content == PDF
