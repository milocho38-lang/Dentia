"""Build the immutable responsible-adult wording revision for C019A.4-SIGNER1-FIX2."""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v2" / "documents.json"
TARGET_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v3" / "documents.json"
REPORT_JSON = ROOT / "DOCS" / "product" / "C019A4-SIGNER1-FIX2-Responsible-Adult-Normalization-Report.json"
REPORT_MD = ROOT / "DOCS" / "product" / "C019A4-SIGNER1-FIX2-Responsible-Adult-Normalization-Report.md"
PACKAGE_VERSION = "LIB1_NORM_V2_SIGNER1_FIX2"
PHRASE = re.compile(r"paciente o tutor legal", re.IGNORECASE)
REPLACEMENT = "paciente o adulto responsable"
TARGET_SCOPES = {"PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_package(source_path: Path = SOURCE_PACKAGE) -> tuple[dict, dict]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    output = {**source, "package_version": PACKAGE_VERSION, "documents": []}
    rows: list[dict] = []
    patient_or_responsible_count = 0

    for source_document in source["documents"]:
        document = {**source_document, "source_package_version": PACKAGE_VERSION}
        scope = document["signer_scope"]
        if scope == "PATIENT_OR_RESPONSIBLE_ADULT":
            patient_or_responsible_count += 1
        versions = []
        for source_version in source_document["versions"]:
            version = dict(source_version)
            original = source_version["content"]
            revised, replacements = PHRASE.subn(REPLACEMENT, original)
            analyzed = scope in TARGET_SCOPES
            if analyzed:
                if replacements == 0:
                    raise RuntimeError(f"{document['code']} {version['country_code']} no contiene la cláusula esperada")
                notes = [
                    *source_version.get("transformation_notes", []),
                    f"normalization_schema_version={PACKAGE_VERSION}",
                    "signer1_fix2=responsible_adult_term_generalization",
                    f"responsible_adult_phrase_replacements={replacements}",
                    "text_diff=paciente o tutor legal -> paciente o adulto responsable",
                ]
                version.update(
                    version_number=int(source_version["version_number"]) + 1,
                    publication_status="READY_FOR_REVIEW",
                    legal_review_status="PENDING_EQUIVALENCE_REVIEW",
                    clinical_review_status="PENDING_EQUIVALENCE_REVIEW",
                    reviewed_countries=[],
                    content=revised,
                    normalized_content_markdown=revised,
                    normalized_content_sha256=_sha256(revised),
                    normalization_schema_version=PACKAGE_VERSION,
                    transformation_notes=notes,
                    review_notes=(
                        "SIGNER1-FIX2: generalización exclusiva del término del firmante para admitir adulto responsable. "
                        "Pendiente revisión humana de equivalencia; no se modificaron riesgos, garantías ni contenido clínico."
                    ),
                )
            versions.append(version)
            if analyzed:
                diff = "\n".join(
                    difflib.unified_diff(
                        original.splitlines(),
                        revised.splitlines(),
                        fromfile=f"{document['code']}-v{source_version['version_number']}",
                        tofile=f"{document['code']}-v{version['version_number']}",
                        lineterm="",
                    )
                )
                rows.append(
                    {
                        "code": document["code"],
                        "title": document["title"],
                        "signer_scope": scope,
                        "country_code": version["country_code"],
                        "previous_version_number": source_version["version_number"],
                        "new_version_number": version["version_number"],
                        "replacements": replacements,
                        "source_text_sha256_before": source_version["source_text_sha256"],
                        "source_text_sha256_after": version["source_text_sha256"],
                        "normalized_content_sha256_before": source_version["normalized_content_sha256"],
                        "normalized_content_sha256_after": version["normalized_content_sha256"],
                        "legal_review_status": version["legal_review_status"],
                        "clinical_review_status": version["clinical_review_status"],
                        "diff": diff,
                    }
                )
        document["versions"] = versions
        output["documents"].append(document)

    if patient_or_responsible_count != 13:
        raise RuntimeError(f"Se esperaban 13 plantillas PATIENT_OR_RESPONSIBLE_ADULT; se encontraron {patient_or_responsible_count}")
    if any(row["source_text_sha256_before"] != row["source_text_sha256_after"] for row in rows):
        raise RuntimeError("El texto fuente histórico fue modificado")
    report = {
        "schema_version": PACKAGE_VERSION,
        "source_package": str(source_path),
        "target_package": str(TARGET_PACKAGE),
        "patient_or_responsible_adult_documents_analyzed": patient_or_responsible_count,
        "responsible_adult_required_documents_analyzed": len({row["code"] for row in rows if row["signer_scope"] == "RESPONSIBLE_ADULT_REQUIRED"}),
        "documents_revised": len({row["code"] for row in rows}),
        "country_versions_revised": len(rows),
        "review_status": "PENDING_EQUIVALENCE_REVIEW",
        "items": rows,
    }
    return output, report


def write_outputs(package: dict, report: dict) -> None:
    TARGET_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PACKAGE.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# C019A.4-SIGNER1-FIX2 — Revisión de lenguaje para adulto responsable",
        "",
        "Esta revisión crea versiones nuevas; conserva literalmente `source_text` y sus hashes. Ninguna variante queda aprobada automáticamente.",
        "",
        f"- Plantillas `PATIENT_OR_RESPONSIBLE_ADULT` analizadas: {report['patient_or_responsible_adult_documents_analyzed']}",
        f"- Plantillas `RESPONSIBLE_ADULT_REQUIRED` analizadas: {report['responsible_adult_required_documents_analyzed']}",
        f"- Documentos revisados: {report['documents_revised']}",
        f"- Variantes CO/CL revisadas: {report['country_versions_revised']}",
        f"- Estado: `{report['review_status']}`",
        "",
        "## Cambios propuestos",
        "",
        "| Código | País | Flujo | Versión | Reemplazos | Fuente inmutable |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in report["items"]:
        lines.append(
            f"| `{row['code']}` | {row['country_code']} | `{row['signer_scope']}` | "
            f"{row['previous_version_number']} → {row['new_version_number']} | {row['replacements']} | Sí |"
        )
    lines.extend([
        "",
        "## Diff aprobado para revisión humana",
        "",
        "En todas las ocurrencias se propone exclusivamente:",
        "",
        "```diff",
        "- paciente o tutor legal",
        "+ paciente o adulto responsable",
        "```",
        "",
        "Los diffs completos, hashes anteriores/nuevos y conteos están en el informe JSON asociado.",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    package, report = build_package()
    write_outputs(package, report)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
