"""Provisional C019A.4 acceptance flow. Not a legal-validity assertion."""
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import unicodedata
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import CondPageBreak, HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.utils import ImageReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Patient
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_acceptance import ConsentAcceptance, ConsentAcceptanceDeclaration, ConsentCopyDelivery, ConsentEvidenceManifest, ConsentFinalDocument, ConsentSignatureArtifact
from app.models.consent_template import ConsentAccessSession, ConsentClarificationRequest, ConsentInstance, ConsentOtpChallenge, ConsentPublicSession, ConsentResponsibleAdult
from app.models.site import Site
from app.schemas.consent_access_schema import AcceptanceEvidenceResponse, AcceptanceRequirementsResponse, AcceptanceSubmitRequest, AcceptanceSubmitResponse, AcceptanceSummaryResponse
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.consent_access_service import ConsentAccessError, _hash, _verified, mask_email
from app.services.consent_access_service import _otp_hash
from app.services.consent_acceptance_context import inspect_acceptance_context
from app.services.consent_declaration_catalog import ConsentDeclarationSet, ConsentDeclarationSetError, TEST_DOCUMENT_NOTICE, declaration_set_for
from app.services.consent_instance_service import _require_instance
from app.services.consent_library_normalization import validate_patient_facing_content
from app.services.email_service import EmailDelivery, EmailDeliveryError, get_email_provider
from app.services.patient_service import calculate_age
from app.services.consent_signer import (
    PATIENT_SELF,
    RESPONSIBLE_ADULT,
    minor_participation_label,
    responsible_relationship_label,
    signer_snapshot_from_instance,
)


class ConsentAcceptanceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400, code: str = "TECHNICAL_ERROR", safe_detail: dict | None = None):
        super().__init__(message); self.status_code = status_code; self.code = code; self.safe_detail = safe_detail or {}


def _now(): return datetime.now(timezone.utc)
def _sha_bytes(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _canonical(value: dict) -> bytes: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
def _enabled() -> bool: return settings.consent_acceptance_enabled and settings.app_env.casefold() != "production"


def _failure_point(_name: str):
    """Stable test seam for proving compensation; intentionally a no-op."""
    return None


def _require_enabled():
    if not _enabled(): raise ConsentAcceptanceError("La aceptación electrónica no está habilitada en este entorno.", 404)


def _normalize_name(value: str) -> str:
    ascii_value = "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-zA-Z0-9 ]+", " ", ascii_value).casefold().split())


def _decode_signature(data_url: str) -> tuple[bytes, int, int]:
    match = re.fullmatch(r"data:image/png;base64,([A-Za-z0-9+/=\s]+)", data_url)
    if not match: raise ConsentAcceptanceError("La firma debe enviarse como una imagen PNG válida.", 422, "SIGNATURE_INVALID", {"declared_mime":"INVALID","data_url_length":len(data_url)})
    try: raw = base64.b64decode(match.group(1), validate=True)
    except Exception as exc: raise ConsentAcceptanceError("La firma no pudo validarse.", 422, "SIGNATURE_INVALID", {"declared_mime":"image/png","data_url_length":len(data_url)}) from exc
    if not (200 <= len(raw) <= 400_000) or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ConsentAcceptanceError("La firma no cumple los límites permitidos.", 422, "SIGNATURE_INVALID", {"declared_mime":"image/png","decoded_byte_size":len(raw),"png_magic_valid":raw.startswith(b"\x89PNG\r\n\x1a\n")})
    try:
        with PillowImage.open(BytesIO(raw)) as image:
            image.verify(); width, height = image.size
    except Exception as exc: raise ConsentAcceptanceError("La firma PNG está dañada.", 422, "SIGNATURE_INVALID", {"declared_mime":"image/png","decoded_byte_size":len(raw),"png_magic_valid":True}) from exc
    signature_metadata={"declared_mime":"image/png","decoded_byte_size":len(raw),"png_magic_valid":True,"width":width,"height":height}
    if not (80 <= width <= 1600 and 30 <= height <= 800): raise ConsentAcceptanceError("Las dimensiones de la firma no son válidas.", 422, "SIGNATURE_INVALID", signature_metadata)
    with PillowImage.open(BytesIO(raw)).convert("RGB") as image:
        resized=image.resize((160,60)); pixels=resized.get_flattened_data() if hasattr(resized,"get_flattened_data") else resized.getdata(); non_white=sum(1 for pixel in pixels if min(pixel)<235)
    if non_white < 12: raise ConsentAcceptanceError("La firma debe contener un trazo reconocible.",422,"SIGNATURE_INVALID",signature_metadata)
    return raw, width, height


def _audit(session: Session, access: ConsentAccessSession, action: str, metadata: RequestMetadata, *, result="SUCCESS", detail=None, user_id=None):
    session.add(AuditEvent(company_id=access.company_id,user_id=user_id,entity="consent_acceptance",entity_id=access.consent_instance_id,action=action,result=result,detail={"access_session_id":str(access.id),**(detail or {})},ip_address=metadata.ip_address,user_agent=(metadata.user_agent or "")[:500] or None))


def audit_acceptance_rejection(session: Session, token: str, payload: AcceptanceSubmitRequest, metadata: RequestMetadata, error: ConsentAcceptanceError) -> None:
    if error.status_code >= 500: return
    access=session.scalar(select(ConsentAccessSession).where(ConsentAccessSession.public_token_hash==_hash(token)))
    if not access: return
    detail={
        "category":error.code,
        "idempotency_key_sha256":_hash(payload.idempotency_key),
        "declaration_count":len(payload.declarations),
        "all_declarations_accepted":all(item.accepted for item in payload.declarations),
        "acting_on_own_behalf":payload.acting_on_own_behalf,
        "typed_name_present":bool(payload.typed_full_name.strip()),
        "signature_present":bool(payload.signature_data_url),
        **error.safe_detail,
    }
    _audit(session,access,"CONSENT_ACCEPTANCE_REJECTED",metadata,result="FAILURE",detail=detail)
    session.commit()


def _patient_for_instance(session: Session, instance: ConsentInstance) -> Patient:
    patient=session.scalar(select(Patient).where(Patient.id==instance.patient_id,Patient.company_id==instance.company_id))
    if not patient: raise ConsentAcceptanceError("El paciente no está disponible.",404)
    return patient


def _sealed_context(instance: ConsentInstance) -> tuple[dict, ConsentDeclarationSet, date]:
    compatibility = inspect_acceptance_context(instance)
    if not compatibility.compatible:
        raise ConsentAcceptanceError(compatibility.public_message, 409)
    context = instance.context_snapshot or {}
    patient = context.get("patient") or {}
    country = compatibility.country_code
    locale = compatibility.locale
    try:
        birth_date = date.fromisoformat(patient["birth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConsentAcceptanceError("No es posible verificar la fecha de nacimiento sellada. Contacta a la clínica.", 422) from exc
    local_date = _now().astimezone(ZoneInfo(instance.timezone_name)).date()
    if birth_date > local_date:
        raise ConsentAcceptanceError("La fecha de nacimiento sellada no es válida. Contacta a la clínica.", 422)
    signer = signer_snapshot_from_instance(instance)
    try:
        declaration_set = declaration_set_for(country, locale, actor_type=signer.actor_type, app_env=settings.app_env, acceptance_enabled=settings.consent_acceptance_enabled, on_date=local_date)
    except ConsentDeclarationSetError as exc:
        raise ConsentAcceptanceError(str(exc), 409) from exc
    return patient, declaration_set, birth_date


def _pdf_inline_markdown(value: str) -> str:
    safe = escape(value)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", safe)
    safe = re.sub(r"_([^_]+)_", r"<i>\1</i>", safe)
    return safe


def _pdf_markdown_story(content: str, body: ParagraphStyle, heading: ParagraphStyle, *, skip_first_heading: str | None = None) -> list:
    result = []
    paragraph = []
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    first_heading_seen = False
    def flush():
        if paragraph:
            result.append(Paragraph(_pdf_inline_markdown(" ".join(paragraph)), body)); paragraph.clear()
    for line in lines:
        stripped = line.strip()
        if not stripped: flush(); continue
        if stripped == "---": flush(); result.append(HRFlowable(width="100%", thickness=.5, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=6)); continue
        markdown_heading = re.match(r"^(#{1,3})\s*(.*)$", stripped)
        if markdown_heading:
            flush()
            level, title = len(markdown_heading.group(1)), markdown_heading.group(2).strip()
            if not title:
                continue
            duplicate = not first_heading_seen and skip_first_heading and _normalize_name(title) == _normalize_name(skip_first_heading)
            first_heading_seen = True
            if duplicate:
                continue
            result.append(Paragraph(_pdf_inline_markdown(title), ParagraphStyle(f"DocumentH{level}", parent=heading, fontSize={1:12,2:10,3:9}[level])))
            continue
        if re.match(r"^[-*]\s+", stripped): flush(); result.append(Paragraph("• " + _pdf_inline_markdown(re.sub(r"^[-*]\s+", "", stripped)), body)); continue
        numbered = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if numbered: flush(); result.append(Paragraph(f"{numbered.group(1)}. " + _pdf_inline_markdown(numbered.group(2)), body)); continue
        paragraph.append(stripped)
    flush()
    return result


_PDF_MONTHS_ES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def _human_datetime(value: datetime | None, timezone_name: str, locale: str) -> str:
    if value is None:
        return "No disponible"
    try:
        local = value.astimezone(ZoneInfo(timezone_name))
    except (ValueError, KeyError):
        local = value.astimezone(timezone.utc)
    hour = local.hour % 12 or 12
    suffix = "a. m." if local.hour < 12 else "p. m."
    # es-CO and es-CL share this unambiguous long-date representation.
    return f"{local.day} de {_PDF_MONTHS_ES[local.month - 1]} de {local.year}, {hour}:{local.minute:02d} {suffix}"


def _acceptance_human_labels(acceptance: ConsentAcceptance) -> tuple[str | None, str | None]:
    return (
        responsible_relationship_label(
            acceptance.signer_relationship_type_snapshot,
            acceptance.signer_relationship_other_snapshot,
        ),
        minor_participation_label(
            acceptance.minor_participation_status_snapshot,
            acceptance.minor_participation_observation_snapshot,
        ),
    )


def _safe_pdf_color(value: str | None, fallback: str) -> str:
    return value if value and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def _visible_text_color(value: str | None, fallback: str = "#0f172a") -> str:
    color = _safe_pdf_color(value, fallback)
    red, green, blue = (int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))
    luminance = .2126 * red + .7152 * green + .0722 * blue
    return fallback if luminance > .72 else color


def _branding_snapshot(company: Company, site: Site) -> tuple[dict, bytes | None]:
    """Freeze tenant-owned institutional data and a validated logo at signing time."""
    logo_snapshot: dict = {
        "configured": bool(company.logo_path),
        "filename": company.logo_filename,
        "rendered": False,
        "sha256": None,
        "mime_type": None,
        "byte_size": None,
        "width": None,
        "height": None,
        "validation": "NOT_CONFIGURED" if not company.logo_path else "INVALID",
    }
    logo_bytes = None
    if company.logo_path:
        root = Path(settings.branding_storage_dir).resolve()
        candidate = (root / company.logo_path).resolve()
        tenant_directory = root / str(company.id)
        tenant_bound = tenant_directory == candidate.parent or tenant_directory in candidate.parents
        if tenant_bound and candidate.is_file():
            raw = candidate.read_bytes()
            logo_snapshot.update(byte_size=len(raw), sha256=_sha_bytes(raw))
            if 0 < len(raw) <= 5 * 1024 * 1024:
                try:
                    with PillowImage.open(BytesIO(raw)) as image:
                        image.verify()
                    with PillowImage.open(BytesIO(raw)) as image:
                        width, height = image.size
                        image_format = (image.format or "").upper()
                    mime_type = {"PNG":"image/png", "JPEG":"image/jpeg"}.get(image_format)
                    logo_snapshot.update(mime_type=mime_type, width=width, height=height)
                    if mime_type and 16 <= width <= 8000 and 16 <= height <= 8000:
                        logo_snapshot.update(rendered=True, validation="VALID")
                        logo_bytes = raw
                    else:
                        logo_snapshot["validation"] = "UNSUPPORTED_OR_INVALID_DIMENSIONS"
                except Exception:
                    logo_snapshot["validation"] = "INVALID_IMAGE"
            else:
                logo_snapshot["validation"] = "INVALID_SIZE"
        elif not tenant_bound:
            logo_snapshot["validation"] = "TENANT_PATH_MISMATCH"
        else:
            logo_snapshot["validation"] = "FILE_NOT_FOUND"
    snapshot = {
        "company": {
            "name": company.name,
            "legal_name": company.legal_name,
            "tax_id": company.tax_id,
            "address": company.address,
            "city": company.city,
            "department": company.department,
            "country": company.country,
            "phone": company.phone,
            "mobile": company.mobile,
            "email": company.email,
            "website": company.website,
            "header_text": company.header_text,
            "footer_text": company.footer_text,
            "primary_color": _safe_pdf_color(company.primary_color, "#16a34a"),
            "secondary_color": _safe_pdf_color(company.secondary_color, "#0f766e"),
            "heading_color": _safe_pdf_color(company.heading_color, "#0f172a"),
            "pdf_heading_color": _visible_text_color(company.heading_color),
        },
        "site": {
            "name": site.name,
            "address": site.address,
            "city": site.city,
            "phone": site.phone,
            "timezone": site.timezone,
        },
        "logo": logo_snapshot,
    }
    snapshot["sha256"] = _sha_bytes(_canonical(snapshot))
    return snapshot, logo_bytes


def _draw_paragraph(canvas: Canvas, text: str, style: ParagraphStyle, x: float, top: float, width: float, max_height: float) -> None:
    paragraph = Paragraph(escape(text or ""), style)
    _, height = paragraph.wrap(width, max_height)
    paragraph.drawOn(canvas, x, top - min(height, max_height))


class _ConsentPdfCanvas(Canvas):
    def __init__(self, *args, chrome: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._chrome = chrome
        self._page_states: list[dict] = []

    def showPage(self):
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._page_states)
        for page_number, state in enumerate(self._page_states, 1):
            self.__dict__.update(state)
            self._draw_chrome(page_number, total)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_number: int, total_pages: int) -> None:
        branding = self._chrome["branding"]
        company = branding["company"]
        site = branding["site"]
        primary = colors.HexColor(company["primary_color"])
        muted = colors.HexColor("#64748b")
        width, height = letter
        left, right = 1.6 * cm, width - 1.6 * cm
        is_test = self._chrome["test_document"]
        self.saveState()
        if is_test:
            banner_y = height - 0.72 * cm
            self.setFillColor(colors.HexColor("#fff1f2"))
            self.setStrokeColor(colors.HexColor("#fca5a5"))
            self.roundRect(left, banner_y - 13, right - left, 18, 4, fill=1, stroke=1)
            self.setFillColor(colors.HexColor("#b91c1c"))
            self.setFont("Helvetica-Bold", 7.5)
            self.drawCentredString(width / 2, banner_y - 6.5, TEST_DOCUMENT_NOTICE)
        header_top = height - (1.12 * cm if is_test else 0.48 * cm)
        logo_bytes = self._chrome.get("logo_bytes")
        logo_width = 28 * mm
        if logo_bytes:
            try:
                self.drawImage(ImageReader(BytesIO(logo_bytes)), left, header_top - 14 * mm, width=logo_width, height=12 * mm, preserveAspectRatio=True, anchor="c", mask="auto")
            except Exception:
                logo_bytes = None
        institution_x = left + (31 * mm if logo_bytes else 0)
        institution_width = 72 * mm if logo_bytes else 100 * mm
        institution_style = ParagraphStyle("PdfChromeInstitution", fontName="Helvetica-Bold", fontSize=9.2, leading=11, textColor=colors.HexColor(company["pdf_heading_color"]), alignment=TA_LEFT)
        detail_style = ParagraphStyle("PdfChromeDetail", fontName="Helvetica", fontSize=6.8, leading=8.5, textColor=muted, alignment=TA_LEFT)
        _draw_paragraph(self, company.get("name") or "Dentia", institution_style, institution_x, header_top, institution_width, 14)
        institution_detail = company.get("header_text") or " · ".join(part for part in [site.get("name"), site.get("city")] if part)
        _draw_paragraph(self, institution_detail, detail_style, institution_x, header_top - 14, institution_width, 20)
        title_style = ParagraphStyle("PdfChromeTitle", fontName="Helvetica-Bold", fontSize=9.5, leading=11, textColor=colors.HexColor(company["pdf_heading_color"]), alignment=TA_RIGHT)
        meta_style = ParagraphStyle("PdfChromeMeta", fontName="Helvetica", fontSize=6.8, leading=8.5, textColor=muted, alignment=TA_RIGHT)
        right_width = 67 * mm
        _draw_paragraph(self, "CONSENTIMIENTO INFORMADO", title_style, right - right_width, header_top, right_width, 14)
        _draw_paragraph(self, f"{self._chrome['visible_number']} · Versión {self._chrome['template_version']}", meta_style, right - right_width, header_top - 14, right_width, 14)
        divider_y = height - self._chrome["top_margin"] + 5
        self.setStrokeColor(primary); self.setLineWidth(0.8); self.line(left, divider_y, right, divider_y)

        footer_y = 1.47 * cm
        self.setStrokeColor(colors.HexColor(company["secondary_color"])); self.setLineWidth(0.45); self.line(left, footer_y, right, footer_y)
        footer_contact = company.get("footer_text") or " · ".join(part for part in [site.get("address") or company.get("address"), site.get("phone") or company.get("phone"), company.get("email"), company.get("website")] if part)
        footer_style = ParagraphStyle("PdfChromeFooter", fontName="Helvetica", fontSize=6.3, leading=7.5, textColor=muted, alignment=TA_LEFT)
        _draw_paragraph(self, footer_contact, footer_style, left, footer_y - 3, right - left, 10)
        self.setFont("Helvetica", 6.2); self.setFillColor(muted)
        verification = self._chrome["verification_id"]
        integrity = self._chrome["integrity_hash"]
        self.drawString(left, 0.54 * cm, f"Verificación {verification} · Integridad {integrity} · Generado {self._chrome['generated_at']}")
        self.drawRightString(right, 0.54 * cm, f"Página {page_number} de {total_pages}")
        self.restoreState()


def _validate_recipient(email: str | None, access: ConsentAccessSession, challenge: ConsentOtpChallenge, actor_type: str) -> str:
    email = (email or "").strip()
    if not email or "@" not in email or mask_email(email) != access.recipient_masked or _otp_hash(email.casefold()) != challenge.recipient_hash:
        label = "adulto responsable" if actor_type == RESPONSIBLE_ADULT else "paciente"
        raise ConsentAcceptanceError(f"El correo del {label} cambió después de verificar el acceso. Contacta a la clínica.", 409)
    return email


def _validate_eligibility(session: Session, access, instance):
    if instance.completion_channel == "PAPER": raise ConsentAcceptanceError("Este consentimiento fue preparado para firma en papel.",409)
    if instance.status!="PENDING_SIGNATURE": raise ConsentAcceptanceError("El consentimiento no está pendiente de aceptación.",409)
    if instance.missing_variables: raise ConsentAcceptanceError("El documento tiene información pendiente.",409)
    patient_snapshot, declaration_set, birth_date = _sealed_context(instance)
    signer = signer_snapshot_from_instance(instance)
    age=calculate_age(birth_date,_now().astimezone(ZoneInfo(instance.timezone_name)).date())
    if age is not None and age < 18 and signer.actor_type != RESPONSIBLE_ADULT: raise ConsentAcceptanceError("Los pacientes menores de edad requieren firma de adulto responsable. Contacta a la clínica.",422)
    if signer.actor_type == RESPONSIBLE_ADULT and not signer.email:
        raise ConsentAcceptanceError("El consentimiento no tiene un adulto responsable válido. Contacta a la clínica.",422)
    if session.scalar(select(ConsentClarificationRequest.id).where(ConsentClarificationRequest.consent_instance_id==instance.id,ConsentClarificationRequest.status=="OPEN")):
        raise ConsentAcceptanceError("Existe una solicitud de aclaración pendiente. Contacta a la clínica.",409)
    challenge=session.scalar(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id==access.id,ConsentOtpChallenge.status=="VERIFIED").order_by(ConsentOtpChallenge.verified_at.desc()))
    if not challenge: raise ConsentAcceptanceError("El canal de identidad no está verificado.",401)
    return challenge, patient_snapshot, declaration_set, birth_date, signer


def acceptance_requirements(session: Session, token: str, cookie: str | None, metadata: RequestMetadata):
    _require_enabled(); access,instance,_=_verified(session,token,cookie,metadata); _patient_for_instance(session,instance); _,patient_snapshot,declaration_set,_,signer=_validate_eligibility(session,access,instance)
    _audit(session,access,"CONSENT_ACCEPTANCE_STARTED",metadata); session.commit()
    return AcceptanceRequirementsResponse(enabled=True,declaration_set_code=declaration_set.code,declarations_country_code=declaration_set.country_code,declarations_locale=declaration_set.locale,declarations_version=declaration_set.version,declarations_legal_status=declaration_set.legal_status,declarations_set_sha256=declaration_set.sha256,declarations=[{"code":code,"text":text,"order":index} for index,(code,text) in enumerate(declaration_set.declarations,1)],patient_name=patient_snapshot["full_name"],signer_actor_type=signer.actor_type,signer_name=signer.full_name,signer_relationship=signer.relationship_label,signature_required=settings.consent_signature_required,legal_review_pending=declaration_set.legal_status!="APPROVED",test_document=declaration_set.is_test_document,test_notice=TEST_DOCUMENT_NOTICE if declaration_set.is_test_document else None)


def _pdf(instance, acceptance, declarations, signature: bytes, branding: dict, logo_bytes: bytes | None, declaration_set: ConsentDeclarationSet) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    company = branding["company"]
    primary = colors.HexColor(company["primary_color"])
    heading_color = colors.HexColor(company["pdf_heading_color"])
    top_margin = 3.05 * cm if declaration_set.is_test_document else 2.45 * cm
    body = ParagraphStyle("ConsentBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.4, spaceAfter=4, textColor=colors.HexColor("#334155"))
    small = ParagraphStyle("ConsentSmall", parent=body, fontSize=7.4, leading=9.6, textColor=colors.HexColor("#64748b"))
    cell = ParagraphStyle("ConsentCell", parent=body, fontSize=8.4, leading=11, spaceAfter=0)
    cell_bold = ParagraphStyle("ConsentCellBold", parent=cell, fontName="Helvetica-Bold", textColor=heading_color)
    centered = ParagraphStyle("ConsentCentered", parent=small, alignment=TA_CENTER)
    heading = ParagraphStyle("ConsentHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.8, leading=13, spaceBefore=7, spaceAfter=5, textColor=primary)
    title = ParagraphStyle("ConsentSpecificTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=15, leading=18, spaceAfter=8, alignment=TA_LEFT, textColor=heading_color)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=top_margin,
        bottomMargin=1.8 * cm,
        title=f"Consentimiento {instance.visible_number}",
        author=company.get("name") or "Dentia",
        pageCompression=0,
    )
    table_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    story = [Paragraph(escape(instance.display_title), title)]
    story.extend(_pdf_markdown_story(instance.rendered_content_snapshot or "", body, heading, skip_first_heading=instance.display_title))
    story.extend([Spacer(1, 7), Paragraph("Declaraciones registradas", heading)])
    for row in declarations:
        story.append(Paragraph(f"• {escape(row.text_snapshot)}", body))
    professional = (instance.context_snapshot or {}).get("professional") or {}
    reviewed_at = _human_datetime(instance.professional_confirmed_at, instance.timezone_name, declaration_set.locale)
    professional_rows = [
        [Paragraph("Profesional que confirmó el contenido clínico", cell_bold), Paragraph(escape(professional.get("full_name") or "No disponible"), cell)],
        [Paragraph("Fecha de revisión profesional", cell_bold), Paragraph(escape(reviewed_at), cell)],
    ]
    story.extend([
        Spacer(1, 7),
        Paragraph("Revisión profesional", heading),
        Table(professional_rows, colWidths=[doc.width * .43, doc.width * .57], style=table_style),
        CondPageBreak(78 * mm),
        Paragraph("Aceptación por adulto responsable" if acceptance.actor_type == RESPONSIBLE_ADULT else "Aceptación del paciente", heading),
        Paragraph("Aceptación electrónica registrada mediante verificación por correo, declaraciones expresas, nombre escrito y firma gráfica.", body),
    ])
    accepted_at = _human_datetime(acceptance.accepted_at, acceptance.timezone_name, declaration_set.locale)
    acceptance_rows = [
        [Paragraph("Paciente", cell_bold), Paragraph(escape(acceptance.patient_name_snapshot), cell)],
    ]
    if acceptance.actor_type == RESPONSIBLE_ADULT:
        relation, _ = _acceptance_human_labels(acceptance)
        relation = relation or "Adulto responsable"
        acceptance_rows.extend([
            [Paragraph("Adulto responsable que firma", cell_bold), Paragraph(escape(acceptance.signer_full_name_snapshot or acceptance.typed_full_name), cell)],
            [Paragraph("Relación con el paciente", cell_bold), Paragraph(escape(relation), cell)],
            [Paragraph("Documento del firmante", cell_bold), Paragraph(escape(" ".join(part for part in [acceptance.signer_document_type_snapshot, acceptance.signer_document_number_snapshot] if part)), cell)],
        ])
    acceptance_rows.extend([
        [Paragraph("Nombre digitado", cell_bold), Paragraph(escape(acceptance.typed_full_name), cell)],
        [Paragraph("Fecha y hora", cell_bold), Paragraph(escape(accepted_at), cell)],
        [Paragraph("Zona horaria", cell_bold), Paragraph(escape(acceptance.timezone_name), cell)],
        [Paragraph("Identificador de verificación", cell_bold), Paragraph(escape(str(acceptance.id)), cell)],
    ])
    story.append(Table(acceptance_rows, colWidths=[doc.width * .30, doc.width * .70], style=table_style))
    if acceptance.actor_type == RESPONSIBLE_ADULT and acceptance.minor_participation_status_snapshot:
        _, participation = _acceptance_human_labels(acceptance)
        participation = participation or "No registrada"
        story.extend([
            Spacer(1, 7),
            Paragraph("Participación del menor", heading),
            Table(
                [[Paragraph("Manifestación registrada", cell_bold), Paragraph(escape(participation), cell)]],
                colWidths=[doc.width * .30, doc.width * .70],
                style=table_style,
            ),
        ])
    with PillowImage.open(BytesIO(signature)) as signature_image:
        signature_width, signature_height = signature_image.size
    max_width, max_height = 76 * mm, 25 * mm
    scale = min(max_width / signature_width, max_height / signature_height)
    rendered_width, rendered_height = signature_width * scale, signature_height * scale
    signature_flowable = Image(BytesIO(signature), width=rendered_width, height=rendered_height)
    signature_table = Table([[signature_flowable]], colWidths=[82 * mm], hAlign="CENTER", style=TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LINEBELOW", (0, 0), (-1, -1), .55, colors.HexColor("#64748b")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    signature_block = [
        Spacer(1, 8),
        Paragraph("Firma gráfica capturada electrónicamente", heading),
        signature_table,
        Spacer(1, 3),
        Paragraph(escape(acceptance.typed_full_name), ParagraphStyle("SignatureName", parent=cell_bold, alignment=TA_CENTER)),
        Paragraph(escape(accepted_at), centered),
        Spacer(1, 5),
        Paragraph("Registro electrónico generado por Dentia. Implementación técnica provisional pendiente de revisión jurídica. Este documento no constituye una afirmación de validez legal.", small),
    ]
    story.append(KeepTogether(signature_block))
    chrome = {
        "branding": branding,
        "logo_bytes": logo_bytes,
        "test_document": declaration_set.is_test_document,
        "visible_number": instance.visible_number,
        "template_version": instance.template_version_number,
        "verification_id": str(acceptance.id).split("-", 1)[0].upper(),
        "integrity_hash": (instance.integrity_hash or "")[:12],
        "generated_at": accepted_at,
        "top_margin": top_margin,
    }
    doc.build(story, canvasmaker=lambda *args, **kwargs: _ConsentPdfCanvas(*args, chrome=chrome, **kwargs))
    return buffer.getvalue()


def _storage_path(company_id: UUID, instance_id: UUID, filename: str) -> Path:
    root=Path(settings.consent_final_storage_dir).resolve(); candidate=(root/str(company_id)/str(instance_id)/"final"/filename).resolve()
    if root not in candidate.parents: raise ConsentAcceptanceError("Ruta de almacenamiento inválida.",500)
    return candidate


def _instance_storage_root(company_id: UUID, instance_id: UUID) -> Path:
    root=Path(settings.consent_final_storage_dir).resolve(); candidate=(root/str(company_id)/str(instance_id)).resolve()
    if root not in candidate.parents: raise ConsentAcceptanceError("Ruta de almacenamiento inválida.",500)
    return candidate


def _atomic_write(path: Path, content: bytes):
    path.parent.mkdir(parents=True,exist_ok=True); temp=path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        with temp.open("xb") as stream: stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def _fsync_directory(path: Path):
    descriptor=os.open(path,os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def _remove_bundle(path: Path):
    if path.exists(): shutil.rmtree(path)


def _cleanup_uncommitted_artifacts(session: Session, instance: ConsentInstance):
    committed=session.scalar(select(ConsentFinalDocument.id).where(ConsentFinalDocument.consent_instance_id==instance.id))
    if committed: return
    instance_root=_instance_storage_root(instance.company_id,instance.id)
    _remove_bundle(instance_root/"final")
    if instance_root.exists():
        for staging in instance_root.glob(".staging-*"): _remove_bundle(staging)


def _promote_bundle(staging: Path, final_directory: Path):
    if final_directory.exists(): raise ConsentAcceptanceError("Ya existe un paquete final no reconciliado.",500)
    os.replace(staging,final_directory)
    _fsync_directory(final_directory.parent)


def _delivery(session: Session, acceptance, final, recipient_email: str, pdf: bytes, requested_by=None):
    now=_now(); delivery=ConsentCopyDelivery(company_id=acceptance.company_id,consent_instance_id=acceptance.consent_instance_id,acceptance_id=acceptance.id,final_document_id=final.id,status="PENDING",recipient_masked=acceptance.recipient_masked_snapshot,attempted_at=now,requested_by=requested_by); session.add(delivery); session.flush()
    test_prefix="[PRUEBA] " if acceptance.test_document else ""; test_notice=f"\n\n{TEST_DOCUMENT_NOTICE}" if acceptance.test_document else ""
    try:
        get_email_provider().send(EmailDelivery(recipient=recipient_email,subject=f"{test_prefix}Copia de consentimiento registrado",body=f"Adjuntamos la copia del documento registrado. Consérvela y contacte directamente a la clínica si requiere soporte.{test_notice}",attachments=((final.filename,"application/pdf",pdf),)))
        delivery.status="SENT"; delivery.delivered_at=_now()
    except EmailDeliveryError: delivery.status="FAILED"; delivery.error_code="DELIVERY_FAILED"
    return delivery


def submit_acceptance(session: Session, token: str, cookie: str | None, payload: AcceptanceSubmitRequest, metadata: RequestMetadata):
    _require_enabled()
    access_by_token=session.scalar(select(ConsentAccessSession).where(ConsentAccessSession.public_token_hash==_hash(token)).with_for_update())
    prior=session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.access_session_id==access_by_token.id,ConsentAcceptance.idempotency_key==payload.idempotency_key)) if access_by_token else None
    prior_public=session.get(ConsentPublicSession,prior.public_session_id) if prior else None
    if prior and prior.status=="COMPLETED" and cookie and prior_public and prior_public.session_token_hash==_hash(cookie):
        _audit(session,access_by_token,"CONSENT_DUPLICATE_SUBMISSION_BLOCKED",metadata,detail={"acceptance_id":str(prior.id),"resolution":"IDEMPOTENT_RESPONSE"})
        final=session.scalar(select(ConsentFinalDocument).where(ConsentFinalDocument.acceptance_id==prior.id)); raw=secrets.token_urlsafe(32); final.public_download_token_hash=_hash(raw); final.public_download_expires_at=_now()+timedelta(minutes=settings.consent_final_download_minutes); delivery=_latest_delivery(session,prior.id); session.commit(); return _submit_response(prior,final,raw,delivery)
    access,instance,public=_verified(session,token,cookie,metadata)
    instance=session.scalar(select(ConsentInstance).where(ConsentInstance.id==instance.id).with_for_update()); existing=session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==instance.id))
    if existing and existing.status=="COMPLETED":
        final=session.scalar(select(ConsentFinalDocument).where(ConsentFinalDocument.acceptance_id==existing.id)); raw=secrets.token_urlsafe(32); final.public_download_token_hash=_hash(raw); final.public_download_expires_at=_now()+timedelta(minutes=settings.consent_final_download_minutes); session.commit(); return _submit_response(existing,final,raw,_latest_delivery(session,existing.id))
    patient=_patient_for_instance(session,instance); challenge,patient_snapshot,declaration_set,birth_date,signer=_validate_eligibility(session,access,instance); recipient_email=_validate_recipient(signer.email,access,challenge,signer.actor_type)
    expected_own_behalf = signer.actor_type == PATIENT_SELF
    if payload.acting_on_own_behalf != expected_own_behalf:
        action = "RESPONSIBLE_ADULT_ACCESS_DENIED" if signer.actor_type == RESPONSIBLE_ADULT else "CONSENT_SIGNING_ACCESS_DENIED"
        _audit(session,access,action,metadata,result="FAILURE",detail={"reason":"ACTOR_MISMATCH","expected_actor":signer.actor_type}); session.commit()
        raise ConsentAcceptanceError("El firmante no coincide con el actor preparado por la clínica. Contacta a la clínica.",422,"IDENTITY_MISMATCH")
    if payload.declarations_version!=declaration_set.version or payload.declaration_set_code!=declaration_set.code or payload.declarations_set_sha256!=declaration_set.sha256: raise ConsentAcceptanceError("Las declaraciones cambiaron. Revísalas nuevamente.",409,"REQUEST_STALE")
    patient_content=instance.rendered_content_snapshot or ""; content_validation=validate_patient_facing_content(patient_content,allowed_variables=None,document_type=instance.document_kind,signer_compatibility=getattr(instance, "signer_policy", "PATIENT_SELF"),normalized_hash=_hash(patient_content),enforce_electronic_readiness=True)
    if content_validation.status=="BLOCKED": raise ConsentAcceptanceError("El documento no está disponible para firma electrónica. Contacta a la clínica.",409,"CONTENT_NOT_PATIENT_FACING")
    received={item.code:item.accepted for item in payload.declarations}; expected={code for code,_ in declaration_set.declarations}
    if set(received)!=expected or not all(received.values()): raise ConsentAcceptanceError("Debes aceptar individualmente todas las declaraciones para continuar.",422,"DECLARATIONS_INCOMPLETE")
    patient_name=patient_snapshot["full_name"]
    if _normalize_name(payload.typed_full_name)!=_normalize_name(signer.full_name): raise ConsentAcceptanceError("El nombre digitado no coincide con el firmante identificado.",422,"IDENTITY_MISMATCH")
    responsible_row=session.scalar(select(ConsentResponsibleAdult).where(ConsentResponsibleAdult.consent_instance_id==instance.id)) if signer.actor_type == RESPONSIBLE_ADULT else None
    if signer.actor_type == RESPONSIBLE_ADULT and responsible_row is None:
        raise ConsentAcceptanceError("El adulto responsable no está disponible. Contacta a la clínica.",422,"IDENTITY_MISMATCH")
    signature,width,height=_decode_signature(payload.signature_data_url); now=_now(); local=now.astimezone(ZoneInfo(instance.timezone_name)); raw_download=secrets.token_urlsafe(32)
    _cleanup_uncommitted_artifacts(session,instance)
    acceptance=ConsentAcceptance(company_id=instance.company_id,site_id=instance.site_id,patient_id=instance.patient_id,consent_instance_id=instance.id,access_session_id=access.id,public_session_id=public.id,otp_challenge_id=challenge.id,status="SUBMITTED",idempotency_key=payload.idempotency_key,actor_type=signer.actor_type,acting_on_own_behalf=expected_own_behalf,responsible_adult_snapshot_id=responsible_row.id if responsible_row else None,typed_full_name=payload.typed_full_name.strip(),signer_full_name_snapshot=signer.full_name,signer_document_type_snapshot=signer.document_type,signer_document_number_snapshot=signer.document_number,signer_relationship_type_snapshot=signer.relationship_type,signer_relationship_other_snapshot=signer.relationship_other,signer_email_masked_snapshot=access.recipient_masked,minor_participation_status_snapshot=signer.minor_participation_status,minor_participation_observation_snapshot=signer.minor_participation_observation,patient_name_snapshot=patient_name,patient_birth_date_snapshot=birth_date,patient_document_type_snapshot=patient_snapshot.get("document_type") or "No informado",patient_document_number_snapshot=patient_snapshot.get("document_number"),recipient_masked_snapshot=access.recipient_masked,declaration_set_code=declaration_set.code,declarations_country_code=declaration_set.country_code,declarations_locale=declaration_set.locale,declarations_version=declaration_set.version,declarations_legal_status=declaration_set.legal_status,declarations_effective_from=declaration_set.effective_from,declarations_set_sha256=declaration_set.sha256,test_document=declaration_set.is_test_document,accepted_at=now,timezone_name=instance.timezone_name,local_datetime=local.isoformat(),ip_hash=_hash(metadata.ip_address) if metadata.ip_address else None,user_agent_summary=(metadata.user_agent or "")[:500] or None,locale=declaration_set.locale,correlation_id=secrets.token_hex(16)); session.add(acceptance); session.flush()
    declarations=[]
    for order,(code,text_value) in enumerate(declaration_set.declarations,1):
        row=ConsentAcceptanceDeclaration(company_id=instance.company_id,acceptance_id=acceptance.id,code=code,text_snapshot=text_value,text_sha256=hashlib.sha256(text_value.encode()).hexdigest(),declaration_version=declaration_set.version,required=True,accepted=True,responded_at=now,order_number=order); session.add(row); declarations.append(row)
    company=session.get(Company,instance.company_id); site=session.get(Site,instance.site_id)
    if company is None or site is None or site.company_id != company.id:
        raise ConsentAcceptanceError("No fue posible obtener la identidad institucional del documento.", 409)
    branding_snapshot, logo_bytes = _branding_snapshot(company, site)
    pdf=_pdf(instance,acceptance,declarations,signature,branding_snapshot,logo_bytes,declaration_set); _failure_point("PDF_GENERATED")
    signature_key=f"{instance.visible_number}-signature.png"; pdf_name=f"{instance.visible_number}-consentimiento-final.pdf"; manifest_key=f"{instance.visible_number}-evidence.json"
    final_directory=_instance_storage_root(instance.company_id,instance.id)/"final"; staging_directory=_instance_storage_root(instance.company_id,instance.id)/f".staging-{acceptance.id}"
    sig_path=final_directory/signature_key; pdf_path=final_directory/pdf_name; manifest_path=final_directory/manifest_key
    stage_sig=staging_directory/signature_key; stage_pdf=staging_directory/pdf_name; stage_manifest=staging_directory/manifest_key
    manifest={"schema_version":"1.2","verification_id":str(acceptance.id),"correlation_id":acceptance.correlation_id,"company_id":str(instance.company_id),"site_id":str(instance.site_id),"patient_id":str(instance.patient_id),"consent_instance_id":str(instance.id),"visible_number":instance.visible_number,"access_session_id":str(access.id),"public_session_id":str(public.id),"otp_challenge_id":str(challenge.id),"otp_verified_at":challenge.verified_at.isoformat() if challenge.verified_at else None,"channel":access.channel,"recipient_masked":acceptance.recipient_masked_snapshot,"accepted_at_utc":now.isoformat(),"accepted_at_local":local.isoformat(),"timezone":instance.timezone_name,"actor_type":signer.actor_type,"acting_on_own_behalf":expected_own_behalf,"typed_full_name":acceptance.typed_full_name,"signer_identity_snapshot":{"full_name":signer.full_name,"document_type":signer.document_type,"document_number":signer.document_number,"relationship_type":signer.relationship_type,"relationship_other":signer.relationship_other,"email_masked":access.recipient_masked,"minor_participation_status":signer.minor_participation_status,"minor_participation_observation":signer.minor_participation_observation},"patient_identity_snapshot":{"full_name":acceptance.patient_name_snapshot,"birth_date":birth_date.isoformat(),"document_type":acceptance.patient_document_type_snapshot,"document_number":acceptance.patient_document_number_snapshot},"branding_snapshot":branding_snapshot,"declaration_set":{"country_code":declaration_set.country_code,"locale":declaration_set.locale,"code":declaration_set.code,"version":declaration_set.version,"legal_status":declaration_set.legal_status,"effective_from":declaration_set.effective_from.isoformat() if declaration_set.effective_from else None,"sha256":declaration_set.sha256},"test_document":declaration_set.is_test_document,"test_notice":TEST_DOCUMENT_NOTICE if declaration_set.is_test_document else None,"template_version":instance.template_version_number,"template_snapshot":instance.template_content_snapshot,"rendered_content_snapshot":instance.rendered_content_snapshot,"context_snapshot":instance.context_snapshot,"professional_role":"REVIEWED_CONTENT","professional_confirmed_by":str(instance.professional_confirmed_by) if instance.professional_confirmed_by else None,"professional_confirmed_at":instance.professional_confirmed_at.isoformat() if instance.professional_confirmed_at else None,"declarations":[{"code":r.code,"version":r.declaration_version,"order":r.order_number,"required":r.required,"text":r.text_snapshot,"sha256":r.text_sha256,"accepted":True,"responded_at":r.responded_at.isoformat()} for r in declarations],"template_content_sha256":instance.template_content_sha256,"instance_content_sha256":instance.instance_content_sha256,"context_sha256":instance.context_sha256,"integrity_hash":instance.integrity_hash,"signature_sha256":_sha_bytes(signature),"final_pdf_sha256":_sha_bytes(pdf),"software":"Dentia/C019A.4"}; manifest_bytes=_canonical(manifest)
    promoted=False
    try:
        staging_directory.mkdir(parents=True,exist_ok=False)
        for label,path,content in (("SIGNATURE_STORED",stage_sig,signature),("MANIFEST_STORED",stage_manifest,manifest_bytes),("PDF_STORED",stage_pdf,pdf)): _atomic_write(path,content); _failure_point(label)
        _fsync_directory(staging_directory)
        for path,content in ((stage_sig,signature),(stage_pdf,pdf),(stage_manifest,manifest_bytes)):
            if _sha_bytes(path.read_bytes())!=_sha_bytes(content): raise ConsentAcceptanceError("Falló la verificación de los artefactos finales.",500)
        _failure_point("HASH_VERIFIED")
        session.add(ConsentSignatureArtifact(company_id=instance.company_id,acceptance_id=acceptance.id,storage_key=str(sig_path.relative_to(Path(settings.consent_final_storage_dir).resolve())),signature_type="DRAWN_CANVAS_PNG",typed_name_snapshot=acceptance.typed_full_name,graphic_present=True,sanitization_version="PNG_CANVAS_V1",sha256=_sha_bytes(signature),mime_type="image/png",byte_size=len(signature),width=width,height=height))
        evidence=ConsentEvidenceManifest(company_id=instance.company_id,acceptance_id=acceptance.id,schema_version="1.2",manifest=manifest,manifest_sha256=_sha_bytes(manifest_bytes),storage_key=str(manifest_path.relative_to(Path(settings.consent_final_storage_dir).resolve())));session.add(evidence);session.flush()
        final=ConsentFinalDocument(company_id=instance.company_id,consent_instance_id=instance.id,acceptance_id=acceptance.id,evidence_manifest_id=evidence.id,storage_key=str(pdf_path.relative_to(Path(settings.consent_final_storage_dir).resolve())),filename=pdf_name,byte_size=len(pdf),sha256=_sha_bytes(pdf),generated_at=now,renderer_version="REPORTLAB_DENTIA_V1",immutable=True,public_download_token_hash=_hash(raw_download),public_download_expires_at=now+timedelta(minutes=settings.consent_final_download_minutes)); session.add(final); session.flush(); _failure_point("DB_PERSISTED")
        acceptance.status="COMPLETED"; instance.status="SIGNED"; instance.completion_channel="ELECTRONIC"; instance.signed_at=now; instance.row_version+=1
        for item in session.scalars(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id==instance.id,ConsentAccessSession.status.notin_(["REVOKED","EXPIRED"]))): item.status="REVOKED";item.revoked_at=now;item.revoke_reason="SIGNED"
        for item in session.scalars(select(ConsentPublicSession).join(ConsentAccessSession,ConsentAccessSession.id==ConsentPublicSession.access_session_id).where(ConsentAccessSession.consent_instance_id==instance.id,ConsentPublicSession.status=="ACTIVE")): item.status="REVOKED";item.revoked_at=now
        for item in session.scalars(select(ConsentOtpChallenge).join(ConsentAccessSession,ConsentAccessSession.id==ConsentOtpChallenge.access_session_id).where(ConsentAccessSession.consent_instance_id==instance.id,ConsentOtpChallenge.status=="PENDING")): item.status="INVALIDATED"
        for action in (("RESPONSIBLE_ADULT_ACCEPTANCE_COMPLETED",) if signer.actor_type == RESPONSIBLE_ADULT else tuple()) + ("CONSENT_DECLARATION_CONFIRMED","CONSENT_SIGNATURE_CAPTURED","CONSENT_ACCEPTANCE_SUBMITTED","CONSENT_EVIDENCE_MANIFEST_GENERATED","CONSENT_FINAL_PDF_GENERATED","CONSENT_ACCEPTANCE_COMPLETED"):_audit(session,access,action,metadata,detail={"acceptance_id":str(acceptance.id),"pdf_sha256":final.sha256})
        _promote_bundle(staging_directory,final_directory); promoted=True
        for path,content in ((sig_path,signature),(pdf_path,pdf),(manifest_path,manifest_bytes)):
            if _sha_bytes(path.read_bytes())!=_sha_bytes(content): raise ConsentAcceptanceError("Falló la verificación del paquete final promovido.",500)
        _failure_point("BEFORE_DB_COMMIT")
        session.commit()
    except Exception:
        session.rollback()
        _remove_bundle(staging_directory)
        if promoted: _remove_bundle(final_directory)
        try:
            _audit(session,access,"CONSENT_FINAL_PDF_STORAGE_FAILED",metadata,result="FAILURE")
            _audit(session,access,"CONSENT_ACCEPTANCE_FAILED",metadata,result="FAILURE",detail={"reason":"FINAL_ARTIFACT_STORAGE"})
            session.commit()
        except Exception:session.rollback()
        raise
    _audit(session,access,"CONSENT_COPY_DELIVERY_REQUESTED",metadata);delivery=_delivery(session,acceptance,final,recipient_email,pdf); _audit(session,access,"CONSENT_COPY_DELIVERY_SUCCEEDED" if delivery.status=="SENT" else "CONSENT_COPY_DELIVERY_FAILED",metadata,result="SUCCESS" if delivery.status=="SENT" else "FAILURE",detail={"delivery_id":str(delivery.id)}); session.commit()
    return _submit_response(acceptance,final,raw_download,delivery)


def _latest_delivery(session, acceptance_id): return session.scalar(select(ConsentCopyDelivery).where(ConsentCopyDelivery.acceptance_id==acceptance_id).order_by(ConsentCopyDelivery.attempted_at.desc()))
def _submit_response(acceptance,final,raw,delivery): return AcceptanceSubmitResponse(acceptance_id=acceptance.id,status=acceptance.status,accepted_at=acceptance.accepted_at,final_document_sha256=final.sha256,verification_id=acceptance.id,download_url=f"/api/public/consents/final-documents/{raw}",copy_delivery_status=delivery.status if delivery else "PENDING",test_document=acceptance.test_document,test_notice=TEST_DOCUMENT_NOTICE if acceptance.test_document else None)


def _verified_final_path(final: ConsentFinalDocument) -> Path:
    path=_storage_path(final.company_id,final.consent_instance_id,Path(final.storage_key).name)
    if not path.is_file() or _sha_bytes(path.read_bytes())!=final.sha256: raise ConsentAcceptanceError("El documento final no superó la verificación de integridad.",409)
    return path


def public_final_document(session: Session, download_token: str, metadata: RequestMetadata):
    _require_enabled(); final=session.scalar(select(ConsentFinalDocument).where(ConsentFinalDocument.public_download_token_hash==_hash(download_token)))
    if not final or not final.public_download_expires_at or final.public_download_expires_at<=_now(): raise ConsentAcceptanceError("La descarga no está disponible.",404)
    path=_verified_final_path(final); final.download_count+=1; acceptance=session.get(ConsentAcceptance,final.acceptance_id);access=session.get(ConsentAccessSession,acceptance.access_session_id);_audit(session,access,"CONSENT_FINAL_DOCUMENT_DOWNLOADED",metadata,detail={"channel":"PUBLIC_TEMPORARY"});session.commit();return final,path


def acceptance_summary(session: Session, context: AuthContext, instance_id: UUID):
    instance=_require_instance(session,context,instance_id); acceptance=session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.company_id==instance.company_id,ConsentAcceptance.consent_instance_id==instance.id));
    if not acceptance: raise ConsentAcceptanceError("La instancia no tiene aceptación completada.",404)
    final=session.scalar(select(ConsentFinalDocument).where(ConsentFinalDocument.acceptance_id==acceptance.id)); delivery=_latest_delivery(session,acceptance.id)
    relation, _ = _acceptance_human_labels(acceptance)
    return AcceptanceSummaryResponse(acceptance_id=acceptance.id,status=acceptance.status,accepted_at=acceptance.accepted_at,actor_type=acceptance.actor_type,patient_name=acceptance.patient_name_snapshot,signer_name=acceptance.signer_full_name_snapshot or acceptance.typed_full_name,signer_relationship=relation,declarations_version=acceptance.declarations_version,declaration_set_code=acceptance.declaration_set_code,declarations_country_code=acceptance.declarations_country_code,declarations_locale=acceptance.declarations_locale,declarations_legal_status=acceptance.declarations_legal_status,declarations_set_sha256=acceptance.declarations_set_sha256,test_document=acceptance.test_document,test_notice=TEST_DOCUMENT_NOTICE if acceptance.test_document else None,final_document_sha256=final.sha256,copy_delivery_status=delivery.status if delivery else None)


def acceptance_evidence(session: Session, context: AuthContext, instance_id: UUID):
    instance=_require_instance(session,context,instance_id); acceptance=session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.company_id==instance.company_id,ConsentAcceptance.consent_instance_id==instance.id)); evidence=session.scalar(select(ConsentEvidenceManifest).where(ConsentEvidenceManifest.acceptance_id==acceptance.id)) if acceptance else None
    if not evidence: raise ConsentAcceptanceError("No existe evidencia para esta instancia.",404)
    if _sha_bytes(_canonical(evidence.manifest))!=evidence.manifest_sha256: raise ConsentAcceptanceError("La evidencia no superó la verificación de integridad.",409)
    return AcceptanceEvidenceResponse(acceptance_id=acceptance.id,schema_version=evidence.schema_version,manifest_sha256=evidence.manifest_sha256,manifest=evidence.manifest)


def private_final_document(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata | None = None):
    instance=_require_instance(session,context,instance_id); final=session.scalar(select(ConsentFinalDocument).where(ConsentFinalDocument.company_id==instance.company_id,ConsentFinalDocument.consent_instance_id==instance.id))
    if not final: raise ConsentAcceptanceError("No existe documento final.",404)
    path=_verified_final_path(final)
    if metadata:
        final.download_count+=1;acceptance=session.get(ConsentAcceptance,final.acceptance_id);access=session.get(ConsentAccessSession,acceptance.access_session_id);_audit(session,access,"CONSENT_FINAL_DOCUMENT_DOWNLOADED",metadata,user_id=context.user.id,detail={"channel":"PRIVATE"});session.commit()
    return final,path


def resend_copy(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata):
    final,path=private_final_document(session,context,instance_id); acceptance=session.get(ConsentAcceptance,final.acceptance_id); instance=session.get(ConsentInstance,acceptance.consent_instance_id); signer=signer_snapshot_from_instance(instance); access=session.get(ConsentAccessSession,acceptance.access_session_id);challenge=session.get(ConsentOtpChallenge,acceptance.otp_challenge_id);recipient_email=_validate_recipient(signer.email,access,challenge,signer.actor_type);_audit(session,access,"CONSENT_COPY_DELIVERY_REQUESTED",metadata,user_id=context.user.id);delivery=_delivery(session,acceptance,final,recipient_email,path.read_bytes(),context.user.id); _audit(session,access,"CONSENT_COPY_RESEND_SUCCEEDED" if delivery.status=="SENT" else "CONSENT_COPY_RESEND_FAILED",metadata,user_id=context.user.id,result="SUCCESS" if delivery.status=="SENT" else "FAILURE"); session.commit(); return {"status":delivery.status,"recipient_masked":delivery.recipient_masked,"attempted_at":delivery.attempted_at}
