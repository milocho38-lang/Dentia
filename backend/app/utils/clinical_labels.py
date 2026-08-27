SURFACE_LABELS = {
    "VESTIBULAR": "Vestibular",
    "LINGUAL": "Lingual",
    "PALATAL": "Palatina",
    "PALATINE": "Palatina",
    "MESIAL": "Mesial",
    "DISTAL": "Distal",
    "OCCLUSAL": "Oclusal",
    "INCISAL": "Incisal",
    "CERVICAL": "Cervical",
}

LEGACY_CLINICAL_FIELD_LABELS = {
    "tobacco": "Tabaco",
    "alcohol": "Alcohol",
    "substances": "Consumo de sustancias",
    "bruxism": "Bruxismo",
    "oral_hygiene": "Higiene oral",
    "brushing_frequency": "Frecuencia de cepillado",
    "dental_floss": "Uso de seda dental",
    "sugary_diet": "Consumo de azúcares",
    "others": "Otros hábitos",
    "last_visit": "Última visita",
    "previous_treatments": "Tratamientos previos",
    "orthodontics": "Ortodoncia",
    "implants": "Implantes",
    "surgeries": "Cirugías",
    "trauma": "Traumatismos",
    "bleeding": "Sangrado",
    "sensitivity": "Sensibilidad",
    "pain": "Dolor",
    "oral_habits": "Hábitos orales",
    "previous_experiences": "Experiencias odontológicas previas",
    "observations": "Observaciones",
}

EVOLUTION_STATUS_LABELS = {
    "DRAFT": "Evolución en borrador",
    "SIGNED": "Evolución firmada",
    "VOIDED_BY_COMPENSATING_RECORD": "Evolución anulada",
    "VOIDED": "Evolución anulada",
}

SEX_LABELS = {
    "FEMALE": "Femenino",
    "FEMENINO": "Femenino",
    "MALE": "Masculino",
    "MASCULINO": "Masculino",
    "OTHER": "Otro",
    "OTRO": "Otro",
    "NOT_REPORTED": "No informa",
    "NO INFORMA": "No informa",
}

TREATMENT_STATUS_LABELS = {
    "DRAFT": "Borrador",
    "BUDGETED": "Presupuestado",
    "APPROVED": "Aprobado",
    "IN_PROGRESS": "En ejecución",
    "PAUSED": "Pausado",
    "FINALIZED": "Finalizado",
    "CANCELLED": "Cancelado",
    "CANCELED": "Cancelado",
    "PENDING": "Pendiente",
    "SCHEDULED": "Agendado",
    "DONE": "Realizado",
    "COMPLETED": "Realizado",
}

ZONE_LABELS = {
    "UPPER_ARCH": "Arcada superior",
    "LOWER_ARCH": "Arcada inferior",
    "FULL_MOUTH": "Boca completa",
    "QUADRANT_1": "Cuadrante 1",
    "QUADRANT_2": "Cuadrante 2",
    "QUADRANT_3": "Cuadrante 3",
    "QUADRANT_4": "Cuadrante 4",
    "ANTERIOR": "Sector anterior",
    "POSTERIOR": "Sector posterior",
}


def humanize_clinical_code(value: object | None, fallback: str = "No registrado") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return text.replace("_", " ").lower().capitalize()


def surface_label(value: object | None) -> str:
    if value is None:
        return "Superficie no especificada"
    code = str(value).strip().upper()
    return SURFACE_LABELS.get(code, humanize_clinical_code(code))


def legacy_clinical_field_label(value: object) -> str:
    key = str(value).strip()
    return LEGACY_CLINICAL_FIELD_LABELS.get(key, humanize_clinical_code(key))


def humanize_legacy_value(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.upper()
    if normalized in {"YES", "TRUE", "SI", "SÍ"}:
        return "Sí"
    if normalized in {"NO", "FALSE"}:
        return "No"
    return text


def evolution_status_label(value: object | None) -> str:
    code = str(value or "").strip().upper()
    return EVOLUTION_STATUS_LABELS.get(code, humanize_clinical_code(code))


def sex_label(value: object | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "No registrado"
    return SEX_LABELS.get(text.upper(), text)


def treatment_status_label(value: object | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "No registrado"
    return TREATMENT_STATUS_LABELS.get(text.upper(), text)


def zone_label(value: object | None) -> str | None:
    if value is None:
        return None
    code = str(value).strip().upper()
    return ZONE_LABELS.get(code, humanize_clinical_code(code))
