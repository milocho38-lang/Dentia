from __future__ import annotations

from typing import Any


ORTHODONTIC_RECORD_SCHEMA_VERSION = "ORTHODONTIC_RECORD_V1"


def _options(*items: tuple[str, str]) -> list[dict[str, str]]:
    return [{"code": code, "label": label} for code, label in items]


ORTHODONTIC_RECORD_SECTIONS: tuple[dict[str, Any], ...] = (
    {"key": "general", "label": "Generales / Anamnesis", "order": 1},
    {"key": "facial", "label": "Características faciales", "order": 2},
    {"key": "occlusal", "label": "Análisis oclusal y dentario", "order": 3},
    {"key": "dentoalveolar", "label": "Dentoalveolar", "order": 4},
    {"key": "articulator", "label": "Montaje de articulador", "order": 5},
    {"key": "periodontal", "label": "Análisis periodontal", "order": 6},
    {"key": "tmj_muscular", "label": "ATM y muscular", "order": 7},
    {"key": "studies", "label": "Radiografías / estudios", "order": 8},
    {"key": "airway", "label": "Vía aérea", "order": 9},
    {"key": "cephalometric", "label": "Análisis cefalométrico", "order": 10},
    {"key": "other_factors", "label": "Otros factores", "order": 11},
)


def _field(
    key: str,
    label: str,
    field_type: str,
    section: str,
    *,
    options: list[dict[str, str]] | None = None,
    pending: str | None = None,
    max_length: int = 4_000,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": field_type,
        "section": section,
        "options": options or [],
        "clinical_pending_flag": pending,
        "max_length": max_length if field_type == "text" else None,
    }


SIDE = _options(("RIGHT", "Derecha"), ("LEFT", "Izquierda"), ("NO", "No"))
PRESENCE = _options(("PRESENT", "Presencia"), ("ABSENT", "Ausencia"))
CLASS_I_III = _options(("CLASS_I", "Clase I"), ("CLASS_II", "Clase II"), ("CLASS_III", "Clase III"))
ARCH_SHAPES = _options(("SQUARE", "Cuadrado"), ("TRIANGULAR", "Triangular"), ("OVOID", "Ovoide"))
TMJ_OPTIONS = _options(
    ("NO_ALTERATION", "Sin alteración"),
    ("OPENING_CLICK", "Click de apertura"),
    ("CLOSING_CLICK", "Click de cierre"),
    ("OPENING_CREPITUS", "Crépito de apertura"),
    ("CLOSING_CREPITUS", "Crépito de cierre"),
)


ORTHODONTIC_RECORD_FIELDS: tuple[dict[str, Any], ...] = (
    _field("chief_complaint", "Motivo de consulta", "text", "general", max_length=12_000),
    _field(
        "habits",
        "Hábitos",
        "multi",
        "general",
        options=_options(
            ("DAYTIME_BRUXISM", "Bruxismo diurno"),
            ("NIGHT_BRUXISM", "Bruxismo nocturno"),
            ("ONYCHOPHAGIA", "Onicofagia"),
            ("PROLONGED_PACIFIER", "Uso prolongado de chupete"),
            ("PROLONGED_BOTTLE", "Uso prolongado de mamadera"),
            ("DIGITAL_SUCKING", "Succión digital"),
            ("TONGUE_INTERPOSITION", "Interposición lingual"),
            ("SPEECH_SOUND_DIFFICULTY", "Dificultad para articular un sonido"),
            ("CHEWING_DIFFICULTY", "Dificultad al masticar"),
            ("MOUTH_BREATHING", "Respiración bucal"),
        ),
    ),
    _field(
        "hand_radiograph_stage",
        "Radiografía de mano",
        "single",
        "general",
        options=_options(
            ("PP2", "Pp2"), ("MP3", "Mp3"), ("MP3_CAP", "Mp3 cap"),
            ("DP3U", "Dp3u"), ("PP3U", "Pp3u"), ("MP3U", "Mp3u"),
            ("RU", "Ru"), ("NONE", "Ninguna"),
        ),
    ),
    _field("williams_asymmetry", "Asimetría de Williams", "single", "facial", options=SIDE),
    _field("mandibular_deviation", "Desviación mandibular", "single", "facial", options=SIDE),
    _field("gingival_exposure", "Exposición gingival", "single", "facial", options=_options(("INCREASED", "Aumentada"), ("IDEAL", "Ideal"), ("DECREASED", "Disminuida"))),
    _field("lip_seal", "Cierre labial", "single", "facial", options=_options(("FORCED", "Forzado"), ("COMPETENT", "Competente"))),
    _field("sagittal_facial_class", "Clase facial sagital", "single", "facial", options=_options(("CLASS_I", "Clase I"), ("CLASS_II_DIV_I", "Clase II división I"), ("CLASS_II_DIV_II", "Clase II división II"), ("CLASS_III", "Clase III"))),
    _field("lower_facial_third", "Tercio inferior", "single", "facial", options=_options(("INCREASED", "Aumentado"), ("DECREASED", "Disminuido"), ("NORMAL", "Normal"))),
    _field("upper_lip", "Labio superior", "text", "facial"),
    _field("lower_lip", "Labio inferior", "text", "facial"),
    _field("chin", "Mentón", "text", "facial"),
    _field("dentition", "Dentición", "single", "occlusal", options=_options(("PRIMARY", "Temporal"), ("MIXED_PHASE_1", "Mixta 1 fase"), ("MIXED_PHASE_2", "Mixta 2 fase"), ("PERMANENT", "Permanente"))),
    _field("upper_midline", "Línea media superior", "single", "occlusal", options=_options(("CENTERED", "Centrada"), ("RIGHT", "Desviada a la derecha"), ("LEFT", "Desviada a la izquierda"))),
    _field("lower_midline", "Línea media inferior", "single", "occlusal", options=_options(("CENTERED", "Centrada"), ("RIGHT", "Desviada a la derecha"), ("LEFT", "Desviada a la izquierda"))),
    _field("left_molar_class", "Clase molar izquierda", "single", "occlusal", options=CLASS_I_III),
    _field("right_molar_class", "Clase molar derecha", "single", "occlusal", options=CLASS_I_III),
    _field("left_canine_class", "Clase canina izquierda", "single", "occlusal", options=CLASS_I_III),
    _field("right_canine_class", "Clase canina derecha", "single", "occlusal", options=CLASS_I_III),
    _field("overjet", "Overjet", "single", "occlusal", options=_options(("NORMAL", "Normal"), ("INCREASED", "Aumentada"), ("DECREASED", "Disminuida"), ("EDGE_TO_EDGE", "Vis a vis"))),
    _field("spee_curve", "Curva de Spee", "single", "occlusal", options=_options(("INCREASED", "Aumentada"), ("NORMAL", "Normal"), ("REVERSED", "Invertida"))),
    _field("overbite", "Overbite", "single", "occlusal", options=_options(("OPEN_BITE", "Mordida abierta"), ("EDGE_TO_EDGE", "Vis a vis"), ("DECREASED", "Disminuido"), ("NORMAL", "Normal"), ("DEEP_BITE", "Sobremordida"))),
    _field("occlusal_plane", "Inclinación del plano oclusal", "single", "occlusal", options=_options(("NORMAL_CLASS_I", "Normal o ligera (Clase I)"), ("STEEP_CLASS_II", "Empinado, alto o divergente (Clase II)"), ("FLAT_CLASS_III", "Aplanado, horizontal o plano (Clase III)"))),
    _field("transverse_bite", "Mordida transversal", "single", "occlusal", options=_options(("NORMAL", "Normal"), ("BILATERAL_CROSSBITE", "Cruzada bilateral"), ("RIGHT_UNILATERAL_CROSSBITE", "Cruzada unilateral derecha"), ("LEFT_UNILATERAL_CROSSBITE", "Cruzada unilateral izquierda"))),
    _field("wilson_curve", "Curva de Wilson", "single", "occlusal", options=_options(("INCREASED", "Aumentada"), ("DECREASED", "Disminuida"), ("NORMAL", "Normal"))),
    _field("upper_arch_shape", "Forma de arco superior", "single", "occlusal", options=ARCH_SHAPES),
    _field("lower_arch_shape", "Forma de arco inferior", "single", "occlusal", options=ARCH_SHAPES),
    _field("upper_dental_discrepancy", "Discrepancia dental superior", "text", "dentoalveolar", pending="CLINICAL_DEFINITION_PENDING"),
    _field("lower_dental_discrepancy", "Discrepancia dental inferior", "text", "dentoalveolar", pending="CLINICAL_DEFINITION_PENDING"),
    _field("posterior_discrepancy", "Discrepancia posterior", "boolean", "dentoalveolar"),
    _field("bolton_index", "Índice de Bolton", "text", "dentoalveolar", pending="CLINICAL_DEFINITION_PENDING"),
    _field("supernumerary_or_agenesis", "Supernumerario o agenesia", "text", "dentoalveolar"),
    _field("absent_or_retained_teeth", "Ausentes o retenidos", "text", "dentoalveolar"),
    _field("second_molars", "Segundos molares", "single", "dentoalveolar", options=_options(("INTRAOSSEOUS_EVOLUTION", "En evolución intraósea"), ("EXTRAOSSEOUS_EVOLUTION", "En evolución extraósea"), ("ERUPTED", "Erupcionados"))),
    _field("third_molars", "Terceros molares", "single", "dentoalveolar", options=_options(("INTRAOSSEOUS_EVOLUTION", "En evolución intraósea"), ("EXTRAOSSEOUS_EVOLUTION", "En evolución extraósea"), ("ERUPTED", "Erupcionado"), ("IMPACTED", "Impactado"))),
    _field("occlusal_trauma", "Trauma oclusal", "text", "dentoalveolar"),
    _field("wear_facets", "Facetas de desgaste", "text", "dentoalveolar"),
    _field("panoramic_radiograph_findings", "Información relevante de radiografía panorámica", "text", "dentoalveolar", max_length=12_000),
    _field("rc_oc_discrepancy", "Discrepancia RC / OC", "single", "articulator", options=_options(("ABSENT", "Ausente"), ("MILD", "Leve"), ("MODERATE", "Moderada"), ("MARKED", "Marcada"))),
    _field("premature_contact", "Contacto prematuro", "text", "articulator"),
    _field("molar_rotation", "Rotación de molares", "text", "articulator"),
    _field("molar_torque", "Torque molar", "text", "articulator"),
    _field("cpi_right", "CPI derecho", "text", "articulator", pending="CLINICAL_DEFINITION_PENDING"),
    _field("cpi_left", "CPI izquierdo", "text", "articulator", pending="CLINICAL_DEFINITION_PENDING"),
    _field("cpi_transverse", "CPI transversal", "text", "articulator", pending="CLINICAL_DEFINITION_PENDING"),
    _field("oral_hygiene", "Higiene", "single", "periodontal", options=_options(("GOOD", "Buena"), ("REGULAR", "Regular"), ("POOR", "Mala"))),
    _field("periodontal_biotype", "Biotipo periodontal", "single", "periodontal", options=_options(("THIN", "Fino"), ("THICK", "Grueso"))),
    _field("recessions", "Recesiones", "single", "periodontal", options=PRESENCE),
    _field("gingival_hyperplasia", "Hiperplasia gingival", "single", "periodontal", options=PRESENCE),
    _field("root_prominence", "Eminencia radicular", "single", "periodontal", options=PRESENCE),
    _field("lingual_frenum", "Frenillo lingual", "single", "periodontal", options=_options(("NORMAL", "Normal"), ("SHORT", "Corto"))),
    _field("upper_median_frenum", "Frenillo medio superior", "single", "periodontal", options=_options(("NORMAL_INSERTION", "Inserción normal"), ("LOW_INSERTION", "Inserción baja"), ("TRANSFIXING_INSERTION", "Inserción transfixiante"))),
    _field("lower_median_frenum", "Frenillo medio inferior", "single", "periodontal", options=_options(("NORMAL_INSERTION", "Inserción normal"), ("HIGH_INSERTION", "Inserción alta"))),
    _field("lateral_frena", "Frenillos laterales", "single", "periodontal", options=_options(("NORMAL_INSERTION", "Inserción normal"), ("ALTERED_INSERTION", "Inserción alterada"))),
    _field("periodontal_others", "Otros hallazgos periodontales", "text", "periodontal"),
    _field("mandibular_manipulation", "Manipulación mandibular", "single", "tmj_muscular", options=_options(("EASY", "Fácil"), ("MEDIUM", "Media"), ("DIFFICULT", "Difícil"), ("OPENING_LIMITATION", "Limitación a la apertura"))),
    _field("right_tmj", "ATM derecha", "multi", "tmj_muscular", options=TMJ_OPTIONS, pending="CLINICAL_SELECTION_MODE_PENDING"),
    _field("left_tmj", "ATM izquierda", "multi", "tmj_muscular", options=TMJ_OPTIONS, pending="CLINICAL_SELECTION_MODE_PENDING"),
    _field("muscle_palpation", "Palpación muscular", "multi", "tmj_muscular", options=_options(("TEMPORAL", "Temporal"), ("MASSETER", "Masetero"), ("SCM", "ECM"), ("INTRAMEATAL", "Intrameato")), pending="CLINICAL_DEFINITION_PENDING"),
    _field("opening_pattern", "Patrón de apertura", "multi", "tmj_muscular", options=_options(("HYPERLAXITY", "Hiperlaxitud"), ("LIMITED", "Limitada"), ("MAX_WITHOUT_PAIN", "Máxima sin dolor"), ("MAX_WITH_PAIN", "Máxima con dolor"), ("CENTERED", "Centrada"), ("RIGHT_DEVIATION", "Desviación a la derecha"), ("LEFT_DEVIATION", "Desviación a la izquierda")), pending="CLINICAL_SELECTION_MODE_PENDING"),
    _field("cbct_diagnosis", "Dx CBCT", "text", "studies"),
    _field("other_studies", "Otro estudio", "text", "studies"),
    _field("mri_diagnosis", "Dx RNM", "text", "studies"),
    _field("breathing_type", "Tipo de respiración", "text", "airway", pending="CLINICAL_OPTIONS_PENDING"),
    _field("sleep", "Sueño", "text", "airway", pending="CLINICAL_OPTIONS_PENDING"),
    _field("airway_others", "Otros hallazgos de vía aérea", "text", "airway", pending="CLINICAL_OPTIONS_PENDING"),
    _field("ricketts_type", "Ricketts — Tipo", "single", "cephalometric", options=_options(("BRACHYFACIAL", "Braquifacial"), ("MESOFACIAL", "Mesofacial"), ("DOLICHOFACIAL", "Dolicofacial"))),
    _field("ricketts_level", "Ricketts — Nivel", "single", "cephalometric", options=_options(("MILD", "Leve"), ("MODERATE", "Moderado"), ("SEVERE", "Severo"))),
    _field("jarabak_type", "Jarabak — Tipo", "multi", "cephalometric", options=_options(("COUNTERCLOCKWISE", "Antihorario"), ("NEUTRAL", "Neutro"), ("CLOCKWISE", "Horario")), pending="CLINICAL_SELECTION_MODE_PENDING"),
    _field("jarabak_level", "Jarabak — Nivel", "single", "cephalometric", options=_options(("GOOD_GROWER", "Buen crecedor"), ("POOR_GROWER", "Mal crecedor"))),
    _field("jarabak_percentage", "Jarabak — Porcentaje", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("upper_incisor_inclination", "Inclinación incisivo superior", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("lower_incisor_inclination", "Inclinación incisivo inferior", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("anb_angle", "Ángulo ANB", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("wits", "WITS", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("skeletal_class", "Clase esqueletal", "multi", "cephalometric", options=CLASS_I_III, pending="CLINICAL_SELECTION_MODE_PENDING"),
    _field("maxillary_vertical_excess", "Exceso vertical maxilar", "boolean", "cephalometric"),
    _field("lower_incisor_to_upper_stomion", "Incisivo inferior a stomion superior", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("upper_incisor_to_stomion", "Incisivo superior a stomion", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("penn_analysis", "Análisis Penn", "text", "cephalometric", pending="CLINICAL_DEFINITION_PENDING"),
    _field("symphysis_width_group_v", "Ancho sínfisis Grupo V", "single", "cephalometric", options=_options(("IDEAL", "Ideal"), ("NARROW", "Angosta"))),
    _field("determining_factors", "Otros factores determinantes", "text", "other_factors", max_length=12_000),
)

for _section in ORTHODONTIC_RECORD_SECTIONS:
    _section_fields = [
        field
        for field in ORTHODONTIC_RECORD_FIELDS
        if field["section"] == _section["key"]
    ]
    for _order, _definition in enumerate(_section_fields, start=1):
        _definition["order"] = _order


ORTHODONTIC_RECORD_FIELD_KEYS = tuple(field["key"] for field in ORTHODONTIC_RECORD_FIELDS)
_FIELDS_BY_KEY = {field["key"]: field for field in ORTHODONTIC_RECORD_FIELDS}


class OrthodonticRecordSchemaError(ValueError):
    pass


def orthodontic_record_schema_payload() -> dict[str, Any]:
    return {
        "version": ORTHODONTIC_RECORD_SCHEMA_VERSION,
        "sections": [dict(section) for section in ORTHODONTIC_RECORD_SECTIONS],
        "fields": [
            {**field, "options": [dict(option) for option in field["options"]]}
            for field in ORTHODONTIC_RECORD_FIELDS
        ],
    }


def validate_orthodontic_record_content(content: dict[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(content) - set(_FIELDS_BY_KEY))
    if unknown:
        raise OrthodonticRecordSchemaError(
            f"Campos no registrados en {ORTHODONTIC_RECORD_SCHEMA_VERSION}: {', '.join(unknown)}"
        )
    normalized: dict[str, Any] = {}
    for key, raw_value in content.items():
        field = _FIELDS_BY_KEY[key]
        field_type = field["type"]
        if raw_value is None or raw_value == "" or raw_value == []:
            continue
        if field_type == "text":
            if not isinstance(raw_value, str):
                raise OrthodonticRecordSchemaError(f"{field['label']} debe ser texto.")
            value = raw_value.strip()
            if not value:
                continue
            if len(value) > field["max_length"]:
                raise OrthodonticRecordSchemaError(
                    f"{field['label']} supera la longitud permitida."
                )
            normalized[key] = value
            continue
        if field_type == "boolean":
            if not isinstance(raw_value, bool):
                raise OrthodonticRecordSchemaError(f"{field['label']} debe ser Sí o No.")
            normalized[key] = raw_value
            continue
        allowed = {option["code"] for option in field["options"]}
        if field_type == "single":
            if not isinstance(raw_value, str) or raw_value not in allowed:
                raise OrthodonticRecordSchemaError(
                    f"La opción de {field['label']} no pertenece al schema vigente."
                )
            normalized[key] = raw_value
            continue
        if field_type == "multi":
            if not isinstance(raw_value, list) or any(
                not isinstance(value, str) or value not in allowed for value in raw_value
            ):
                raise OrthodonticRecordSchemaError(
                    f"Una o más opciones de {field['label']} no pertenecen al schema vigente."
                )
            if len(raw_value) != len(set(raw_value)):
                raise OrthodonticRecordSchemaError(
                    f"{field['label']} contiene opciones duplicadas."
                )
            normalized[key] = raw_value
            continue
        raise OrthodonticRecordSchemaError(f"Tipo de campo no soportado: {field_type}.")
    return normalized


def orthodontic_record_content_snapshot(content: dict[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key, value in content.items():
        field = _FIELDS_BY_KEY[key]
        labels = {option["code"]: option["label"] for option in field["options"]}
        if field["type"] == "single":
            display_value: Any = labels[value]
        elif field["type"] == "multi":
            display_value = [labels[item] for item in value]
        elif field["type"] == "boolean":
            display_value = "Sí" if value else "No"
        else:
            display_value = value
        snapshot[key] = {
            "field_label": field["label"],
            "field_type": field["type"],
            "value": value,
            "display_value": display_value,
        }
    return snapshot


def orthodontic_record_section_progress(content: dict[str, Any]) -> dict[str, str]:
    progress: dict[str, str] = {}
    for section in ORTHODONTIC_RECORD_SECTIONS:
        keys = [
            field["key"]
            for field in ORTHODONTIC_RECORD_FIELDS
            if field["section"] == section["key"]
        ]
        completed = sum(key in content for key in keys)
        progress[section["key"]] = (
            "NOT_STARTED"
            if completed == 0
            else "COMPLETED"
            if completed == len(keys)
            else "IN_PROGRESS"
        )
    return progress
