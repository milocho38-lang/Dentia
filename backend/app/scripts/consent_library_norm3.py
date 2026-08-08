from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from app.services.consent_library_normalization import (
    NORM3_SCHEMA_VERSION,
    NORMALIZED_CONTENT_FIELD,
    normalize_patient_content_v2,
    sha256_text,
)


ROOT = Path(__file__).resolve().parents[3]
V1_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v1" / "documents.json"
V2_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v2" / "documents.json"
REPORT_JSON = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Report.json"
REPORT_MD = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Human-Review.md"
REPORT_HTML = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM3-Human-Review.html"


def _status_for_report(normalization_status: str, signer_compatibility: str, document_type: str) -> str:
    if normalization_status == "BLOCKED":
        return "BLOCKED"
    if document_type != "INFORMED_CONSENT" or signer_compatibility != "ADULT_SELF":
        return "BLOCKED"
    return "NEEDS_REVIEW"


def _document_signer_scope(document_type: str, signer_compatibility: str) -> str:
    if signer_compatibility == "NO_PATIENT_SIGNATURE":
        return "NO_SIGNATURE_REQUIRED"
    if signer_compatibility == "FUTURE_WORKFLOW":
        return "ADULT_SELF"
    return signer_compatibility


def build_norm3_package(v1_path: Path = V1_PACKAGE) -> tuple[dict, dict]:
    source = json.loads(v1_path.read_text(encoding="utf-8"))
    output = {key: value for key, value in source.items() if key != "documents"}
    output["package_version"] = "LIB1_NORM_V2"
    output["normalization_schema_version"] = NORM3_SCHEMA_VERSION
    output["patient_facing_content_field"] = NORMALIZED_CONTENT_FIELD
    output["source_text_contract"] = "source_text is immutable provenance text and must never be rendered to patients."
    output["normalized_content_contract"] = "content and normalized_content_markdown are the only patient-facing markdown fields."
    output["documents"] = []
    report_rows: list[dict] = []

    for document in source.get("documents", []):
        normalized_versions = []
        signer_by_version: list[str] = []
        status_by_version: list[str] = []
        for version in document.get("versions", []):
            normalization = normalize_patient_content_v2(
                version.get("content", ""),
                document_type=document["document_type"],
                signer_scope=document["signer_scope"],
            )
            signer_by_version.append(normalization.signer_compatibility)
            status_by_version.append(normalization.status)
            review_status = _status_for_report(normalization.status, normalization.signer_compatibility, document["document_type"])
            normalized_hash = sha256_text(normalization.content)
            transformation_notes = [
                *version.get("transformation_notes", []),
                *normalization.transformations,
                *(f"normalization_alert={alert}" for alert in normalization.alerts),
                *(f"representative_phrase={phrase}" for phrase in normalization.representative_phrases),
                *(f"localized_term={term}" for term in normalization.local_terms),
            ]
            normalized_versions.append(
                {
                    **version,
                    "version_number": int(version.get("version_number") or 1) + 1,
                    "publication_status": "READY_FOR_REVIEW",
                    "legal_review_status": "PENDING_EQUIVALENCE_REVIEW",
                    "clinical_review_status": "PENDING_EQUIVALENCE_REVIEW",
                    "reviewed_countries": [],
                    "content": normalization.content,
                    NORMALIZED_CONTENT_FIELD: normalization.content,
                    "normalized_content_sha256": normalized_hash,
                    "normalization_schema_version": NORM3_SCHEMA_VERSION,
                    "signer_compatibility": normalization.signer_compatibility,
                    "normalization_status": review_status,
                    "transformation_notes": transformation_notes,
                    "review_notes": "NORM3: contenido para paciente separado de source_text. Requiere revisión humana de equivalencia antes de instalación oficial.",
                }
            )
            report_rows.append(
                {
                    "code": document["code"],
                    "title": document["title"],
                    "document_type": document["document_type"],
                    "country_code": version["country_code"],
                    "language_code": version["language_code"],
                    "source_pages": version.get("source_pages", []),
                    "source_text_sha256": version["source_text_sha256"],
                    "v1_normalized_content_sha256": version["normalized_content_sha256"],
                    "v2_normalized_content_sha256": normalized_hash,
                    "source_text": version.get("source_text", ""),
                    "normalized_content_v1": version.get("content", ""),
                    "normalized_content_v2": normalization.content,
                    "removed_markers": normalization.removed_markers,
                    "removed_signature_lines": normalization.removed_signature_lines,
                    "joined_paragraphs": normalization.joined_paragraphs,
                    "representative_phrases": normalization.representative_phrases,
                    "localized_terms": normalization.local_terms,
                    "signer_compatibility": normalization.signer_compatibility,
                    "normalization_status": review_status,
                    "alerts": normalization.alerts,
                    "variables": version.get("variables", []),
                    "transformations": transformation_notes,
                }
            )
        strict_signer = next((item for item in signer_by_version if item != "ADULT_SELF"), signer_by_version[0] if signer_by_version else document["signer_scope"])
        output["documents"].append(
            {
                **document,
                "source_package_version": "LIB1_NORM_V2",
                "signer_scope": _document_signer_scope(document["document_type"], strict_signer),
                "versions": normalized_versions,
                "norm3_status": "BLOCKED" if "BLOCKED" in status_by_version or strict_signer != "ADULT_SELF" or document["document_type"] != "INFORMED_CONSENT" else "NEEDS_REVIEW",
            }
        )

    report = {
        "schema_version": NORM3_SCHEMA_VERSION,
        "source_package": str(v1_path),
        "v2_package": str(V2_PACKAGE),
        "documents": len(output["documents"]),
        "versions": len(report_rows),
        "countries": {
            "CO": sum(1 for row in report_rows if row["country_code"] == "CO"),
            "CL": sum(1 for row in report_rows if row["country_code"] == "CL"),
        },
        "status_counts": {
            status: sum(1 for row in report_rows if row["normalization_status"] == status)
            for status in sorted({row["normalization_status"] for row in report_rows})
        },
        "items": report_rows,
    }
    return output, report


def _truncate(value: str, limit: int = 4500) -> str:
    return value if len(value) <= limit else value[:limit] + "\n\n[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]"


def write_reports(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# C019A4-LIB1-NORM3 — Revisión humana de normalización v2",
        "",
        "Este informe separa el texto fuente de procedencia y el contenido normalizado destinado al paciente.",
        "",
        f"- Esquema: `{report['schema_version']}`",
        f"- Documentos: {report['documents']}",
        f"- Variantes: {report['versions']}",
        f"- CO: {report['countries']['CO']}",
        f"- CL: {report['countries']['CL']}",
        f"- Estados: {report['status_counts']}",
        "",
        "## Contrato",
        "",
        "- `source_text`: evidencia de procedencia, no editable, nunca destinada al paciente.",
        "- `normalized_content_v2`: Markdown restringido para paciente, sin marcadores de página ni bloques de firma manuscrita.",
        "- Ninguna variante queda aprobada automáticamente; todas requieren revisión humana de equivalencia.",
        "",
    ]
    for item in report["items"]:
        lines.extend(
            [
                f"## {item['code']} — {item['country_code']} / {item['language_code']}",
                "",
                f"- Título: {item['title']}",
                f"- Tipo: {item['document_type']}",
                f"- Páginas fuente: {item['source_pages']}",
                f"- Estado: **{item['normalization_status']}**",
                f"- Compatibilidad firmante: `{item['signer_compatibility']}`",
                f"- Marcadores eliminados: {len(item['removed_markers'])}",
                f"- Líneas de firma eliminadas: {len(item['removed_signature_lines'])}",
                f"- Párrafos unidos: {item['joined_paragraphs']}",
                f"- Frases de representante: {item['representative_phrases'] or 'No detectadas'}",
                f"- Términos locales: {item['localized_terms'] or 'No detectados'}",
                f"- Variables: {item['variables']}",
                f"- Alertas: {item['alerts'] or 'Sin alertas técnicas'}",
                "",
                "### Texto fuente",
                "",
                "```text",
                _truncate(item["source_text"]),
                "```",
                "",
                "### Contenido normalizado v1",
                "",
                "```markdown",
                _truncate(item["normalized_content_v1"]),
                "```",
                "",
                "### Contenido normalizado v2",
                "",
                "```markdown",
                _truncate(item["normalized_content_v2"]),
                "```",
                "",
            ]
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    html_parts = [
        "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>C019A4 LIB1 NORM3</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#0f172a}article{border:1px solid #cbd5e1;border-radius:14px;padding:18px;margin:18px 0}pre{white-space:pre-wrap;background:#f8fafc;border-radius:10px;padding:12px;max-height:420px;overflow:auto}.blocked{border-left:8px solid #dc2626}.needs{border-left:8px solid #f59e0b}.pass{border-left:8px solid #16a34a}code{background:#e2e8f0;padding:2px 5px;border-radius:5px}</style></head><body>",
        "<h1>C019A4-LIB1-NORM3 — Revisión humana de normalización v2</h1>",
        f"<p><b>Documentos:</b> {report['documents']} · <b>Variantes:</b> {report['versions']} · <b>CO:</b> {report['countries']['CO']} · <b>CL:</b> {report['countries']['CL']}</p>",
    ]
    for item in report["items"]:
        klass = "blocked" if item["normalization_status"] == "BLOCKED" else "needs" if item["normalization_status"] == "NEEDS_REVIEW" else "pass"
        html_parts.extend(
            [
                f"<article class='{klass}'><h2>{html.escape(item['code'])} — {html.escape(item['country_code'])}</h2>",
                f"<p><b>{html.escape(item['title'])}</b><br>Estado: <code>{html.escape(item['normalization_status'])}</code> · Firmante: <code>{html.escape(item['signer_compatibility'])}</code></p>",
                f"<p>Marcadores eliminados: {len(item['removed_markers'])} · Líneas de firma eliminadas: {len(item['removed_signature_lines'])} · Párrafos unidos: {item['joined_paragraphs']}</p>",
                f"<p>Frases representante: {html.escape(str(item['representative_phrases']))}<br>Términos locales: {html.escape(str(item['localized_terms']))}<br>Alertas: {html.escape(str(item['alerts']))}</p>",
                "<h3>Texto fuente</h3>",
                f"<pre>{html.escape(_truncate(item['source_text']))}</pre>",
                "<h3>Contenido normalizado v1</h3>",
                f"<pre>{html.escape(_truncate(item['normalized_content_v1']))}</pre>",
                "<h3>Contenido normalizado v2</h3>",
                f"<pre>{html.escape(_truncate(item['normalized_content_v2']))}</pre></article>",
            ]
        )
    html_parts.append("</body></html>")
    REPORT_HTML.write_text("\n".join(html_parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera paquete Dentia LIB1 NORM3 v2")
    parser.add_argument("--input", default=str(V1_PACKAGE))
    parser.add_argument("--output", default=str(V2_PACKAGE))
    parser.add_argument("--reports", action="store_true")
    args = parser.parse_args()
    package, report = build_norm3_package(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.reports:
        write_reports(report)
    print(json.dumps({"ok": True, "documents": len(package["documents"]), "versions": report["versions"], "countries": report["countries"], "status_counts": report["status_counts"], "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
