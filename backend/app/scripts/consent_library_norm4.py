from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

from app.services.consent_library_normalization import (
    NORM3_SCHEMA_VERSION,
    NORMALIZED_CONTENT_FIELD,
    classify_signer_context,
    normalize_patient_content_v2,
    sha256_text,
)


ROOT = Path(__file__).resolve().parents[3]
V1_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v1" / "documents.json"
V2_PACKAGE = ROOT / "backend" / "app" / "library_data" / "consents" / "v2" / "documents.json"
REPORT_JSON = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Report.json"
REPORT_MD = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Human-Review.md"
REPORT_HTML = ROOT / "DOCS" / "product" / "C019A4-LIB1-NORM4-Human-Review.html"
PRIORITY_CODES = {
    "CONS_DESTARTRAJE_OPERATORIA",
    "CONS_OBTURACION_DIRECTA",
    "CONS_ENDODONCIA",
    "CONS_CIRUGIA",
    "CONS_IMPLANTOLOGIA",
    "CONS_ORTODONCIA",
    "CONS_PERIODONCIA",
    "CONS_URGENCIA",
}


def _status_for_report(normalization_status: str, signer_compatibility: str, document_type: str) -> str:
    if document_type != "INFORMED_CONSENT":
        return "BLOCKED"
    if signer_compatibility not in {"PATIENT_SELF", "PATIENT_OR_RESPONSIBLE_ADULT", "RESPONSIBLE_ADULT_REQUIRED", "ADULT_SELF", "ADULT_OR_REPRESENTATIVE", "REPRESENTATIVE_REQUIRED"}:
        return "BLOCKED"
    if normalization_status == "BLOCKED":
        return "BLOCKED"
    return "NEEDS_REVIEW"


def _document_signer_scope(signer_compatibility: str) -> str:
    if signer_compatibility in {"NO_SIGNATURE", "NO_PATIENT_SIGNATURE"}:
        return "NO_PATIENT_SIGNATURE"
    if signer_compatibility == "SPECIAL_WORKFLOW":
        return "SPECIAL_WORKFLOW"
    mapping = {"ADULT_SELF":"PATIENT_SELF", "ADULT_OR_REPRESENTATIVE":"PATIENT_OR_RESPONSIBLE_ADULT", "REPRESENTATIVE_REQUIRED":"RESPONSIBLE_ADULT_REQUIRED"}
    return mapping.get(signer_compatibility, signer_compatibility)


def _flow_classification(document_type: str, signer_compatibility: str) -> str:
    if signer_compatibility in {"NO_SIGNATURE", "NO_PATIENT_SIGNATURE"}:
        return "NO_PATIENT_SIGNATURE"
    if signer_compatibility == "SPECIAL_WORKFLOW" or document_type != "INFORMED_CONSENT":
        return "SPECIAL_WORKFLOW"
    if signer_compatibility in {"REPRESENTATIVE_REQUIRED", "RESPONSIBLE_ADULT_REQUIRED"}:
        return "RESPONSIBLE_ADULT_REQUIRED"
    if signer_compatibility in {"ADULT_OR_REPRESENTATIVE", "PATIENT_OR_RESPONSIBLE_ADULT"}:
        return "PATIENT_OR_RESPONSIBLE_ADULT"
    return "PATIENT_SELF"


def _human_status(row: dict) -> str:
    if row["flow_classification"] == "PATIENT_SELF" and row["normalization_status"] == "NEEDS_REVIEW":
        return "Apto para adulto en nombre propio; pendiente equivalencia humana."
    if row["flow_classification"] == "PATIENT_OR_RESPONSIBLE_ADULT":
        return "El texto contempla paciente y representante. El flujo electrónico actual solo permite adultos que actúan en nombre propio."
    if row["flow_classification"] == "RESPONSIBLE_ADULT_REQUIRED":
        return "Requiere adulto responsable o flujo pediátrico; no apto para adulto en nombre propio tal como está."
    if row["flow_classification"] == "NO_PATIENT_SIGNATURE":
        return "Documento de indicaciones/certificado. No requiere firma de consentimiento."
    return "Requiere un flujo especial todavía no implementado para consentimientos comunes."


def build_norm4_package(v1_path: Path = V1_PACKAGE) -> tuple[dict, dict]:
    source = json.loads(v1_path.read_text(encoding="utf-8"))
    output = {key: value for key, value in source.items() if key != "documents"}
    output["package_version"] = "LIB1_NORM_V2"
    output["normalization_schema_version"] = NORM3_SCHEMA_VERSION
    output["patient_facing_content_field"] = NORMALIZED_CONTENT_FIELD
    output["source_text_contract"] = "source_text is immutable provenance text and must never be rendered to patients."
    output["normalized_content_contract"] = "content and normalized_content_markdown are the only patient-facing markdown fields."
    output["documents"] = []
    report_rows: list[dict] = []
    document_rows: list[dict] = []

    for document in source.get("documents", []):
        normalized_versions = []
        version_rows: list[dict] = []
        for version in document.get("versions", []):
            normalization = normalize_patient_content_v2(
                version.get("content", ""),
                document_type=document["document_type"],
                signer_scope=document["signer_scope"],
                title=document.get("title"),
            )
            review_status = _status_for_report(normalization.status, normalization.signer_compatibility, document["document_type"])
            normalized_hash = sha256_text(normalization.content)
            transformation_notes = [
                *version.get("transformation_notes", []),
                *normalization.transformations,
                *(f"normalization_alert={alert}" for alert in normalization.alerts),
                *(f"representative_phrase={phrase}" for phrase in normalization.representative_phrases),
                *(f"localized_term={term}" for term in normalization.local_terms),
            ]
            if normalization.adult_variant_proposal:
                transformation_notes.append("adult_variant_proposal=available_in_norm4_report_only")
            version_payload = {
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
                "review_notes": "NORM4: clasificación contextual de firmantes; requiere revisión humana de equivalencia antes de instalación oficial.",
            }
            normalized_versions.append(version_payload)
            row = {
                "code": document["code"],
                "title": document["title"],
                "category": document["category"],
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
                "signer_blocking_category": normalization.signer_blocking_category,
                "signer_blocking_term": normalization.signer_blocking_term,
                "signer_blocking_line": normalization.signer_blocking_line,
                "signer_blocking_context": normalization.signer_blocking_context,
                "signer_blocking_reason": normalization.signer_blocking_reason,
                "adult_variant_required": normalization.adult_variant_required,
                "adult_variant_proposal": normalization.adult_variant_proposal,
                "flow_classification": _flow_classification(document["document_type"], normalization.signer_compatibility),
                "normalization_status": review_status,
                "alerts": normalization.alerts,
                "variables": version.get("variables", []),
                "transformations": transformation_notes,
                "priority_document": document["code"] in PRIORITY_CODES,
            }
            row["human_status"] = _human_status(row)
            report_rows.append(row)
            version_rows.append(row)
        representative_rank = {"RESPONSIBLE_ADULT_REQUIRED": 4, "REPRESENTATIVE_REQUIRED": 4, "PATIENT_OR_RESPONSIBLE_ADULT": 3, "ADULT_OR_REPRESENTATIVE": 3, "SPECIAL_WORKFLOW": 2, "NO_PATIENT_SIGNATURE": 1, "NO_SIGNATURE": 1, "PATIENT_SELF": 0, "ADULT_SELF": 0}
        strict_row = max(version_rows, key=lambda item: representative_rank.get(item["signer_compatibility"], 0))
        document_status = "BLOCKED" if any(row["normalization_status"] == "BLOCKED" for row in version_rows) else "NEEDS_REVIEW"
        document_flow = strict_row["flow_classification"]
        output["documents"].append(
            {
                **document,
                "source_package_version": "LIB1_NORM_V2",
                "signer_scope": _document_signer_scope(strict_row["signer_compatibility"]),
                "versions": normalized_versions,
                "norm3_status": document_status,
                "norm4_flow_classification": document_flow,
                "norm4_status_reason": strict_row["human_status"],
            }
        )
        document_rows.append(
            {
                "code": document["code"],
                "title": document["title"],
                "category": document["category"],
                "document_type": document["document_type"],
                "co_status": next((row["normalization_status"] for row in version_rows if row["country_code"] == "CO"), None),
                "cl_status": next((row["normalization_status"] for row in version_rows if row["country_code"] == "CL"), None),
                "signer_scope_detected": strict_row["signer_compatibility"],
                "flow_classification": document_flow,
                "blocking_term": strict_row["signer_blocking_term"],
                "blocking_line": strict_row["signer_blocking_line"],
                "blocking_context": strict_row["signer_blocking_context"],
                "blocking_cause": strict_row["signer_blocking_category"],
                "adult_variant_required": any(row["adult_variant_required"] for row in version_rows),
                "adult_variant_proposals": [row["adult_variant_proposal"] for row in version_rows if row["adult_variant_proposal"]],
                "human_status": strict_row["human_status"],
                "priority_document": document["code"] in PRIORITY_CODES,
            }
        )

    document_flow_counts = Counter(row["flow_classification"] for row in document_rows)
    document_status_counts = Counter("NEEDS_REVIEW" if row["co_status"] == "NEEDS_REVIEW" and row["cl_status"] == "NEEDS_REVIEW" else "BLOCKED" for row in document_rows)
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
        "status_counts": dict(Counter(row["normalization_status"] for row in report_rows)),
        "document_status_counts": dict(document_status_counts),
        "document_flow_counts": dict(document_flow_counts),
        "electronic_consent_candidates": [row for row in document_rows if row["flow_classification"] == "PATIENT_SELF"],
        "adult_variant_required": [row for row in document_rows if row["adult_variant_required"]],
        "priority_review": [row for row in document_rows if row["priority_document"]],
        "document_inventory": document_rows,
        "items": report_rows,
    }
    return output, report


def _truncate(value: str, limit: int = 4500) -> str:
    return value if len(value) <= limit else value[:limit] + "\n\n[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]"


def write_reports(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# C019A4-LIB1-NORM4 — Clasificación contextual de firmantes",
        "",
        "Este informe explica los 35 documentos base, separa firmante real de coincidencias de palabra y deja propuestas de variante adulta solo como borrador de equivalencia.",
        "",
        f"- Esquema: `{report['schema_version']}`",
        f"- Documentos: {report['documents']}",
        f"- Variantes: {report['versions']}",
        f"- CO: {report['countries']['CO']}",
        f"- CL: {report['countries']['CL']}",
        f"- Estados por variante: {report['status_counts']}",
        f"- Estados por documento: {report['document_status_counts']}",
        f"- Clasificación por flujo: {report['document_flow_counts']}",
        "",
        "## Inventario por documento",
        "",
        "| Código | Título | Categoría | CO | CL | Firmante | Causa | Línea | Término | Contexto |",
        "|---|---|---|---|---|---|---|---:|---|---|",
    ]
    for item in report["document_inventory"]:
        context = (item.get("blocking_context") or item["human_status"] or "").replace("|", "\\|")
        lines.append(f"| {item['code']} | {item['title']} | {item['category']} | {item['co_status']} | {item['cl_status']} | {item['signer_scope_detected']} | {item['blocking_cause']} | {item.get('blocking_line') or ''} | {item.get('blocking_term') or ''} | {context[:240]} |")
    lines.extend(["", "## Documentos prioritarios", ""])
    for item in report["priority_review"]:
        lines.extend([
            f"### {item['code']} — {item['title']}",
            "",
            f"- Compatible PATIENT_SELF tal como está: {'Sí' if item['flow_classification'] == 'PATIENT_SELF' else 'No'}",
            f"- Línea que bloquea: {item.get('blocking_line') or 'No aplica'}",
            f"- Término: {item.get('blocking_term') or 'No aplica'}",
            f"- Sigue en normalized_content: {'Sí' if item.get('blocking_term') else 'No'}",
            f"- Requiere variante adulta: {'Sí' if item['adult_variant_required'] else 'No'}",
            f"- Requiere adulto responsable: {'Sí' if item['flow_classification'] == 'RESPONSIBLE_ADULT_REQUIRED' else 'No'}",
            f"- Apto para flujo electrónico local: {'Sí' if item['flow_classification'] == 'PATIENT_SELF' else 'No'}",
            f"- Motivo: {item['human_status']}",
            "",
        ])
    lines.extend(["", "## Variantes adultas propuestas", ""])
    for item in report["adult_variant_required"]:
        lines.extend([f"### {item['code']} — {item['title']}", ""])
        for proposal in item.get("adult_variant_proposals") or []:
            lines.extend([
                f"- Línea: {proposal.get('line_number')}",
                f"- Término: {proposal.get('modified_term')}",
                "- Texto original:",
                "",
                "> " + proposal.get("original_fragment", "").replace("\n", " ")[:900],
                "",
                "- Texto propuesto:",
                "",
                "> " + proposal.get("proposed_fragment", "").replace("\n", " ")[:900],
                "",
                f"- Justificación: {proposal.get('justification')}",
                "- Aprobación clínica requerida: Sí",
                "- Aprobación jurídica requerida: Sí",
                "",
            ])
    for item in report["items"]:
        lines.extend([
            f"## {item['code']} — {item['country_code']} / {item['language_code']}",
            "",
            f"- Título: {item['title']}",
            f"- Tipo: {item['document_type']}",
            f"- Estado: **{item['normalization_status']}**",
            f"- Firmante: `{item['signer_compatibility']}`",
            f"- Causa: {item['signer_blocking_category']}",
            f"- Línea/contexto: {item.get('signer_blocking_line') or 'No aplica'} — {item.get('signer_blocking_context') or item['human_status']}",
            f"- Alertas: {item['alerts'] or 'Sin alertas técnicas'}",
            "",
            "### Contenido normalizado v2",
            "",
            "```markdown",
            _truncate(item["normalized_content_v2"]),
            "```",
            "",
        ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    html_parts = [
        "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>C019A4 LIB1 NORM4</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#0f172a}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #cbd5e1;padding:6px;vertical-align:top}article{border:1px solid #cbd5e1;border-radius:14px;padding:18px;margin:18px 0}pre{white-space:pre-wrap;background:#f8fafc;border-radius:10px;padding:12px;max-height:360px;overflow:auto}.blocked{border-left:8px solid #dc2626}.needs{border-left:8px solid #f59e0b}.adult{border-left:8px solid #16a34a}code{background:#e2e8f0;padding:2px 5px;border-radius:5px}</style></head><body>",
        "<h1>C019A4-LIB1-NORM4 — Clasificación contextual de firmantes</h1>",
        f"<p><b>Documentos:</b> {report['documents']} · <b>Variantes:</b> {report['versions']} · <b>Estados:</b> {html.escape(str(report['status_counts']))}</p>",
        "<h2>Inventario de 35 documentos</h2><table><thead><tr><th>Código</th><th>Título</th><th>CO</th><th>CL</th><th>Firmante</th><th>Causa</th><th>Línea</th><th>Contexto</th></tr></thead><tbody>",
    ]
    for item in report["document_inventory"]:
        html_parts.append(f"<tr><td>{html.escape(item['code'])}</td><td>{html.escape(item['title'])}</td><td>{html.escape(str(item['co_status']))}</td><td>{html.escape(str(item['cl_status']))}</td><td>{html.escape(item['signer_scope_detected'])}</td><td>{html.escape(str(item['blocking_cause']))}</td><td>{html.escape(str(item.get('blocking_line') or ''))}</td><td>{html.escape(str(item.get('blocking_context') or item['human_status']))}</td></tr>")
    html_parts.append("</tbody></table>")
    for item in report["items"]:
        klass = "adult" if item["flow_classification"] == "PATIENT_SELF" else "blocked"
        html_parts.extend([
            f"<article class='{klass}'><h2>{html.escape(item['code'])} — {html.escape(item['country_code'])}</h2>",
            f"<p><b>{html.escape(item['title'])}</b><br>Estado: <code>{html.escape(item['normalization_status'])}</code> · Firmante: <code>{html.escape(item['signer_compatibility'])}</code></p>",
            f"<p>Causa: {html.escape(str(item['signer_blocking_category']))}<br>Contexto: {html.escape(str(item.get('signer_blocking_context') or item['human_status']))}</p>",
            "<h3>Contenido normalizado v2</h3>",
            f"<pre>{html.escape(_truncate(item['normalized_content_v2']))}</pre></article>",
        ])
    html_parts.append("</body></html>")
    REPORT_HTML.write_text("\n".join(html_parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera paquete Dentia LIB1 NORM4 contextual")
    parser.add_argument("--input", default=str(V1_PACKAGE))
    parser.add_argument("--output", default=str(V2_PACKAGE))
    parser.add_argument("--reports", action="store_true")
    args = parser.parse_args()
    package, report = build_norm4_package(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.reports:
        write_reports(report)
    print(json.dumps({"ok": True, "documents": len(package["documents"]), "versions": report["versions"], "countries": report["countries"], "status_counts": report["status_counts"], "document_flow_counts": report["document_flow_counts"], "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
