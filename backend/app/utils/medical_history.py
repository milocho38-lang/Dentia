from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


LEGACY_MEDICAL_HISTORY_TYPES = frozenset({
    "hipertensión",
    "enfermedad cardiovascular",
    "diabetes",
    "trastorno de coagulación",
    "enfermedad respiratoria",
    "enfermedad renal",
    "enfermedad hepática",
    "enfermedad neurológica",
    "inmunosupresión",
    "cáncer",
    "hospitalización",
    "cirugía",
    "transfusión",
    "prótesis o dispositivo",
    "embarazo",
    "lactancia",
    "otro",
})


class MedicalHistoryRecord(Protocol):
    type: str
    present: str
    status: str
    source: str | None


def _normalized(value: object | None) -> str:
    return str(value or "").strip().casefold()


def is_current_positive_medical_history(record: MedicalHistoryRecord) -> bool:
    """Return whether a row represents a currently positive clinical antecedent."""
    return _normalized(record.present) == "si" and _normalized(record.status) == "activo"


def is_legacy_medical_history_questionnaire(
    records: Iterable[MedicalHistoryRecord],
) -> bool:
    """Conservatively identify the complete fixed 17-question legacy form."""
    items = list(records)
    sources = {_normalized(item.source) for item in items if item.source}
    if any(source.startswith("legacy") for source in sources):
        return True
    types = {_normalized(item.type) for item in items}
    return LEGACY_MEDICAL_HISTORY_TYPES.issubset(types)


def is_legacy_medical_history_record(
    record: MedicalHistoryRecord,
    questionnaire_records: Iterable[MedicalHistoryRecord],
) -> bool:
    return (
        is_legacy_medical_history_questionnaire(questionnaire_records)
        and _normalized(record.type) in LEGACY_MEDICAL_HISTORY_TYPES
    )


def medical_history_response_label(record: MedicalHistoryRecord) -> str:
    present = _normalized(record.present)
    if present == "si":
        return "Sí" if _normalized(record.status) == "activo" else "Sí · Registro inactivo"
    if present == "no":
        return "No"
    return "Información no confirmada"


def medical_history_type_label(value: object) -> str:
    text = str(value).strip()
    normalized = _normalized(text)
    return normalized.capitalize() if normalized in LEGACY_MEDICAL_HISTORY_TYPES else text
