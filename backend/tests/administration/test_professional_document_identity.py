from datetime import date
import base64
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import fitz
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate

from app.services.clinical_document_service import _generate_pdf as generate_clinical_document_pdf
from app.services.document_style import (
    ProfessionalDocumentIdentity,
    missing_professional_identity_fields,
    professional_document_label,
    render_professional_identity_block,
    require_complete_professional_identity,
)
from app.services.prescription_service import _generate_pdf as generate_prescription_pdf
from app.services import treatment_service
from app.models.audit_event import AuditEvent
from app.core.config import settings
from sqlalchemy import select


def _pdf_text(content: bytes) -> str:
    with fitz.open(stream=content, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


def _write_test_signature(relative_path: str) -> None:
    path = Path(settings.branding_storage_dir) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
    )


def _identity() -> ProfessionalDocumentIdentity:
    return ProfessionalDocumentIdentity(
        full_name="Dra. Valentina Rojas",
        specialty="Odontología general",
        document_type="CC",
        document_number="123456789",
        professional_license="RETHUS-9988",
        email="valentina@example.test",
        signature_path="tenant/dentists/signature.png",
        signature_filename="signature.png",
    )


def _institution() -> dict:
    return {
        "company": {
            "name": "Clínica Dental Test",
            "address": "Calle 1",
            "city": "Bogotá",
            "country": "Colombia",
            "phone": "6010000000",
            "email": "clinica@example.test",
            "document_font_family": "HELVETICA",
            "primary_color": "#176b45",
            "secondary_color": "#0f766e",
            "heading_color": "#0f172a",
        },
        "site": {"name": "Sede principal", "address": "Calle 1", "phone": "6010000000"},
    }


def test_professional_identity_reports_clear_missing_fields() -> None:
    incomplete = ProfessionalDocumentIdentity(
        full_name="Dra. Valentina Rojas",
        specialty="Odontología general",
        document_type=None,
        document_number=None,
        professional_license=None,
        email="valentina@example.test",
        signature_path=None,
    )

    assert missing_professional_identity_fields(incomplete) == [
        "tipo de documento",
        "número de documento",
        "registro profesional",
        "firma gráfica",
    ]
    try:
        require_complete_professional_identity(incomplete)
    except ValueError as exc:
        assert str(exc) == (
            "No es posible finalizar el documento. Completa la identidad profesional: "
            "tipo de documento, número de documento, registro profesional, firma gráfica."
        )
    else:
        raise AssertionError("La identidad incompleta debía bloquear la finalización.")


def test_professional_document_labels_are_human_readable_and_country_neutral() -> None:
    assert professional_document_label("CC") == "Cédula de ciudadanía"
    assert professional_document_label("RUT") == "RUT"
    assert professional_document_label("RUN") == "RUN"
    assert professional_document_label("DNI") == "Documento nacional de identidad"
    assert professional_document_label("custom-id") == "custom-id"


def test_shared_block_renders_name_document_registration_and_email() -> None:
    buffer = BytesIO()
    base = getSampleStyleSheet()
    styles = {
        "body": base["BodyText"],
        "cell_bold": ParagraphStyle("IdentityBold", parent=base["BodyText"], fontName="Helvetica-Bold"),
        "small": base["BodyText"],
    }
    document = SimpleDocTemplate(buffer)
    document.build([
        render_professional_identity_block(
            _identity().snapshot(),
            styles=styles,
            show_intro=True,
        )
    ])

    text = _pdf_text(buffer.getvalue())
    assert "Dra. Valentina Rojas" in text
    assert "Documento: Cédula de ciudadanía 123456789" in text
    assert "Registro profesional: RETHUS-9988" in text
    assert "valentina@example.test" in text


def test_prescription_uses_shared_identity_and_human_birth_date() -> None:
    prescription = SimpleNamespace(
        prescription_number="RX-000001",
        clinical_date=date(2026, 8, 27),
        institution_snapshot=_institution(),
        patient_snapshot={
            "name": "Paciente Ejemplo",
            "document_type": "CC",
            "document": "9001",
            "birth_date": "1984-06-19",
            "age": 42,
            "responsible": None,
        },
        professional_snapshot={**_identity().snapshot(), "signature_path": None},
        prescription_snapshot={
            "items": [{
                "position": 1,
                "generic_name": "Acetaminofén",
                "concentration": "500 mg",
                "pharmaceutical_form": "Tableta",
                "dose": "1 tableta",
                "route": "Oral",
                "frequency": "Cada 8 horas",
                "duration": "3 días",
                "total_quantity": "9",
                "quantity_unit": "tabletas",
                "instructions": None,
                "brand_name": None,
            }],
            "general_instructions": None,
        },
    )

    text = _pdf_text(generate_prescription_pdf(prescription, []).content)
    assert "19 de junio de 1984 · 42 años" in text
    assert "1984-06-19" not in text
    assert "Documento: Cédula de ciudadanía 123456789" in text
    assert "Registro profesional: RETHUS-9988" in text


def test_clinical_document_uses_same_professional_block() -> None:
    document = SimpleNamespace(
        document_type="REFERRAL",
        document_number="DOC-000001",
        clinical_date=date(2026, 8, 27),
        institution_snapshot=_institution(),
        patient_snapshot={
            "name": "Paciente Ejemplo",
            "document_type": "CC",
            "document": "9001",
            "birth_date": "1984-06-19",
        },
        professional_snapshot={**_identity().snapshot(), "signature_path": None},
        document_snapshot={"body": "Se remite para valoración especializada."},
        recipient_name="Especialista Ejemplo",
        recipient_entity=None,
        recipient_specialty="Endodoncia",
        subject="Valoración",
    )

    text = _pdf_text(generate_clinical_document_pdf(document).content)
    assert "Dra. Valentina Rojas" in text
    assert "Documento: Cédula de ciudadanía 123456789" in text
    assert "Registro profesional: RETHUS-9988" in text
    assert "valentina@example.test" in text


def test_historical_snapshot_without_new_fields_remains_renderable() -> None:
    legacy = {
        "name": "Dr. Histórico",
        "specialty": "Odontología",
        "professional_license": "LEGACY-1",
    }
    buffer = BytesIO()
    base = getSampleStyleSheet()
    document = SimpleDocTemplate(buffer)
    document.build([
        render_professional_identity_block(
            legacy,
            styles={"cell_bold": base["BodyText"], "small": base["BodyText"]},
        )
    ])
    assert "Dr. Histórico" in _pdf_text(buffer.getvalue())


def test_tenant_updates_only_own_professional_identity_without_auditing_document_value(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other = security_world.tenant_b
    dentist = tenant.dentist_profile
    other_dentist = other.dentist_profile
    assert dentist is not None and other_dentist is not None
    payload = {
        "name": "Dra. Valentina Tenant A",
        "document_type": "CC",
        "document_number": "123456789",
        "specialty": "Odontología general",
        "professional_license": "RETHUS-9988",
    }

    updated = api_client.patch(
        f"/api/dentists/{dentist.id}/professional-profile",
        token=tenant.admin.token,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Dra. Valentina Tenant A"
    assert updated.json()["document_number"] == "123456789"
    assert updated.json()["professional_email"] == tenant.dentist_admin.user.email

    cross_tenant = api_client.patch(
        f"/api/dentists/{other_dentist.id}/professional-profile",
        token=tenant.admin.token,
        json=payload,
    )
    assert cross_tenant.status_code == 404

    forbidden = api_client.patch(
        f"/api/dentists/{dentist.id}/professional-profile",
        token=tenant.secretary.token,
        json=payload,
    )
    assert forbidden.status_code == 403

    audit = db_session.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "DENTIST_PROFESSIONAL_IDENTITY_UPDATED")
        .order_by(AuditEvent.created_at.desc())
    )
    assert audit is not None
    assert audit.detail == {
        "changed_fields": [
            "document_number",
            "document_type",
            "name",
            "professional_license",
            "specialty",
        ]
    }
    assert "123456789" not in str(audit.detail)


def test_professional_signature_is_tenant_scoped_and_owned_by_one_dentist(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other = security_world.tenant_b
    dentist = tenant.dentist_profile
    other_dentist = other.dentist_profile
    assert dentist is not None and other_dentist is not None

    tenant.company.signature_path = f"{tenant.company.id}/legacy-signature.png"
    dentist.signature_path = None
    dentist.signature_filename = None
    db_session.commit()

    listed = api_client.get("/api/dentists", token=tenant.admin.token)
    assert listed.status_code == 200, listed.text
    own = next(item for item in listed.json()["items"] if item["id"] == str(dentist.id))
    assert own["has_professional_signature"] is False
    assert own["sites"]

    uploaded = api_client.post(
        f"/api/dentists/{dentist.id}/professional-signature",
        token=tenant.admin.token,
        files={"file": ("firma.png", b"tenant-specific-signature", "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["has_professional_signature"] is True
    db_session.refresh(dentist)
    assert dentist.signature_path is not None
    assert f"/{dentist.id}/" in dentist.signature_path

    downloaded = api_client.get(
        f"/api/dentists/{dentist.id}/professional-signature",
        token=tenant.admin.token,
    )
    assert downloaded.status_code == 200
    assert downloaded.content == b"tenant-specific-signature"

    cross_tenant = api_client.post(
        f"/api/dentists/{other_dentist.id}/professional-signature",
        token=tenant.admin.token,
        files={"file": ("firma.png", b"cross-tenant", "image/png")},
    )
    assert cross_tenant.status_code == 404
    cross_tenant_download = api_client.get(
        f"/api/dentists/{other_dentist.id}/professional-signature",
        token=tenant.admin.token,
    )
    assert cross_tenant_download.status_code == 404

    deleted = api_client.delete(
        f"/api/dentists/{dentist.id}/professional-signature",
        token=tenant.admin.token,
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["has_professional_signature"] is False
    db_session.refresh(dentist)
    assert dentist.signature_path is None

    actions = set(
        db_session.scalars(
            select(AuditEvent.action).where(
                AuditEvent.entity_id == dentist.id,
                AuditEvent.action.in_(
                    {
                        "DENTIST_PROFESSIONAL_SIGNATURE_UPDATED",
                        "DENTIST_PROFESSIONAL_SIGNATURE_DELETED",
                    }
                ),
            )
        )
    )
    assert actions == {
        "DENTIST_PROFESSIONAL_SIGNATURE_UPDATED",
        "DENTIST_PROFESSIONAL_SIGNATURE_DELETED",
    }


def test_prescription_finalization_unblocks_after_completing_professional_profile(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    dentist = tenant.dentist_profile
    dentist.document_type = None
    dentist.document_number = None
    dentist.specialty = "Odontología general"
    dentist.professional_license = "REG-CO-100"
    relative_signature = f"{tenant.company.id}/dentists/{dentist.id}/test-signature.png"
    signature_path = Path(settings.branding_storage_dir) / relative_signature
    signature_path.parent.mkdir(parents=True, exist_ok=True)
    signature_path.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
    )
    dentist.signature_path = relative_signature
    dentist.signature_filename = "test-signature.png"
    db_session.commit()

    created = api_client.post(
        f"/api/patients/{tenant.patient.id}/prescriptions",
        token=tenant.dentist_admin.token,
        json={
            "site_id": str(tenant.site_1.id),
            "dentist_profile_id": str(dentist.id),
            "clinical_date": "2026-08-27",
            "items": [
                {
                    "generic_name": "Acetaminofén",
                    "pharmaceutical_form": "Tableta",
                    "concentration": "500 mg",
                    "dose": "1 tableta",
                    "route": "Oral",
                    "frequency": "Cada 8 horas",
                    "duration": "3 días",
                    "total_quantity": "9",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    prescription_id = created.json()["id"]

    blocked = api_client.post(
        f"/api/prescriptions/{prescription_id}/finalize",
        token=tenant.dentist_admin.token,
        json={"allergies_reviewed": True},
    )
    assert blocked.status_code == 422
    assert "tipo de documento, número de documento" in blocked.json()["detail"]

    completed = api_client.patch(
        f"/api/dentists/{dentist.id}/professional-profile",
        token=tenant.admin.token,
        json={
            "name": dentist.name,
            "document_type": "CC",
            "document_number": "123456789",
            "specialty": dentist.specialty,
            "professional_license": dentist.professional_license,
        },
    )
    assert completed.status_code == 200, completed.text

    finalized = api_client.post(
        f"/api/prescriptions/{prescription_id}/finalize",
        token=tenant.dentist_admin.token,
        json={"allergies_reviewed": True},
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["status"] == "FINALIZED"

    pdf = api_client.get(
        f"/api/prescriptions/{prescription_id}/pdf",
        token=tenant.dentist_admin.token,
    )
    assert pdf.status_code == 200
    pdf_text = _pdf_text(pdf.content)
    assert "Documento: Cédula de ciudadanía 123456789" in pdf_text
    assert "Registro profesional: REG-CO-100" in pdf_text


def test_budget_uses_only_responsible_dentist_identity_and_own_signature(
    api_client, db_session, security_world, monkeypatch
) -> None:
    tenant = security_world.tenant_a
    dentist = tenant.dentist_profile
    treatment = tenant.treatment
    company = tenant.company
    dentist.name = "Dra. Presupuesto Responsable"
    dentist.document_type = "CC"
    dentist.document_number = "987654321"
    dentist.specialty = "Rehabilitación oral"
    dentist.professional_license = "REG-BUDGET-100"
    dentist.signature_path = f"{company.id}/dentists/{dentist.id}/own-signature.png"
    company.primary_dentist_name = "Profesional institucional legacy"
    company.professional_specialty = "Especialidad institucional legacy"
    company.professional_license = "REG-COMPANY-LEGACY"
    company.signature_path = f"{company.id}/company-signature.png"
    company.logo_path = None
    treatment.responsible_dentist_id = dentist.id
    _write_test_signature(dentist.signature_path)
    _write_test_signature(company.signature_path)
    db_session.commit()

    requested_images: list[str | None] = []

    def record_image(path, **_kwargs):
        requested_images.append(str(path) if path else None)
        return None

    monkeypatch.setattr(treatment_service, "_image_if_exists", record_image)
    response = api_client.get(
        f"/api/budgets/{tenant.budget.id}/pdf",
        token=tenant.admin.token,
    )

    assert response.status_code == 200, response.text
    text = _pdf_text(response.content)
    assert "Dra. Presupuesto Responsable" in text
    assert "Documento: Cédula de ciudadanía 987654321" in text
    assert "Registro profesional: REG-BUDGET-100" in text
    assert tenant.dentist_admin.user.email in text
    assert "Profesional institucional legacy" not in text
    assert "REG-COMPANY-LEGACY" not in text
    assert any(path and path.endswith("own-signature.png") for path in requested_images)
    assert not any(path and path.endswith("company-signature.png") for path in requested_images)


def test_budget_without_responsible_dentist_omits_professional_block_and_company_fallback(
    api_client, db_session, security_world, monkeypatch
) -> None:
    tenant = security_world.tenant_a
    company = tenant.company
    tenant.treatment.responsible_dentist_id = None
    company.primary_dentist_name = "Profesional institucional no permitido"
    company.professional_specialty = "Especialidad institucional no permitida"
    company.professional_license = "REG-COMPANY-NOT-ALLOWED"
    company.signature_path = f"{company.id}/company-signature.png"
    company.logo_path = None
    _write_test_signature(company.signature_path)
    db_session.commit()

    requested_images: list[str | None] = []

    def record_image(path, **_kwargs):
        requested_images.append(str(path) if path else None)
        return None

    monkeypatch.setattr(treatment_service, "_image_if_exists", record_image)
    response = api_client.get(
        f"/api/budgets/{tenant.budget.id}/pdf",
        token=tenant.admin.token,
    )

    assert response.status_code == 200, response.text
    text = _pdf_text(response.content)
    assert "Profesional institucional no permitido" not in text
    assert "Especialidad institucional no permitida" not in text
    assert "REG-COMPANY-NOT-ALLOWED" not in text
    assert "Profesional no disponible" not in text
    assert not any(path and path.endswith("company-signature.png") for path in requested_images)


def test_budget_with_partial_dentist_identity_does_not_invent_company_values(
    api_client, db_session, security_world, monkeypatch
) -> None:
    tenant = security_world.tenant_a
    dentist = tenant.dentist_profile
    company = tenant.company
    dentist.name = "Dr. Identidad Parcial"
    dentist.document_type = None
    dentist.document_number = None
    dentist.specialty = None
    dentist.professional_license = None
    dentist.signature_path = None
    company.primary_dentist_name = "Nombre Company prohibido"
    company.professional_specialty = "Especialidad Company prohibida"
    company.professional_license = "REG-COMPANY-PROHIBIDO"
    company.signature_path = f"{company.id}/company-signature.png"
    company.logo_path = None
    tenant.treatment.responsible_dentist_id = dentist.id
    _write_test_signature(company.signature_path)
    db_session.commit()

    requested_images: list[str | None] = []

    def record_image(path, **_kwargs):
        requested_images.append(str(path) if path else None)
        return None

    monkeypatch.setattr(treatment_service, "_image_if_exists", record_image)
    response = api_client.get(
        f"/api/budgets/{tenant.budget.id}/pdf",
        token=tenant.admin.token,
    )

    assert response.status_code == 200, response.text
    text = _pdf_text(response.content)
    assert "Dr. Identidad Parcial" in text
    assert "Nombre Company prohibido" not in text
    assert "Especialidad Company prohibida" not in text
    assert "REG-COMPANY-PROHIBIDO" not in text
    assert not any(path and path.endswith("company-signature.png") for path in requested_images)


def test_budget_rejects_cross_tenant_responsible_dentist(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other_dentist = security_world.tenant_b.dentist_profile
    tenant.treatment.responsible_dentist_id = other_dentist.id
    db_session.commit()

    response = api_client.get(
        f"/api/budgets/{tenant.budget.id}/pdf",
        token=tenant.admin.token,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "El odontólogo responsable no está disponible para este presupuesto."
    )
    assert other_dentist.name not in response.text
