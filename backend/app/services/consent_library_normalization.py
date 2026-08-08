from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


NORM3_SCHEMA_VERSION = "LIB1_NORM_V2_CONTEXTUAL"
NORM5_SCHEMA_VERSION = "LIB1_NORM_V2_ELECTRONIC_READINESS"
NORMALIZED_CONTENT_FIELD = "normalized_content_markdown"

SOURCE_HEADING_PATTERN = re.compile(r"^\s*#{0,3}\s*Texto del documento fuente\s*$", re.IGNORECASE)
PAGE_MARKER_PATTERN = re.compile(r"\[P[áa]gina\s+\d+\]", re.IGNORECASE)
EXTRACTION_HEADING_PATTERN = re.compile(r"^\s*(texto extra[ií]do|documento fuente|fuente pdf|origen pdf)\s*:?\s*$", re.IGNORECASE)
LONG_FILL_LINE_PATTERN = re.compile(r"^\s*[_\-]{6,}\s*$")
MANUAL_SIGNATURE_LINE_PATTERN = re.compile(r"^\s*#{0,3}\s*(firma(?:\s+(?:paciente|profesional|tutor|apoderad[oa]))?|paciente(?:\s+o\s+responsable)?|profesional|ciudad\s+y\s+fecha|fecha)\s*:?\s*[_\- ]*\s*$", re.IGNORECASE)
MANUAL_FIELD_LINE_PATTERN = re.compile(r"^\s*(paciente(?:\s+o\s+responsable)?|profesional|registro\s+profesional|doctor(?:a)?|dr\(a\)|rut|identificaci[oó]n|fecha|ciudad|firma\s+tutor|firma\s+apoderad[oa])\s*:?\s*[_\-]{3,}.*$", re.IGNORECASE)
PROFESSIONAL_SIGNATURE_VALUE_PATTERN = re.compile(r"^\s*profesional\s*:\s*\{\{professional\.full_name\}\}.*$", re.IGNORECASE)
PROFESSIONAL_LICENSE_SIGNATURE_VALUE_PATTERN = re.compile(r"^\s*registro\s+profesional\s*:\s*\{\{professional\.license_number\}\}\s*$", re.IGNORECASE)
HTML_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
DANGEROUS_SCRIPT_PATTERN = re.compile(r"(<\s*script\b|<\s*iframe\b|javascript\s*:)", re.IGNORECASE)
UNKNOWN_VARIABLE_PATTERN = re.compile(r"\{\{\s*([^{}\s]+)\s*\}\}")

LOCAL_TERM_PATTERN = re.compile(r"\b(tapadura|cabritas|bombilla|calugas|calugones|contralor[ií]a|garant[ií]as?|montos?)\b", re.IGNORECASE)
ADMINISTRATIVE_RESPONSIBLE_PATTERN = re.compile(r"\b(profesional\s+responsable|responsable\s+del\s+tratamiento|responsable\s+con\s+las\s+indicaciones|responsable\s+de\s+pago|responsabilidad\s+del\s+paciente|siendo\s+responsable)\b", re.IGNORECASE)
REAL_REPRESENTATIVE_PATTERN = re.compile(r"\b(representante\s+legal\s+del\s+paciente|tutor\s+legal\s+firma|tutor\s+legal\s+autoriza|padre\s*,?\s+madre\s+o\s+apoderad[oa]|padre\s+o\s+madre|madre\s+o\s+padre|menor\s+de\s+edad|menores\s+de\s+edad|lactante(?:s)?)\b", re.IGNORECASE)
PEDIATRIC_PATTERN = re.compile(r"\b(odontopediatr[ií]a|odontopediatra|niñ[oa]s?|infante|recambio\s+dentario|dientes\s+temporales|fl[uú]or\s+barniz|trauma\s+dentoalveolar)\b", re.IGNORECASE)
DISJUNCTIVE_REPRESENTATIVE_PATTERN = re.compile(r"\b(paciente\s+o\s+tutor(?:a)?(?:\s+legal)?|paciente\s+o\s+responsable|paciente\s*/\s*apoderad[oa]|tutor\s+acompañante|apoderad[oa])\b", re.IGNORECASE)
MANUAL_REPRESENTATIVE_LABEL_PATTERN = re.compile(r"\b(paciente\s+o\s+responsable|firma\s+tutor|firma\s+apoderad[oa])\s*:?\s*[_\-]{3,}", re.IGNORECASE)
INLINE_MANUAL_BLANK_PATTERN = re.compile(r"[_]{3,}")
MANUAL_IDENTITY_FIELD_PATTERN = re.compile(r"\b(yo|nombre|rut|cc|c[eé]dula|documento|identificaci[oó]n|paciente)\b\s*:?\s*_{3,}", re.IGNORECASE)
MANUAL_SIGNATURE_FIELD_PATTERN = re.compile(r"\b(firma|fecha|ciudad\s+y\s+fecha)\b\s*:?\s*_{3,}", re.IGNORECASE)
MANUAL_DATE_TEXT_PATTERN = re.compile(r"\b(curic[oó]|ciudad)\b\s*_{3,}|\b(?:del|de)\s*_{3,}", re.IGNORECASE)
GENERIC_TUTOR_LEGAL_PATTERN = re.compile(r"\btutor\s+legal\b", re.IGNORECASE)
CO_SIGNER_RUT_PATTERN = re.compile(r"\bRUT\b\s*:?\s*_{0,}", re.IGNORECASE)

SPECIAL_DOCUMENT_TYPES = {"TREATMENT_REFUSAL", "NO_WARRANTY_ACKNOWLEDGEMENT", "AESTHETIC_APPROVAL", "TREATMENT_TERMINATION_ACKNOWLEDGEMENT"}
NO_SIGNATURE_DOCUMENT_TYPES = {"CERTIFICATE", "POST_CARE_INSTRUCTIONS", "PRE_CARE_INSTRUCTIONS"}
INFORMED_CONSENT_TYPES = {"INFORMED_CONSENT", "PROCEDURE_CONSENT", "GENERAL_CLINICAL_CONSENT", "TREATMENT_AUTHORIZATION"}


@dataclass(frozen=True)
class SignerFinding:
    scope: str
    category: str
    term: str | None = None
    line_number: int | None = None
    context: str | None = None
    reason: str | None = None
    adult_variant_required: bool = False
    adult_variant_proposal: dict | None = None


@dataclass(frozen=True)
class NormalizationResult:
    content: str
    removed_markers: list[str]
    removed_signature_lines: list[str]
    joined_paragraphs: int
    representative_phrases: list[str]
    local_terms: list[str]
    signer_compatibility: str
    status: str
    alerts: list[str]
    transformations: list[str]
    signer_blocking_category: str = "none"
    signer_blocking_term: str | None = None
    signer_blocking_line: int | None = None
    signer_blocking_context: str | None = None
    signer_blocking_reason: str | None = None
    adult_variant_required: bool = False
    adult_variant_proposal: dict | None = None


@dataclass(frozen=True)
class PatientContentValidation:
    status: str
    blockers: list[str]
    warnings: list[str]

    @property
    def passed(self) -> bool:
        return self.status != "BLOCKED"


@dataclass(frozen=True)
class LegacyContentAssessment:
    is_legacy: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ElectronicReadinessFinding:
    severity: str
    code: str
    message: str
    line_number: int | None = None
    context: str | None = None


@dataclass(frozen=True)
class ElectronicReadinessAssessment:
    status: str
    findings: list[ElectronicReadinessFinding] = field(default_factory=list)

    @property
    def errors(self) -> list[ElectronicReadinessFinding]:
        return [item for item in self.findings if item.severity == "ERROR"]

    @property
    def warnings(self) -> list[ElectronicReadinessFinding]:
        return [item for item in self.findings if item.severity == "WARNING"]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _line_context(lines: list[str], index: int) -> str:
    start = max(0, index - 2)
    end = min(len(lines), index + 3)
    return " ".join(part.strip() for part in lines[start:end] if part.strip())[:700]


def _is_structural_signature_line(line: str) -> bool:
    stripped = line.strip()
    return bool(LONG_FILL_LINE_PATTERN.match(stripped) or MANUAL_SIGNATURE_LINE_PATTERN.match(stripped) or MANUAL_FIELD_LINE_PATTERN.match(stripped) or MANUAL_REPRESENTATIVE_LABEL_PATTERN.search(stripped))


def _compact_markdown_lines(lines: list[str]) -> tuple[str, int]:
    blocks: list[str] = []
    paragraph: list[str] = []
    joined = 0

    def flush() -> None:
        nonlocal joined
        if paragraph:
            if len(paragraph) > 1:
                joined += len(paragraph) - 1
            blocks.append(" ".join(part.strip() for part in paragraph if part.strip()))
            paragraph.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped == "---" or stripped.startswith("# ") or stripped.startswith("## ") or re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            flush()
            blocks.append(stripped)
            continue
        paragraph.append(stripped)
    flush()
    return "\n\n".join(blocks).strip() + "\n", joined


def _first_match(lines: list[str], pattern: re.Pattern[str]) -> tuple[str, int, str] | None:
    for index, line in enumerate(lines, 1):
        match = pattern.search(line)
        if match:
            return match.group(0), index, _line_context(lines, index - 1)
    return None


def _adult_variant_for_disjunctive(term: str, line_number: int, context: str) -> dict:
    proposed = context
    replacements = {
        r"paciente\s+o\s+tutor(?:a)?(?:\s+legal)?": "paciente",
        r"paciente\s+o\s+responsable": "paciente",
        r"paciente\s*/\s*apoderad[oa]": "paciente",
        r"tutor\s+acompañante": "acompañante adulto",
        r"apoderad[oa]": "representante",
    }
    for pattern, replacement in replacements.items():
        proposed = re.sub(pattern, replacement, proposed, flags=re.IGNORECASE)
    return {
        "original_fragment": context,
        "proposed_fragment": proposed,
        "modified_term": term,
        "line_number": line_number,
        "justification": "El texto fuente mezcla paciente adulto y representante. La variante adulta propuesta conserva el sentido para paciente que actúa en nombre propio, pero requiere equivalencia clínica y jurídica.",
        "impact": "La variante derivada no debe publicarse ni aprobarse automáticamente.",
        "clinical_approval_required": True,
        "legal_approval_required": True,
    }


def classify_signer_context(content: str, *, document_type: str, title: str | None = None, current_signer_scope: str = "ADULT_SELF") -> SignerFinding:
    lines = content.splitlines()
    title_text = title or ""
    if document_type in NO_SIGNATURE_DOCUMENT_TYPES:
        return SignerFinding(scope="NO_PATIENT_SIGNATURE", category="no requiere firma", reason="Documento informativo o certificado que no debe entrar al flujo de consentimiento firmado.")
    if document_type in SPECIAL_DOCUMENT_TYPES:
        return SignerFinding(scope="SPECIAL_WORKFLOW", category="documento especial", reason=f"Tipo documental {document_type} requiere flujo dedicado diferente al consentimiento adulto estándar.")
    pediatric_title = PEDIATRIC_PATTERN.search(title_text)
    pediatric_content = _first_match(lines, PEDIATRIC_PATTERN)
    if pediatric_title or pediatric_content:
        term, line, context = pediatric_content if pediatric_content else (pediatric_title.group(0), None, title_text)
        return SignerFinding(scope="RESPONSIBLE_ADULT_REQUIRED", category="contenido pediátrico", term=term, line_number=line, context=context, reason="El documento contiene contenido pediátrico o de menor de edad; el flujo adulto en nombre propio no aplica.")
    real = _first_match(lines, REAL_REPRESENTATIVE_PATTERN)
    if real:
        term, line, context = real
        return SignerFinding(scope="RESPONSIBLE_ADULT_REQUIRED", category="representante real", term=term, line_number=line, context=context, reason="La cláusula exige o describe representación legal real.")
    disjunctive = _first_match(lines, DISJUNCTIVE_REPRESENTATIVE_PATTERN)
    if disjunctive:
        term, line, context = disjunctive
        return SignerFinding(scope="PATIENT_OR_RESPONSIBLE_ADULT", category="texto disyuntivo", term=term, line_number=line, context=context, reason="El texto contempla paciente y representante. El flujo electrónico actual solo permite adultos que actúan en nombre propio.", adult_variant_required=True, adult_variant_proposal=_adult_variant_for_disjunctive(term, line, context))
    administrative = _first_match(lines, ADMINISTRATIVE_RESPONSIBLE_PATTERN)
    if administrative:
        term, line, context = administrative
        return SignerFinding(scope="PATIENT_SELF", category="término administrativo", term=term, line_number=line, context=context, reason="El término responsable se usa en sentido administrativo/clínico, no como representante legal.")
    if current_signer_scope in {"ADULT_OR_REPRESENTATIVE", "REPRESENTATIVE_REQUIRED", "PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}:
        mapped_scope = {"ADULT_OR_REPRESENTATIVE": "PATIENT_OR_RESPONSIBLE_ADULT", "REPRESENTATIVE_REQUIRED": "RESPONSIBLE_ADULT_REQUIRED"}.get(current_signer_scope, current_signer_scope)
        return SignerFinding(scope=mapped_scope, category="clasificación heredada", reason="El paquete fuente trae un alcance de firmante que requiere revisión humana.", adult_variant_required=mapped_scope == "PATIENT_OR_RESPONSIBLE_ADULT")
    if current_signer_scope in {"NO_SIGNATURE_REQUIRED", "ADMINISTRATIVE_RECORD", "NO_PATIENT_SIGNATURE"}:
        return SignerFinding(scope="NO_PATIENT_SIGNATURE", category="no requiere firma", reason="El alcance fuente indica que no requiere firma de paciente.")
    return SignerFinding(scope="PATIENT_SELF", category="adulto en nombre propio", reason="No se detectaron expresiones contextuales que exijan representante.")


def classify_signer_compatibility(content: str, document_type: str, current_signer_scope: str) -> str:
    return classify_signer_context(content, document_type=document_type, current_signer_scope=current_signer_scope).scope


def normalize_patient_content_v2(content: str, *, document_type: str, signer_scope: str, title: str | None = None) -> NormalizationResult:
    removed_markers: list[str] = []
    removed_signature_lines: list[str] = []
    kept_lines: list[str] = []
    in_source_section = False
    for raw_line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if SOURCE_HEADING_PATTERN.match(stripped):
            in_source_section = True
            removed_markers.append(stripped)
            continue
        if EXTRACTION_HEADING_PATTERN.match(stripped):
            removed_markers.append(stripped)
            continue
        if PAGE_MARKER_PATTERN.search(stripped):
            marker = PAGE_MARKER_PATTERN.findall(stripped)
            removed_markers.extend(marker)
            stripped = PAGE_MARKER_PATTERN.sub("", stripped).strip()
            if not stripped:
                continue
            line = stripped
        if in_source_section and _is_structural_signature_line(stripped):
            removed_signature_lines.append(stripped)
            continue
        if in_source_section and PROFESSIONAL_SIGNATURE_VALUE_PATTERN.match(stripped):
            removed_signature_lines.append(stripped)
            continue
        if in_source_section and PROFESSIONAL_LICENSE_SIGNATURE_VALUE_PATTERN.match(stripped):
            removed_signature_lines.append(stripped)
            continue
        if _is_structural_signature_line(stripped) and kept_lines:
            removed_signature_lines.append(stripped)
            continue
        if stripped.casefold().startswith("profesional responsable:"):
            removed_markers.append(stripped)
            continue
        kept_lines.append(line)
    normalized, joined_paragraphs = _compact_markdown_lines(kept_lines)
    signer = classify_signer_context(normalized, document_type=document_type, title=title, current_signer_scope=signer_scope)
    representative_phrases = _unique([item for pattern in (REAL_REPRESENTATIVE_PATTERN, DISJUNCTIVE_REPRESENTATIVE_PATTERN, PEDIATRIC_PATTERN) for item in pattern.findall(normalized)])
    local_terms = _unique(LOCAL_TERM_PATTERN.findall(normalized))
    validation = validate_patient_facing_content(normalized, allowed_variables=None, document_type=document_type, signer_compatibility=signer.scope, normalized_hash=sha256_text(normalized))
    transformations = [f"normalization_schema_version={NORM3_SCHEMA_VERSION}", "source_text preserved without mutation", "patient-facing content rebuilt from normalized markdown only"]
    if removed_markers:
        transformations.append(f"removed_source_markers={len(removed_markers)}")
    if removed_signature_lines:
        transformations.append(f"removed_manual_signature_lines={len(removed_signature_lines)}")
    if joined_paragraphs:
        transformations.append(f"joined_structural_line_breaks={joined_paragraphs}")
    transformations.extend([f"signer_compatibility={signer.scope}", f"signer_blocking_category={signer.category}", f"signer_blocking_reason={signer.reason or ''}", f"adult_variant_required={str(signer.adult_variant_required).lower()}", f"normalization_status={validation.status}"])
    if signer.term:
        transformations.append(f"signer_blocking_term={signer.term}")
    if signer.line_number:
        transformations.append(f"signer_blocking_line={signer.line_number}")
    if signer.context:
        transformations.append(f"signer_blocking_context={signer.context}")
    return NormalizationResult(content=normalized, removed_markers=removed_markers, removed_signature_lines=removed_signature_lines, joined_paragraphs=joined_paragraphs, representative_phrases=representative_phrases, local_terms=local_terms, signer_compatibility=signer.scope, status=validation.status, alerts=[*validation.blockers, *validation.warnings], transformations=transformations, signer_blocking_category=signer.category, signer_blocking_term=signer.term, signer_blocking_line=signer.line_number, signer_blocking_context=signer.context, signer_blocking_reason=signer.reason, adult_variant_required=signer.adult_variant_required, adult_variant_proposal=signer.adult_variant_proposal)


def assess_legacy_patient_content(content: str, *, source_library_version_schema: str | None = None) -> LegacyContentAssessment:
    reasons: list[str] = []
    if PAGE_MARKER_PATTERN.search(content):
        reasons.append("source_page_marker_present")
    lines = content.splitlines()
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if SOURCE_HEADING_PATTERN.match(stripped):
            reasons.append("source_heading_present")
        if EXTRACTION_HEADING_PATTERN.match(stripped):
            reasons.append("extraction_heading_present")
        if LONG_FILL_LINE_PATTERN.match(stripped):
            reasons.append(f"manual_fill_line_present:{index}")
        elif MANUAL_REPRESENTATIVE_LABEL_PATTERN.search(stripped):
            reasons.append(f"manual_representative_label_present:{index}")
        elif index > max(1, len(lines) - 10) and _is_structural_signature_line(stripped):
            reasons.append(f"manual_signature_block_present:{index}")
    if source_library_version_schema and source_library_version_schema != NORM3_SCHEMA_VERSION:
        reasons.append(f"pre_norm4_library_schema:{source_library_version_schema}")
    return LegacyContentAssessment(is_legacy=bool(reasons), reasons=_unique(reasons))


def assess_electronic_readiness(content: str, *, country_code: str | None = None, document_type: str | None = None, signer_compatibility: str | None = None) -> ElectronicReadinessAssessment:
    findings: list[ElectronicReadinessFinding] = []
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    def add(severity: str, code: str, message: str, line_number: int | None = None, context: str | None = None) -> None:
        findings.append(ElectronicReadinessFinding(severity=severity, code=code, message=message, line_number=line_number, context=context))

    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if INLINE_MANUAL_BLANK_PATTERN.search(stripped):
            add("ERROR", "manual_blank_present", "El contenido electrónico conserva espacios manuales de formulario.", index, stripped[:220])
        if MANUAL_IDENTITY_FIELD_PATTERN.search(stripped):
            add("ERROR", "manual_identity_field_present", "El contenido electrónico conserva un campo manual de identidad.", index, stripped[:220])
        if MANUAL_SIGNATURE_FIELD_PATTERN.search(stripped) or MANUAL_DATE_TEXT_PATTERN.search(stripped):
            add("ERROR", "manual_signature_or_date_present", "El contenido electrónico conserva un bloque manual de firma o fecha.", index, stripped[:220])
        if country_code == "CO" and CO_SIGNER_RUT_PATTERN.search(stripped):
            add("ERROR", "rut_in_colombia_variant", "La variante Colombia no debe mostrar RUT como identificación manual del firmante.", index, stripped[:220])
        if GENERIC_TUTOR_LEGAL_PATTERN.search(stripped) and signer_compatibility in {"PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}:
            add("ERROR", "generic_tutor_legal_present", "El rol genérico debe expresarse como adulto responsable en el flujo electrónico.", index, stripped[:220])

    if document_type in SPECIAL_DOCUMENT_TYPES:
        add("ERROR", "special_workflow", f"El tipo documental {document_type} requiere flujo dedicado.", None, None)
    if document_type in NO_SIGNATURE_DOCUMENT_TYPES:
        add("INFO", "no_patient_signature", f"El tipo documental {document_type} no entra al flujo común de firma de paciente.", None, None)
    if document_type in INFORMED_CONSENT_TYPES and signer_compatibility not in {"ADULT_SELF", "PATIENT_SELF", "PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}:
        add("ERROR", "incompatible_signer_policy", f"El firmante {signer_compatibility} no es compatible con el flujo electrónico estándar.", None, None)

    status = "BLOCKED" if any(item.severity == "ERROR" for item in findings) else "READY"
    return ElectronicReadinessAssessment(status=status, findings=findings)


def validate_patient_facing_content(content: str, *, allowed_variables: set[str] | None, document_type: str, signer_compatibility: str, normalized_hash: str | None, source_text: str | None = None, country_code: str | None = None, enforce_electronic_readiness: bool = False) -> PatientContentValidation:
    blockers: list[str] = []
    warnings: list[str] = []
    stripped = content.strip()
    if not stripped:
        blockers.append("normalized_content_empty")
    if source_text is not None and stripped == source_text.strip():
        blockers.append("normalized_content_equals_source_text")
    if not normalized_hash or len(normalized_hash) != 64:
        blockers.append("normalized_content_hash_missing_or_invalid")
    blockers.extend(assess_legacy_patient_content(content).reasons)
    if DANGEROUS_SCRIPT_PATTERN.search(content):
        blockers.append("dangerous_script_or_uri_present")
    if HTML_PATTERN.search(content):
        blockers.append("html_not_allowed")
    if allowed_variables is not None:
        for variable in UNKNOWN_VARIABLE_PATTERN.findall(content):
            if variable not in allowed_variables:
                blockers.append(f"unknown_variable:{variable}")
    if document_type in INFORMED_CONSENT_TYPES and signer_compatibility not in {"ADULT_SELF", "PATIENT_SELF", "PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}:
        blockers.append(f"incompatible_signer_for_standard_electronic_flow:{signer_compatibility}")
    if document_type in SPECIAL_DOCUMENT_TYPES:
        warnings.append(f"special_document_type_requires_dedicated_workflow:{document_type}")
    if document_type in NO_SIGNATURE_DOCUMENT_TYPES:
        warnings.append(f"document_does_not_require_patient_signature:{document_type}")
    if LOCAL_TERM_PATTERN.search(content):
        warnings.append("localized_terms_require_human_review")
    if enforce_electronic_readiness:
        readiness = assess_electronic_readiness(content, country_code=country_code, document_type=document_type, signer_compatibility=signer_compatibility)
        blockers.extend(f"electronic_readiness:{item.code}" for item in readiness.errors)
        warnings.extend(f"electronic_readiness:{item.code}" for item in readiness.warnings)
    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return PatientContentValidation(status=status, blockers=_unique(blockers), warnings=_unique(warnings))


def parse_normalization_metadata(transformation_notes: list[str] | None) -> dict:
    metadata = {"normalization_schema_version": None, "normalization_status": "UNKNOWN", "signer_compatibility": "UNKNOWN", "normalization_alerts": [], "signer_blocking_category": None, "signer_blocking_reason": None, "signer_blocking_term": None, "signer_blocking_line": None, "signer_blocking_context": None, "adult_variant_required": False, "electronic_readiness_status": "UNKNOWN", "electronic_readiness_findings": [], "norm5_result": None}
    for note in transformation_notes or []:
        if not isinstance(note, str):
            continue
        if note.startswith("normalization_schema_version="):
            metadata["normalization_schema_version"] = note.split("=", 1)[1]
        elif note.startswith("normalization_status="):
            metadata["normalization_status"] = note.split("=", 1)[1]
        elif note.startswith("signer_compatibility="):
            metadata["signer_compatibility"] = note.split("=", 1)[1]
        elif note.startswith("normalization_alert="):
            metadata["normalization_alerts"].append(note.split("=", 1)[1])
        elif note.startswith("signer_blocking_category="):
            metadata["signer_blocking_category"] = note.split("=", 1)[1]
        elif note.startswith("signer_blocking_reason="):
            metadata["signer_blocking_reason"] = note.split("=", 1)[1]
        elif note.startswith("signer_blocking_term="):
            metadata["signer_blocking_term"] = note.split("=", 1)[1]
        elif note.startswith("signer_blocking_line="):
            try:
                metadata["signer_blocking_line"] = int(note.split("=", 1)[1])
            except ValueError:
                metadata["signer_blocking_line"] = None
        elif note.startswith("signer_blocking_context="):
            metadata["signer_blocking_context"] = note.split("=", 1)[1]
        elif note.startswith("adult_variant_required="):
            metadata["adult_variant_required"] = note.split("=", 1)[1].casefold() == "true"
        elif note.startswith("electronic_readiness_status="):
            metadata["electronic_readiness_status"] = note.split("=", 1)[1]
        elif note.startswith("electronic_readiness_finding="):
            metadata["electronic_readiness_findings"].append(note.split("=", 1)[1])
        elif note.startswith("norm5_result="):
            metadata["norm5_result"] = note.split("=", 1)[1]
    return metadata
