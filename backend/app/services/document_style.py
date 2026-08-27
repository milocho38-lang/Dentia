from dataclasses import dataclass
import re


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
