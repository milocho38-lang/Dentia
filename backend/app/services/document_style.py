from dataclasses import dataclass
import re

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, KeepTogether, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agenda import Dentist
from app.models.company import Company
from app.models.user import User


DEFAULT_DOCUMENT_FONT = "HELVETICA"
DEFAULT_DOCUMENT_HEADING_COLOR = "#0f172a"
MINIMUM_TEXT_CONTRAST = 4.5
_HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class DocumentFont:
    code: str
    label: str
    regular: str
    bold: str
    css_family: str


@dataclass(frozen=True)
class ProfessionalDocumentIdentity:
    full_name: str | None
    specialty: str | None
    document_type: str | None
    document_number: str | None
    professional_license: str | None
    email: str | None
    signature_path: str | None
    signature_filename: str | None = None

    def snapshot(self) -> dict[str, str | None]:
        return {
            "full_name": self.full_name,
            # Keep name for backward-compatible readers of historical snapshots.
            "name": self.full_name,
            "specialty": self.specialty,
            "document_type": self.document_type,
            "document_number": self.document_number,
            "professional_license": self.professional_license,
            "license_number": self.professional_license,
            "email": self.email,
            "signature_path": self.signature_path,
            "signature_filename": self.signature_filename,
        }


DOCUMENT_TYPE_LABELS = {
    "CC": "Cédula de ciudadanía",
    "CE": "Cédula de extranjería",
    "TI": "Tarjeta de identidad",
    "PASAPORTE": "Pasaporte",
    "PASSPORT": "Pasaporte",
    "RUT": "RUT",
    "RUN": "RUN",
    "DNI": "Documento nacional de identidad",
    "OTRO": "Otro documento",
    "OTHER": "Otro documento",
}


REQUIRED_PROFESSIONAL_IDENTITY_FIELDS = {
    "full_name": "nombre completo",
    "document_type": "tipo de documento",
    "document_number": "número de documento",
    "professional_license": "registro profesional",
    "email": "correo profesional",
    "signature_path": "firma gráfica",
}


DOCUMENT_FONTS = {
    "HELVETICA": DocumentFont(
        "HELVETICA", "Helvetica", "Helvetica", "Helvetica-Bold", "Helvetica, Arial, sans-serif"
    ),
    "ARIAL_COMPATIBLE": DocumentFont(
        "ARIAL_COMPATIBLE", "Arial (compatible)", "Helvetica", "Helvetica-Bold", "Arial, Helvetica, sans-serif"
    ),
    "TIMES_COMPATIBLE": DocumentFont(
        "TIMES_COMPATIBLE", "Times New Roman (compatible)", "Times-Roman", "Times-Bold", '"Times New Roman", Times, serif'
    ),
    "GEORGIA_COMPATIBLE": DocumentFont(
        "GEORGIA_COMPATIBLE", "Georgia (compatible)", "Times-Roman", "Times-Bold", "Georgia, serif"
    ),
    "VERDANA_COMPATIBLE": DocumentFont(
        "VERDANA_COMPATIBLE", "Verdana (compatible)", "Helvetica", "Helvetica-Bold", "Verdana, Arial, sans-serif"
    ),
    "TREBUCHET_COMPATIBLE": DocumentFont(
        "TREBUCHET_COMPATIBLE", "Trebuchet MS (compatible)", "Helvetica", "Helvetica-Bold", '"Trebuchet MS", Arial, sans-serif'
    ),
}


def resolve_document_font(code: str | None) -> DocumentFont:
    return DOCUMENT_FONTS.get(code or DEFAULT_DOCUMENT_FONT, DOCUMENT_FONTS[DEFAULT_DOCUMENT_FONT])


def validate_document_font(code: str) -> str:
    normalized = code.strip().upper()
    if normalized not in DOCUMENT_FONTS:
        raise ValueError("Tipografía documental no permitida.")
    return normalized


def apply_reportlab_font(styles: dict, code: str | None) -> DocumentFont:
    font = resolve_document_font(code)
    style_values = styles.values() if hasattr(styles, "values") else styles.byName.values()
    for style in style_values:
        current = str(getattr(style, "fontName", ""))
        style.fontName = font.bold if "Bold" in current else font.regular
    return font


def resolve_professional_document_identity(
    session: Session,
    company: Company,
    dentist: Dentist,
) -> ProfessionalDocumentIdentity:
    """Resolve one tenant-scoped canonical identity for newly issued documents."""
    if dentist.company_id != company.id:
        raise ValueError("El profesional no pertenece a la empresa del documento.")
    user = session.scalar(
        select(User).where(
            User.id == dentist.user_id,
            User.company_id == company.id,
        )
    ) if dentist.user_id else None
    return ProfessionalDocumentIdentity(
        full_name=(dentist.name or (user.name if user else None)),
        specialty=dentist.specialty or "Odontólogo/a",
        document_type=dentist.document_type,
        document_number=dentist.document_number,
        professional_license=dentist.professional_license,
        email=user.email if user else None,
        signature_path=dentist.signature_path,
        signature_filename=dentist.signature_filename,
    )


def professional_identity_from_snapshot(snapshot: dict | None) -> ProfessionalDocumentIdentity:
    value = snapshot or {}
    return ProfessionalDocumentIdentity(
        full_name=value.get("full_name") or value.get("name"),
        specialty=value.get("specialty"),
        document_type=value.get("document_type"),
        document_number=value.get("document_number"),
        professional_license=value.get("professional_license") or value.get("license_number"),
        email=value.get("email"),
        signature_path=value.get("signature_path"),
        signature_filename=value.get("signature_filename"),
    )


def missing_professional_identity_fields(
    identity: ProfessionalDocumentIdentity,
    *,
    require_signature: bool = True,
) -> list[str]:
    values = identity.snapshot()
    keys = list(REQUIRED_PROFESSIONAL_IDENTITY_FIELDS)
    if not require_signature:
        keys.remove("signature_path")
    return [REQUIRED_PROFESSIONAL_IDENTITY_FIELDS[key] for key in keys if not values.get(key)]


def require_complete_professional_identity(
    identity: ProfessionalDocumentIdentity,
    *,
    require_signature: bool = True,
) -> None:
    missing = missing_professional_identity_fields(identity, require_signature=require_signature)
    if missing:
        raise ValueError(
            "No es posible finalizar el documento. Completa la identidad profesional: "
            + ", ".join(missing)
            + "."
        )


def professional_document_label(document_type: str | None) -> str | None:
    if not document_type:
        return None
    normalized = document_type.strip().upper()
    return DOCUMENT_TYPE_LABELS.get(normalized, document_type.strip())


def render_professional_identity_block(
    snapshot: dict | None,
    *,
    styles: dict,
    signature: Flowable | None = None,
    width: float = 86 * mm,
    show_intro: bool = False,
    separator: bool = True,
) -> Flowable:
    """Build a compact, left-aligned identity unit shared by PDF generators."""
    identity = professional_identity_from_snapshot(snapshot)
    strong = styles["cell_bold"]
    small = styles["small"]
    lines: list[Flowable] = []
    if show_intro:
        lines.extend([Paragraph("Atentamente,", styles.get("body", small)), Spacer(1, 3 * mm)])
    if signature is not None:
        if hasattr(signature, "hAlign"):
            signature.hAlign = "LEFT"
        lines.extend([signature, Spacer(1, 1.5 * mm)])
    lines.append(Paragraph(identity.full_name or "Profesional no disponible", strong))
    if identity.specialty:
        lines.append(Paragraph(identity.specialty, small))
    document_label = professional_document_label(identity.document_type)
    if document_label and identity.document_number:
        lines.append(Paragraph(f"Documento: {document_label} {identity.document_number}", small))
    if identity.professional_license:
        lines.append(Paragraph(f"Registro profesional: {identity.professional_license}", small))
    if identity.email:
        lines.append(Paragraph(identity.email, small))
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm if separator else 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]
    if separator:
        commands.append(("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")))
    return KeepTogether(
        Table([[lines]], colWidths=[width], hAlign="LEFT", style=TableStyle(commands))
    )


def _relative_luminance(red: int, green: int, blue: int) -> float:
    def channel(value: int) -> float:
        normalized = value / 255
        return normalized / 12.92 if normalized <= 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_against_white(red: int, green: int, blue: int) -> float:
    return 1.05 / (_relative_luminance(red, green, blue) + 0.05)


def resolve_readable_document_heading_color(
    value: str | None,
    *,
    minimum_contrast: float = MINIMUM_TEXT_CONTRAST,
) -> str:
    """Return a PDF-only heading color readable on white without mutating branding.

    Colors that already meet WCAG AA text contrast are preserved exactly. Lighter
    colors are darkened by scaling their RGB channels together, which preserves hue
    and saturation as far as the source color allows.
    """
    match = _HEX_COLOR.fullmatch((value or "").strip())
    source = match.group(1) if match else DEFAULT_DOCUMENT_HEADING_COLOR.removeprefix("#")
    red, green, blue = (int(source[index:index + 2], 16) for index in (0, 2, 4))
    if _contrast_against_white(red, green, blue) >= minimum_contrast:
        return f"#{source.lower()}"

    # Find the lightest proportional variant that satisfies the target contrast.
    safe_factor = 0.0
    unsafe_factor = 1.0
    for _ in range(24):
        factor = (safe_factor + unsafe_factor) / 2
        candidate = tuple(round(channel * factor) for channel in (red, green, blue))
        if _contrast_against_white(*candidate) >= minimum_contrast:
            safe_factor = factor
        else:
            unsafe_factor = factor
    resolved = tuple(int(channel * safe_factor) for channel in (red, green, blue))
    return "#" + "".join(f"{channel:02x}" for channel in resolved)
