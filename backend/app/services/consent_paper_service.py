import hashlib
import io
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import fitz
from PIL import Image, UnidentifiedImageError
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_acceptance import ConsentPaperPacket, ConsentPaperPage
from app.models.consent_template import ConsentAccessSession, ConsentInstance, ConsentOtpChallenge, ConsentPublicSession, ConsentTemplate, ConsentTemplateVersion
from app.models.site import Site
from app.schemas.consent_instance_schema import ConsentPaperPacketResponse, ConsentPaperPageResponse, ConsentPaperVerificationRequest
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.document_style import apply_reportlab_font
from app.services.consent_instance_service import _require_instance
from app.services.consent_production_readiness import ConsentProductionReadinessError, assert_template_ready
from app.services.consent_signer import RESPONSIBLE_ADULT, responsible_relationship_label, signer_policy_from_library_version

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_PAGES = 50
MAX_IMAGE_PIXELS = 40_000_000
VERIFICATION_VERSION = "PAPER_VERIFY_V1"


class ConsentPaperError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _root() -> Path:
    root = (Path(settings.consent_final_storage_dir).resolve() / "paper").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _packet_root(packet: ConsentPaperPacket) -> Path:
    candidate = (_root() / str(packet.company_id) / str(packet.consent_instance_id) / str(packet.id)).resolve()
    if _root() not in candidate.parents:
        raise ConsentPaperError("La ubicación del documento no es válida.", 500)
    return candidate


def _path(storage_key: str) -> Path:
    candidate = (_root() / storage_key).resolve()
    if _root() not in candidate.parents:
        raise ConsentPaperError("El documento solicitado no está disponible.", 404)
    return candidate


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, packet: ConsentPaperPacket, action: str, detail: dict | None = None) -> None:
    session.add(AuditEvent(
        company_id=packet.company_id, user_id=context.user.id, session_id=context.auth_session.id,
        entity="consent_paper_packet", entity_id=packet.id, action=action, result="SUCCESS",
        detail={"consent_instance_id": str(packet.consent_instance_id), "paper_packet_id": str(packet.id), **(detail or {})},
        ip_address=metadata.ip_address, user_agent=metadata.user_agent,
    ))


def _snapshot(instance: ConsentInstance, section: str, field: str, fallback: str = "No registrado") -> str:
    value = instance.context_snapshot.get(section, {}) if isinstance(instance.context_snapshot, dict) else {}
    result = value.get(field) if isinstance(value, dict) else None
    return str(result).strip() if result is not None and str(result).strip() else fallback


def _plain_lines(markdown: str) -> list[str]:
    lines = []
    for line in (markdown or "").splitlines():
        text = line.strip().lstrip("#").strip()
        if text:
            lines.append(text.replace("<", "&lt;").replace(">", "&gt;"))
    return lines or ["Contenido clínico revisado sin texto disponible."]


def _packet_pdf(instance: ConsentInstance, packet_id: UUID, company: Company, site: Site, *, test_document: bool, total_pages: int | None = None) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    body = ParagraphStyle("paper-body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=13, spaceAfter=4)
    heading = ParagraphStyle("paper-heading", parent=styles["Heading2"], textColor=colors.HexColor("#176B45"), fontSize=12, leading=15, spaceBefore=7, spaceAfter=5)
    title = ParagraphStyle("paper-title", parent=styles["Title"], textColor=colors.HexColor("#123047"), fontSize=17, leading=21, alignment=TA_CENTER)
    document_font = apply_reportlab_font(
        {"body": body, "heading": heading, "title": title},
        company.document_font_family,
    )
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=17*mm, leftMargin=17*mm, topMargin=20*mm, bottomMargin=19*mm, title=instance.display_title, author="Dentia", invariant=1)
    story = [Paragraph(str(company.name), heading), Paragraph("CONSENTIMIENTO PARA FIRMA MANUSCRITA", title), Spacer(1, 4*mm)]
    patient_name = _snapshot(instance, "patient", "full_name")
    patient_document = " ".join(filter(None, [_snapshot(instance, "patient", "document_type", ""), _snapshot(instance, "patient", "document_number", "")])) or "No registrado"
    details = [
        ["Consentimiento", instance.visible_number], ["Versión", str(instance.template_version_number)],
        ["Paciente", patient_name], ["Identificación", patient_document], ["Sede", site.name],
        ["Profesional revisor", _snapshot(instance, "professional", "full_name")], ["Fecha de emisión", instance.clinical_date.isoformat()],
        ["Identificador del packet", str(packet_id)],
    ]
    table = Table(details, colWidths=[42*mm, 123*mm])
    table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#CBD5E1")),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#ECFDF5")),("FONTNAME",(0,0),(0,-1),document_font.bold),("FONTNAME",(1,0),(1,-1),document_font.regular),("FONTSIZE",(0,0),(-1,-1),8.5),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),5)]))
    story += [table, Paragraph("Contenido clínico revisado", heading)]
    story += [Paragraph(line, body) for line in _plain_lines(instance.rendered_content_snapshot or "")]
    story += [Spacer(1, 5*mm), Paragraph("Firma manuscrita", heading)]
    if instance.signer_actor_type == RESPONSIBLE_ADULT:
        relation = responsible_relationship_label(instance.signer_relationship_type_snapshot, instance.signer_relationship_other_snapshot)
        signature_rows = [["Paciente menor", patient_name], ["Adulto responsable", instance.signer_full_name_snapshot or ""], ["Relación", relation], ["Documento del adulto", f"{instance.signer_document_type_snapshot or ''} {instance.signer_document_number_snapshot or ''}".strip()], ["Firma del adulto responsable", "\n\n\n"], ["Fecha", ""]]
    else:
        signature_rows = [["Paciente que firma", instance.signer_full_name_snapshot or patient_name], ["Documento", f"{instance.signer_document_type_snapshot or ''} {instance.signer_document_number_snapshot or ''}".strip()], ["Firma", "\n\n\n"], ["Fecha", ""]]
    signatures = Table(signature_rows, colWidths=[50*mm,115*mm])
    signatures.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.45,colors.HexColor("#64748B")),("FONTNAME",(0,0),(0,-1),document_font.bold),("FONTSIZE",(0,0),(-1,-1),9),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),7)]))
    story.append(signatures)
    if test_document:
        story.insert(0, Paragraph("DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO", ParagraphStyle("warning", parent=body, textColor=colors.HexColor("#B91C1C"), fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=11)))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1")); canvas.line(17*mm, 15*mm, 199*mm, 15*mm)
        canvas.setFont(document_font.regular, 7); canvas.setFillColor(colors.HexColor("#475569"))
        canvas.drawString(17*mm, 10*mm, f"Packet {packet_id}")
        suffix = f" de {total_pages}" if total_pages else ""
        canvas.drawRightString(199*mm, 10*mm, f"Página {document.page}{suffix} · Integridad: {instance.integrity_hash or 'pendiente'}")
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def _pages(session: Session, packet_id: UUID) -> list[ConsentPaperPage]:
    return list(session.scalars(select(ConsentPaperPage).where(ConsentPaperPage.paper_packet_id == packet_id).order_by(ConsentPaperPage.position)))


def _response(session: Session, packet: ConsentPaperPacket) -> ConsentPaperPacketResponse:
    rows = _pages(session, packet.id)
    return ConsentPaperPacketResponse(
        id=packet.id, consent_instance_id=packet.consent_instance_id, status=packet.status,
        expected_page_count=packet.expected_page_count, uploaded_page_count=len(rows), print_sha256=packet.print_sha256,
        print_byte_size=packet.print_byte_size, printed_at=packet.printed_at, printed_by=packet.printed_by,
        paper_signed_at=packet.paper_signed_at, paper_signed_recorded_by=packet.paper_signed_recorded_by,
        digitalization_started_at=packet.digitalization_started_at, digitization_finalized_at=packet.digitization_finalized_at,
        finalized_by=packet.finalized_by, final_pdf_sha256=packet.final_pdf_sha256, final_pdf_size=packet.final_pdf_size,
        final_page_count=packet.final_page_count, verification_version=packet.verification_version, row_version=packet.row_version,
        pages=[ConsentPaperPageResponse(id=x.id, position=x.position, sha256=x.sha256, byte_size=x.byte_size, source_mime_type=x.source_mime_type, original_page_number=x.original_page_number) for x in rows],
    )


def _packet_for(session: Session, context: AuthContext, instance_id: UUID, *, lock=False) -> tuple[ConsentInstance, ConsentPaperPacket]:
    instance = _require_instance(session, context, instance_id, lock=lock)
    statement = select(ConsentPaperPacket).where(ConsentPaperPacket.company_id == context.user.company_id, ConsentPaperPacket.consent_instance_id == instance.id)
    if lock: statement = statement.with_for_update()
    packet = session.scalar(statement)
    if packet is None:
        raise ConsentPaperError("El consentimiento no tiene un packet para firma en papel.", 404)
    return instance, packet


def get_packet(session: Session, context: AuthContext, instance_id: UUID) -> ConsentPaperPacketResponse:
    _, packet = _packet_for(session, context, instance_id)
    return _response(session, packet)


def prepare_packet(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata) -> ConsentPaperPacketResponse:
    instance = _require_instance(session, context, instance_id, lock=True)
    if instance.status not in {"READY_FOR_REVIEW", "PENDING_SIGNATURE"} or instance.completion_channel not in {None, "ELECTRONIC", "PAPER"}:
        raise ConsentPaperError("El consentimiento no está disponible para firma en papel.", 409)
    existing = session.scalar(select(ConsentPaperPacket).where(ConsentPaperPacket.consent_instance_id == instance.id).with_for_update())
    if existing:
        return _response(session, existing)
    company, site = session.get(Company, instance.company_id), session.get(Site, instance.site_id)
    if company is None or site is None:
        raise ConsentPaperError("No fue posible obtener la identidad institucional.", 409)
    packet_id = uuid4()
    template_version = session.get(ConsentTemplateVersion, instance.template_version_id)
    template = session.get(ConsentTemplate, instance.template_id)
    if template_version is None or template is None:
        raise ConsentPaperError("La plantilla sellada ya no está disponible.", 409)
    try:
        assert_template_ready(
            session,
            template=template,
            version=template_version,
            signer_policy=signer_policy_from_library_version(session, template_version),
            channel="PAPER",
        )
    except ConsentProductionReadinessError as exc:
        raise ConsentPaperError(str(exc), 409) from exc
    test_document = settings.app_env.casefold() != "production"
    first = _packet_pdf(instance, packet_id, company, site, test_document=test_document)
    try:
        with fitz.open(stream=first, filetype="pdf") as document: page_count = document.page_count
    except Exception as exc:
        raise ConsentPaperError("No fue posible preparar el documento para impresión.", 500) from exc
    raw = _packet_pdf(instance, packet_id, company, site, test_document=test_document, total_pages=page_count)
    with fitz.open(stream=raw, filetype="pdf") as document: page_count = document.page_count
    relative = Path(str(instance.company_id)) / str(instance.id) / str(packet_id) / "print" / f"{secrets.token_hex(24)}.pdf"
    target = _root() / relative
    packet = ConsentPaperPacket(id=packet_id, company_id=instance.company_id, site_id=instance.site_id, patient_id=instance.patient_id,
        consent_instance_id=instance.id, status="PRINTED", print_storage_key=str(relative), print_sha256=_sha(raw), print_byte_size=len(raw),
        expected_page_count=page_count, uploaded_page_count=0, printed_at=_now(), printed_by=context.user.id)
    _atomic_write(target, raw)
    now = _now()
    for access in session.scalars(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id == instance.id, ConsentAccessSession.status.notin_(["REVOKED", "EXPIRED"])).with_for_update()):
        access.status="REVOKED"; access.revoked_at=now; access.revoked_by=context.user.id; access.revoke_reason="PAPER_CHANNEL_SELECTED"; access.row_version += 1
        for challenge in session.scalars(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id==access.id, ConsentOtpChallenge.status=="PENDING")): challenge.status="INVALIDATED"
        for public in session.scalars(select(ConsentPublicSession).where(ConsentPublicSession.access_session_id==access.id, ConsentPublicSession.status=="ACTIVE")): public.status="REVOKED"; public.revoked_at=now
    instance.status="PENDING_SIGNATURE"; instance.completion_channel="PAPER"; instance.updated_by=context.user.id; instance.row_version += 1
    session.add(packet); _audit(session, context, metadata, packet, "CONSENT_PAPER_CHANNEL_SELECTED"); _audit(session, context, metadata, packet, "CONSENT_PAPER_PACKET_GENERATED", {"page_count": page_count, "sha256": packet.print_sha256})
    session.commit()
    return _response(session, packet)


def document_bytes(session: Session, context: AuthContext, instance_id: UUID, *, final: bool, metadata: RequestMetadata, download: bool = False) -> tuple[bytes, str]:
    _, packet = _packet_for(session, context, instance_id)
    key = packet.final_pdf_storage_key if final else packet.print_storage_key
    if final and packet.status != "FINALIZED": raise ConsentPaperError("La copia digitalizada aún no está finalizada.", 409)
    if not key: raise ConsentPaperError("El documento no está disponible.", 404)
    raw = _path(key).read_bytes()
    expected = packet.final_pdf_sha256 if final else packet.print_sha256
    if not expected or _sha(raw) != expected: raise ConsentPaperError("La integridad del documento no pudo verificarse.", 409)
    action = "CONSENT_PAPER_FINAL_DOCUMENT_DOWNLOADED" if final and download else "CONSENT_PAPER_FINAL_DOCUMENT_VIEWED" if final else "CONSENT_PAPER_PACKET_VIEWED"
    _audit(session, context, metadata, packet, action); session.commit()
    return raw, f"{instance_id}-{'copia-digitalizada' if final else 'firma-papel'}.pdf"


def record_signed(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata, confirmed: bool) -> ConsentPaperPacketResponse:
    if not confirmed: raise ConsentPaperError("Debes confirmar que el original físico fue firmado.", 422)
    _, packet = _packet_for(session, context, instance_id, lock=True)
    if packet.status != "PRINTED": raise ConsentPaperError("La firma manuscrita ya fue registrada o el expediente está finalizado.", 409)
    packet.status="SIGNED_PENDING_DIGITIZATION"; packet.paper_signed_at=_now(); packet.paper_signed_recorded_by=context.user.id; packet.row_version += 1
    _audit(session, context, metadata, packet, "CONSENT_PAPER_SIGNED_RECORDED"); session.commit(); return _response(session, packet)


def _normalized_pages(raw: bytes) -> tuple[str, list[bytes]]:
    if len(raw) > MAX_FILE_BYTES: raise ConsentPaperError("El archivo supera el límite de 15 MB.", 413)
    if raw.startswith(b"%PDF-"):
        try:
            with fitz.open(stream=raw, filetype="pdf") as source:
                if source.needs_pass: raise ConsentPaperError("No se aceptan PDF protegidos con contraseña.", 422)
                if source.page_count < 1 or source.page_count > MAX_PAGES: raise ConsentPaperError("El PDF no cumple el límite de páginas.", 422)
                pages=[]
                for index in range(source.page_count):
                    target=fitz.open(); target.insert_pdf(source, from_page=index, to_page=index); pages.append(target.tobytes(garbage=4, deflate=True)); target.close()
                return "application/pdf", pages
        except ConsentPaperError: raise
        except Exception as exc: raise ConsentPaperError("El PDF está dañado o no es válido.", 422) from exc
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in {"JPEG", "PNG"}: raise ConsentPaperError("Solo se aceptan PDF, JPEG o PNG.", 422)
            if image.width * image.height > MAX_IMAGE_PIXELS: raise ConsentPaperError("La imagen supera las dimensiones permitidas.", 422)
            mime = "image/jpeg" if image.format == "JPEG" else "image/png"
            converted = image.convert("RGB"); output=io.BytesIO(); converted.save(output, format="PDF", resolution=150.0)
            return mime, [output.getvalue()]
    except ConsentPaperError: raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as exc: raise ConsentPaperError("El archivo no es un PDF, JPEG o PNG válido.", 422) from exc


def upload_pages(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata, raw: bytes) -> ConsentPaperPacketResponse:
    _, packet = _packet_for(session, context, instance_id, lock=True)
    if packet.status not in {"SIGNED_PENDING_DIGITIZATION", "DIGITIZING"}: raise ConsentPaperError("La digitalización no está disponible en este estado.", 409)
    mime, page_bytes = _normalized_pages(raw); existing=_pages(session, packet.id)
    if len(existing)+len(page_bytes)>MAX_PAGES or sum(x.byte_size for x in existing)+sum(len(x) for x in page_bytes)>MAX_TOTAL_BYTES: raise ConsentPaperError("La digitalización supera los límites del expediente.", 413)
    group=uuid4(); root=_packet_root(packet)/"pages"; created=[]
    try:
        for index, page_raw in enumerate(page_bytes, 1):
            key_path=root/f"{secrets.token_hex(24)}.pdf"; _atomic_write(key_path,page_raw)
            relative=str(key_path.relative_to(_root())); row=ConsentPaperPage(company_id=packet.company_id,paper_packet_id=packet.id,position=len(existing)+index,storage_key=relative,sha256=_sha(page_raw),byte_size=len(page_raw),source_mime_type=mime,upload_group_id=group,original_page_number=index,created_by=context.user.id); session.add(row); created.append(key_path)
        now=_now(); packet.status="DIGITIZING"; packet.digitalization_started_at=packet.digitalization_started_at or now; packet.uploaded_page_count=len(existing)+len(page_bytes); packet.row_version += 1
        _audit(session,context,metadata,packet,"CONSENT_PAPER_DIGITIZATION_STARTED") if not existing else None
        _audit(session,context,metadata,packet,"CONSENT_PAPER_PAGE_UPLOADED",{"page_count":len(page_bytes),"source_mime_type":mime}); session.commit()
    except Exception:
        session.rollback()
        for path in created: path.unlink(missing_ok=True)
        raise
    return _response(session,packet)


def remove_page(session: Session, context: AuthContext, instance_id: UUID, page_id: UUID, metadata: RequestMetadata) -> ConsentPaperPacketResponse:
    _,packet=_packet_for(session,context,instance_id,lock=True)
    if packet.status!="DIGITIZING": raise ConsentPaperError("Las páginas ya no pueden modificarse.",409)
    page=session.scalar(select(ConsentPaperPage).where(ConsentPaperPage.id==page_id,ConsentPaperPage.company_id==packet.company_id,ConsentPaperPage.paper_packet_id==packet.id).with_for_update())
    if not page: raise ConsentPaperError("Página no encontrada.",404)
    target=_path(page.storage_key); session.delete(page); session.flush()
    for position,row in enumerate(_pages(session,packet.id),1): row.position=position
    packet.uploaded_page_count-=1; packet.row_version+=1; _audit(session,context,metadata,packet,"CONSENT_PAPER_PAGE_REMOVED",{"page_id":str(page.id)}); session.commit(); target.unlink(missing_ok=True); return _response(session,packet)


def reorder_pages(session: Session, context: AuthContext, instance_id: UUID, page_ids: list[UUID], metadata: RequestMetadata) -> ConsentPaperPacketResponse:
    _,packet=_packet_for(session,context,instance_id,lock=True)
    if packet.status!="DIGITIZING": raise ConsentPaperError("Las páginas ya no pueden reordenarse.",409)
    rows=_pages(session,packet.id)
    if len(page_ids)!=len(rows) or set(page_ids)!={x.id for x in rows}: raise ConsentPaperError("Debes incluir cada página exactamente una vez.",422)
    by_id={x.id:x for x in rows}
    for index,page_id in enumerate(page_ids,1): by_id[page_id].position=-index
    session.flush()
    for index,page_id in enumerate(page_ids,1): by_id[page_id].position=index
    packet.row_version+=1; _audit(session,context,metadata,packet,"CONSENT_PAPER_PAGE_REORDERED"); session.commit(); return _response(session,packet)


def page_preview(session: Session, context: AuthContext, instance_id: UUID, page_id: UUID) -> bytes:
    _,packet=_packet_for(session,context,instance_id)
    page=session.scalar(select(ConsentPaperPage).where(ConsentPaperPage.id==page_id,ConsentPaperPage.company_id==packet.company_id,ConsentPaperPage.paper_packet_id==packet.id))
    if not page: raise ConsentPaperError("Página no encontrada.",404)
    raw=_path(page.storage_key).read_bytes()
    if _sha(raw)!=page.sha256: raise ConsentPaperError("La integridad de la página no pudo verificarse.",409)
    with fitz.open(stream=raw,filetype="pdf") as document: return document[0].get_pixmap(matrix=fitz.Matrix(0.8,0.8),alpha=False).tobytes("png")


def finalize(session: Session, context: AuthContext, instance_id: UUID, payload: ConsentPaperVerificationRequest, metadata: RequestMetadata) -> ConsentPaperPacketResponse:
    instance,packet=_packet_for(session,context,instance_id,lock=True)
    if packet.status=="FINALIZED": return _response(session,packet)
    if packet.status!="DIGITIZING": raise ConsentPaperError("Primero debes registrar la firma y cargar las páginas.",409)
    statements=payload.model_dump()
    if not all(statements.values()): raise ConsentPaperError("Debes confirmar todas las verificaciones antes de finalizar.",422)
    rows=_pages(session,packet.id)
    if len(rows)!=packet.expected_page_count: raise ConsentPaperError(f"Se esperaban {packet.expected_page_count} páginas y hay {len(rows)} cargadas.",422)
    output=fitz.open()
    for row in rows:
        raw=_path(row.storage_key).read_bytes()
        if _sha(raw)!=row.sha256: raise ConsentPaperError("La integridad de una página no pudo verificarse.",409)
        with fitz.open(stream=raw,filetype="pdf") as source: output.insert_pdf(source)
    final_raw=output.tobytes(garbage=4,deflate=True); output.close()
    relative=Path(str(packet.company_id))/str(packet.consent_instance_id)/str(packet.id)/"final"/f"{secrets.token_hex(24)}.pdf"; target=_root()/relative
    _atomic_write(target,final_raw)
    now=_now(); packet.status="FINALIZED"; packet.verification_statements=statements; packet.verification_version=VERIFICATION_VERSION; packet.original_physical_retention_acknowledged_at=now; packet.digitization_finalized_at=now; packet.finalized_by=context.user.id; packet.final_pdf_storage_key=str(relative); packet.final_pdf_sha256=_sha(final_raw); packet.final_pdf_size=len(final_raw); packet.final_page_count=len(rows); packet.uploaded_page_count=len(rows); packet.row_version+=1
    instance.status="SIGNED"; instance.completion_channel="PAPER"; instance.signed_at=packet.paper_signed_at or now; instance.updated_by=context.user.id; instance.row_version+=1
    _audit(session,context,metadata,packet,"CONSENT_PAPER_VERIFICATION_CONFIRMED",{"verification_version":VERIFICATION_VERSION}); _audit(session,context,metadata,packet,"CONSENT_PAPER_FINALIZED",{"page_count":len(rows),"sha256":packet.final_pdf_sha256}); session.commit(); return _response(session,packet)
