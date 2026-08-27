from datetime import datetime, timedelta, timezone
from uuid import uuid4

import fitz
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalAllergy, ClinicalEvolution, ClinicalEvolutionAddendum, ClinicalMedicalHistoryItem, ClinicalMedication
from app.models.company import Company
from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import TreatmentProcedure
from app.services.clinical_history_export_service import _allergy_rows, _legacy_rows, _medication_rows, _procedure_details
from app.services.document_style import (
    DOCUMENT_FONTS,
    resolve_document_font,
    resolve_readable_document_heading_color,
    validate_document_font,
)
from app.utils.clinical_dates import format_human_date, format_human_datetime_in_timezone, format_human_local_datetime
from app.utils.clinical_labels import evolution_status_label, legacy_clinical_field_label, sex_label, surface_label
from app.utils.medical_history import (
    LEGACY_MEDICAL_HISTORY_TYPES,
    is_current_positive_medical_history,
    is_legacy_medical_history_questionnaire,
    medical_history_response_label,
)


def _seed_legacy_medical_questionnaire(db_session, tenant, values: dict[str, str]):
    items = []
    for item_type in sorted(LEGACY_MEDICAL_HISTORY_TYPES):
        item = ClinicalMedicalHistoryItem(
            company_id=tenant.company.id,
            clinical_record_id=tenant.clinical_record.id,
            patient_id=tenant.patient.id,
            type=item_type,
            present=values.get(item_type, "NO"),
            status="activo",
            created_by=tenant.dentist_admin.user.id,
        )
        db_session.add(item)
        items.append(item)
    db_session.flush()
    return items


def test_free_medical_history_lifecycle_is_audited(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    record = tenant.clinical_record
    created = api_client.put(
        f"/api/patients/{tenant.patient.id}/medical-history",
        token=tenant.dentist_admin.token,
        json={
            "record_version": record.version,
            "medical_history_state": "CON_ANTECEDENTES",
            "items": [
                {"type": "Hipertensión controlada", "detail": "En seguimiento", "present": "SI", "status": "activo"},
                {"type": "Asma", "detail": None, "present": "SI", "status": "activo"},
            ],
        },
    )
    assert created.status_code == 200, created.text
    item = created.json()["items"][0]
    assert item["created_by_name"]
    deactivated = api_client.put(
        f"/api/patients/{tenant.patient.id}/medical-history",
        token=tenant.dentist_admin.token,
        json={
            "record_version": created.json()["record_version"],
            "medical_history_state": "CON_ANTECEDENTES",
            "items": [{"id": item["id"], "type": item["type"], "detail": item["detail"], "present": "SI", "status": "inactivo", "version": item["version"]}],
        },
    )
    assert deactivated.status_code == 200, deactivated.text
    deactivated_item = next(entry for entry in deactivated.json()["items"] if entry["id"] == item["id"])
    reactivated = api_client.put(
        f"/api/patients/{tenant.patient.id}/medical-history",
        token=tenant.dentist_admin.token,
        json={
            "record_version": deactivated.json()["record_version"],
            "medical_history_state": "CON_ANTECEDENTES",
            "items": [{**deactivated_item, "status": "activo"}],
        },
    )
    assert reactivated.status_code == 200, reactivated.text
    stored = db_session.get(ClinicalMedicalHistoryItem, item["id"])
    db_session.refresh(stored)
    assert stored.status == "activo"
    actions = set(db_session.scalars(select(AuditEvent.action).where(AuditEvent.entity_id == stored.id)))
    assert {"CLINICAL_MEDICAL_HISTORY_CREATED", "CLINICAL_MEDICAL_HISTORY_DEACTIVATED", "CLINICAL_MEDICAL_HISTORY_REACTIVATED"} <= actions
    summary = api_client.get(f"/api/patients/{tenant.patient.id}/clinical-summary", token=tenant.dentist_admin.token)
    assert summary.status_code == 200
    assert {entry["type"] for entry in summary.json()["relevant_medical_history"]} >= {"Hipertensión controlada", "Asma"}


def test_clinical_history_pdf_is_tenant_scoped_and_audited(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    tenant.clinical_record.current_situation = "Anamnesis con caracteres: áéíóú ñ <seguro>. " * 1200
    db_session.commit()
    response = api_client.get(
        f"/api/patients/{tenant.patient.id}/clinical-record/pdf",
        token=tenant.dentist_admin.token,
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
    pdf = fitz.open(stream=response.content, filetype="pdf")
    assert pdf.page_count >= 10
    extracted = "\n".join(page.get_text() for page in pdf)
    assert "Anamnesis" in extracted
    assert "Evoluciones clínicas" in extracted
    assert all(f"Historia clínica · página {page_number}" in pdf[page_number - 1].get_text() for page_number in range(1, pdf.page_count + 1))
    assert response.headers.get("x-content-sha256")
    audit = db_session.scalar(select(AuditEvent).where(AuditEvent.action == "CLINICAL_HISTORY_EXPORTED", AuditEvent.entity_id == tenant.clinical_record.id).order_by(AuditEvent.occurred_at.desc()))
    assert audit is not None
    cross = api_client.get(
        f"/api/patients/{security_world.tenant_b.patient.id}/clinical-record/pdf",
        token=tenant.dentist_admin.token,
    )
    assert cross.status_code == 404
    denied = api_client.get(
        f"/api/patients/{tenant.patient.id}/clinical-record/pdf",
        token=tenant.secretary.token,
    )
    assert denied.status_code == 403
    platform_denied = api_client.get(
        f"/api/patients/{tenant.patient.id}/clinical-record/pdf",
        token=security_world.platform_admin.token,
    )
    assert platform_denied.status_code == 403


def test_clinical_history_pdf_handles_partial_record_without_signed_evolutions(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    tenant.clinical_record.current_situation = None
    tenant.clinical_record.habits = {}
    tenant.clinical_record.dental_history = {}
    tenant.evolution.status = "DRAFT"
    db_session.commit()
    response = api_client.get(f"/api/patients/{tenant.patient.id}/clinical-record/pdf", token=tenant.dentist_admin.token)
    assert response.status_code == 200, response.text
    pdf = fitz.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in pdf)
    assert "Sin evoluciones clínicas firmadas" in text


def test_document_font_allowlist_and_tenant_setting(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    company = db_session.get(Company, tenant.company.id)
    company.document_font_family = "TIMES_COMPATIBLE"
    db_session.commit()
    branding = api_client.get("/api/company/branding", token=tenant.admin.token)
    assert branding.status_code == 200
    assert branding.json()["document_font_family"] == "TIMES_COMPATIBLE"


def test_document_font_catalog_is_closed_and_resolvable() -> None:
    assert set(DOCUMENT_FONTS) == {
        "HELVETICA", "ARIAL_COMPATIBLE", "TIMES_COMPATIBLE",
        "GEORGIA_COMPATIBLE", "VERDANA_COMPATIBLE", "TREBUCHET_COMPATIBLE",
    }
    for code in DOCUMENT_FONTS:
        assert validate_document_font(code.lower()) == code
        assert resolve_document_font(code).regular in {"Helvetica", "Times-Roman"}
    try:
        validate_document_font("url(https://example.test/font.woff2)")
    except ValueError:
        pass
    else:
        raise AssertionError("Una fuente externa no debe superar la allowlist.")


def test_document_heading_color_preserves_readable_branding_and_darkens_light_colors() -> None:
    assert resolve_readable_document_heading_color("#0f172a") == "#0f172a"
    assert resolve_readable_document_heading_color("#0f766e") == "#0f766e"
    pale = resolve_readable_document_heading_color("#fef08a")
    white = resolve_readable_document_heading_color("#ffffff")
    assert pale not in {"#fef08a", "#0f172a"}
    assert white not in {"#ffffff", "#0f172a"}
    assert resolve_readable_document_heading_color("not-a-color") == "#0f172a"


def test_human_document_datetime_uses_site_timezone() -> None:
    class CompanyTimezone:
        timezone = "America/Santiago"

    class SiteTimezone:
        timezone = "America/Bogota"

    rendered = format_human_local_datetime(
        datetime(2026, 8, 27, 1, 9, tzinfo=timezone.utc),
        CompanyTimezone(),
        SiteTimezone(),
    )
    assert rendered == "26 de agosto de 2026, 8:09 p. m."
    assert format_human_datetime_in_timezone(
        datetime(2026, 8, 27, 1, 9, tzinfo=timezone.utc), "America/Santiago"
    ) == "26 de agosto de 2026, 9:09 p. m."
    assert format_human_datetime_in_timezone(
        datetime(2026, 8, 27, 4, 30, tzinfo=timezone.utc), "America/Bogota"
    ) == "26 de agosto de 2026, 11:30 p. m."
    assert format_human_date(datetime(1995, 1, 5, tzinfo=timezone.utc)) == "5 de enero de 1995"


def test_optional_allergy_and_medication_fields_never_create_empty_separators() -> None:
    complete_allergy = ClinicalAllergy(
        substance="Anestesia",
        status="confirmada",
        severity="severa",
        reaction="Urticaria",
        observations="Evitar exposición",
    )
    partial_allergy = ClinicalAllergy(
        substance="Látex",
        status="confirmada",
        severity="",
        reaction=None,
        observations=None,
    )
    minimal_allergy = ClinicalAllergy(
        substance="Otro",
        status="",
        severity="",
        reaction=None,
        observations=None,
    )
    complete_medication = ClinicalMedication(
        name="Ibuprofeno",
        status="activo",
        dose="media pastilla",
        frequency="cada 8 horas",
        route="oral",
        observations="Con alimentos",
    )
    partial_medication = ClinicalMedication(
        name="Acetaminofén",
        status="activo",
        dose=None,
        frequency=None,
        route=None,
        observations=None,
    )
    minimal_medication = ClinicalMedication(
        name="Otro",
        status="",
        dose=None,
        frequency=None,
        route=None,
        observations=None,
    )
    rows = _allergy_rows([complete_allergy, partial_allergy, minimal_allergy]) + _medication_rows(
        [complete_medication, partial_medication, minimal_medication]
    )
    rendered = " | ".join(detail for _, details in rows for detail in details)
    assert "Confirmada · Severa" in rendered
    assert "Activo · media pastilla · cada 8 horas · Vía: oral" in rendered
    assert "; ;" not in rendered
    assert "· ·" not in rendered
    assert rows[2] == ("Otro", [])
    assert rows[-1] == ("Otro", [])


def test_legacy_labels_values_and_unknown_keys_are_humanized_without_rewriting_free_text() -> None:
    rows = _legacy_rows({
        "alcohol": "NO",
        "bruxism": "FALSE",
        "tobacco": False,
        "dental_floss": "YES",
        "last_visit": "hace un ano",
        "unknown_legacy_field": "Texto libre EXACTO",
        "empty_value": None,
    })
    assert ("Alcohol", ["No"]) in rows
    assert ("Bruxismo", ["No"]) in rows
    assert ("Tabaco", ["No"]) in rows
    assert ("Uso de seda dental", ["Sí"]) in rows
    assert ("Última visita", ["hace un ano"]) in rows
    assert ("Unknown legacy field", ["Texto libre EXACTO"]) in rows
    assert all("_" not in label for label, _ in rows)
    assert all(label != "Empty value" for label, _ in rows)
    assert legacy_clinical_field_label("previous_experiences") == "Experiencias odontológicas previas"


def test_evolution_demographic_and_procedure_labels_cover_real_and_general_scopes() -> None:
    assert evolution_status_label("SIGNED") == "Evolución firmada"
    assert evolution_status_label("VOIDED_BY_COMPENSATING_RECORD") == "Evolución anulada"
    assert sex_label("MALE") == "Masculino"
    assert sex_label("femenino") == "Femenino"
    assert sex_label(None) == "No registrado"
    general = TreatmentProcedure(name="blanqueamiento", status="Realizado", scope_type="GENERAL", tooth=None, surfaces=None)
    real = TreatmentProcedure(name="resina", status="IN_PROGRESS", scope_type="TOOTH_SURFACE", tooth="14", surfaces=["VESTIBULAR"])
    sentinel = TreatmentProcedure(name="control", status="DONE", scope_type="GENERAL", tooth="general", surfaces=["NOT_APPLICABLE"])
    assert _procedure_details(general) == ["Realizado", "General"]
    assert _procedure_details(real) == ["En ejecución", "Pieza 14", "Vestibular"]
    assert _procedure_details(sentinel) == ["Realizado", "General"]


def test_clinical_history_pdf_uses_human_labels_and_omits_internal_notes(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    company = db_session.get(Company, tenant.company.id)
    company.heading_color = "#ffffff"
    company.document_font_family = "TIMES_COMPATIBLE"
    tenant.clinical_record.medical_history_state = "CON_ANTECEDENTES"
    db_session.add(ClinicalMedicalHistoryItem(
        company_id=company.id,
        clinical_record_id=tenant.clinical_record.id,
        patient_id=tenant.patient.id,
        type="Hipertensión",
        present="SI",
        detail="Controlada con medicamento",
        status="activo",
        created_by=tenant.dentist_admin.user.id,
    ))
    db_session.add(ClinicalAllergy(
        company_id=company.id,
        clinical_record_id=tenant.clinical_record.id,
        patient_id=tenant.patient.id,
        type="medicamento",
        substance="Anestesia",
        reaction=None,
        severity="severa",
        status="confirmada",
        observations=None,
        created_by=tenant.dentist_admin.user.id,
    ))
    db_session.add(ClinicalMedication(
        company_id=company.id,
        clinical_record_id=tenant.clinical_record.id,
        patient_id=tenant.patient.id,
        name="Ibuprofeno",
        status="activo",
        dose=None,
        frequency="cada 8 horas",
        route=None,
        created_by=tenant.dentist_admin.user.id,
    ))
    catalog = OdontogramCatalogItem(
        company_id=company.id,
        code=f"HC2_CARIES_{uuid4().hex}",
        name="Caries activa",
        type="DIAGNOSIS",
        allowed_scopes=["TOOTH_SURFACE"],
        allowed_surfaces=["LINGUAL", "OCCLUSAL"],
    )
    db_session.add(catalog)
    db_session.flush()
    event = OdontogramEvent(
        company_id=company.id,
        patient_id=tenant.patient.id,
        clinical_record_id=tenant.clinical_record.id,
        odontogram_id=tenant.odontogram.id,
        site_id=tenant.site_1.id,
        dentist_id=tenant.dentist_profile.id,
        event_type="DIAGNOSIS_ADDED",
        status="CONFIRMED",
        clinical_date=datetime.now(timezone.utc),
        timezone_name="America/Bogota",
        confirmed_by=tenant.dentist_admin.user.id,
        confirmed_at=datetime.now(timezone.utc),
        created_by=tenant.dentist_admin.user.id,
    )
    db_session.add(event)
    db_session.flush()
    db_session.add(OdontogramEventDetail(
        company_id=company.id,
        event_id=event.id,
        catalog_item_id=catalog.id,
        scope_type="TOOTH_SURFACE",
        tooth_code="11",
        dentition="PERMANENT",
        surfaces=["LINGUAL", "OCCLUSAL"],
        layer="DIAGNOSIS",
    ))
    db_session.commit()

    response = api_client.get(f"/api/patients/{tenant.patient.id}/clinical-record/pdf", token=tenant.dentist_admin.token)
    assert response.status_code == 200, response.text
    pdf = fitz.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in pdf)
    assert "Hipertensión" in text
    assert "Activo" in text
    assert "CON_ANTECEDENTES" not in text
    assert "Caries activa · Lingual, Oclusal" in text
    assert "Representación imprimible inicial" not in text
    assert "mapa gráfico de cinco caras" not in text
    assert "Sin eventos confirmados" not in text
    assert "Generado:" in text and "UTC" not in text
    assert "Anestesia" in text and "Confirmada · Severa" in text
    assert "Ibuprofeno" in text and "Activo · cada 8 horas" in text
    assert "; ;" not in text and "· ·" not in text
    assert surface_label("PALATAL") == "Palatina"
    assert "1 de enero de 1990" in text
    assert "No informa" in text
    assert "SIGNED" not in text
    assert "Firmado por" not in text
    assert "Evolución firmada" in text
    assert "2026-08-01T" not in text
    assert text.count("Dra. A") == 1
    font_names = {font[3] for page in pdf for font in page.get_fonts()}
    assert any("Times" in name for name in font_names)


def test_clinical_history_pdf_humanizes_legacy_addenda_voided_and_one_hundred_evolutions(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    tenant.clinical_record.habits = {
        "tobacco": False,
        "alcohol": "YES",
        "dental_floss": "NO",
        "unknown_habit": "Conservar texto libre",
    }
    tenant.clinical_record.dental_history = {
        "implants": "NO",
        "surgeries": "FALSE",
        "last_visit": "hace un ano",
        "observations": "ninguna",
    }
    db_session.add(ClinicalEvolutionAddendum(
        company_id=tenant.company.id,
        patient_id=tenant.patient.id,
        evolution_id=tenant.evolution.id,
        reason="Aclaración clínica",
        content="Texto de adenda sin reescritura.",
        dentist_id=tenant.dentist_profile.id,
        site_id=tenant.site_1.id,
        created_by=tenant.dentist_admin.user.id,
    ))
    base_time = datetime(2026, 8, 2, 2, 0, tzinfo=timezone.utc)
    for index in range(99):
        db_session.add(ClinicalEvolution(
            company_id=tenant.company.id,
            patient_id=tenant.patient.id,
            clinical_record_id=tenant.clinical_record.id,
            appointment_id=None,
            site_id=tenant.site_1.id,
            dentist_id=tenant.dentist_profile.id,
            attended_at=base_time + timedelta(minutes=index),
            timezone_name="America/Bogota" if index < 98 else "America/Santiago",
            evolution_text=f"Evolución histórica exacta {index}.",
            status="VOIDED_BY_COMPENSATING_RECORD" if index == 98 else "SIGNED",
            signed_at=base_time + timedelta(minutes=index),
            signed_by=tenant.dentist_admin.user.id,
            created_by=tenant.dentist_admin.user.id,
        ))
    db_session.commit()

    response = api_client.get(f"/api/patients/{tenant.patient.id}/clinical-record/pdf", token=tenant.dentist_admin.token)
    assert response.status_code == 200, response.text
    pdf = fitz.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in pdf)
    assert pdf.page_count >= 10
    assert "Hábitos históricos" in text
    assert "Antecedentes odontológicos históricos" in text
    assert "Uso de seda dental" in text
    assert "Tabaco" in text
    assert "Unknown habit" in text and "unknown_habit" not in text
    assert "hace un ano" in text
    assert "Evolución anulada" in text
    assert "VOIDED_BY_COMPENSATING_RECORD" not in text
    assert "SIGNED" not in text
    assert "Firmado por" not in text
    assert "Adenda" in text
    assert "Aclaración clínica" in text
    assert "Texto de adenda sin reescritura." in text
    assert "T02:" not in text and "T14:" not in text
    assert all(f"Historia clínica · página {number}" in pdf[number - 1].get_text() for number in range(1, pdf.page_count + 1))


def test_medical_history_semantics_and_legacy_detection_are_canonical() -> None:
    positive = ClinicalMedicalHistoryItem(type="Hipertensión", present="si", status="ACTIVO")
    negative = ClinicalMedicalHistoryItem(type="Diabetes", present="NO", status="activo")
    unknown = ClinicalMedicalHistoryItem(type="Cáncer", present="DESCONOCIDO", status="activo")
    inactive = ClinicalMedicalHistoryItem(type="Asma", present="SI", status="inactivo")
    assert is_current_positive_medical_history(positive)
    assert not is_current_positive_medical_history(negative)
    assert not is_current_positive_medical_history(unknown)
    assert not is_current_positive_medical_history(inactive)
    questionnaire = [
        ClinicalMedicalHistoryItem(type=item_type, present="NO", status="activo")
        for item_type in LEGACY_MEDICAL_HISTORY_TYPES
    ]
    assert is_legacy_medical_history_questionnaire(questionnaire)
    assert not is_legacy_medical_history_questionnaire(questionnaire[:-1])
    assert medical_history_response_label(negative) == "No"
    assert medical_history_response_label(unknown) == "Información no confirmada"


def test_legacy_medical_history_is_partitioned_between_current_and_historical_pdf(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    _seed_legacy_medical_questionnaire(
        db_session,
        tenant,
        {"hipertensión": "SI", "enfermedad renal": "DESCONOCIDO"},
    )
    tenant.clinical_record.medical_history_state = "CON_ANTECEDENTES"
    db_session.commit()

    response = api_client.get(
        f"/api/patients/{tenant.patient.id}/clinical-record/pdf",
        token=tenant.dentist_admin.token,
    )
    assert response.status_code == 200, response.text
    text = "\n".join(page.get_text() for page in fitz.open(stream=response.content, filetype="pdf"))
    assert "Respuestas históricas de antecedentes médicos" in text
    assert "Hipertensión\nActivo" in text
    assert "Diabetes\nNo" in text
    assert "Enfermedad renal\nInformación no confirmada" in text
    assert "Diabetes\nActivo" not in text
    assert "Enfermedad renal\nActivo" not in text


def test_legacy_medical_response_cannot_be_silently_changed_to_positive(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    items = _seed_legacy_medical_questionnaire(db_session, tenant, {})
    diabetes = next(item for item in items if item.type == "diabetes")
    db_session.commit()

    rejected = api_client.put(
        f"/api/patients/{tenant.patient.id}/medical-history",
        token=tenant.dentist_admin.token,
        json={
            "record_version": tenant.clinical_record.version,
            "medical_history_state": "NO_CONFIRMADO",
            "items": [{
                "id": str(diabetes.id),
                "type": diabetes.type,
                "present": "SI",
                "status": "activo",
                "version": diabetes.version,
            }],
        },
    )
    assert rejected.status_code == 409
    db_session.refresh(diabetes)
    assert diabetes.present == "NO"

    lifecycle = api_client.put(
        f"/api/patients/{tenant.patient.id}/medical-history",
        token=tenant.dentist_admin.token,
        json={
            "record_version": tenant.clinical_record.version,
            "medical_history_state": "NO_CONFIRMADO",
            "items": [{
                "id": str(diabetes.id),
                "type": diabetes.type,
                "present": "NO",
                "status": "inactivo",
                "version": diabetes.version,
            }],
        },
    )
    assert lifecycle.status_code == 200, lifecycle.text
    stored = next(item for item in lifecycle.json()["items"] if item["id"] == str(diabetes.id))
    assert stored["present"] == "NO"
    assert stored["status"] == "inactivo"


def test_clinical_summary_only_exposes_current_positive_medical_history(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    _seed_legacy_medical_questionnaire(
        db_session,
        tenant,
        {"hipertensión": "SI", "enfermedad renal": "DESCONOCIDO"},
    )
    inactive = db_session.scalar(select(ClinicalMedicalHistoryItem).where(
        ClinicalMedicalHistoryItem.patient_id == tenant.patient.id,
        ClinicalMedicalHistoryItem.type == "hipertensión",
    ))
    db_session.add(ClinicalMedicalHistoryItem(
        company_id=tenant.company.id,
        clinical_record_id=tenant.clinical_record.id,
        patient_id=tenant.patient.id,
        type="Asma",
        present="SI",
        status="inactivo",
        created_by=tenant.dentist_admin.user.id,
    ))
    db_session.commit()
    assert inactive is not None

    summary = api_client.get(
        f"/api/patients/{tenant.patient.id}/clinical-summary",
        token=tenant.dentist_admin.token,
    )
    assert summary.status_code == 200, summary.text
    visible = {item["type"] for item in summary.json()["relevant_medical_history"]}
    assert visible == {"hipertensión"}
