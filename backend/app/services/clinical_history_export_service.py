import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Dentist, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalAllergy, ClinicalEvolution, ClinicalEvolutionAddendum, ClinicalMedicalHistoryItem, ClinicalMedication, ClinicalRecord
from app.models.company import Company
from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.site import Site
from app.models.treatment import Treatment, TreatmentProcedure
from app.models.user import User
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.document_style import apply_reportlab_font, resolve_readable_document_heading_color
from app.utils.clinical_dates import format_human_date, format_human_datetime_in_timezone, format_human_local_datetime
from app.utils.clinical_labels import (
    evolution_status_label,
    humanize_clinical_code,
    humanize_legacy_value,
    legacy_clinical_field_label,
    sex_label,
    surface_label,
    treatment_status_label,
    zone_label,
)
from app.utils.medical_history import (
    is_current_positive_medical_history,
    is_legacy_medical_history_questionnaire,
    is_legacy_medical_history_record,
    medical_history_response_label,
    medical_history_type_label,
)


class ClinicalHistoryExportError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ClinicalHistoryExport:
    content: bytes
    filename: str
    sha256: str


def _text(value: object | None) -> str:
    return escape(str(value).strip()) if value not in (None, "") else "No registrado"


def _present(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _has_legacy_value(value: object | None) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _table(values: list[tuple[str, object | None]], styles: dict) -> Table:
    result = Table(
        [[Paragraph(f"<b>{escape(label)}</b>", styles["BodyText"]), Paragraph(_text(value), styles["BodyText"])] for label, value in values],
        colWidths=[48 * mm, 125 * mm],
    )
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def _stacked_table(values: list[tuple[str, list[str]]], styles: dict) -> Table:
    rows = []
    for label, details in values:
        detail_flowables = [Paragraph(escape(detail), styles["BodyText"]) for detail in details if detail]
        rows.append([
            Paragraph(f"<b>{escape(label)}</b>", styles["BodyText"]),
            detail_flowables or Paragraph("", styles["BodyText"]),
        ])
    result = Table(rows, colWidths=[48 * mm, 125 * mm], repeatRows=0)
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def _compact_response_table(values: list[tuple[str, str]], styles: dict) -> Table:
    result = Table(
        [
            [
                Paragraph(escape(label).capitalize(), styles["BodyText"]),
                Paragraph(escape(value), styles["BodyText"]),
            ]
            for label, value in values
        ],
        colWidths=[115 * mm, 58 * mm],
        repeatRows=0,
    )
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.2, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return result


def _joined_details(*values: object | None) -> str | None:
    present = [_present(value) for value in values]
    return " · ".join(value for value in present if value) or None


def _medical_rows(items: list[ClinicalMedicalHistoryItem]) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for item in items:
        details = [humanize_clinical_code(item.status)]
        if item.severity:
            details.append(f"Severidad: {humanize_clinical_code(item.severity)}")
        if item.detail:
            details.append(item.detail)
        rows.append((medical_history_type_label(item.type), details))
    return rows


def _allergy_rows(items: list[ClinicalAllergy]) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for item in items:
        summary = _joined_details(
            humanize_clinical_code(item.status) if _present(item.status) else None,
            humanize_clinical_code(item.severity) if item.severity else None,
        )
        details = [value for value in [
            summary,
            f"Reacción: {item.reaction}" if item.reaction else None,
            f"Observación: {item.observations}" if item.observations else None,
        ] if value]
        rows.append((item.substance, details))
    return rows


def _medication_rows(items: list[ClinicalMedication]) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for item in items:
        summary = _joined_details(
            humanize_clinical_code(item.status) if _present(item.status) else None,
            item.dose,
            item.frequency,
            f"Vía: {item.route}" if item.route else None,
        )
        details = [value for value in [
            summary,
            f"Desde: {item.since}" if item.since else None,
            f"Motivo: {item.reason}" if item.reason else None,
            f"Prescriptor: {item.prescriber}" if item.prescriber else None,
            f"Observación: {item.observations}" if item.observations else None,
        ] if value]
        rows.append((item.name, details))
    return rows


def _odontogram_rows(values: list[tuple[OdontogramEventDetail, str]]) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    for detail, name in values:
        tooth = detail.tooth_code or "General"
        surfaces = [surface_label(surface) for surface in (detail.surfaces or [])]
        location = ", ".join(surfaces) if surfaces else "Superficie no especificada"
        grouped.setdefault(tooth, []).append(f"{name} · {location}")
    return [(f"Pieza {tooth}", findings) for tooth, findings in grouped.items()]


def _legacy_rows(values: dict) -> list[tuple[str, list[str]]]:
    return [
        (legacy_clinical_field_label(key), [rendered])
        for key, value in values.items()
        if (rendered := humanize_legacy_value(value)) is not None
    ]


def _procedure_details(item: TreatmentProcedure) -> list[str]:
    details = [treatment_status_label(item.status)]
    scope = (item.scope_type or "").upper()
    tooth = _present(item.tooth)
    if tooth and tooth.upper() in {"GENERAL", "NOT_APPLICABLE", "NO_APLICA", "N/A"}:
        tooth = None
    surfaces = [
        surface_label(value)
        for value in (item.surfaces or [])
        if str(value).strip().upper() not in {"GENERAL", "NOT_APPLICABLE", "NO_APLICA", "N/A"}
    ]
    if scope == "GENERAL" or (not tooth and not surfaces and not item.zone):
        details.append("General")
        return details
    if scope == "ZONE" and item.zone:
        label = zone_label(item.zone)
        if label:
            details.append(label)
    if tooth:
        details.append(f"Pieza {tooth}")
    if surfaces:
        details.append(", ".join(surfaces))
    return details


def _heading(story: list, value: str, styles: dict) -> None:
    story.append(Paragraph(escape(value), styles["Heading2"]))


def _subheading(story: list, value: str, styles: dict) -> None:
    story.append(Paragraph(escape(value), styles["Heading3"]))


def _narrative(story: list, values: list[tuple[str, object | None]], styles: dict) -> None:
    for label, value in values:
        story.append(Paragraph(f"<b>{escape(label)}</b>", styles["BodyText"]))
        story.append(Paragraph(_text(value), styles["BodyText"]))
        story.append(Spacer(1, 2 * mm))


def _logo(company: Company) -> Path | None:
    if not company.logo_path:
        return None
    root = Path(settings.branding_storage_dir).resolve()
    candidate = (root / company.logo_path).resolve()
    return candidate if root in candidate.parents and candidate.is_file() else None


def export_clinical_history(session: Session, context: AuthContext, patient_id, metadata: RequestMetadata) -> ClinicalHistoryExport:
    if "clinical_records.view_sensitive" not in context.permissions:
        raise ClinicalHistoryExportError("No tienes permiso para exportar esta historia.", 403)
    patient = session.scalar(select(Patient).where(Patient.id == patient_id, Patient.company_id == context.user.company_id))
    record = session.scalar(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient_id, ClinicalRecord.company_id == context.user.company_id))
    company = session.get(Company, context.user.company_id)
    if not patient or not record or not company:
        raise ClinicalHistoryExportError("Historia clínica no encontrada.", 404)
    site = session.get(Site, record.opening_site_id) if record.opening_site_id else None
    styles = getSampleStyleSheet()
    font = apply_reportlab_font(styles, company.document_font_family)
    readable_heading = resolve_readable_document_heading_color(company.heading_color)
    styles["Title"].textColor = colors.HexColor(readable_heading)
    styles["Heading1"].textColor = colors.HexColor(readable_heading)
    styles["Heading2"].textColor = colors.HexColor(readable_heading)
    styles["Heading2"].spaceBefore = 4 * mm
    styles["Heading2"].spaceAfter = 2 * mm
    styles["Heading2"].keepWithNext = True
    styles["Heading3"].spaceBefore = 2 * mm
    styles["Heading3"].spaceAfter = 1.5 * mm
    styles["Heading3"].keepWithNext = True
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=15 * mm, bottomMargin=16 * mm)
    story: list = []
    logo = _logo(company)
    if logo:
        story.append(Image(str(logo), width=28 * mm, height=18 * mm, kind="proportional"))
    contact = " · ".join(part for part in [site.name if site else None, site.address if site else company.address, site.phone if site else company.phone, company.email] if part)
    story.extend([
        Paragraph(_text(company.legal_name or company.name), styles["Title"]),
        Paragraph("HISTORIA CLÍNICA ODONTOLÓGICA", styles["Heading1"]),
        Paragraph(_text(contact), styles["BodyText"]),
        Paragraph(f"Generado: {format_human_local_datetime(datetime.now(timezone.utc), company, site)}", styles["BodyText"]),
    ])
    _heading(story, "Paciente", styles)
    story.append(_table([("Nombre", f"{patient.first_names} {patient.last_names}"), ("Documento", f"{patient.document_type}: {patient.document or 'No registrado'}"), ("Fecha de nacimiento", format_human_date(patient.birth_date)), ("Sexo", sex_label(patient.sex)), ("Teléfono", patient.mobile), ("Correo", patient.email)], styles))
    _heading(story, "Historia clínica inicial", styles)
    initial_history = [("Motivo de consulta", record.chief_complaint), ("Anamnesis", record.current_situation), ("Hábitos", (record.habits or {}).get("notes")), ("Antecedentes odontológicos", (record.dental_history or {}).get("summary")), ("Observaciones", record.observations)]
    initial_history = [(label, value) for label, value in initial_history if _present(value)]
    if initial_history:
        _narrative(story, initial_history, styles)
    else:
        story.append(Paragraph("Sin información clínica inicial registrada.", styles["BodyText"]))
    medical = list(session.scalars(
        select(ClinicalMedicalHistoryItem)
        .where(
            ClinicalMedicalHistoryItem.company_id == company.id,
            ClinicalMedicalHistoryItem.patient_id == patient_id,
        )
        .order_by(ClinicalMedicalHistoryItem.created_at, ClinicalMedicalHistoryItem.type)
    ))
    has_legacy_medical = is_legacy_medical_history_questionnaire(medical)
    historical_medical = [
        item
        for item in medical
        if has_legacy_medical
        and is_legacy_medical_history_record(item, medical)
        and not is_current_positive_medical_history(item)
    ]
    legacy = [("Inicio de la situación", record.situation_start), ("Síntomas", record.symptoms), ("Evolución inicial", record.situation_evolution), ("Tratamientos previos", record.previous_treatments)]
    old_habits = {
        key: value
        for key, value in (record.habits or {}).items()
        if key != "notes" and _has_legacy_value(value)
    }
    old_dental = {
        key: value
        for key, value in (record.dental_history or {}).items()
        if key != "summary" and _has_legacy_value(value)
    }
    if any(value for _, value in legacy) or old_habits or old_dental or historical_medical:
        _heading(story, "Información histórica preservada", styles)
        legacy_values = [(label, value) for label, value in legacy if _present(value)]
        if legacy_values:
            _subheading(story, "Datos clínicos iniciales históricos", styles)
            _narrative(story, legacy_values, styles)
        habit_rows = _legacy_rows(old_habits)
        if habit_rows:
            _subheading(story, "Hábitos históricos", styles)
            story.append(_stacked_table(habit_rows, styles))
        dental_rows = _legacy_rows(old_dental)
        if dental_rows:
            _subheading(story, "Antecedentes odontológicos históricos", styles)
            story.append(_stacked_table(dental_rows, styles))
        if historical_medical:
            _subheading(story, "Respuestas históricas de antecedentes médicos", styles)
            story.append(_compact_response_table([
                (medical_history_type_label(item.type), medical_history_response_label(item))
                for item in historical_medical
            ], styles))
    current_medical = [item for item in medical if is_current_positive_medical_history(item)]
    _heading(story, "Antecedentes médicos", styles)
    if current_medical:
        story.append(_stacked_table(_medical_rows(current_medical), styles))
    else:
        story.append(Paragraph("Sin antecedentes médicos vigentes registrados.", styles["BodyText"]))
    allergies = list(session.scalars(select(ClinicalAllergy).where(ClinicalAllergy.company_id == company.id, ClinicalAllergy.patient_id == patient_id)))
    medications = list(session.scalars(select(ClinicalMedication).where(ClinicalMedication.company_id == company.id, ClinicalMedication.patient_id == patient_id)))
    _heading(story, "Alergias y medicamentos", styles)
    allergy_medication_rows = _allergy_rows(allergies) + _medication_rows(medications)
    if allergy_medication_rows:
        story.append(_stacked_table(allergy_medication_rows, styles))
    else:
        story.append(Paragraph("Sin registros.", styles["BodyText"]))
    odontogram_rows = list(session.execute(select(OdontogramEventDetail, OdontogramCatalogItem.name).join(OdontogramEvent, OdontogramEvent.id == OdontogramEventDetail.event_id).join(OdontogramCatalogItem, OdontogramCatalogItem.id == OdontogramEventDetail.catalog_item_id).where(OdontogramEvent.company_id == company.id, OdontogramEvent.patient_id == patient_id, OdontogramEvent.status == "CONFIRMED").order_by(OdontogramEventDetail.tooth_code)))
    _heading(story, "Odontograma", styles)
    if odontogram_rows:
        story.append(_stacked_table(_odontogram_rows(odontogram_rows), styles))
    else:
        story.append(Paragraph("Sin registros odontológicos confirmados.", styles["BodyText"]))
    treatments = list(session.scalars(select(Treatment).where(Treatment.company_id == company.id, Treatment.patient_id == patient_id).order_by(Treatment.created_at)))
    procedures = list(session.scalars(select(TreatmentProcedure).where(TreatmentProcedure.company_id == company.id, TreatmentProcedure.patient_id == patient_id).order_by(TreatmentProcedure.created_at)))
    _heading(story, "Tratamientos y procedimientos clínicos", styles)
    treatment_rows = [(f"Tratamiento: {item.name}", [treatment_status_label(item.status)]) for item in treatments] + [(f"Procedimiento: {item.name}", [" · ".join(_procedure_details(item))]) for item in procedures]
    if treatment_rows:
        story.append(_stacked_table(treatment_rows, styles))
    else:
        story.append(Paragraph("Sin registros.", styles["BodyText"]))
    evolutions = list(session.scalars(select(ClinicalEvolution).where(ClinicalEvolution.company_id == company.id, ClinicalEvolution.patient_id == patient_id, ClinicalEvolution.status.in_(["SIGNED", "VOIDED_BY_COMPENSATING_RECORD"])).order_by(ClinicalEvolution.attended_at)))
    _heading(story, "Evoluciones clínicas", styles)
    fields = [("Evolución", "evolution_text"), ("Motivo", "reason"), ("Subjetivo", "subjective"), ("Objetivo", "objective"), ("Evaluación", "assessment"), ("Procedimiento realizado", "performed_procedure"), ("Anestesia", "anesthesia"), ("Materiales", "materials"), ("Medicamentos administrados", "administered_medications"), ("Hallazgos", "findings"), ("Complicaciones", "complications"), ("Indicaciones", "indications"), ("Recomendaciones", "recommendations"), ("Observaciones", "observations")]
    if not evolutions:
        story.append(Paragraph("Sin evoluciones clínicas firmadas.", styles["BodyText"]))
    for evolution in evolutions:
        dentist = session.get(Dentist, evolution.dentist_id)
        signer = session.get(User, evolution.signed_by) if evolution.signed_by else None
        professional = dentist.name if dentist else (signer.name if signer else "Profesional no disponible")
        story.append(KeepTogether([
            Paragraph(f"<b>{escape(format_human_datetime_in_timezone(evolution.attended_at, evolution.timezone_name))}</b>", styles["BodyText"]),
            Paragraph(f"{escape(professional)} · {escape(evolution_status_label(evolution.status))}", styles["BodyText"]),
            Spacer(1, 1.5 * mm),
        ]))
        values = [(label, getattr(evolution, attr)) for label, attr in fields if getattr(evolution, attr)]
        if values:
            _narrative(story, values, styles)
        addenda = list(session.scalars(select(ClinicalEvolutionAddendum).where(ClinicalEvolutionAddendum.evolution_id == evolution.id).order_by(ClinicalEvolutionAddendum.created_at)))
        for addendum in addenda:
            addendum_dentist = session.get(Dentist, addendum.dentist_id)
            story.append(KeepTogether([
                Paragraph("<b>Adenda</b>", styles["BodyText"]),
                Paragraph(escape(format_human_datetime_in_timezone(addendum.created_at, evolution.timezone_name)), styles["BodyText"]),
                Paragraph(escape(addendum_dentist.name if addendum_dentist else "Profesional no disponible"), styles["BodyText"]),
            ]))
            _narrative(story, [("Motivo", addendum.reason), ("Contenido", addendum.content)], styles)
        story.extend([
            HRFlowable(width="100%", thickness=0.35, color=colors.HexColor("#cbd5e1"), spaceBefore=2 * mm, spaceAfter=3 * mm),
        ])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font.regular, 8)
        canvas.drawCentredString(A4[0] / 2, 8 * mm, f"Historia clínica · página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    content = buffer.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    session.add(AuditEvent(company_id=company.id, user_id=context.user.id, session_id=context.auth_session.id, entity="clinical_record", entity_id=record.id, action="CLINICAL_HISTORY_EXPORTED", result="SUCCESS", detail={"patient_id": str(patient_id), "format": "PDF", "sha256": digest, "bytes": len(content)}, ip_address=metadata.ip_address, user_agent=metadata.user_agent))
    session.commit()
    return ClinicalHistoryExport(content, f"historia-clinica-{patient_id}.pdf", digest)
