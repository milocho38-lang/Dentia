import base64
import hashlib
import json
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
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Appointment, Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_document import ClinicalDocument
from app.models.clinical_record import ClinicalEvolution
from app.models.company import Company
from app.models.site import Site
from app.models.treatment import Treatment
from app.schemas.clinical_document_schema import (
    ClinicalDocumentCreateRequest,
    ClinicalDocumentListResponse,
    ClinicalDocumentPreviewResponse,
    ClinicalDocumentResponse,
    ClinicalDocumentUpdateRequest,
    ClinicalDocumentVoidRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.document_style import (
    apply_reportlab_font,
    render_professional_identity_block,
    require_complete_professional_identity,
    resolve_professional_document_identity,
)
from app.utils.clinical_dates import format_human_date
from app.services.site_access_service import authorized_site_ids
from app.services.treatment_service import (
    BudgetPdfResult,
    _branding_asset_path,
    _content_hash,
    _date_text,
    _effective_timezone,
    _image_if_exists,
    _pdf_color,
    _soft_accent_background,
    _text_on_background,
    _visible_accent,
)
from app.utils.clinical_dates import local_clinical_date


DOCUMENT_TYPE_LABELS = {
    "REFERRAL": "Remisión",
    "CLINICAL_REPORT": "Informe clínico",
    "CERTIFICATE": "Certificado / constancia",
    "GENERAL_LETTER": "Carta general",
}


class ClinicalDocumentError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _require_permission(context: AuthContext, permission: str) -> None:
    if permission not in context.permissions:
        raise ClinicalDocumentError("No tienes permiso para realizar esta acción.", 403)


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
    document: ClinicalDocument,
    action: str,
    detail: dict | None = None,
    result: str = "SUCCESS",
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="clinical_document",
            entity_id=document.id,
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
        raise ClinicalDocumentError("No tienes acceso a la sede seleccionada.", 403)
    site = session.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.company_id == context.user.company_id,
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
    )
    if site is None:
        raise ClinicalDocumentError("La sede no existe o no está activa.", 404)
    return site


def _require_patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
            Patient.is_active.is_(True),
        )
    )
    if patient is None:
        raise ClinicalDocumentError("Paciente no encontrado.", 404)
    return patient


def _require_dentist(
    session: Session,
    context: AuthContext,
    dentist_id: UUID | None,
    site_id: UUID,
) -> Dentist:
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
        raise ClinicalDocumentError("Seleccione el profesional firmante.", 422)
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
        raise ClinicalDocumentError("Profesional no disponible para la sede seleccionada.", 422)
    if dentist.user_id != context.user.id and "clinical_documents.void" not in context.permissions:
        raise ClinicalDocumentError("No tienes permiso para firmar con otro profesional.", 403)
    return dentist


def _validate_references(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    treatment_id: UUID | None,
    evolution_id: UUID | None,
    appointment_id: UUID | None,
) -> None:
    if treatment_id and not session.scalar(
        select(Treatment.id).where(
            Treatment.id == treatment_id,
            Treatment.company_id == context.user.company_id,
            Treatment.patient_id == patient_id,
        )
    ):
        raise ClinicalDocumentError("Tratamiento relacionado inválido.", 422)
    if evolution_id and not session.scalar(
        select(ClinicalEvolution.id).where(
            ClinicalEvolution.id == evolution_id,
            ClinicalEvolution.company_id == context.user.company_id,
            ClinicalEvolution.patient_id == patient_id,
        )
    ):
        raise ClinicalDocumentError("Evolución relacionada inválida.", 422)
    if appointment_id and not session.scalar(
        select(Appointment.id).where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == patient_id,
        )
    ):
        raise ClinicalDocumentError("Cita relacionada inválida.", 422)


def _patient_name(patient: Patient) -> str:
    return f"{patient.first_names} {patient.last_names}".strip()


def _storage_root() -> Path:
    return Path(settings.branding_storage_dir).resolve().parent / "clinical_documents"


def _sanitize_filename(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return normalized[:80] or "documento"


def _storage_path(relative_path: str) -> Path:
    root = _storage_root().resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        raise ClinicalDocumentError("Ruta de documento inválida.", 400)
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
            "document_font_family": company.document_font_family,
        },
        "site": {
            "name": site.name,
            "address": site.address,
            "city": site.city,
            "phone": site.phone,
            "timezone": site.timezone,
        },
    }


def _snapshot_patient(patient: Patient) -> dict:
    return {
        "name": _patient_name(patient),
        "document_type": patient.document_type,
        "document": patient.document,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
    }


def _snapshot_professional(session: Session, company: Company, dentist: Dentist) -> dict:
    return resolve_professional_document_identity(session, company, dentist).snapshot()


def _snapshot_document(document: ClinicalDocument) -> dict:
    return {
        "document_type": document.document_type,
        "clinical_date": document.clinical_date.isoformat(),
        "title": document.title,
        "recipient_name": document.recipient_name,
        "recipient_entity": document.recipient_entity,
        "recipient_specialty": document.recipient_specialty,
        "subject": document.subject,
        "body": document.body,
    }


def _response(
    document: ClinicalDocument,
    patient: Patient | None = None,
    dentist: Dentist | None = None,
    site: Site | None = None,
) -> ClinicalDocumentResponse:
    patient_name = _patient_name(patient) if patient else (document.patient_snapshot or {}).get("name", "Paciente")
    professional_name = dentist.name if dentist else (document.professional_snapshot or {}).get("name")
    return ClinicalDocumentResponse(
        id=document.id,
        company_id=document.company_id,
        site_id=document.site_id,
        site_name=site.name if site else (document.institution_snapshot or {}).get("site", {}).get("name"),
        patient_id=document.patient_id,
        patient_name=patient_name,
        professional_user_id=document.professional_user_id,
        dentist_profile_id=document.dentist_profile_id,
        professional_name=professional_name,
        document_type=document.document_type,
        status=document.status,
        document_number=document.document_number,
        title=document.title,
        recipient_name=document.recipient_name,
        recipient_entity=document.recipient_entity,
        recipient_specialty=document.recipient_specialty,
        subject=document.subject,
        body=document.body,
        clinical_date=document.clinical_date,
        finalized_at=document.finalized_at,
        voided_at=document.voided_at,
        void_reason=document.void_reason,
        related_treatment_id=document.related_treatment_id,
        related_evolution_id=document.related_evolution_id,
        related_appointment_id=document.related_appointment_id,
        previous_document_id=document.previous_document_id,
        pdf_sha256=document.pdf_sha256,
        integrity_hash=document.integrity_hash,
        version=document.version,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def list_documents(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    document_type: str | None = None,
    status: str | None = None,
    dentist_id: UUID | None = None,
) -> ClinicalDocumentListResponse:
    _require_permission(context, "clinical_documents.view")
    patient = _require_patient(session, context, patient_id)
    statement = (
        select(ClinicalDocument, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == ClinicalDocument.dentist_profile_id)
        .outerjoin(Site, Site.id == ClinicalDocument.site_id)
        .where(
            ClinicalDocument.company_id == context.user.company_id,
            ClinicalDocument.patient_id == patient.id,
        )
    )
    if document_type:
        statement = statement.where(ClinicalDocument.document_type == document_type.strip().upper())
    if status:
        statement = statement.where(ClinicalDocument.status == status.strip().upper())
    if dentist_id:
        statement = statement.where(ClinicalDocument.dentist_profile_id == dentist_id)
    rows = session.execute(statement.order_by(ClinicalDocument.created_at.desc())).all()
    return ClinicalDocumentListResponse(
        items=[_response(document, patient, dentist, site) for document, dentist, site in rows],
        total=len(rows),
    )


def get_document(session: Session, context: AuthContext, document_id: UUID) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.view")
    row = session.execute(
        select(ClinicalDocument, Patient, Dentist, Site)
        .join(Patient, Patient.id == ClinicalDocument.patient_id)
        .outerjoin(Dentist, Dentist.id == ClinicalDocument.dentist_profile_id)
        .outerjoin(Site, Site.id == ClinicalDocument.site_id)
        .where(
            ClinicalDocument.id == document_id,
            ClinicalDocument.company_id == context.user.company_id,
        )
    ).one_or_none()
    if row is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    return _response(*row)


def create_document(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: ClinicalDocumentCreateRequest,
    metadata: RequestMetadata,
) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.create")
    patient = _require_patient(session, context, patient_id)
    site = _require_site(session, context, payload.site_id)
    dentist = _require_dentist(session, context, payload.dentist_profile_id, site.id)
    _validate_references(session, context, patient.id, payload.related_treatment_id, payload.related_evolution_id, payload.related_appointment_id)
    document = ClinicalDocument(
        company_id=context.user.company_id,
        site_id=site.id,
        patient_id=patient.id,
        professional_user_id=dentist.user_id,
        dentist_profile_id=dentist.id,
        document_type=payload.document_type,
        title=payload.title,
        recipient_name=payload.recipient_name,
        recipient_entity=payload.recipient_entity,
        recipient_specialty=payload.recipient_specialty,
        subject=payload.subject,
        body=payload.body,
        clinical_date=payload.clinical_date,
        related_treatment_id=payload.related_treatment_id,
        related_evolution_id=payload.related_evolution_id,
        related_appointment_id=payload.related_appointment_id,
        status="DRAFT",
        created_by=context.user.id,
    )
    session.add(document)
    session.flush()
    _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_DRAFT_CREATED", detail={"type": document.document_type, "patient_id": patient.id})
    session.commit()
    session.refresh(document)
    return _response(document, patient, dentist, site)


def update_document(
    session: Session,
    context: AuthContext,
    document_id: UUID,
    payload: ClinicalDocumentUpdateRequest,
    metadata: RequestMetadata,
) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.edit_draft")
    document = session.scalar(
        select(ClinicalDocument)
        .where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id)
        .with_for_update()
    )
    if document is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    if document.status != "DRAFT":
        raise ClinicalDocumentError("Solo se pueden editar documentos en borrador.", 409)
    if payload.version != document.version:
        raise ClinicalDocumentError("Otro usuario modificó este documento. Actualice la información.", 409)
    data = payload.model_dump(exclude_unset=True)
    site = _require_site(session, context, data.get("site_id", document.site_id))
    dentist = _require_dentist(session, context, data.get("dentist_profile_id", document.dentist_profile_id), site.id)
    _validate_references(
        session,
        context,
        document.patient_id,
        data.get("related_treatment_id", document.related_treatment_id),
        data.get("related_evolution_id", document.related_evolution_id),
        data.get("related_appointment_id", document.related_appointment_id),
    )
    for key, attr in {
        "site_id": "site_id",
        "dentist_profile_id": "dentist_profile_id",
        "document_type": "document_type",
        "title": "title",
        "recipient_name": "recipient_name",
        "recipient_entity": "recipient_entity",
        "recipient_specialty": "recipient_specialty",
        "subject": "subject",
        "body": "body",
        "clinical_date": "clinical_date",
        "related_treatment_id": "related_treatment_id",
        "related_evolution_id": "related_evolution_id",
        "related_appointment_id": "related_appointment_id",
    }.items():
        if key in data:
            setattr(document, attr, data[key])
    document.professional_user_id = dentist.user_id
    document.updated_by = context.user.id
    document.version += 1
    patient = session.get(Patient, document.patient_id)
    _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_DRAFT_UPDATED", detail={"version": document.version})
    session.commit()
    session.refresh(document)
    return _response(document, patient, dentist, site)


def _paragraph(text: object | None, style: ParagraphStyle) -> Paragraph:
    value = "" if text is None else str(text)
    escaped = "<br/>".join(escape(line) for line in value.splitlines())
    return Paragraph(escaped or "—", style)


def _generate_pdf(document: ClinicalDocument, *, preview: bool = False) -> BudgetPdfResult:
    institution = document.institution_snapshot or {}
    company = institution.get("company", {})
    site = institution.get("site", {})
    patient = document.patient_snapshot or {}
    professional = document.professional_snapshot or {}
    doc_snapshot = document.document_snapshot or _snapshot_document(document)
    primary = _pdf_color(company.get("primary_color"), "#16a34a")
    secondary = _visible_accent(_pdf_color(company.get("secondary_color"), "#0f766e"), "#64748b")
    heading = _pdf_color(company.get("heading_color"), "#0f172a")
    table_header_background = _visible_accent(primary, "#1e3a8a")
    table_header_text = _text_on_background(table_header_background)
    light_primary = _soft_accent_background(primary)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.5 * cm,
        title=f"{DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)} {document.document_number or 'borrador'}",
        author=company.get("name") or "Dentia",
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("ClinicalDocTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=heading, alignment=TA_RIGHT),
        "subtitle": ParagraphStyle("ClinicalDocSubtitle", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#475569"), alignment=TA_RIGHT),
        "h2": ParagraphStyle("ClinicalDocH2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=primary, spaceBefore=8, spaceAfter=6),
        "body": ParagraphStyle("ClinicalDocBody", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=15, textColor=colors.HexColor("#334155")),
        "small": ParagraphStyle("ClinicalDocSmall", parent=base["Normal"], fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#64748b")),
        "cell": ParagraphStyle("ClinicalDocCell", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155")),
        "cell_bold": ParagraphStyle("ClinicalDocCellBold", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a")),
        "center": ParagraphStyle("ClinicalDocCenter", parent=base["Normal"], fontName="Helvetica", fontSize=8, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#64748b")),
    }
    document_font = apply_reportlab_font(styles, company.get("document_font_family"))
    company_lines = [
        company.get("name"),
        company.get("address"),
        " · ".join(part for part in [company.get("city"), company.get("country")] if part),
        company.get("phone"),
        company.get("email"),
    ]
    logo = _image_if_exists(_branding_asset_path(company.get("logo_path")), width=38 * mm, height=22 * mm)
    header_left = logo or _paragraph(company.get("name"), styles["h2"])
    header_right = [
        _paragraph(DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type).upper(), styles["title"]),
        _paragraph(" · ".join(part for part in [document.document_number or "BORRADOR", _date_text(document.clinical_date)] if part), styles["subtitle"]),
        Paragraph("<br/>".join(escape(line) for line in company_lines if line), styles["subtitle"]),
    ]
    story = [
        Table(
            [[header_left, header_right]],
            colWidths=[doc.width * 0.34, doc.width * 0.66],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEBELOW", (0, 0), (-1, -1), 1.1, table_header_background),
            ]),
        ),
        Spacer(1, 10),
    ]
    if preview:
        story.append(Table([[_paragraph("BORRADOR — SIN VALIDEZ COMO DOCUMENTO FINAL", styles["center"])]], colWidths=[doc.width], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fdba74")), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])))
        story.append(Spacer(1, 8))
    patient_document = " ".join(part for part in [patient.get("document_type"), patient.get("document")] if part)
    patient_rows = [
        [_paragraph("Paciente", styles["cell_bold"]), _paragraph(patient.get("name"), styles["cell"]), _paragraph("Documento", styles["cell_bold"]), _paragraph(patient_document or "—", styles["cell"])],
        [_paragraph("Nacimiento", styles["cell_bold"]), _paragraph(format_human_date(date.fromisoformat(patient["birth_date"])) if patient.get("birth_date") else "—", styles["cell"]), _paragraph("Fecha", styles["cell_bold"]), _paragraph(_date_text(document.clinical_date), styles["cell"])],
    ]
    story.append(_paragraph("Datos del paciente", styles["h2"]))
    story.append(Table(patient_rows, colWidths=[doc.width * 0.16, doc.width * 0.34, doc.width * 0.16, doc.width * 0.34], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), light_primary), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])))
    if document.recipient_name or document.recipient_entity or document.recipient_specialty:
        recipient = "<br/>".join(escape(part) for part in [document.recipient_name, document.recipient_entity, document.recipient_specialty] if part)
        story.extend([_paragraph("Destinatario", styles["h2"]), Paragraph(recipient, styles["body"])])
    if document.subject:
        story.extend([_paragraph("Asunto", styles["h2"]), _paragraph(document.subject, styles["body"])])
    story.extend([_paragraph("Contenido", styles["h2"]), _paragraph(doc_snapshot.get("body"), styles["body"]), Spacer(1, 18)])
    signature = _image_if_exists(_branding_asset_path(professional.get("signature_path")), width=46 * mm, height=21 * mm)
    story.extend([
        render_professional_identity_block(
            professional,
            styles=styles,
            signature=signature,
            width=min(doc.width, 88 * mm),
            show_intro=True,
            separator=False,
        ),
        Spacer(1, 4),
        _paragraph("Documento generado y finalizado en Dentia. La firma gráfica no equivale a firma digital certificada.", styles["small"]),
    ])
    footer_lines = [
        company.get("footer_text"),
        site.get("address") or company.get("address"),
        " · ".join(part for part in [site.get("phone"), company.get("email")] if part),
    ]

    def on_page(canvas, document_canvas):
        canvas.saveState()
        canvas.setStrokeColor(secondary)
        canvas.setLineWidth(0.4)
        canvas.line(document_canvas.leftMargin, 1.02 * cm, letter[0] - document_canvas.rightMargin, 1.02 * cm)
        canvas.setFont(document_font.regular, 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(document_canvas.leftMargin, 0.68 * cm, " · ".join(line for line in footer_lines if line)[:170])
        canvas.drawRightString(letter[0] - document_canvas.rightMargin, 0.68 * cm, f"Página {document_canvas.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    base_name = document.document_number or "borrador"
    filename = f"{base_name}-{_sanitize_filename(DOCUMENT_TYPE_LABELS.get(document.document_type, 'documento'))}.pdf"
    return BudgetPdfResult(content=buffer.getvalue(), filename=filename)


def preview_document(session: Session, context: AuthContext, document_id: UUID) -> ClinicalDocumentPreviewResponse:
    _require_permission(context, "clinical_documents.view")
    document = session.scalar(select(ClinicalDocument).where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id))
    if document is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    if document.status != "DRAFT":
        raise ClinicalDocumentError("Solo los borradores se previsualizan dinámicamente.", 409)
    company = session.get(Company, context.user.company_id)
    site = session.get(Site, document.site_id)
    patient = session.get(Patient, document.patient_id)
    dentist = session.get(Dentist, document.dentist_profile_id) if document.dentist_profile_id else None
    if company is None or site is None or patient is None or dentist is None:
        raise ClinicalDocumentError("Documento incompleto.", 409)
    document.institution_snapshot = _snapshot_company(company, site)
    document.patient_snapshot = _snapshot_patient(patient)
    document.professional_snapshot = _snapshot_professional(session, company, dentist)
    document.document_snapshot = _snapshot_document(document)
    pdf = _generate_pdf(document, preview=True)
    return ClinicalDocumentPreviewResponse(content_base64=base64.b64encode(pdf.content).decode("ascii"), filename=pdf.filename)


def finalize_document(
    session: Session,
    context: AuthContext,
    document_id: UUID,
    metadata: RequestMetadata,
) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.finalize")
    document = session.scalar(
        select(ClinicalDocument)
        .where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id)
        .with_for_update()
    )
    if document is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    if document.status == "FINALIZED":
        patient = session.get(Patient, document.patient_id)
        dentist = session.get(Dentist, document.dentist_profile_id) if document.dentist_profile_id else None
        site = session.get(Site, document.site_id)
        return _response(document, patient, dentist, site)
    if document.status != "DRAFT":
        raise ClinicalDocumentError("Solo se pueden finalizar documentos en borrador.", 409)
    if not document.body.strip():
        raise ClinicalDocumentError("El contenido del documento es obligatorio.", 422)
    company = session.get(Company, context.user.company_id)
    site = _require_site(session, context, document.site_id)
    patient = _require_patient(session, context, document.patient_id)
    dentist = _require_dentist(session, context, document.dentist_profile_id, site.id)
    if company is None:
        raise ClinicalDocumentError("Empresa no encontrada.", 500)
    identity = resolve_professional_document_identity(session, company, dentist)
    try:
        require_complete_professional_identity(identity)
    except ValueError as exc:
        raise ClinicalDocumentError(str(exc), 422) from exc
    session.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(context.user.company_id) + ":clinical-documents"))))
    current_sequence = session.scalar(
        select(func.coalesce(func.max(ClinicalDocument.sequence), 0)).where(ClinicalDocument.company_id == context.user.company_id)
    )
    sequence = int(current_sequence or 0) + 1
    document.sequence = sequence
    document.document_number = f"DOC-{sequence:06d}"
    document.institution_snapshot = _snapshot_company(company, site)
    document.patient_snapshot = _snapshot_patient(patient)
    document.professional_snapshot = identity.snapshot()
    document.document_snapshot = _snapshot_document(document)
    pdf = _generate_pdf(document)
    sha = hashlib.sha256(pdf.content).hexdigest()
    relative_path = f"{context.user.company_id}/{document.id}/{_sanitize_filename(pdf.filename)}"
    path = _storage_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf.content)
    document.pdf_storage_path = relative_path
    document.pdf_sha256 = sha
    document.integrity_hash = _content_hash(
        {
            "document": document.document_snapshot,
            "institution": document.institution_snapshot,
            "patient": document.patient_snapshot,
            "professional": document.professional_snapshot,
            "pdf_sha256": sha,
        }
    )
    document.status = "FINALIZED"
    document.finalized_at = datetime.now(timezone.utc)
    document.finalized_by = context.user.id
    document.updated_by = context.user.id
    document.version += 1
    _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_FINALIZED", detail={"number": document.document_number, "sha256": sha, "type": document.document_type})
    session.commit()
    session.refresh(document)
    return _response(document, patient, dentist, site)


def download_document_pdf(
    session: Session,
    context: AuthContext,
    document_id: UUID,
    metadata: RequestMetadata,
) -> BudgetPdfResult:
    _require_permission(context, "clinical_documents.download")
    document = session.scalar(select(ClinicalDocument).where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id))
    if document is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    if document.status not in {"FINALIZED", "VOIDED"} or not document.pdf_storage_path or not document.pdf_sha256:
        raise ClinicalDocumentError("El documento aún no tiene PDF final almacenado.", 409)
    path = _storage_path(document.pdf_storage_path)
    if not path.exists():
        _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_PDF_INTEGRITY_FAILED", detail={"reason": "missing_file"}, result="FAILURE")
        session.commit()
        raise ClinicalDocumentError("El archivo histórico no está disponible.", 409)
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != document.pdf_sha256:
        _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_PDF_INTEGRITY_FAILED", detail={"reason": "hash_mismatch"}, result="FAILURE")
        session.commit()
        raise ClinicalDocumentError("El archivo histórico falló la verificación de integridad.", 409)
    _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_PDF_DOWNLOADED", detail={"number": document.document_number})
    session.commit()
    filename = f"{document.document_number or 'documento'}-{_sanitize_filename(DOCUMENT_TYPE_LABELS.get(document.document_type, 'documento'))}.pdf"
    return BudgetPdfResult(content=content, filename=filename)


def duplicate_document(
    session: Session,
    context: AuthContext,
    document_id: UUID,
    metadata: RequestMetadata,
) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.create")
    original = session.scalar(select(ClinicalDocument).where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id))
    if original is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    patient = _require_patient(session, context, original.patient_id)
    site = _require_site(session, context, original.site_id)
    company = session.get(Company, context.user.company_id)
    dentist = _require_dentist(session, context, original.dentist_profile_id, site.id)
    copy = ClinicalDocument(
        company_id=context.user.company_id,
        site_id=original.site_id,
        patient_id=original.patient_id,
        professional_user_id=dentist.user_id,
        dentist_profile_id=dentist.id,
        related_treatment_id=original.related_treatment_id,
        related_evolution_id=original.related_evolution_id,
        related_appointment_id=original.related_appointment_id,
        previous_document_id=original.id,
        document_type=original.document_type,
        status="DRAFT",
        title=original.title,
        recipient_name=original.recipient_name,
        recipient_entity=original.recipient_entity,
        recipient_specialty=original.recipient_specialty,
        subject=original.subject,
        body=original.body,
        clinical_date=local_clinical_date(company, site),
        created_by=context.user.id,
    )
    session.add(copy)
    session.flush()
    _audit(session, context, metadata, document=copy, action="CLINICAL_DOCUMENT_DUPLICATED", detail={"previous_document_id": original.id})
    session.commit()
    session.refresh(copy)
    return _response(copy, patient, dentist, site)


def void_document(
    session: Session,
    context: AuthContext,
    document_id: UUID,
    payload: ClinicalDocumentVoidRequest,
    metadata: RequestMetadata,
) -> ClinicalDocumentResponse:
    _require_permission(context, "clinical_documents.void")
    document = session.scalar(
        select(ClinicalDocument)
        .where(ClinicalDocument.id == document_id, ClinicalDocument.company_id == context.user.company_id)
        .with_for_update()
    )
    if document is None:
        raise ClinicalDocumentError("Documento clínico no encontrado.", 404)
    if document.status != "FINALIZED":
        raise ClinicalDocumentError("Solo se pueden anular documentos finalizados.", 409)
    previous_status = document.status
    document.status = "VOIDED"
    document.voided_at = datetime.now(timezone.utc)
    document.voided_by = context.user.id
    document.void_reason = payload.reason
    document.updated_by = context.user.id
    document.version += 1
    patient = session.get(Patient, document.patient_id)
    dentist = session.get(Dentist, document.dentist_profile_id) if document.dentist_profile_id else None
    site = session.get(Site, document.site_id)
    _audit(session, context, metadata, document=document, action="CLINICAL_DOCUMENT_VOIDED", detail={"previous_status": previous_status, "new_status": document.status, "reason": payload.reason})
    session.commit()
    session.refresh(document)
    return _response(document, patient, dentist, site)
