from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from uuid import UUID
from xml.sax.saxutils import escape

import qrcode
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings
from app.models.agenda import Appointment, Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.site import Site
from app.models.treatment import (
    Budget,
    BudgetDetail,
    ProcedureCatalogItem,
    Treatment,
    TreatmentEvent,
    TreatmentPayment,
    TreatmentProcedure,
)
from app.schemas.treatment_schema import (
    BudgetCreateRequest,
    BudgetDetailResponse,
    BudgetResponse,
    FinanceBreakdownItem,
    FinanceBreakdownResponse,
    FinanceDashboardResponse,
    PatientBalanceItem,
    PatientBalancesResponse,
    PaymentCreateRequest,
    PaymentResponse,
    ProcedureCatalogCreateRequest,
    ProcedureCatalogItemResponse,
    ProcedureCatalogListResponse,
    ProcedureCatalogUpdateRequest,
    PROCEDURE_SCOPE_TYPES,
    PROCEDURE_SURFACES,
    PROCEDURE_ZONES,
    ProcedureCreateRequest,
    ProcedureResponse,
    ProcedureUpdateRequest,
    TreatmentCreateRequest,
    TreatmentListItemResponse,
    TreatmentListResponse,
    TreatmentResponse,
    TreatmentSummaryResponse,
    TreatmentUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_site_ids


TREATMENT_ACTIVE_STATUSES = {"Borrador", "Presupuestado", "Aprobado", "En ejecución", "Pausado"}
TREATMENT_FINAL_STATUSES = {"Finalizado", "Cancelado"}
APPROVED_BUDGET_STATUSES = {"Aprobado", "En ejecución", "Finalizado"}
EDITABLE_BUDGET_STATUSES = {"Borrador", "Pendiente de aprobación"}
VALID_PAYMENT_STATUS = "valido"
REVERSED_PAYMENT_STATUS = "reversado"
CENT = Decimal("0.01")
VALID_FDI_PERMANENT_TEETH = {
    f"{quadrant}{tooth}"
    for quadrant in (1, 2, 3, 4)
    for tooth in range(1, 9)
}
ZONE_LABELS = {
    "UPPER_ARCH": "Arcada superior",
    "LOWER_ARCH": "Arcada inferior",
    "FULL_MOUTH": "Boca completa",
    "QUADRANT_1": "Cuadrante 1",
    "QUADRANT_2": "Cuadrante 2",
    "QUADRANT_3": "Cuadrante 3",
    "QUADRANT_4": "Cuadrante 4",
    "ANTERIOR": "Anterior",
    "POSTERIOR": "Posterior",
}
SURFACE_LABELS = {
    "VESTIBULAR": "Vestibular",
    "LINGUAL": "Lingual",
    "PALATAL": "Palatal",
    "MESIAL": "Mesial",
    "DISTAL": "Distal",
    "OCCLUSAL": "Oclusal",
    "INCISAL": "Incisal",
}


class BudgetPdfResult:
    def __init__(self, content: bytes, filename: str):
        self.content = content
        self.filename = filename


class TreatmentError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_catalog_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _validate_dental_scope(
    scope_type: str | None,
    zone: str | None,
    tooth: str | None,
    surfaces: list[str] | None,
) -> tuple[str, str | None, str | None, list[str] | None]:
    normalized_scope = (scope_type or "GENERAL").strip().upper()
    if normalized_scope not in PROCEDURE_SCOPE_TYPES:
        raise TreatmentError("Tipo de alcance dental no válido.")

    normalized_zone = _normalize_optional_text(zone)
    normalized_zone = normalized_zone.upper() if normalized_zone else None
    normalized_tooth = _normalize_optional_text(tooth)
    normalized_surfaces = [
        surface.strip().upper()
        for surface in (surfaces or [])
        if surface and surface.strip()
    ]

    if normalized_zone and normalized_zone not in PROCEDURE_ZONES:
        raise TreatmentError("Zona dental no válida.")
    invalid_surfaces = [
        surface for surface in normalized_surfaces if surface not in PROCEDURE_SURFACES
    ]
    if invalid_surfaces:
        raise TreatmentError("Cara dental no válida.")
    if normalized_tooth and normalized_tooth not in VALID_FDI_PERMANENT_TEETH:
        raise TreatmentError("Diente no válido.")

    if normalized_scope == "GENERAL":
        return "GENERAL", None, None, None
    if normalized_scope == "ZONE":
        if not normalized_zone:
            raise TreatmentError("Debe seleccionar una zona.")
        return "ZONE", normalized_zone, None, None
    if normalized_scope == "TOOTH":
        if not normalized_tooth:
            raise TreatmentError("Debe seleccionar un diente.")
        return "TOOTH", None, normalized_tooth, None
    if not normalized_tooth:
        raise TreatmentError("Debe seleccionar un diente.")
    if not normalized_surfaces:
        raise TreatmentError("Debe seleccionar al menos una cara del diente.")
    return "TOOTH_SURFACE", None, normalized_tooth, normalized_surfaces


def _scope_label(
    scope_type: str | None,
    zone: str | None,
    tooth: str | None,
    surfaces: list[str] | None,
) -> str:
    if scope_type == "ZONE" and zone:
        return ZONE_LABELS.get(zone, zone)
    if scope_type == "TOOTH" and tooth:
        return f"Diente {tooth}"
    if scope_type == "TOOTH_SURFACE" and tooth:
        surface_text = ", ".join(SURFACE_LABELS.get(surface, surface) for surface in (surfaces or []))
        return f"Diente {tooth} — {surface_text}" if surface_text else f"Diente {tooth}"
    return "General"


def _branding_asset_path(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    root = Path(settings.branding_storage_dir).resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        return None
    return candidate if candidate.exists() else None


def _pdf_color(value: str | None, fallback: str) -> colors.Color:
    try:
        return colors.HexColor(value or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _relative_luminance(color: colors.Color) -> float:
    def channel(value: float) -> float:
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(color.red) + 0.7152 * channel(color.green) + 0.0722 * channel(color.blue)


def _contrast_ratio(first: colors.Color, second: colors.Color) -> float:
    light = max(_relative_luminance(first), _relative_luminance(second))
    dark = min(_relative_luminance(first), _relative_luminance(second))
    return (light + 0.05) / (dark + 0.05)


def _safe_text_color(accent: colors.Color, fallback: str = "#111827") -> colors.Color:
    white = colors.white
    return accent if _contrast_ratio(accent, white) >= 4.5 else colors.HexColor(fallback)


def _text_on_background(background: colors.Color) -> colors.Color:
    dark = colors.HexColor("#111827")
    return colors.white if _contrast_ratio(colors.white, background) >= 4.5 else dark


def _visible_accent(accent: colors.Color, fallback: str = "#2563eb") -> colors.Color:
    return accent if _contrast_ratio(accent, colors.white) >= 1.6 else colors.HexColor(fallback)


def _soft_accent_background(accent: colors.Color) -> colors.Color:
    if _contrast_ratio(accent, colors.white) < 1.25:
        return colors.HexColor("#f1f5f9")
    return colors.Color(accent.red, accent.green, accent.blue, alpha=0.10)


def _money_text(value: Decimal | int | float | None) -> str:
    amount = int(_money(value))
    return f"${amount:,.0f}".replace(",", ".")


def _date_text(value: datetime | date | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d/%m/%Y")


def _safe_text(value: object | None, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _paragraph(text: object | None, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_safe_text(text, "")), style)


def _image_if_exists(path: Path | None, *, width: float, height: float) -> Image | None:
    if path is None:
        return None
    try:
        image = Image(str(path))
        image._restrictSize(width, height)
        return image
    except Exception:
        return None


def _qr_image() -> Image:
    qr = qrcode.QRCode(box_size=5, border=1)
    qr.add_data("https://dentiapro.com")
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    qr_image = Image(buffer)
    qr_image._restrictSize(28 * mm, 28 * mm)
    return qr_image


def _info_table(
    rows: list[list[object | None]],
    styles: dict[str, ParagraphStyle],
    primary: colors.Color,
    background: colors.Color,
    width: float,
) -> Table:
    table_rows = []
    for row in rows:
        table_rows.append(
            [
                _paragraph(row[0], styles["cell_bold"]),
                _paragraph(row[1], styles["cell"]),
                _paragraph(row[2], styles["cell_bold"]),
                _paragraph(row[3], styles["cell"]),
            ]
        )
    return Table(
        table_rows,
        colWidths=[width * 0.16, width * 0.34, width * 0.16, width * 0.34],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), background),
                ("BACKGROUND", (2, 0), (2, -1), background),
                ("TEXTCOLOR", (0, 0), (0, -1), _safe_text_color(primary, "#0f172a")),
                ("TEXTCOLOR", (2, 0), (2, -1), _safe_text_color(primary, "#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    entity: str,
    entity_id: UUID,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result="SUCCESS",
            detail=_json_safe(detail),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _event(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    event_type: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    session.add(
        TreatmentEvent(
            company_id=context.user.company_id,
            treatment_id=treatment_id,
            event_type=event_type,
            description=description,
            event_metadata=_json_safe(metadata),
            user_id=context.user.id,
        )
    )


def _json_safe(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


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
        raise TreatmentError("No tienes acceso a la sede seleccionada.", 403)
    site = session.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.company_id == context.user.company_id,
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
    )
    if site is None:
        raise TreatmentError("La sede no existe o no está activa.")
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
        raise TreatmentError("Paciente no encontrado.", 404)
    return patient


def _require_dentist(
    session: Session,
    context: AuthContext,
    dentist_id: UUID,
    site_id: UUID | None = None,
) -> Dentist:
    statement = select(Dentist).where(
        Dentist.id == dentist_id,
        Dentist.company_id == context.user.company_id,
        Dentist.is_active.is_(True),
        Dentist.status == "Activo",
    )
    if site_id:
        statement = statement.join(DentistSite, DentistSite.dentist_id == Dentist.id).where(
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    dentist = session.scalar(statement)
    if dentist is None:
        raise TreatmentError("Odontólogo no disponible para la sede seleccionada.")
    return dentist


def _catalog_response(item: ProcedureCatalogItem) -> ProcedureCatalogItemResponse:
    return ProcedureCatalogItemResponse(
        id=item.id,
        name=item.name,
        category=item.category,
        description=item.description,
        suggested_value=_money(item.suggested_value) if item.suggested_value is not None else None,
        suggested_scope_type=item.suggested_scope_type,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _require_catalog_item(
    session: Session,
    context: AuthContext,
    item_id: UUID,
    *,
    active_only: bool = False,
    lock: bool = False,
) -> ProcedureCatalogItem:
    statement = select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.id == item_id,
        ProcedureCatalogItem.company_id == context.user.company_id,
    )
    if active_only:
        statement = statement.where(ProcedureCatalogItem.is_active.is_(True))
    if lock:
        statement = statement.with_for_update()
    item = session.scalar(statement)
    if item is None:
        raise TreatmentError("Procedimiento de catálogo no encontrado.", 404)
    return item


def _ensure_catalog_name_available(
    session: Session,
    context: AuthContext,
    normalized_name: str,
    *,
    exclude_id: UUID | None = None,
) -> None:
    statement = select(ProcedureCatalogItem.id).where(
        ProcedureCatalogItem.company_id == context.user.company_id,
        ProcedureCatalogItem.normalized_name == normalized_name,
    )
    if exclude_id:
        statement = statement.where(ProcedureCatalogItem.id != exclude_id)
    if session.scalar(statement):
        raise TreatmentError("Ya existe un procedimiento con ese nombre en el catálogo.")


def list_procedure_catalog(
    session: Session,
    context: AuthContext,
    *,
    search: str | None = None,
    active: bool | None = None,
    category: str | None = None,
) -> ProcedureCatalogListResponse:
    statement = select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == context.user.company_id
    )
    if active is not None:
        statement = statement.where(ProcedureCatalogItem.is_active.is_(active))
    if category:
        statement = statement.where(ProcedureCatalogItem.category.ilike(f"%{category.strip()}%"))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                ProcedureCatalogItem.name.ilike(term),
                ProcedureCatalogItem.category.ilike(term),
            )
        )
    items = session.scalars(
        statement.order_by(
            ProcedureCatalogItem.is_active.desc(),
            ProcedureCatalogItem.name.asc(),
        )
    ).all()
    return ProcedureCatalogListResponse(
        items=[_catalog_response(item) for item in items],
        total=len(items),
    )


def create_procedure_catalog_item(
    session: Session,
    context: AuthContext,
    payload: ProcedureCatalogCreateRequest,
    metadata: RequestMetadata,
) -> ProcedureCatalogItemResponse:
    normalized_name = _normalize_catalog_name(payload.name)
    _ensure_catalog_name_available(session, context, normalized_name)
    item = ProcedureCatalogItem(
        company_id=context.user.company_id,
        name=payload.name,
        normalized_name=normalized_name,
        category=payload.category,
        description=payload.description,
        suggested_value=_money(payload.suggested_value) if payload.suggested_value is not None else None,
        suggested_scope_type=payload.suggested_scope_type,
        is_active=payload.is_active,
        created_by=context.user.id,
    )
    session.add(item)
    session.flush()
    _audit(
        session,
        context,
        metadata,
        entity="procedure_catalog",
        entity_id=item.id,
        action="PROCEDURE_CATALOG_CREATED",
        detail={"name": item.name, "category": item.category},
    )
    session.commit()
    session.refresh(item)
    return _catalog_response(item)


def update_procedure_catalog_item(
    session: Session,
    context: AuthContext,
    item_id: UUID,
    payload: ProcedureCatalogUpdateRequest,
    metadata: RequestMetadata,
) -> ProcedureCatalogItemResponse:
    item = _require_catalog_item(session, context, item_id, lock=True)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        normalized_name = _normalize_catalog_name(data["name"])
        _ensure_catalog_name_available(session, context, normalized_name, exclude_id=item.id)
        item.name = data["name"]
        item.normalized_name = normalized_name
    for key, attr in {
        "category": "category",
        "description": "description",
        "suggested_scope_type": "suggested_scope_type",
        "is_active": "is_active",
    }.items():
        if key in data:
            setattr(item, attr, data[key])
    if "suggested_value" in data:
        item.suggested_value = (
            _money(data["suggested_value"]) if data["suggested_value"] is not None else None
        )
    item.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        entity="procedure_catalog",
        entity_id=item.id,
        action="PROCEDURE_CATALOG_UPDATED",
        detail=data,
    )
    session.commit()
    session.refresh(item)
    return _catalog_response(item)


def change_procedure_catalog_status(
    session: Session,
    context: AuthContext,
    item_id: UUID,
    is_active: bool,
    metadata: RequestMetadata,
) -> ProcedureCatalogItemResponse:
    item = _require_catalog_item(session, context, item_id, lock=True)
    item.is_active = is_active
    item.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        entity="procedure_catalog",
        entity_id=item.id,
        action="PROCEDURE_CATALOG_ACTIVATED" if is_active else "PROCEDURE_CATALOG_DEACTIVATED",
    )
    session.commit()
    session.refresh(item)
    return _catalog_response(item)


def _require_treatment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    *,
    lock: bool = False,
) -> Treatment:
    statement = select(Treatment).where(
        Treatment.id == treatment_id,
        Treatment.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    treatment = session.scalar(statement)
    if treatment is None:
        raise TreatmentError("Tratamiento no encontrado.", 404)
    if treatment.main_site_id and treatment.main_site_id not in _authorized_sites(session, context):
        raise TreatmentError("No tienes acceso a este tratamiento.", 403)
    return treatment


def _require_procedure(
    session: Session,
    context: AuthContext,
    treatment: Treatment,
    procedure_id: UUID,
    *,
    lock: bool = False,
) -> TreatmentProcedure:
    statement = select(TreatmentProcedure).where(
        TreatmentProcedure.id == procedure_id,
        TreatmentProcedure.company_id == context.user.company_id,
        TreatmentProcedure.treatment_id == treatment.id,
    )
    if lock:
        statement = statement.with_for_update()
    procedure = session.scalar(statement)
    if procedure is None:
        raise TreatmentError("Procedimiento no encontrado.", 404)
    return procedure


def _budget_value(session: Session, treatment_id: UUID) -> tuple[Decimal, Decimal, Decimal]:
    budget = session.scalar(
        select(Budget)
        .where(
            Budget.treatment_id == treatment_id,
            Budget.status.in_(APPROVED_BUDGET_STATUSES),
        )
        .order_by(Budget.version.desc())
        .limit(1)
    )
    if budget:
        return (
            _money(budget.gross_value),
            _money(budget.discount_calculated_value),
            _money(budget.final_value),
        )
    gross = _money(
        session.scalar(
            select(func.coalesce(func.sum(TreatmentProcedure.total_value), 0)).where(
                TreatmentProcedure.treatment_id == treatment_id,
                TreatmentProcedure.status != "Cancelado",
            )
        )
    )
    return gross, Decimal("0.00"), gross


def _paid_value(session: Session, treatment_id: UUID) -> Decimal:
    return _money(
        session.scalar(
            select(func.coalesce(func.sum(TreatmentPayment.value), 0)).where(
                TreatmentPayment.treatment_id == treatment_id,
                TreatmentPayment.status == VALID_PAYMENT_STATUS,
            )
        )
    )


def _summary(session: Session, treatment_id: UUID) -> TreatmentSummaryResponse:
    gross, discount, final = _budget_value(session, treatment_id)
    paid = _paid_value(session, treatment_id)
    procedures_total = session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.treatment_id == treatment_id,
            TreatmentProcedure.status != "Cancelado",
        )
    ) or 0
    procedures_done = session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.treatment_id == treatment_id,
            TreatmentProcedure.status == "Realizado",
        )
    ) or 0
    return TreatmentSummaryResponse(
        gross_value=gross,
        discount_value=discount,
        final_value=final,
        paid_value=paid,
        balance=max(final - paid, Decimal("0.00")),
        procedures_total=procedures_total,
        procedures_done=procedures_done,
    )


def _treatment_item(session: Session, treatment: Treatment) -> TreatmentListItemResponse:
    patient = session.get(Patient, treatment.patient_id)
    dentist = (
        session.get(Dentist, treatment.responsible_dentist_id)
        if treatment.responsible_dentist_id
        else None
    )
    site = session.get(Site, treatment.main_site_id) if treatment.main_site_id else None
    if patient is None:
        raise TreatmentError("Tratamiento sin paciente válido.", 500)
    summary = _summary(session, treatment.id)
    return TreatmentListItemResponse(
        id=treatment.id,
        patient_id=treatment.patient_id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        name=treatment.name,
        status=treatment.status,
        responsible_dentist_id=treatment.responsible_dentist_id,
        responsible_dentist_name=dentist.name if dentist else None,
        main_site_id=treatment.main_site_id,
        main_site_name=site.name if site else None,
        final_value=summary.final_value,
        paid_value=summary.paid_value,
        balance=summary.balance,
        updated_at=treatment.updated_at,
    )


def _treatment_response(session: Session, treatment: Treatment) -> TreatmentResponse:
    item = _treatment_item(session, treatment)
    return TreatmentResponse(
        **item.model_dump(),
        description=treatment.description,
        specialty=treatment.specialty,
        start_date=treatment.start_date,
        end_date=treatment.end_date,
        observations=treatment.observations,
        created_at=treatment.created_at,
        summary=_summary(session, treatment.id),
    )


def list_treatments(
    session: Session,
    context: AuthContext,
    *,
    patient_id: UUID | None = None,
    status: str | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
    has_balance: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TreatmentListResponse:
    statement = select(Treatment).where(Treatment.company_id == context.user.company_id)
    authorized = _authorized_sites(session, context)
    statement = statement.where(
        or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(authorized))
    )
    if patient_id:
        statement = statement.where(Treatment.patient_id == patient_id)
    if status:
        statement = statement.where(Treatment.status == status)
    if site_id:
        _require_site(session, context, site_id)
        statement = statement.where(Treatment.main_site_id == site_id)
    if dentist_id:
        statement = statement.where(Treatment.responsible_dentist_id == dentist_id)
    if date_from:
        statement = statement.where(Treatment.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        statement = statement.where(Treatment.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    treatments = session.scalars(statement.order_by(Treatment.updated_at.desc())).all()
    items = [_treatment_item(session, treatment) for treatment in treatments]
    if has_balance is not None:
        items = [item for item in items if (item.balance > 0) is has_balance]
    return TreatmentListResponse(items=items, total=len(items))


def create_treatment(
    session: Session,
    context: AuthContext,
    payload: TreatmentCreateRequest,
    metadata: RequestMetadata,
) -> TreatmentResponse:
    _require_patient(session, context, payload.patient_id)
    if payload.main_site_id:
        _require_site(session, context, payload.main_site_id)
    if payload.responsible_dentist_id:
        _require_dentist(session, context, payload.responsible_dentist_id, payload.main_site_id)
    treatment = Treatment(
        company_id=context.user.company_id,
        patient_id=payload.patient_id,
        name=payload.name,
        description=payload.description,
        specialty=payload.specialty,
        status="Borrador",
        responsible_dentist_id=payload.responsible_dentist_id,
        main_site_id=payload.main_site_id,
        start_date=payload.start_date,
        observations=payload.observations,
        created_by=context.user.id,
    )
    session.add(treatment)
    session.flush()
    _event(session, context, treatment.id, "TREATMENT_CREATED", "Tratamiento creado.")
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action="TREATMENT_CREATED")
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def get_treatment(session: Session, context: AuthContext, treatment_id: UUID) -> TreatmentResponse:
    return _treatment_response(session, _require_treatment(session, context, treatment_id))


def update_treatment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    payload: TreatmentUpdateRequest,
    metadata: RequestMetadata,
) -> TreatmentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status in TREATMENT_FINAL_STATUSES:
        raise TreatmentError("No se puede editar un tratamiento finalizado o cancelado.")
    data = payload.model_dump(exclude_unset=True)
    if "main_site_id" in data and data["main_site_id"]:
        _require_site(session, context, data["main_site_id"])
    if "responsible_dentist_id" in data and data["responsible_dentist_id"]:
        _require_dentist(session, context, data["responsible_dentist_id"], data.get("main_site_id", treatment.main_site_id))
    mapping = {
        "name": "name",
        "description": "description",
        "specialty": "specialty",
        "responsible_dentist_id": "responsible_dentist_id",
        "main_site_id": "main_site_id",
        "start_date": "start_date",
        "end_date": "end_date",
        "observations": "observations",
    }
    for key, attr in mapping.items():
        if key in data:
            setattr(treatment, attr, data[key])
    treatment.updated_by = context.user.id
    _event(session, context, treatment.id, "TREATMENT_UPDATED", "Tratamiento actualizado.", data)
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action="TREATMENT_UPDATED", detail=data)
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def change_treatment_status(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    status: str,
    action: str,
    metadata: RequestMetadata,
    reason: str | None = None,
) -> TreatmentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status == "Cancelado" and status != "Cancelado":
        raise TreatmentError("No se puede cambiar un tratamiento cancelado.")
    if status == "Finalizado":
        pending = session.scalar(
            select(func.count(TreatmentProcedure.id)).where(
                TreatmentProcedure.treatment_id == treatment.id,
                TreatmentProcedure.status.in_(["Pendiente", "Agendado", "En proceso"]),
            )
        )
        if pending:
            raise TreatmentError("No se puede cerrar con procedimientos pendientes.")
        treatment.end_date = date.today()
    if status == "Cancelado" and not reason:
        raise TreatmentError("Cancelar tratamiento requiere motivo.")
    treatment.status = status
    treatment.updated_by = context.user.id
    _event(session, context, treatment.id, action, reason or f"Estado cambiado a {status}.")
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action=action, detail={"status": status, "reason": reason})
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def list_procedures(session: Session, context: AuthContext, treatment_id: UUID) -> list[ProcedureResponse]:
    treatment = _require_treatment(session, context, treatment_id)
    rows = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.treatment_id == treatment.id)
        .order_by(TreatmentProcedure.created_at)
    ).all()
    return [_procedure_response(*row) for row in rows]


def _procedure_response(
    procedure: TreatmentProcedure,
    dentist: Dentist | None = None,
    site: Site | None = None,
) -> ProcedureResponse:
    return ProcedureResponse(
        id=procedure.id,
        treatment_id=procedure.treatment_id,
        patient_id=procedure.patient_id,
        catalog_procedure_id=procedure.catalog_procedure_id,
        name=procedure.name,
        category=procedure.category,
        dentist_id=procedure.dentist_id,
        dentist_name=dentist.name if dentist else None,
        site_id=procedure.site_id,
        site_name=site.name if site else None,
        appointment_id=procedure.appointment_id,
        unit_value=_money(procedure.unit_value),
        quantity=Decimal(procedure.quantity),
        total_value=_money(procedure.total_value),
        status=procedure.status,
        estimated_date=procedure.estimated_date,
        performed_at=procedure.performed_at,
        observations=procedure.observations,
        requires_tooth=procedure.requires_tooth,
        scope_type=procedure.scope_type or "GENERAL",
        zone=procedure.zone,
        tooth=procedure.tooth,
        surfaces=procedure.surfaces,
        scope_label=_scope_label(procedure.scope_type, procedure.zone, procedure.tooth, procedure.surfaces),
    )


def create_procedure(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    payload: ProcedureCreateRequest,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status in TREATMENT_FINAL_STATUSES:
        raise TreatmentError("No se pueden agregar procedimientos a este tratamiento.")
    if payload.site_id:
        _require_site(session, context, payload.site_id)
    if payload.dentist_id:
        _require_dentist(session, context, payload.dentist_id, payload.site_id)
    catalog_item: ProcedureCatalogItem | None = None
    if payload.catalog_procedure_id:
        catalog_item = _require_catalog_item(
            session,
            context,
            payload.catalog_procedure_id,
            active_only=True,
        )
    scope_type, zone, tooth, surfaces = _validate_dental_scope(
        payload.scope_type,
        payload.zone,
        payload.tooth,
        payload.surfaces,
    )
    procedure = TreatmentProcedure(
        company_id=context.user.company_id,
        treatment_id=treatment.id,
        patient_id=treatment.patient_id,
        catalog_procedure_id=catalog_item.id if catalog_item else None,
        name=payload.name,
        category=payload.category if payload.category is not None else (catalog_item.category if catalog_item else None),
        dentist_id=payload.dentist_id,
        site_id=payload.site_id,
        unit_value=_money(payload.unit_value),
        quantity=payload.quantity,
        total_value=_money(payload.unit_value * payload.quantity),
        status=payload.status,
        estimated_date=payload.estimated_date,
        observations=payload.observations,
        requires_tooth=scope_type in {"TOOTH", "TOOTH_SURFACE"} or payload.requires_tooth,
        scope_type=scope_type,
        zone=zone,
        tooth=tooth,
        surfaces=surfaces,
        created_by=context.user.id,
    )
    session.add(procedure)
    treatment.updated_by = context.user.id
    session.flush()
    _recalculate_editable_budgets(session, context, treatment)
    scope_detail = {
        "procedure_id": str(procedure.id),
        "scope_type": procedure.scope_type,
        "zone": procedure.zone,
        "tooth": procedure.tooth,
        "surfaces": procedure.surfaces,
    }
    _event(session, context, treatment.id, "PROCEDURE_CREATED", "Procedimiento creado.", scope_detail)
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_CREATED", detail=scope_detail)
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def update_procedure(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    procedure_id: UUID,
    payload: ProcedureUpdateRequest,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Realizado":
        raise TreatmentError("No se puede modificar un procedimiento realizado sin flujo de corrección.")
    if _has_approved_budget(session, treatment.id) and not _has_editable_budget(session, treatment.id):
        raise TreatmentError("Este procedimiento pertenece a un presupuesto aprobado. Cree una nueva versión del presupuesto antes de modificarlo.")
    data = payload.model_dump(exclude_unset=True)
    if "site_id" in data and data["site_id"]:
        _require_site(session, context, data["site_id"])
    if "dentist_id" in data and data["dentist_id"]:
        _require_dentist(session, context, data["dentist_id"], data.get("site_id", procedure.site_id))
    if "catalog_procedure_id" in data:
        procedure.catalog_procedure_id = None
        if data["catalog_procedure_id"]:
            catalog_item = _require_catalog_item(
                session,
                context,
                data["catalog_procedure_id"],
                active_only=True,
            )
            procedure.catalog_procedure_id = catalog_item.id
            if "category" not in data:
                procedure.category = catalog_item.category
    scope_keys = {"scope_type", "zone", "tooth", "surfaces"}
    if scope_keys.intersection(data):
        scope_type, zone, tooth, surfaces = _validate_dental_scope(
            data.get("scope_type", procedure.scope_type),
            data["zone"] if "zone" in data else procedure.zone,
            data["tooth"] if "tooth" in data else procedure.tooth,
            data["surfaces"] if "surfaces" in data else procedure.surfaces,
        )
        procedure.scope_type = scope_type
        procedure.zone = zone
        procedure.tooth = tooth
        procedure.surfaces = surfaces
        procedure.requires_tooth = scope_type in {"TOOTH", "TOOTH_SURFACE"}
    for key, attr in {
        "name": "name",
        "category": "category",
        "catalog_procedure_id": "catalog_procedure_id",
        "dentist_id": "dentist_id",
        "site_id": "site_id",
        "status": "status",
        "estimated_date": "estimated_date",
        "observations": "observations",
        "requires_tooth": "requires_tooth",
    }.items():
        if key in data:
            setattr(procedure, attr, data[key])
    if scope_keys.intersection(data):
        procedure.requires_tooth = procedure.scope_type in {"TOOTH", "TOOTH_SURFACE"}
    if "unit_value" in data:
        procedure.unit_value = _money(data["unit_value"])
    if "quantity" in data:
        procedure.quantity = data["quantity"]
    procedure.total_value = _money(procedure.unit_value * procedure.quantity)
    procedure.updated_by = context.user.id
    treatment.updated_by = context.user.id
    _recalculate_editable_budgets(session, context, treatment)
    _event(session, context, treatment.id, "PROCEDURE_UPDATED", "Procedimiento actualizado.", data)
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_UPDATED", detail=data)
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def mark_procedure_done(session: Session, context: AuthContext, treatment_id: UUID, procedure_id: UUID, metadata: RequestMetadata) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Cancelado":
        raise TreatmentError("No se puede realizar un procedimiento cancelado.")
    procedure.status = "Realizado"
    procedure.performed_at = datetime.now(timezone.utc)
    procedure.updated_by = context.user.id
    if treatment.status in {"Borrador", "Presupuestado", "Aprobado"}:
        treatment.status = "En ejecución"
    _event(session, context, treatment.id, "PROCEDURE_MARKED_DONE", "Procedimiento marcado como realizado.", {"procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_MARKED_DONE")
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def cancel_procedure(session: Session, context: AuthContext, treatment_id: UUID, procedure_id: UUID, metadata: RequestMetadata, reason: str | None) -> ProcedureResponse:
    if not reason:
        raise TreatmentError("Cancelar procedimiento requiere motivo.")
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Realizado":
        raise TreatmentError("No se puede cancelar un procedimiento realizado.")
    if _has_approved_budget(session, treatment.id) and not _has_editable_budget(session, treatment.id):
        raise TreatmentError("Este procedimiento pertenece a un presupuesto aprobado. Cree una nueva versión del presupuesto antes de cancelarlo.")
    procedure.status = "Cancelado"
    procedure.updated_by = context.user.id
    treatment.updated_by = context.user.id
    _recalculate_editable_budgets(session, context, treatment)
    _event(session, context, treatment.id, "PROCEDURE_CANCELLED", reason, {"procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_CANCELLED", detail={"reason": reason})
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def delete_procedure(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    procedure_id: UUID,
    metadata: RequestMetadata,
) -> None:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Realizado":
        raise TreatmentError("No se puede eliminar un procedimiento realizado.")
    if _has_valid_payments(session, treatment.id):
        raise TreatmentError("No se puede eliminar un procedimiento cuando el tratamiento tiene pagos registrados.")
    if _has_approved_budget(session, treatment.id):
        raise TreatmentError("Este procedimiento pertenece a un presupuesto aprobado.")
    detail = {
        "procedure_id": str(procedure.id),
        "name": procedure.name,
        "scope_type": procedure.scope_type,
        "zone": procedure.zone,
        "tooth": procedure.tooth,
        "surfaces": procedure.surfaces,
        "unit_value": str(procedure.unit_value),
        "quantity": str(procedure.quantity),
    }
    session.delete(procedure)
    treatment.updated_by = context.user.id
    session.flush()
    _recalculate_editable_budgets(session, context, treatment)
    _event(session, context, treatment.id, "PROCEDURE_DELETED", "Procedimiento eliminado.", detail)
    _audit(
        session,
        context,
        metadata,
        entity="treatment_procedure",
        entity_id=procedure_id,
        action="PROCEDURE_DELETED",
        detail=detail,
    )
    session.commit()


def link_procedure_appointment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    procedure_id: UUID,
    appointment_id: UUID,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == treatment.patient_id,
        )
    )
    if appointment is None:
        raise TreatmentError("Cita no encontrada para este paciente.", 404)
    _require_site(session, context, appointment.site_id)
    appointment.treatment_id = treatment.id
    appointment.treatment_procedure_id = procedure.id
    procedure.appointment_id = appointment.id
    procedure.status = "Agendado" if procedure.status == "Pendiente" else procedure.status
    _event(session, context, treatment.id, "PROCEDURE_LINKED_APPOINTMENT", "Procedimiento asociado a cita.", {"appointment_id": str(appointment.id), "procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="appointment", entity_id=appointment.id, action="APPOINTMENT_LINKED_TREATMENT_PROCEDURE")
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def link_appointment_treatment_procedure(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    treatment_id: UUID,
    procedure_id: UUID | None,
    metadata: RequestMetadata,
) -> None:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == treatment.patient_id,
        )
    )
    if appointment is None:
        raise TreatmentError("Cita no encontrada para este paciente.", 404)
    _require_site(session, context, appointment.site_id)
    appointment.treatment_id = treatment.id
    if procedure_id:
        procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
        procedure.appointment_id = appointment.id
        procedure.status = "Agendado" if procedure.status == "Pendiente" else procedure.status
        appointment.treatment_procedure_id = procedure.id
    _audit(session, context, metadata, entity="appointment", entity_id=appointment.id, action="APPOINTMENT_LINKED_TREATMENT_PROCEDURE")
    session.commit()


def _calculate_discount(gross: Decimal, discount_type: str | None, discount_value: Decimal) -> Decimal:
    if not discount_type or discount_value == 0:
        return Decimal("0.00")
    if discount_type == "porcentaje":
        if discount_value > 100:
            raise TreatmentError("El descuento porcentual no puede superar 100%.")
        return _money(gross * discount_value / Decimal("100"))
    if discount_type == "valor":
        if discount_value > gross:
            raise TreatmentError("El descuento no puede superar el valor bruto.")
        return _money(discount_value)
    raise TreatmentError("Tipo de descuento no válido.")


def _active_procedures_for_budget(session: Session, treatment_id: UUID) -> list[TreatmentProcedure]:
    return session.scalars(
        select(TreatmentProcedure)
        .where(
            TreatmentProcedure.treatment_id == treatment_id,
            TreatmentProcedure.status != "Cancelado",
        )
        .order_by(TreatmentProcedure.created_at)
    ).all()


def _add_budget_detail_snapshot(
    session: Session,
    *,
    company_id: UUID,
    budget_id: UUID,
    procedures: list[TreatmentProcedure],
) -> None:
    for index, procedure in enumerate(procedures, start=1):
        session.add(
            BudgetDetail(
                company_id=company_id,
                budget_id=budget_id,
                procedure_id=procedure.id,
                name=procedure.name,
                category=procedure.category,
                quantity=procedure.quantity,
                unit_value=procedure.unit_value,
                total_value=procedure.total_value,
                order=index,
                observations=procedure.observations,
                scope_type=procedure.scope_type or "GENERAL",
                zone=procedure.zone,
                tooth=procedure.tooth,
                surfaces=procedure.surfaces,
            )
        )


def _recalculate_editable_budgets(
    session: Session,
    context: AuthContext,
    treatment: Treatment,
) -> None:
    budgets = session.scalars(
        select(Budget)
        .where(
            Budget.treatment_id == treatment.id,
            Budget.company_id == context.user.company_id,
            Budget.status.in_(EDITABLE_BUDGET_STATUSES),
        )
        .order_by(Budget.version)
    ).all()
    if not budgets:
        return
    procedures = _active_procedures_for_budget(session, treatment.id)
    gross = _money(sum((procedure.total_value for procedure in procedures), Decimal("0")))
    for budget in budgets:
        discount = _calculate_discount(gross, budget.discount_type, budget.discount_value)
        budget.gross_value = gross
        budget.discount_calculated_value = discount
        budget.final_value = _money(gross - discount)
        budget.updated_by = context.user.id
        session.execute(delete(BudgetDetail).where(BudgetDetail.budget_id == budget.id))
        _add_budget_detail_snapshot(
            session,
            company_id=context.user.company_id,
            budget_id=budget.id,
            procedures=procedures,
        )


def _has_approved_budget(session: Session, treatment_id: UUID) -> bool:
    return bool(
        session.scalar(
            select(func.count())
            .select_from(Budget)
            .where(
                Budget.treatment_id == treatment_id,
                Budget.status.in_(APPROVED_BUDGET_STATUSES),
            )
        )
    )


def _has_editable_budget(session: Session, treatment_id: UUID) -> bool:
    return bool(
        session.scalar(
            select(func.count())
            .select_from(Budget)
            .where(
                Budget.treatment_id == treatment_id,
                Budget.status.in_(EDITABLE_BUDGET_STATUSES),
            )
        )
    )


def _has_valid_payments(session: Session, treatment_id: UUID) -> bool:
    return bool(
        session.scalar(
            select(func.count())
            .select_from(TreatmentPayment)
            .where(
                TreatmentPayment.treatment_id == treatment_id,
                TreatmentPayment.status == VALID_PAYMENT_STATUS,
            )
        )
    )


def create_budget(session: Session, context: AuthContext, treatment_id: UUID, payload: BudgetCreateRequest, metadata: RequestMetadata) -> BudgetResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedures = _active_procedures_for_budget(session, treatment.id)
    if not procedures:
        raise TreatmentError("No se puede crear presupuesto sin procedimientos.")
    gross = _money(sum((procedure.total_value for procedure in procedures), Decimal("0")))
    discount = _calculate_discount(gross, payload.discount_type, payload.discount_value)
    version = (session.scalar(select(func.coalesce(func.max(Budget.version), 0)).where(Budget.treatment_id == treatment.id)) or 0) + 1
    budget = Budget(
        company_id=context.user.company_id,
        patient_id=treatment.patient_id,
        treatment_id=treatment.id,
        number=f"P-{version}",
        version=version,
        status="Borrador",
        gross_value=gross,
        discount_type=payload.discount_type,
        discount_value=_money(payload.discount_value),
        discount_calculated_value=discount,
        final_value=_money(gross - discount),
        observations=payload.observations,
        issued_at=datetime.now(timezone.utc),
        expires_on=payload.expires_on,
        created_by=context.user.id,
    )
    session.add(budget)
    session.flush()
    _add_budget_detail_snapshot(
        session,
        company_id=context.user.company_id,
        budget_id=budget.id,
        procedures=procedures,
    )
    treatment.status = "Presupuestado" if treatment.status == "Borrador" else treatment.status
    _event(session, context, treatment.id, "BUDGET_CREATED", "Presupuesto creado.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action="BUDGET_CREATED")
    session.commit()
    return get_budget(session, context, budget.id)


def _budget_response(session: Session, budget: Budget) -> BudgetResponse:
    details = session.scalars(
        select(BudgetDetail).where(BudgetDetail.budget_id == budget.id).order_by(BudgetDetail.order)
    ).all()
    return BudgetResponse(
        id=budget.id,
        patient_id=budget.patient_id,
        treatment_id=budget.treatment_id,
        number=budget.number,
        version=budget.version,
        status=budget.status,
        gross_value=_money(budget.gross_value),
        discount_type=budget.discount_type,
        discount_value=_money(budget.discount_value),
        discount_calculated_value=_money(budget.discount_calculated_value),
        final_value=_money(budget.final_value),
        observations=budget.observations,
        issued_at=budget.issued_at,
        expires_on=budget.expires_on,
        approved_at=budget.approved_at,
        rejected_at=budget.rejected_at,
        details=[
            BudgetDetailResponse(
                id=detail.id,
                procedure_id=detail.procedure_id,
                name=detail.name,
                category=detail.category,
                quantity=detail.quantity,
                unit_value=_money(detail.unit_value),
                total_value=_money(detail.total_value),
                order=detail.order,
                observations=detail.observations,
                scope_type=detail.scope_type or "GENERAL",
                zone=detail.zone,
                tooth=detail.tooth,
                surfaces=detail.surfaces,
                scope_label=_scope_label(detail.scope_type, detail.zone, detail.tooth, detail.surfaces),
            )
            for detail in details
        ],
    )


def get_budget(session: Session, context: AuthContext, budget_id: UUID) -> BudgetResponse:
    budget = session.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id)
    )
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    _require_treatment(session, context, budget.treatment_id)
    return _budget_response(session, budget)


def generate_budget_pdf(
    session: Session,
    context: AuthContext,
    budget_id: UUID,
) -> BudgetPdfResult:
    budget = session.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.company_id == context.user.company_id,
        )
    )
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    treatment = _require_treatment(session, context, budget.treatment_id)
    company = session.get(Company, context.user.company_id)
    patient = session.get(Patient, budget.patient_id)
    if company is None or patient is None:
        raise TreatmentError("Presupuesto incompleto.", 500)
    dentist = session.get(Dentist, treatment.responsible_dentist_id) if treatment.responsible_dentist_id else None
    site = session.get(Site, treatment.main_site_id) if treatment.main_site_id else None
    details = session.scalars(
        select(BudgetDetail)
        .where(BudgetDetail.budget_id == budget.id)
        .order_by(BudgetDetail.order)
    ).all()
    summary = _summary(session, treatment.id)

    primary = _pdf_color(company.primary_color, "#16a34a")
    secondary = _visible_accent(_pdf_color(company.secondary_color, "#0f766e"), "#64748b")
    heading = _safe_text_color(_pdf_color(company.heading_color, "#0f172a"), "#0f172a")
    section_heading = _safe_text_color(primary, "#0f172a")
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
        title=f"Presupuesto {budget.number or budget.version}",
        author=company.name,
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "DentiaBudgetTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=heading,
            alignment=TA_RIGHT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "DentiaBudgetSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569"),
            alignment=TA_RIGHT,
        ),
        "h2": ParagraphStyle(
            "DentiaBudgetH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=section_heading,
            spaceBefore=8,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "DentiaBudgetBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        ),
        "small": ParagraphStyle(
            "DentiaBudgetSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
        ),
        "small_right": ParagraphStyle(
            "DentiaBudgetSmallRight",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_RIGHT,
        ),
        "cell": ParagraphStyle(
            "DentiaBudgetCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        ),
        "cell_bold": ParagraphStyle(
            "DentiaBudgetCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        ),
        "cell_header": ParagraphStyle(
            "DentiaBudgetCellHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=table_header_text,
        ),
        "center": ParagraphStyle(
            "DentiaBudgetCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
        ),
    }

    company_lines = [
        company.name,
        company.address,
        " · ".join(part for part in [company.city, company.country] if part),
        company.phone,
        company.email,
        company.website,
    ]
    professional_lines = [
        company.primary_dentist_name or (dentist.name if dentist else None),
        company.professional_specialty,
        f"Registro profesional: {company.professional_license}" if company.professional_license else None,
    ]
    logo = _image_if_exists(_branding_asset_path(company.logo_path), width=43 * mm, height=24 * mm)
    header_left = logo or _paragraph(company.name, styles["h2"])
    header_right = [
        _paragraph("Presupuesto odontológico", styles["title"]),
        Paragraph("<br/>".join(escape(line) for line in company_lines if line), styles["subtitle"]),
        Paragraph("<br/>".join(escape(line) for line in professional_lines if line), styles["subtitle"]),
    ]
    story: list[Flowable] = []
    story.append(
        Table(
            [[header_left, header_right]],
            colWidths=[doc.width * 0.36, doc.width * 0.64],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ("LINEBELOW", (0, 0), (-1, -1), 1.2, table_header_background),
                ]
            ),
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        Table(
            [[
                _paragraph("Plan de tratamiento personalizado", styles["h2"]),
                _paragraph(
                    "Después de la valoración realizada recomendamos el siguiente plan de tratamiento para recuperar y mantener su salud oral.",
                    styles["body"],
                ),
            ]],
            colWidths=[doc.width * 0.33, doc.width * 0.67],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), light_primary),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            ),
        )
    )
    story.append(Spacer(1, 8))

    patient_name = f"{patient.first_names} {patient.last_names}".strip()
    patient_document = " ".join(part for part in [patient.document_type, patient.document] if part)
    patient_data = [
        ["Paciente", patient_name, "Fecha", _date_text(budget.issued_at)],
        ["Documento", patient_document or "—", "Presupuesto", budget.number or f"Versión {budget.version}"],
        ["Teléfono", patient.mobile, "Versión", str(budget.version)],
        ["Correo", patient.email or "—", "Estado", budget.status],
    ]
    story.append(_paragraph("Datos del paciente", styles["h2"]))
    story.append(_info_table(patient_data, styles, primary, light_primary, doc.width))

    treatment_data = [
        ["Tratamiento", treatment.name, "Odontólogo", dentist.name if dentist else company.primary_dentist_name or "—"],
        ["Descripción", treatment.description or "—", "Sede", site.name if site else "—"],
    ]
    story.append(_paragraph("Información del tratamiento", styles["h2"]))
    story.append(_info_table(treatment_data, styles, primary, light_primary, doc.width))

    table_data = [[
        _paragraph("Procedimiento", styles["cell_header"]),
        _paragraph("Alcance", styles["cell_header"]),
        _paragraph("Cantidad", styles["cell_header"]),
        _paragraph("Valor unitario", styles["cell_header"]),
        _paragraph("Valor total", styles["cell_header"]),
    ]]
    for detail in details:
        table_data.append(
            [
                _paragraph(detail.name, styles["cell_bold"]),
                _paragraph(_scope_label(detail.scope_type, detail.zone, detail.tooth, detail.surfaces), styles["cell"]),
                _paragraph(f"{detail.quantity.normalize():f}", styles["cell"]),
                _paragraph(_money_text(detail.unit_value), styles["cell"]),
                _paragraph(_money_text(detail.total_value), styles["cell_bold"]),
            ]
        )
    story.append(_paragraph("Procedimientos", styles["h2"]))
    story.append(
        Table(
            table_data,
            colWidths=[doc.width * 0.30, doc.width * 0.25, doc.width * 0.12, doc.width * 0.17, doc.width * 0.16],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), table_header_background),
                    ("TEXTCOLOR", (0, 0), (-1, 0), table_header_text),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        )
    )

    summary_rows = [["Subtotal", _money_text(budget.gross_value)]]
    has_discount = _money(budget.discount_calculated_value) > 0
    if has_discount:
        discount_label = _money_text(budget.discount_value)
        if budget.discount_type == "porcentaje":
            discount_label = f"{budget.discount_value.normalize()}%"
        summary_rows.extend(
            [
                ["Descuento", discount_label],
                ["Valor descuento", _money_text(budget.discount_calculated_value)],
            ]
        )
    summary_rows.extend(
        [
            ["Valor final", _money_text(budget.final_value)],
            ["Pagado", _money_text(summary.paid_value)],
            ["Saldo pendiente", _money_text(summary.balance)],
        ]
    )
    final_row = len(summary_rows) - 3
    balance_row = len(summary_rows) - 1
    summary_table = Table(
        summary_rows,
        colWidths=[doc.width * 0.27, doc.width * 0.23],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, final_row), (-1, final_row), light_primary),
                ("BACKGROUND", (0, balance_row), (-1, balance_row), colors.HexColor("#fff7ed")),
                ("TEXTCOLOR", (0, balance_row), (-1, balance_row), colors.HexColor("#9a3412")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#e2e8f0")),
            ]
        ),
        hAlign="RIGHT",
    )
    story.append(Spacer(1, 12))
    story.append(KeepTogether([_paragraph("Resumen económico", styles["h2"]), summary_table]))

    observation_items: list[Flowable] = []
    if budget.observations:
        observation_items.extend(
            [
                _paragraph("Observaciones del presupuesto", styles["h2"]),
                Table(
                    [[_paragraph(budget.observations, styles["body"])]],
                    colWidths=[doc.width],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    ),
                ),
            ]
        )
    if company.header_text:
        observation_items.extend([Spacer(1, 5), _paragraph(company.header_text, styles["body"])])
    if company.thank_you_message:
        observation_items.extend([Spacer(1, 5), _paragraph(company.thank_you_message, styles["body"])])
    if budget.expires_on:
        observation_items.extend([Spacer(1, 8), _paragraph(f"Válido hasta: {_date_text(budget.expires_on)}", styles["cell_bold"])])
    if observation_items:
        story.append(Spacer(1, 10))
        story.extend(observation_items)

    signature = _image_if_exists(_branding_asset_path(company.signature_path), width=48 * mm, height=22 * mm)
    signature_block: list[Flowable] = []
    if signature:
        signature_block.append(signature)
    signature_block.extend(
        [
            Spacer(1, 4),
            _paragraph(company.primary_dentist_name or (dentist.name if dentist else company.name), styles["cell_bold"]),
            _paragraph(company.professional_specialty or "", styles["small"]),
            _paragraph(f"Registro profesional: {company.professional_license}" if company.professional_license else "", styles["small"]),
        ]
    )
    story.append(Spacer(1, 16))
    story.append(
        Table(
            [[signature_block]],
            colWidths=[doc.width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEABOVE", (0, 0), (0, 0), 0.6, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        )
    )

    footer_lines = [
        company.footer_text,
        company.address,
        " · ".join(part for part in [company.phone, company.email] if part),
    ]
    if company.social_media:
        footer_lines.append(" · ".join(f"{key}: {value}" for key, value in company.social_media.items()))

    def on_page(canvas, document):
        if budget.status == "Borrador":
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 62)
            canvas.setFillColor(colors.Color(0.5, 0.5, 0.5, alpha=0.11))
            canvas.translate(letter[0] / 2, letter[1] / 2)
            canvas.rotate(35)
            canvas.drawCentredString(0, 0, "BORRADOR")
            canvas.restoreState()
        canvas.saveState()
        canvas.setStrokeColor(secondary)
        canvas.setLineWidth(0.4)
        canvas.line(document.leftMargin, 1.02 * cm, letter[0] - document.rightMargin, 1.02 * cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(document.leftMargin, 0.68 * cm, " · ".join(line for line in footer_lines if line)[:170])
        canvas.drawRightString(letter[0] - document.rightMargin, 0.68 * cm, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    filename = f"presupuesto-{budget.number or budget.version}.pdf".replace("/", "-")
    return BudgetPdfResult(content=buffer.getvalue(), filename=filename)


def list_budgets(session: Session, context: AuthContext) -> list[BudgetResponse]:
    budgets = session.scalars(select(Budget).where(Budget.company_id == context.user.company_id).order_by(Budget.issued_at.desc())).all()
    return [_budget_response(session, budget) for budget in budgets if _can_access_treatment(session, context, budget.treatment_id)]


def _can_access_treatment(session: Session, context: AuthContext, treatment_id: UUID) -> bool:
    try:
        _require_treatment(session, context, treatment_id)
        return True
    except TreatmentError:
        return False


def update_budget(session: Session, context: AuthContext, budget_id: UUID, payload: BudgetCreateRequest, metadata: RequestMetadata) -> BudgetResponse:
    budget = session.scalar(select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id).with_for_update())
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    if budget.status not in {"Borrador", "Pendiente de aprobación"}:
        raise TreatmentError("Un presupuesto aprobado/rechazado no permite edición económica directa.")
    gross = _money(budget.gross_value)
    discount = _calculate_discount(gross, payload.discount_type, payload.discount_value)
    budget.discount_type = payload.discount_type
    budget.discount_value = _money(payload.discount_value)
    budget.discount_calculated_value = discount
    budget.final_value = _money(gross - discount)
    budget.observations = payload.observations
    budget.expires_on = payload.expires_on
    budget.updated_by = context.user.id
    _event(session, context, budget.treatment_id, "BUDGET_UPDATED", "Presupuesto actualizado.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action="BUDGET_UPDATED")
    session.commit()
    return get_budget(session, context, budget.id)


def change_budget_status(session: Session, context: AuthContext, budget_id: UUID, status: str, action: str, metadata: RequestMetadata) -> BudgetResponse:
    budget = session.scalar(select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id).with_for_update())
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    treatment = _require_treatment(session, context, budget.treatment_id, lock=True)
    if status == "Aprobado":
        if budget.final_value < 0:
            raise TreatmentError("No se puede aprobar un presupuesto con valor negativo.")
        budget.approved_at = datetime.now(timezone.utc)
        budget.approved_by = context.user.id
        treatment.status = "Aprobado" if treatment.status in {"Borrador", "Presupuestado"} else treatment.status
    if status == "Rechazado":
        budget.rejected_at = datetime.now(timezone.utc)
        budget.rejected_by = context.user.id
    budget.status = status
    budget.updated_by = context.user.id
    _event(session, context, treatment.id, action, f"Presupuesto {status}.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action=action)
    session.commit()
    return get_budget(session, context, budget.id)


def create_payment(session: Session, context: AuthContext, treatment_id: UUID, payload: PaymentCreateRequest, metadata: RequestMetadata) -> PaymentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    site = _require_site(session, context, payload.site_id)
    dentist = _require_dentist(session, context, payload.dentist_id, payload.site_id) if payload.dentist_id else None
    approved_budget = session.scalar(
        select(Budget)
        .where(Budget.treatment_id == treatment.id, Budget.status.in_(APPROVED_BUDGET_STATUSES))
        .order_by(Budget.version.desc())
        .limit(1)
    )
    if approved_budget is None and treatment.status not in {"Aprobado", "En ejecución", "Finalizado"}:
        raise TreatmentError("Para registrar pagos se requiere presupuesto o tratamiento aprobado.")
    summary = _summary(session, treatment.id)
    if payload.value > summary.balance:
        raise TreatmentError("El pago no puede superar el saldo pendiente.")
    payment = TreatmentPayment(
        company_id=context.user.company_id,
        patient_id=treatment.patient_id,
        treatment_id=treatment.id,
        budget_id=approved_budget.id if approved_budget else None,
        site_id=site.id,
        dentist_id=dentist.id if dentist else treatment.responsible_dentist_id,
        paid_at=payload.paid_at,
        value=_money(payload.value),
        payment_method=payload.payment_method,
        reference=payload.reference,
        observation=payload.observation,
        status=VALID_PAYMENT_STATUS,
        registered_by=context.user.id,
    )
    session.add(payment)
    if treatment.status == "Aprobado":
        treatment.status = "En ejecución"
    session.flush()
    _event(session, context, treatment.id, "PAYMENT_REGISTERED", "Pago registrado.", {"payment_id": str(payment.id), "value": str(payment.value)})
    _audit(session, context, metadata, entity="payment", entity_id=payment.id, action="PAYMENT_REGISTERED", detail={"value": str(payment.value)})
    session.commit()
    return get_payment(session, context, payment.id)


def _payment_response(session: Session, payment: TreatmentPayment) -> PaymentResponse:
    patient = session.get(Patient, payment.patient_id)
    treatment = session.get(Treatment, payment.treatment_id)
    site = session.get(Site, payment.site_id)
    dentist = session.get(Dentist, payment.dentist_id) if payment.dentist_id else None
    if patient is None or treatment is None or site is None:
        raise TreatmentError("Pago inválido o incompleto.", 500)
    return PaymentResponse(
        id=payment.id,
        patient_id=payment.patient_id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        treatment_id=payment.treatment_id,
        treatment_name=treatment.name,
        budget_id=payment.budget_id,
        site_id=payment.site_id,
        site_name=site.name,
        dentist_id=payment.dentist_id,
        dentist_name=dentist.name if dentist else None,
        paid_at=payment.paid_at,
        value=_money(payment.value),
        payment_method=payment.payment_method,
        reference=payment.reference,
        observation=payment.observation,
        status=payment.status,
        reversed_at=payment.reversed_at,
        reversal_reason=payment.reversal_reason,
    )


def get_payment(session: Session, context: AuthContext, payment_id: UUID) -> PaymentResponse:
    payment = session.scalar(
        select(TreatmentPayment).where(
            TreatmentPayment.id == payment_id,
            TreatmentPayment.company_id == context.user.company_id,
        )
    )
    if payment is None:
        raise TreatmentError("Pago no encontrado.", 404)
    _require_treatment(session, context, payment.treatment_id)
    return _payment_response(session, payment)


def list_payments(session: Session, context: AuthContext) -> list[PaymentResponse]:
    payments = session.scalars(
        select(TreatmentPayment).where(TreatmentPayment.company_id == context.user.company_id).order_by(TreatmentPayment.paid_at.desc())
    ).all()
    return [_payment_response(session, payment) for payment in payments if _can_access_treatment(session, context, payment.treatment_id)]


def reverse_payment(session: Session, context: AuthContext, payment_id: UUID, reason: str, metadata: RequestMetadata) -> PaymentResponse:
    payment = session.scalar(
        select(TreatmentPayment).where(
            TreatmentPayment.id == payment_id,
            TreatmentPayment.company_id == context.user.company_id,
        ).with_for_update()
    )
    if payment is None:
        raise TreatmentError("Pago no encontrado.", 404)
    if payment.status == REVERSED_PAYMENT_STATUS:
        raise TreatmentError("El pago ya fue reversado.")
    _require_treatment(session, context, payment.treatment_id)
    payment.status = REVERSED_PAYMENT_STATUS
    payment.reversed_at = datetime.now(timezone.utc)
    payment.reversed_by = context.user.id
    payment.reversal_reason = reason
    _event(session, context, payment.treatment_id, "PAYMENT_REVERSED", reason, {"payment_id": str(payment.id), "value": str(payment.value)})
    _audit(session, context, metadata, entity="payment", entity_id=payment.id, action="PAYMENT_REVERSED", detail={"reason": reason})
    session.commit()
    return get_payment(session, context, payment.id)


def finance_dashboard(session: Session, context: AuthContext) -> FinanceDashboardResponse:
    now = datetime.now(timezone.utc)
    start_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    start_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    start_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)

    def income_since(start: datetime) -> Decimal:
        return _money(session.scalar(select(func.coalesce(func.sum(TreatmentPayment.value), 0)).where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS, TreatmentPayment.paid_at >= start)))

    treatments = session.scalars(select(Treatment).where(Treatment.company_id == context.user.company_id)).all()
    balances = [_summary(session, treatment.id).balance for treatment in treatments]
    active_count = sum(1 for treatment in treatments if treatment.status in TREATMENT_ACTIVE_STATUSES)
    approved_finals = [_summary(session, treatment.id).final_value for treatment in treatments if _summary(session, treatment.id).final_value > 0]
    return FinanceDashboardResponse(
        income_today=income_since(start_day),
        income_month=income_since(start_month),
        income_year=income_since(start_year),
        receivables_total=_money(sum(balances, Decimal("0"))),
        active_treatments=active_count,
        average_ticket=_money(sum(approved_finals, Decimal("0")) / len(approved_finals)) if approved_finals else Decimal("0.00"),
    )


def _breakdown(session: Session, context: AuthContext, group: str) -> FinanceBreakdownResponse:
    if group == "site":
        rows = session.execute(
            select(Site.id, Site.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
            .join(TreatmentPayment, TreatmentPayment.site_id == Site.id)
            .where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS)
            .group_by(Site.id, Site.name)
        ).all()
    elif group == "dentist":
        rows = session.execute(
            select(Dentist.id, Dentist.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
            .join(TreatmentPayment, TreatmentPayment.dentist_id == Dentist.id)
            .where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS)
            .group_by(Dentist.id, Dentist.name)
        ).all()
    else:
        rows = session.execute(
            select(TreatmentProcedure.id, TreatmentProcedure.name, func.coalesce(func.sum(TreatmentProcedure.total_value), 0))
            .where(TreatmentProcedure.company_id == context.user.company_id, TreatmentProcedure.status == "Realizado")
            .group_by(TreatmentProcedure.id, TreatmentProcedure.name)
        ).all()
    return FinanceBreakdownResponse(items=[FinanceBreakdownItem(id=row[0], name=row[1], value=_money(row[2])) for row in rows])


def finance_by_site(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "site")


def finance_by_dentist(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "dentist")


def finance_by_procedure(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "procedure")


def patient_balances(session: Session, context: AuthContext) -> PatientBalancesResponse:
    patients = {}
    for treatment in session.scalars(select(Treatment).where(Treatment.company_id == context.user.company_id)).all():
        balance = _summary(session, treatment.id).balance
        if balance <= 0:
            continue
        patients[treatment.patient_id] = patients.get(treatment.patient_id, Decimal("0")) + balance
    items = []
    for patient_id, balance in patients.items():
        patient = session.get(Patient, patient_id)
        if patient:
            items.append(PatientBalanceItem(patient_id=patient_id, patient_name=f"{patient.first_names} {patient.last_names}".strip(), balance=_money(balance)))
    return PatientBalancesResponse(items=items)
