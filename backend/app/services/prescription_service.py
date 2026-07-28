import base64
import hashlib
import re
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Appointment, Dentist, DentistSite, Patient, PatientResponsible
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalAllergy, ClinicalEvolution, ClinicalMedication
from app.models.company import Company
from app.models.prescription import Prescription, PrescriptionItem
from app.models.site import Site
from app.models.treatment import Treatment
from app.schemas.prescription_schema import (
    PrescriptionCreateRequest,
    PrescriptionFinalizeRequest,
    PrescriptionItemInput,
    PrescriptionItemResponse,
    PrescriptionListResponse,
    PrescriptionPreviewResponse,
    PrescriptionResponse,
    PrescriptionUpdateRequest,
    PrescriptionVoidRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.clinical_document_service import (
    _branding_asset_path,
    _content_hash,
    _date_text,
    _image_if_exists,
    _pdf_color,
    _soft_accent_background,
    _text_on_background,
    _visible_accent,
)
from app.services.patient_service import calculate_age
from app.services.site_access_service import authorized_site_ids
from app.services.treatment_service import BudgetPdfResult


class PrescriptionError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _require_permission(context: AuthContext, permission: str) -> None:
    if permission not in context.permissions:
        raise PrescriptionError("No tienes permiso para realizar esta acción.", 403)


def _json_safe(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    prescription: Prescription,
    action: str,
    detail: dict | None = None,
    result: str = "SUCCESS",
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="prescription",
            entity_id=prescription.id,
            action=action,
            result=result,
            detail=_json_safe(detail),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _authorized_sites(session: Session, context: AuthContext) -> set[UUID]:
    return authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        active_only=True,
    )


def _require_site(session: Session, context: AuthContext, site_id: UUID) -> Site:
    if site_id not in _authorized_sites(session, context):
        raise PrescriptionError("No tienes acceso a la sede seleccionada.", 403)
    site = session.scalar(select(Site).where(Site.id == site_id, Site.company_id == context.user.company_id, Site.is_active.is_(True), Site.status == "Activa"))
    if site is None:
        raise PrescriptionError("La sede no existe o no está activa.", 404)
    return site


def _require_patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(select(Patient).where(Patient.id == patient_id, Patient.company_id == context.user.company_id, Patient.is_active.is_(True)))
    if patient is None:
        raise PrescriptionError("Paciente no encontrado.", 404)
    return patient


def _require_dentist(session: Session, context: AuthContext, dentist_id: UUID | None, site_id: UUID) -> Dentist:
    if dentist_id is None:
        dentist = session.scalar(
            select(Dentist)
            .join(DentistSite, DentistSite.dentist_id == Dentist.id)
            .where(
                Dentist.company_id == context.user.company_id,
                Dentist.user_id == context.user.id,
                Dentist.status == "Activo",
                Dentist.is_active.is_(True),
                DentistSite.site_id == site_id,
                DentistSite.is_active.is_(True),
            )
        )
        if dentist is not None:
            return dentist
        raise PrescriptionError("Seleccione el profesional firmante.", 422)
    dentist = session.scalar(
        select(Dentist)
        .join(DentistSite, DentistSite.dentist_id == Dentist.id)
        .where(
            Dentist.id == dentist_id,
            Dentist.company_id == context.user.company_id,
            Dentist.status == "Activo",
            Dentist.is_active.is_(True),
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if dentist is None:
        raise PrescriptionError("Profesional no disponible para la sede seleccionada.", 422)
    if dentist.user_id != context.user.id and "prescriptions.void" not in context.permissions:
        raise PrescriptionError("No tienes permiso para firmar con otro profesional.", 403)
    return dentist


def _validate_references(session: Session, context: AuthContext, patient_id: UUID, treatment_id: UUID | None, evolution_id: UUID | None, appointment_id: UUID | None) -> None:
    if treatment_id and not session.scalar(select(Treatment.id).where(Treatment.id == treatment_id, Treatment.company_id == context.user.company_id, Treatment.patient_id == patient_id)):
        raise PrescriptionError("Tratamiento relacionado inválido.", 422)
    if evolution_id and not session.scalar(select(ClinicalEvolution.id).where(ClinicalEvolution.id == evolution_id, ClinicalEvolution.company_id == context.user.company_id, ClinicalEvolution.patient_id == patient_id)):
        raise PrescriptionError("Evolución relacionada inválida.", 422)
    if appointment_id and not session.scalar(select(Appointment.id).where(Appointment.id == appointment_id, Appointment.company_id == context.user.company_id, Appointment.patient_id == patient_id)):
        raise PrescriptionError("Cita relacionada inválida.", 422)


def _patient_name(patient: Patient) -> str:
    return f"{patient.first_names} {patient.last_names}".strip()


def _storage_root() -> Path:
    return Path(settings.branding_storage_dir).resolve().parent / "prescriptions"


def _sanitize_filename(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return normalized[:80] or "receta"


def _storage_path(relative_path: str) -> Path:
    root = _storage_root().resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        raise PrescriptionError("Ruta de receta inválida.", 400)
    return candidate


def _snapshot_company(company: Company, site: Site) -> dict:
    return {
        "company": {
            "name": company.name,
            "legal_name": company.legal_name,
            "tax_id": company.tax_id,
            "phone": company.phone,
            "email": company.email,
            "address": company.address,
            "city": company.city,
            "country": company.country,
            "logo_path": company.logo_path,
            "primary_color": company.primary_color,
            "secondary_color": company.secondary_color,
            "heading_color": company.heading_color,
            "footer_text": company.footer_text,
        },
        "site": {
            "name": site.name,
            "address": site.address,
            "city": site.city,
            "phone": site.phone,
            "timezone": site.timezone,
        },
    }


def _snapshot_patient(session: Session, patient: Patient, reference_date: date) -> dict:
    primary_responsible = session.scalar(
        select(PatientResponsible).where(PatientResponsible.patient_id == patient.id, PatientResponsible.is_primary.is_(True), PatientResponsible.is_active.is_(True))
    )
    age = calculate_age(patient.birth_date, reference_date)
    return {
        "name": _patient_name(patient),
        "document_type": patient.document_type,
        "document": patient.document,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "age": age,
        "is_minor": age is not None and age < 18,
        "responsible": {
            "name": primary_responsible.name,
            "relationship": primary_responsible.relationship,
            "document_type": primary_responsible.document_type,
            "document": primary_responsible.document,
        } if primary_responsible else None,
    }


def _snapshot_professional(company: Company, dentist: Dentist) -> dict:
    return {
        "name": dentist.name,
        "specialty": company.professional_specialty,
        "professional_license": company.professional_license,
        "signature_path": company.signature_path,
        "signature_filename": company.signature_filename,
        "signature_source": "company_branding_professional_signature",
        "signature_notice": "Firma gráfica configurada en Dentia; no equivale a firma digital certificada.",
    }


def _clinical_alerts(session: Session, context: AuthContext, patient_id: UUID) -> dict:
    allergies = session.scalars(
        select(ClinicalAllergy)
        .where(ClinicalAllergy.company_id == context.user.company_id, ClinicalAllergy.patient_id == patient_id)
        .order_by(ClinicalAllergy.critical_alert.desc(), ClinicalAllergy.created_at.desc())
    ).all()
    medications = session.scalars(
        select(ClinicalMedication)
        .where(ClinicalMedication.company_id == context.user.company_id, ClinicalMedication.patient_id == patient_id, ClinicalMedication.status.ilike("activo"))
        .order_by(ClinicalMedication.created_at.desc())
    ).all()
    return {
        "allergies": [
            {
                "substance": item.substance,
                "reaction": item.reaction,
                "severity": item.severity,
                "status": item.status,
                "critical_alert": item.critical_alert,
            }
            for item in allergies
        ],
        "active_medications": [
            {
                "name": item.name,
                "dose": item.dose,
                "frequency": item.frequency,
                "route": item.route,
                "reason": item.reason,
            }
            for item in medications
        ],
        "warning": "Revise las alergias, medicamentos actuales y antecedentes del paciente antes de finalizar la receta.",
    }


def _items_snapshot(items: list[PrescriptionItem]) -> list[dict]:
    return [
        {
            "position": item.position,
            "generic_name": item.generic_name,
            "brand_name": item.brand_name,
            "pharmaceutical_form": item.pharmaceutical_form,
            "concentration": item.concentration,
            "dose": item.dose,
            "route": item.route,
            "frequency": item.frequency,
            "duration": item.duration,
            "total_quantity": item.total_quantity,
            "quantity_unit": item.quantity_unit,
            "instructions": item.instructions,
        }
        for item in sorted(items, key=lambda current: current.position)
    ]


def _snapshot_prescription(prescription: Prescription, items: list[PrescriptionItem]) -> dict:
    return {
        "clinical_date": prescription.clinical_date.isoformat(),
        "general_instructions": prescription.general_instructions,
        "notes": prescription.notes,
        "items": _items_snapshot(items),
    }


def _item_response(item: PrescriptionItem) -> PrescriptionItemResponse:
    return PrescriptionItemResponse(
        id=item.id,
        position=item.position,
        generic_name=item.generic_name,
        brand_name=item.brand_name,
        pharmaceutical_form=item.pharmaceutical_form,
        concentration=item.concentration,
        dose=item.dose,
        route=item.route,
        frequency=item.frequency,
        duration=item.duration,
        total_quantity=item.total_quantity,
        quantity_unit=item.quantity_unit,
        instructions=item.instructions,
    )


def _response(prescription: Prescription, items: list[PrescriptionItem], patient: Patient | None = None, dentist: Dentist | None = None, site: Site | None = None, clinical_alerts: dict | None = None) -> PrescriptionResponse:
    patient_name = _patient_name(patient) if patient else (prescription.patient_snapshot or {}).get("name", "Paciente")
    professional_name = dentist.name if dentist else (prescription.professional_snapshot or {}).get("name")
    return PrescriptionResponse(
        id=prescription.id,
        company_id=prescription.company_id,
        site_id=prescription.site_id,
        site_name=site.name if site else (prescription.institution_snapshot or {}).get("site", {}).get("name"),
        patient_id=prescription.patient_id,
        patient_name=patient_name,
        professional_user_id=prescription.professional_user_id,
        dentist_profile_id=prescription.dentist_profile_id,
        professional_name=professional_name,
        status=prescription.status,
        prescription_number=prescription.prescription_number,
        clinical_date=prescription.clinical_date,
        related_treatment_id=prescription.related_treatment_id,
        related_evolution_id=prescription.related_evolution_id,
        related_appointment_id=prescription.related_appointment_id,
        previous_prescription_id=prescription.previous_prescription_id,
        general_instructions=prescription.general_instructions,
        notes=prescription.notes,
        allergies_reviewed=prescription.allergies_reviewed,
        finalized_at=prescription.finalized_at,
        voided_at=prescription.voided_at,
        void_reason=prescription.void_reason,
        pdf_sha256=prescription.pdf_sha256,
        integrity_hash=prescription.integrity_hash,
        version=prescription.version,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
        items=[_item_response(item) for item in sorted(items, key=lambda current: current.position)],
        clinical_alerts=clinical_alerts,
    )


def _set_items(session: Session, prescription: Prescription, item_inputs: list[PrescriptionItemInput]) -> None:
    session.execute(delete(PrescriptionItem).where(PrescriptionItem.prescription_id == prescription.id))
    for index, payload in enumerate(item_inputs, start=1):
        session.add(
            PrescriptionItem(
                company_id=prescription.company_id,
                prescription_id=prescription.id,
                position=index,
                generic_name=payload.generic_name,
                brand_name=payload.brand_name,
                pharmaceutical_form=payload.pharmaceutical_form,
                concentration=payload.concentration,
                dose=payload.dose,
                route=payload.route,
                frequency=payload.frequency,
                duration=payload.duration,
                total_quantity=payload.total_quantity,
                quantity_unit=payload.quantity_unit,
                instructions=payload.instructions,
            )
        )


def _load_items(session: Session, prescription_id: UUID) -> list[PrescriptionItem]:
    return list(session.scalars(select(PrescriptionItem).where(PrescriptionItem.prescription_id == prescription_id).order_by(PrescriptionItem.position.asc())).all())


def list_prescriptions(session: Session, context: AuthContext, patient_id: UUID, *, status: str | None = None, dentist_id: UUID | None = None, medication: str | None = None) -> PrescriptionListResponse:
    _require_permission(context, "prescriptions.view")
    patient = _require_patient(session, context, patient_id)
    statement = (
        select(Prescription, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == Prescription.dentist_profile_id)
        .outerjoin(Site, Site.id == Prescription.site_id)
        .where(Prescription.company_id == context.user.company_id, Prescription.patient_id == patient.id)
    )
    if status:
        statement = statement.where(Prescription.status == status.strip().upper())
    if dentist_id:
        statement = statement.where(Prescription.dentist_profile_id == dentist_id)
    rows = session.execute(statement.order_by(Prescription.created_at.desc())).all()
    responses: list[PrescriptionResponse] = []
    for prescription, dentist, site in rows:
        items = _load_items(session, prescription.id)
        if medication and not any(medication.lower() in item.generic_name.lower() for item in items):
            continue
        responses.append(_response(prescription, items, patient, dentist, site))
    return PrescriptionListResponse(items=responses, total=len(responses))


def create_prescription(session: Session, context: AuthContext, patient_id: UUID, payload: PrescriptionCreateRequest, metadata: RequestMetadata) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.create")
    patient = _require_patient(session, context, patient_id)
    site = _require_site(session, context, payload.site_id)
    dentist = _require_dentist(session, context, payload.dentist_profile_id, site.id)
    _validate_references(session, context, patient.id, payload.related_treatment_id, payload.related_evolution_id, payload.related_appointment_id)
    prescription = Prescription(
        company_id=context.user.company_id,
        site_id=site.id,
        patient_id=patient.id,
        professional_user_id=dentist.user_id,
        dentist_profile_id=dentist.id,
        related_treatment_id=payload.related_treatment_id,
        related_evolution_id=payload.related_evolution_id,
        related_appointment_id=payload.related_appointment_id,
        status="DRAFT",
        clinical_date=payload.clinical_date,
        general_instructions=payload.general_instructions,
        notes=payload.notes,
        created_by=context.user.id,
    )
    session.add(prescription)
    session.flush()
    _set_items(session, prescription, payload.items)
    session.flush()
    _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_DRAFT_CREATED", detail={"patient_id": patient.id, "items_count": len(payload.items)})
    session.commit()
    session.refresh(prescription)
    return _response(prescription, _load_items(session, prescription.id), patient, dentist, site, _clinical_alerts(session, context, patient.id))


def get_prescription(session: Session, context: AuthContext, prescription_id: UUID) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.view")
    row = session.execute(
        select(Prescription, Patient, Dentist, Site)
        .join(Patient, Patient.id == Prescription.patient_id)
        .outerjoin(Dentist, Dentist.id == Prescription.dentist_profile_id)
        .outerjoin(Site, Site.id == Prescription.site_id)
        .where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id)
    ).one_or_none()
    if row is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    prescription, patient, dentist, site = row
    return _response(prescription, _load_items(session, prescription.id), patient, dentist, site, _clinical_alerts(session, context, patient.id))


def update_prescription(session: Session, context: AuthContext, prescription_id: UUID, payload: PrescriptionUpdateRequest, metadata: RequestMetadata) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.edit_draft")
    prescription = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id).with_for_update())
    if prescription is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    if prescription.status != "DRAFT":
        raise PrescriptionError("Solo se pueden editar recetas en borrador.", 409)
    if payload.version != prescription.version:
        raise PrescriptionError("Otro usuario modificó esta receta. Actualice la información.", 409)
    data = payload.model_dump(exclude_unset=True)
    site = _require_site(session, context, data.get("site_id", prescription.site_id))
    dentist = _require_dentist(session, context, data.get("dentist_profile_id", prescription.dentist_profile_id), site.id)
    _validate_references(
        session,
        context,
        prescription.patient_id,
        data.get("related_treatment_id", prescription.related_treatment_id),
        data.get("related_evolution_id", prescription.related_evolution_id),
        data.get("related_appointment_id", prescription.related_appointment_id),
    )
    for key in [
        "site_id",
        "dentist_profile_id",
        "clinical_date",
        "related_treatment_id",
        "related_evolution_id",
        "related_appointment_id",
        "general_instructions",
        "notes",
    ]:
        if key in data:
            setattr(prescription, key, data[key])
    prescription.professional_user_id = dentist.user_id
    prescription.updated_by = context.user.id
    prescription.version += 1
    if payload.items is not None:
        _set_items(session, prescription, payload.items)
    patient = session.get(Patient, prescription.patient_id)
    _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_DRAFT_UPDATED", detail={"version": prescription.version, "items_count": len(payload.items or [])})
    session.commit()
    session.refresh(prescription)
    return _response(prescription, _load_items(session, prescription.id), patient, dentist, site, _clinical_alerts(session, context, prescription.patient_id))


def _paragraph(text: object | None, style: ParagraphStyle) -> Paragraph:
    value = "" if text is None else str(text)
    escaped = "<br/>".join(escape(line) for line in value.splitlines())
    return Paragraph(escaped or "—", style)


def _generate_pdf(prescription: Prescription, items: list[PrescriptionItem], *, preview: bool = False) -> BudgetPdfResult:
    institution = prescription.institution_snapshot or {}
    company = institution.get("company", {})
    site = institution.get("site", {})
    patient = prescription.patient_snapshot or {}
    professional = prescription.professional_snapshot or {}
    snapshot = prescription.prescription_snapshot or _snapshot_prescription(prescription, items)
    primary = _pdf_color(company.get("primary_color"), "#16a34a")
    heading = _pdf_color(company.get("heading_color"), "#0f172a")
    secondary = _visible_accent(_pdf_color(company.get("secondary_color"), "#0f766e"), "#64748b")
    table_header_background = _visible_accent(primary, "#1e3a8a")
    table_header_text = _text_on_background(table_header_background)
    light_primary = _soft_accent_background(primary)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.5 * cm, title=f"Receta {prescription.prescription_number or 'borrador'}", author=company.get("name") or "Dentia")
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("PrescriptionTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=heading, alignment=TA_RIGHT),
        "subtitle": ParagraphStyle("PrescriptionSubtitle", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#475569"), alignment=TA_RIGHT),
        "h2": ParagraphStyle("PrescriptionH2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=primary, spaceBefore=8, spaceAfter=6),
        "body": ParagraphStyle("PrescriptionBody", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=15, textColor=colors.HexColor("#334155")),
        "small": ParagraphStyle("PrescriptionSmall", parent=base["Normal"], fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#64748b")),
        "cell": ParagraphStyle("PrescriptionCell", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155")),
        "cell_bold": ParagraphStyle("PrescriptionCellBold", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a")),
        "med": ParagraphStyle("PrescriptionMedication", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=colors.HexColor("#0f172a")),
        "center": ParagraphStyle("PrescriptionCenter", parent=base["Normal"], fontName="Helvetica", fontSize=8, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#64748b")),
    }
    company_lines = [company.get("name"), company.get("address"), " · ".join(part for part in [company.get("city"), company.get("country")] if part), company.get("phone"), company.get("email")]
    logo = _image_if_exists(_branding_asset_path(company.get("logo_path")), width=38 * mm, height=22 * mm)
    story = [
        Table(
            [[logo or _paragraph(company.get("name"), styles["h2"]), [_paragraph("RECETA ODONTOLÓGICA", styles["title"]), _paragraph(" · ".join(part for part in [prescription.prescription_number or "BORRADOR", _date_text(prescription.clinical_date)] if part), styles["subtitle"]), Paragraph("<br/>".join(escape(line) for line in company_lines if line), styles["subtitle"])]]],
            colWidths=[doc.width * 0.34, doc.width * 0.66],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("LINEBELOW", (0, 0), (-1, -1), 1.1, table_header_background)]),
        ),
        Spacer(1, 10),
    ]
    if preview:
        story.append(Table([[_paragraph("BORRADOR — NO VÁLIDA PARA DISPENSACIÓN", styles["center"])]], colWidths=[doc.width], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fdba74")), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])))
        story.append(Spacer(1, 8))
    patient_document = " ".join(part for part in [patient.get("document_type"), patient.get("document")] if part)
    patient_age = f"{patient.get('age')} años" if patient.get("age") is not None else None
    patient_birth_age = " · ".join(str(part) for part in [patient.get("birth_date"), patient_age] if part)
    patient_rows = [
        [_paragraph("Paciente", styles["cell_bold"]), _paragraph(patient.get("name"), styles["cell"]), _paragraph("Documento", styles["cell_bold"]), _paragraph(patient_document or "—", styles["cell"])],
        [_paragraph("Nacimiento / edad", styles["cell_bold"]), _paragraph(patient_birth_age, styles["cell"]), _paragraph("Fecha", styles["cell_bold"]), _paragraph(_date_text(prescription.clinical_date), styles["cell"])],
    ]
    if patient.get("responsible"):
        responsible = patient["responsible"]
        patient_rows.append([_paragraph("Responsable", styles["cell_bold"]), _paragraph(f"{responsible.get('name')} · {responsible.get('relationship')}", styles["cell"]), _paragraph("Documento responsable", styles["cell_bold"]), _paragraph(" ".join(part for part in [responsible.get("document_type"), responsible.get("document")] if part), styles["cell"])])
    story.extend([_paragraph("Datos del paciente", styles["h2"]), Table(patient_rows, colWidths=[doc.width * 0.16, doc.width * 0.34, doc.width * 0.16, doc.width * 0.34], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), light_primary), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))])
    story.append(_paragraph("Medicamentos", styles["h2"]))
    for item in snapshot.get("items", []):
        title = f"{item.get('position')}. {item.get('generic_name', '').upper()} {item.get('concentration') or ''}".strip()
        if item.get("brand_name"):
            title += f" · Marca opcional: {item.get('brand_name')}"
        rows = [
            [_paragraph("Forma", styles["cell_bold"]), _paragraph(item.get("pharmaceutical_form"), styles["cell"]), _paragraph("Dosis", styles["cell_bold"]), _paragraph(item.get("dose"), styles["cell"])],
            [_paragraph("Vía", styles["cell_bold"]), _paragraph(item.get("route"), styles["cell"]), _paragraph("Frecuencia", styles["cell_bold"]), _paragraph(item.get("frequency"), styles["cell"])],
            [_paragraph("Duración", styles["cell_bold"]), _paragraph(item.get("duration"), styles["cell"]), _paragraph("Cantidad", styles["cell_bold"]), _paragraph(" ".join(part for part in [item.get("total_quantity"), item.get("quantity_unit")] if part), styles["cell"])],
        ]
        table_style = [("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
        if item.get("instructions"):
            rows.append([_paragraph("Indicaciones", styles["cell_bold"]), _paragraph(item.get("instructions"), styles["cell"]), "", ""])
            table_style.append(("SPAN", (1, 3), (-1, 3)))
        story.append(KeepTogether([_paragraph(title, styles["med"]), Table(rows, colWidths=[doc.width * 0.16, doc.width * 0.34, doc.width * 0.16, doc.width * 0.34], style=TableStyle(table_style)), Spacer(1, 8)]))
    if snapshot.get("general_instructions"):
        story.extend([_paragraph("Indicaciones generales", styles["h2"]), _paragraph(snapshot.get("general_instructions"), styles["body"])])
    story.extend([Spacer(1, 16), _paragraph("Atentamente,", styles["body"]), Spacer(1, 8)])
    signature = _image_if_exists(_branding_asset_path(professional.get("signature_path")), width=46 * mm, height=21 * mm)
    if signature:
        story.append(signature)
    story.extend([
        Spacer(1, 4),
        _paragraph(professional.get("name"), styles["cell_bold"]),
        _paragraph(professional.get("specialty") or "", styles["small"]),
        _paragraph(f"Registro profesional: {professional.get('professional_license')}" if professional.get("professional_license") else "", styles["small"]),
        Spacer(1, 4),
        _paragraph("Documento generado y finalizado en Dentia. La firma gráfica no equivale a firma digital certificada. Dentia no sustituye recetarios oficiales exigidos para medicamentos sometidos a control especial.", styles["small"]),
    ])
    footer_lines = [company.get("footer_text"), site.get("address") or company.get("address"), " · ".join(part for part in [site.get("phone"), company.get("email")] if part)]

    def on_page(canvas, document_canvas):
        canvas.saveState()
        canvas.setStrokeColor(secondary)
        canvas.setLineWidth(0.4)
        canvas.line(document_canvas.leftMargin, 1.02 * cm, letter[0] - document_canvas.rightMargin, 1.02 * cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(document_canvas.leftMargin, 0.68 * cm, " · ".join(line for line in footer_lines if line)[:170])
        canvas.drawRightString(letter[0] - document_canvas.rightMargin, 0.68 * cm, f"Página {document_canvas.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    filename = f"{prescription.prescription_number or 'borrador'}-receta-odontologica.pdf"
    return BudgetPdfResult(content=buffer.getvalue(), filename=filename)


def preview_prescription(session: Session, context: AuthContext, prescription_id: UUID) -> PrescriptionPreviewResponse:
    _require_permission(context, "prescriptions.view")
    prescription = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id))
    if prescription is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    if prescription.status != "DRAFT":
        raise PrescriptionError("Solo los borradores se previsualizan dinámicamente.", 409)
    company = session.get(Company, context.user.company_id)
    site = session.get(Site, prescription.site_id)
    patient = session.get(Patient, prescription.patient_id)
    dentist = session.get(Dentist, prescription.dentist_profile_id) if prescription.dentist_profile_id else None
    if company is None or site is None or patient is None or dentist is None:
        raise PrescriptionError("Receta incompleta.", 409)
    items = _load_items(session, prescription.id)
    prescription.institution_snapshot = _snapshot_company(company, site)
    prescription.patient_snapshot = _snapshot_patient(session, patient, prescription.clinical_date)
    prescription.professional_snapshot = _snapshot_professional(company, dentist)
    prescription.prescription_snapshot = _snapshot_prescription(prescription, items)
    prescription.clinical_alerts_snapshot = _clinical_alerts(session, context, patient.id)
    pdf = _generate_pdf(prescription, items, preview=True)
    return PrescriptionPreviewResponse(content_base64=base64.b64encode(pdf.content).decode("ascii"), filename=pdf.filename)


def finalize_prescription(session: Session, context: AuthContext, prescription_id: UUID, payload: PrescriptionFinalizeRequest, metadata: RequestMetadata) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.finalize")
    prescription = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id).with_for_update())
    if prescription is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    if prescription.status == "FINALIZED":
        return get_prescription(session, context, prescription.id)
    if prescription.status != "DRAFT":
        raise PrescriptionError("Solo se pueden finalizar recetas en borrador.", 409)
    items = _load_items(session, prescription.id)
    if not items:
        raise PrescriptionError("Agregue al menos un medicamento antes de finalizar.", 422)
    company = session.get(Company, context.user.company_id)
    site = _require_site(session, context, prescription.site_id)
    patient = _require_patient(session, context, prescription.patient_id)
    dentist = _require_dentist(session, context, prescription.dentist_profile_id, site.id)
    if company is None:
        raise PrescriptionError("Empresa no encontrada.", 500)
    if not company.signature_path:
        raise PrescriptionError("El profesional seleccionado no tiene firma configurada.", 422)
    if not company.professional_license:
        raise PrescriptionError("El profesional seleccionado no tiene registro profesional configurado.", 422)
    prescription.allergies_reviewed = payload.allergies_reviewed
    session.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(context.user.company_id) + ":prescriptions"))))
    current_sequence = session.scalar(select(func.coalesce(func.max(Prescription.sequence), 0)).where(Prescription.company_id == context.user.company_id))
    sequence = int(current_sequence or 0) + 1
    prescription.sequence = sequence
    prescription.prescription_number = f"RX-{sequence:06d}"
    prescription.institution_snapshot = _snapshot_company(company, site)
    prescription.patient_snapshot = _snapshot_patient(session, patient, prescription.clinical_date)
    prescription.professional_snapshot = _snapshot_professional(company, dentist)
    prescription.prescription_snapshot = _snapshot_prescription(prescription, items)
    prescription.clinical_alerts_snapshot = _clinical_alerts(session, context, patient.id)
    pdf = _generate_pdf(prescription, items)
    sha = hashlib.sha256(pdf.content).hexdigest()
    relative_path = f"{context.user.company_id}/{prescription.id}/{_sanitize_filename(pdf.filename)}"
    path = _storage_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf.content)
    prescription.pdf_storage_path = relative_path
    prescription.pdf_sha256 = sha
    prescription.integrity_hash = _content_hash({"prescription": prescription.prescription_snapshot, "institution": prescription.institution_snapshot, "patient": prescription.patient_snapshot, "professional": prescription.professional_snapshot, "clinical_alerts": prescription.clinical_alerts_snapshot, "pdf_sha256": sha})
    prescription.status = "FINALIZED"
    prescription.finalized_at = datetime.now(timezone.utc)
    prescription.finalized_by = context.user.id
    prescription.updated_by = context.user.id
    prescription.version += 1
    _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_FINALIZED", detail={"number": prescription.prescription_number, "sha256": sha, "items_count": len(items)})
    session.commit()
    session.refresh(prescription)
    return _response(prescription, _load_items(session, prescription.id), patient, dentist, site, prescription.clinical_alerts_snapshot)


def download_prescription_pdf(session: Session, context: AuthContext, prescription_id: UUID, metadata: RequestMetadata) -> BudgetPdfResult:
    _require_permission(context, "prescriptions.download")
    prescription = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id))
    if prescription is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    if prescription.status not in {"FINALIZED", "VOIDED"} or not prescription.pdf_storage_path or not prescription.pdf_sha256:
        raise PrescriptionError("La receta aún no tiene PDF final almacenado.", 409)
    path = _storage_path(prescription.pdf_storage_path)
    if not path.exists():
        _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_PDF_INTEGRITY_FAILED", detail={"reason": "missing_file"}, result="FAILURE")
        session.commit()
        raise PrescriptionError("El archivo histórico no está disponible.", 409)
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != prescription.pdf_sha256:
        _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_PDF_INTEGRITY_FAILED", detail={"reason": "hash_mismatch"}, result="FAILURE")
        session.commit()
        raise PrescriptionError("El archivo histórico falló la verificación de integridad.", 409)
    _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_PDF_DOWNLOADED", detail={"number": prescription.prescription_number})
    session.commit()
    return BudgetPdfResult(content=content, filename=f"{prescription.prescription_number or 'receta'}-receta-odontologica.pdf")


def duplicate_prescription(session: Session, context: AuthContext, prescription_id: UUID, metadata: RequestMetadata) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.create")
    original = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id))
    if original is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    patient = _require_patient(session, context, original.patient_id)
    site = _require_site(session, context, original.site_id)
    dentist = _require_dentist(session, context, original.dentist_profile_id, site.id)
    copy = Prescription(
        company_id=context.user.company_id,
        site_id=original.site_id,
        patient_id=original.patient_id,
        professional_user_id=dentist.user_id,
        dentist_profile_id=dentist.id,
        related_treatment_id=original.related_treatment_id,
        related_evolution_id=original.related_evolution_id,
        related_appointment_id=original.related_appointment_id,
        previous_prescription_id=original.id,
        status="DRAFT",
        clinical_date=date.today(),
        general_instructions=original.general_instructions,
        notes=original.notes,
        created_by=context.user.id,
    )
    session.add(copy)
    session.flush()
    original_items = _load_items(session, original.id)
    _set_items(session, copy, [PrescriptionItemInput(**snapshot) for snapshot in _items_snapshot(original_items)])
    session.flush()
    _audit(session, context, metadata, prescription=copy, action="PRESCRIPTION_DUPLICATED", detail={"previous_prescription_id": original.id, "items_count": len(original_items)})
    session.commit()
    session.refresh(copy)
    return _response(copy, _load_items(session, copy.id), patient, dentist, site, _clinical_alerts(session, context, patient.id))


def void_prescription(session: Session, context: AuthContext, prescription_id: UUID, payload: PrescriptionVoidRequest, metadata: RequestMetadata) -> PrescriptionResponse:
    _require_permission(context, "prescriptions.void")
    prescription = session.scalar(select(Prescription).where(Prescription.id == prescription_id, Prescription.company_id == context.user.company_id).with_for_update())
    if prescription is None:
        raise PrescriptionError("Receta no encontrada.", 404)
    if prescription.status != "FINALIZED":
        raise PrescriptionError("Solo se pueden anular recetas finalizadas.", 409)
    previous_status = prescription.status
    prescription.status = "VOIDED"
    prescription.voided_at = datetime.now(timezone.utc)
    prescription.voided_by = context.user.id
    prescription.void_reason = payload.reason
    prescription.updated_by = context.user.id
    prescription.version += 1
    patient = session.get(Patient, prescription.patient_id)
    dentist = session.get(Dentist, prescription.dentist_profile_id) if prescription.dentist_profile_id else None
    site = session.get(Site, prescription.site_id)
    _audit(session, context, metadata, prescription=prescription, action="PRESCRIPTION_VOIDED", detail={"previous_status": previous_status, "new_status": prescription.status, "reason": payload.reason})
    session.commit()
    session.refresh(prescription)
    return _response(prescription, _load_items(session, prescription.id), patient, dentist, site, prescription.clinical_alerts_snapshot)
