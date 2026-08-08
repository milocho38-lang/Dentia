"""Build C019A.4-LIB1-NORM5 electronic-readiness library package."""
from __future__ import annotations

import difflib
import json
import re
from collections import Counter
from pathlib import Path

from app.services.consent_library_normalization import (
    NORM5_SCHEMA_VERSION,
    NORMALIZED_CONTENT_FIELD,
    assess_electronic_readiness,
    sha256_text,
)


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v3" / "documents.json"
TARGET_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v4" / "documents.json"
REPORT_JSON = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM5-Report.json"
REPORT_MD = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM5-Report.md"
PACKAGE_VERSION = "LIB1_NORM_V2_NORM5_ELECTRONIC_READINESS"

PROCEDURE_BLANK_RE = re.compile(r"\bPROCEDIMIENTO(?:\(S\))?\s*:?\s*_{3,}", re.IGNORECASE)
OXIDO_PREAMBLE_RE = re.compile(
    r"CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO\s+Yo\s+_{3,}\s*,\s*RUT:\s*_{3,}\s*"
    r"como paciente o en calidad de tutor legal del paciente\s+_{3,}\s*,\s*",
    re.IGNORECASE,
)
OXIDO_SIGNATURE_RE = re.compile(r"\s*Firma\s+_{3,}\s+CURICÓ\s+_{3,}\s+de\s+_{3,}\s*del\s+_{3,}\s*$", re.IGNORECASE)
CERT_ASISTENCIA_RE = re.compile(
    r"CERTIFICADO DE ASISTENCIA\s+Este certificado indica que el usuario\s+_{3,}\s*,\s*"
    r"rut:\s*_{3,}\s*es paciente activo de la clínica y asistió:\s*"
    r"El dia\s+_{2,}\s+de\s+_{3,}\s+del\s+_{3,}",
    re.IGNORECASE,
)
URGENCIA_DIAGNOSIS_RE = re.compile(r"(?:posible|p\s*o\s*s\s*i\s*b\s*l\s*e)\s+diagn[oó]stico\s*_{3,}", re.IGNORECASE)
URGENCIA_TREATMENT_RE = re.compile(r"Y\s+p a r a s o l u c i o n a r m i u r g e n c i a a c e p t o e l t r a t a m i e n t o d e\s+_{3,}\.", re.IGNORECASE)

PROCEDURE_VARIABLE_CODES = {
    "CONS_CIRUGIA",
    "CONS_ENDODONCIA",
    "CONS_IMPLANTOLOGIA",
    "CONS_PROTESIS_FIJA",
    "CONS_PROTESIS_REMOVIBLE",
    "CONS_REHAB_IMPLANTES",
}
NEEDS_STRUCTURED_FIELD_CODES = {"RECHAZO_TRATAMIENTO"}
NEEDS_HUMAN_REVIEW_CODES = {"CONS_APROBACION_ESTETICA"}


def _diff(before: str, after: str, code: str, country: str, old_version: int, new_version: int) -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"{code}-{country}-v{old_version}",
            tofile=f"{code}-{country}-v{new_version}",
            lineterm="",
        )
    )


def _append_norm5_notes(version: dict, *, result: str, readiness_status: str, findings: list[str], signer: str, changes: list[str]) -> list[str]:
    notes = [
        *version.get("transformation_notes", []),
        f"normalization_schema_version={NORM5_SCHEMA_VERSION}",
        f"signer_compatibility={signer}",
        f"normalization_status={'BLOCKED' if readiness_status == 'BLOCKED' else 'PASS'}",
        f"norm5_result={result}",
        f"electronic_readiness_status={readiness_status}",
        *[f"electronic_readiness_finding={finding}" for finding in findings],
        *[f"norm5_change={change}" for change in changes],
        "source_text preserved without mutation",
    ]
    return notes


def _oxido_content(content: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    revised, count = OXIDO_PREAMBLE_RE.subn("CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO ", content)
    if count:
        changes.append("removed_manual_identity_preamble")
    revised, count = OXIDO_SIGNATURE_RE.subn("", revised)
    if count:
        changes.append("removed_manual_signature_and_date_block")
    revised, count = re.subn(r"a mi o a mi tutor legal", "a mí o al adulto responsable", revised, flags=re.IGNORECASE)
    if count:
        changes.append("normalized_tutor_legal_term")
    revised = revised.strip() + "\n"
    return revised, changes


def _procedure_content(content: str) -> tuple[str, list[str]]:
    revised, count = PROCEDURE_BLANK_RE.subn("Procedimientos: {{procedures.list}}", content)
    return revised, ["procedure_blank_replaced_with_procedures.list"] if count else []


def _cert_asistencia_content(content: str) -> tuple[str, list[str]]:
    replacement = (
        "CERTIFICADO DE ASISTENCIA Este certificado indica que el usuario {{patient.full_name}}, "
        "identificado como {{patient.document_type}} {{patient.document_number}}, es paciente activo "
        "de la clínica y asistió el {{document.clinical_date}}"
    )
    revised, count = CERT_ASISTENCIA_RE.subn(replacement, content)
    return revised, ["attendance_manual_identity_and_date_replaced_with_structured_variables"] if count else []


def _urgencia_content(content: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    revised, count = URGENCIA_DIAGNOSIS_RE.subn("posible diagnóstico: {{treatment.diagnosis}}.", content)
    if count:
        changes.append("diagnosis_blank_replaced_with_treatment.diagnosis")
    revised, count = URGENCIA_TREATMENT_RE.subn("Y para solucionar mi urgencia acepto el tratamiento: {{treatment.description}}.", revised)
    if count:
        changes.append("treatment_blank_replaced_with_treatment.description")
    return revised, changes


def _classify_and_transform(document: dict, version: dict) -> tuple[dict, dict]:
    code = document["code"]
    original = version["content"]
    signer = version.get("signer_compatibility") or document["signer_scope"]
    result = "NO_CHANGE"
    changes: list[str] = []
    revised = original

    if code == "CONS_OXIDO_NITROSO":
        signer = "PATIENT_OR_RESPONSIBLE_ADULT"
        revised, changes = _oxido_content(original)
        result = "SAFE_NORMALIZED"
    elif code in PROCEDURE_VARIABLE_CODES:
        revised, changes = _procedure_content(original)
        if changes:
            result = "SAFE_NORMALIZED"
    elif code == "CONS_URGENCIA":
        revised, changes = _urgencia_content(original)
        if changes:
            result = "SAFE_NORMALIZED"
    elif code == "CERT_ASISTENCIA":
        revised, changes = _cert_asistencia_content(original)
        if changes:
            result = "SAFE_NORMALIZED"
    elif code in NEEDS_STRUCTURED_FIELD_CODES:
        result = "NEEDS_STRUCTURED_FIELD"
    elif code in NEEDS_HUMAN_REVIEW_CODES:
        result = "NEEDS_HUMAN_REVIEW"

    assessment = assess_electronic_readiness(revised, country_code=version["country_code"], document_type=document["document_type"], signer_compatibility=signer)
    finding_notes = [f"{item.severity}:{item.code}" for item in assessment.findings]
    changed = bool(changes) or signer != (version.get("signer_compatibility") or document["signer_scope"])
    should_create_version = changed

    new_version = dict(version)
    new_version["norm5_result"] = result
    new_version["electronic_readiness_status"] = assessment.status
    new_version["electronic_readiness_findings"] = finding_notes
    if should_create_version:
        new_version["version_number"] = int(version["version_number"]) + 1
        new_version["publication_status"] = "READY_FOR_REVIEW"
        new_version["legal_review_status"] = "PENDING_EQUIVALENCE_REVIEW"
        new_version["clinical_review_status"] = "PENDING_EQUIVALENCE_REVIEW"
        new_version["reviewed_countries"] = []
        new_version["content"] = revised
        new_version[NORMALIZED_CONTENT_FIELD] = revised
        new_version["normalized_content_sha256"] = sha256_text(revised)
        new_version["normalization_schema_version"] = NORM5_SCHEMA_VERSION
        new_version["signer_compatibility"] = signer
        new_version["normalization_status"] = "BLOCKED" if assessment.status == "BLOCKED" else "PASS"
        new_version["transformation_notes"] = _append_norm5_notes(
            version,
            result=result,
            readiness_status=assessment.status,
            findings=finding_notes,
            signer=signer,
            changes=changes,
        )
        new_version["review_notes"] = "NORM5: adaptación segura para visualización electrónica; pendiente revisión humana de equivalencia antes de instalación oficial."

    row = {
        "code": code,
        "title": document["title"],
        "document_type": document["document_type"],
        "country_code": version["country_code"],
        "previous_version_number": version["version_number"],
        "new_version_number": new_version["version_number"],
        "created_new_version": should_create_version,
        "signer_before": version.get("signer_compatibility") or document["signer_scope"],
        "signer_after": signer,
        "norm5_result": result,
        "electronic_readiness_status": assessment.status,
        "electronic_readiness_findings": finding_notes,
        "changes": changes,
        "source_text_sha256_before": version["source_text_sha256"],
        "source_text_sha256_after": new_version["source_text_sha256"],
        "normalized_content_sha256_before": version["normalized_content_sha256"],
        "normalized_content_sha256_after": new_version["normalized_content_sha256"],
        "source_text_preserved": version["source_text"] == new_version["source_text"],
        "diff": _diff(original, revised, code, version["country_code"], version["version_number"], new_version["version_number"]) if should_create_version else "",
    }
    return new_version, row


def _document_signer_scope(document: dict, versions: list[dict]) -> str:
    if document["code"] == "CONS_OXIDO_NITROSO":
        return "PATIENT_OR_RESPONSIBLE_ADULT"
    return document["signer_scope"]


def build_package(source_path: Path = SOURCE_PACKAGE) -> tuple[dict, dict]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    output = {key: value for key, value in source.items() if key != "documents"}
    output["package_version"] = PACKAGE_VERSION
    output["normalization_schema_version"] = NORM5_SCHEMA_VERSION
    output["patient_facing_content_field"] = NORMALIZED_CONTENT_FIELD
    output["source_text_contract"] = "source_text is immutable provenance text and must never be rendered to patients."
    output["normalized_content_contract"] = "content and normalized_content_markdown are the only patient-facing markdown fields."
    output["documents"] = []
    rows: list[dict] = []
    signer_policy_reviews: list[dict] = []

    for source_document in source["documents"]:
        versions: list[dict] = []
        document_rows: list[dict] = []
        for source_version in source_document["versions"]:
            new_version, row = _classify_and_transform(source_document, source_version)
            versions.append(new_version)
            rows.append(row)
            document_rows.append(row)
            if row["signer_before"] != row["signer_after"]:
                signer_policy_reviews.append(row)
        document = {
            **source_document,
            "source_package_version": PACKAGE_VERSION,
            "signer_scope": _document_signer_scope(source_document, versions),
            "versions": versions,
        }
        output["documents"].append(document)

    if any(not row["source_text_preserved"] for row in rows):
        raise RuntimeError("NORM5 attempted to mutate source_text")
    if len(output["documents"]) != 35 or sum(len(item["versions"]) for item in output["documents"]) != 70:
        raise RuntimeError("NORM5 must keep the full 35 document / 70 variant inventory")

    result_counts = Counter(row["norm5_result"] for row in rows)
    readiness_counts = Counter(row["electronic_readiness_status"] for row in rows)
    new_versions = [row for row in rows if row["created_new_version"]]
    report = {
        "schema_version": NORM5_SCHEMA_VERSION,
        "package_version": PACKAGE_VERSION,
        "source_package": str(source_path),
        "target_package": str(TARGET_PACKAGE),
        "documents": len(output["documents"]),
        "versions": len(rows),
        "source_file_sha256": source["source_file_sha256"],
        "signer_policy_reviews": signer_policy_reviews,
        "signer_policy_changes": signer_policy_reviews,
        "result_counts": dict(result_counts),
        "readiness_counts": dict(readiness_counts),
        "new_versions_count": len(new_versions),
        "new_versions": new_versions,
        "safe_normalized": [row for row in rows if row["norm5_result"] == "SAFE_NORMALIZED"],
        "needs_structured_field": [row for row in rows if row["norm5_result"] == "NEEDS_STRUCTURED_FIELD"],
        "needs_human_review": [row for row in rows if row["norm5_result"] == "NEEDS_HUMAN_REVIEW"],
        "blocked": [row for row in rows if row["electronic_readiness_status"] == "BLOCKED"],
        "rut_co_audit": [row for row in rows if row["country_code"] == "CO" and any("rut_in_colombia_variant" in item for item in row["electronic_readiness_findings"])],
        "tutor_legal_audit": [row for row in rows if any("generic_tutor_legal_present" in item for item in row["electronic_readiness_findings"])],
        "underscore_audit": [row for row in rows if any("manual_blank_present" in item for item in row["electronic_readiness_findings"])],
        "items": rows,
    }
    return output, report


def write_outputs(package: dict, report: dict) -> None:
    TARGET_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PACKAGE.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# C019A.4-LIB1-NORM5 — Normalización electrónica segura",
        "",
        "NORM5 crea un paquete inmutable v4 desde v3. Limpia artefactos administrativos seguros, conserva `source_text` y bloquea las variantes ambiguas para diseño/revisión posterior.",
        "",
        f"- Esquema: `{report['schema_version']}`",
        f"- Documentos: {report['documents']}",
        f"- Variantes: {report['versions']}",
        f"- Nuevas versiones: {report['new_versions_count']}",
        f"- Resultados: `{report['result_counts']}`",
        f"- Aptitud electrónica: `{report['readiness_counts']}`",
        "",
        "## Cambios de signer policy",
        "",
        "| Código | País | Versión | Antes | Después |",
        "|---|---|---:|---|---|",
    ]
    for row in report["signer_policy_changes"]:
        lines.append(f"| `{row['code']}` | {row['country_code']} | {row['previous_version_number']} → {row['new_version_number']} | `{row['signer_before']}` | `{row['signer_after']}` |")
    lines.extend([
        "",
        "## Nuevas versiones",
        "",
        "| Código | País | Versión | Resultado | Aptitud | Cambios |",
        "|---|---|---:|---|---|---|",
    ])
    for row in report["new_versions"]:
        lines.append(
            f"| `{row['code']}` | {row['country_code']} | {row['previous_version_number']} → {row['new_version_number']} | "
            f"`{row['norm5_result']}` | `{row['electronic_readiness_status']}` | {', '.join(row['changes'])} |"
        )
    lines.extend([
        "",
        "## Bloqueadas",
        "",
        "| Código | País | Motivos |",
        "|---|---|---|",
    ])
    for row in report["blocked"]:
        lines.append(f"| `{row['code']}` | {row['country_code']} | {', '.join(row['electronic_readiness_findings'])} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    package, report = build_package()
    write_outputs(package, report)
    print(json.dumps({key: value for key, value in report.items() if key not in {"items", "new_versions", "safe_normalized", "blocked", "needs_structured_field", "needs_human_review"}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
