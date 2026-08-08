from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.services.consent_library_service import PACKAGE_PATH, default_source_pdf_path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_PRODUCT = REPO_ROOT / "DOCS" / "product"
SOURCE_FRAGMENTS_PATH = DOCS_PRODUCT / "C019A4-LIB1-Source-Fragments.json"
HUMAN_REVIEW_MD_PATH = DOCS_PRODUCT / "C019A4-LIB1-Human-Equivalence-Review.md"
HUMAN_REVIEW_HTML_PATH = DOCS_PRODUCT / "C019A4-LIB1-Human-Equivalence-Review.html"
CHECKLIST_PATH = DOCS_PRODUCT / "C019A4-LIB1-Normalization-Equivalence-Checklist.md"

INSTITUTIONAL_REPLACEMENTS = (
    ("CLINICA DENTAL SEIS", "{{company.name}}"),
    ("Clínica Dental Seis", "{{company.name}}"),
    ("Clinica Dental Seis", "{{company.name}}"),
    ("DENTAL SEIS", "{{company.name}}"),
    ("Avenida España 105, Curicó", "{{site.address}}, {{site.city}}"),
    ("Avenida España 105", "{{site.address}}"),
    ("Curicó", "{{site.city}}"),
)

REVIEW_KEYWORDS = (
    "riesgo",
    "riesgos",
    "complicación",
    "complicaciones",
    "contraindicación",
    "contraindicaciones",
    "advertencia",
    "garantía",
    "garantia",
    "dolor",
    "infección",
    "infeccion",
    "sangrado",
    "medicamento",
    "anestesia",
    "rechazo",
    "responsabilidad",
    "obligación",
    "obligacion",
)

VALUE_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:%|d[ií]as?|semanas?|meses?|a[nñ]os?|horas?|mg|ml|gr|uf|pesos?)\b",
    re.IGNORECASE,
)
VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def _extract_pages_with_pdfkit(pdf_path: Path) -> list[dict[str, Any]]:
    swift_source = """
import Foundation
import PDFKit

let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let document = PDFDocument(url: url) else {
    FileHandle.standardError.write("No fue posible abrir el PDF fuente.\\n".data(using: .utf8)!)
    exit(2)
}

var pages: [[String: Any]] = []
for index in 0..<document.pageCount {
    let page = document.page(at: index)
    pages.append([
        "page": index + 1,
        "text": page?.string ?? ""
    ])
}

let data = try JSONSerialization.data(withJSONObject: pages, options: [.sortedKeys])
FileHandle.standardOutput.write(data)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as handle:
        handle.write(swift_source)
        swift_path = Path(handle.name)
    try:
        result = subprocess.run(["swift", str(swift_path), str(pdf_path)], check=True, capture_output=True, text=True, timeout=120)
        return json.loads(result.stdout)
    finally:
        swift_path.unlink(missing_ok=True)


def _normalize_source_for_dentia(source_text: str) -> tuple[str, list[str]]:
    normalized = source_text
    replacements_used: list[str] = []
    for source, target in INSTITUTIONAL_REPLACEMENTS:
        if source in normalized:
            normalized = normalized.replace(source, target)
            replacements_used.append(f"`{source}` → `{target}`")
    return _clean_text(normalized), replacements_used


def _normal_content(title: str, source_text: str, country_code: str) -> str:
    normalized_source, _ = _normalize_source_for_dentia(source_text)
    country_name = "Colombia" if country_code == "CO" else "Chile"
    return _clean_text(
        f"""# {title}

Paciente: {{{{patient.full_name}}}}
Identificación: {{{{patient.document_type}}}} {{{{patient.document_number}}}}
Fecha clínica: {{{{document.clinical_date}}}}
País documental: {country_name}
Clínica: {{{{company.name}}}}
Sede: {{{{site.name}}}}
Dirección de sede: {{{{site.address}}}}, {{{{site.city}}}}
Profesional responsable: {{{{professional.full_name}}}}

## Texto del documento fuente

{normalized_source}

## Firma

Paciente o responsable: ______________________________

Profesional: {{{{professional.full_name}}}}
Registro profesional: {{{{professional.license_number}}}}
"""
    )


def _variables(content: str) -> list[str]:
    return sorted(set(VARIABLE_PATTERN.findall(content)))


def _source_for_document(pages_by_number: dict[int, str], start: int, end: int) -> str:
    chunks = []
    for page in range(start, end + 1):
        text = _clean_text(pages_by_number.get(page, ""))
        chunks.append(f"[Página {page}]\n{text}")
    return _clean_text("\n\n".join(chunks))


def _review_lines(source_text: str) -> list[str]:
    lines = []
    for line in source_text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped and any(keyword in lower for keyword in REVIEW_KEYWORDS):
            lines.append(stripped)
    return lines[:12]


def _values(source_text: str) -> list[str]:
    return sorted(set(match.group(0) for match in VALUE_PATTERN.finditer(source_text)))


def _diff(source_text: str, normalized_text: str) -> str:
    source_lines = [line.strip() for line in source_text.splitlines() if line.strip()]
    normalized_lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    return "\n".join(difflib.unified_diff(source_lines, normalized_lines, fromfile="fuente", tofile="normalizado", lineterm="", n=2))


def _content_without_header(content: str) -> str:
    marker = "## Texto del documento fuente"
    if marker not in content:
        return content
    body = content.split(marker, 1)[1]
    if "## Firma" in body:
        body = body.split("## Firma", 1)[0]
    return _clean_text(body)


def update_package_from_pdf(package_path: Path, pdf_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    pages = _extract_pages_with_pdfkit(pdf_path)
    pages_by_number = {item["page"]: _clean_text(item.get("text", "")) for item in pages}
    fragments: list[dict[str, Any]] = []

    for document_index, document in enumerate(package["documents"], start=1):
        source_text = _source_for_document(pages_by_number, document["source_page_start"], document["source_page_end"])
        quality_warnings = []
        if not source_text.strip():
            quality_warnings.append("PDFKit no extrajo texto para este rango de páginas.")
        for version in document["versions"]:
            content = _normal_content(document["title"], source_text, version["country_code"])
            version["source_text"] = source_text
            version["source_text_sha256"] = _sha256(source_text)
            version["content"] = content
            version["normalized_content_sha256"] = _sha256(content)
            version["variables"] = _variables(content)
            version["transformation_notes"] = [
                "Extracción de texto fuente mediante PDFKit local de macOS, sin OCR.",
                "Se reemplazaron datos institucionales de Clínica/Dental Seis por variables Dentia.",
                "Se conservaron riesgos, advertencias, porcentajes, plazos y términos clínicos extraídos cuando PDFKit los entregó como texto.",
                "Se agregó encabezado Dentia con variables institucionales y datos del paciente/profesional.",
                "Se conservaron líneas de firma manual como soporte de revisión; la firma electrónica se controla por flujo Dentia cuando aplique.",
                "No se incorporaron datos de pacientes reales ni identificadores personales.",
            ]
        fragments.append(
            {
                "number": document_index,
                "code": document["code"],
                "title": document["source_title_exact"],
                "category": document["category"],
                "specialty": document.get("specialty_name") or "General",
                "signer_scope": document["signer_scope"],
                "pages": list(range(document["source_page_start"], document["source_page_end"] + 1)),
                "source_text": source_text,
                "source_text_sha256": _sha256(source_text),
                "extraction_method": "Apple PDFKit via Swift local, sin OCR",
                "quality_warnings": quality_warnings or ["Texto extraído por capa textual del PDF; revisar saltos de línea y orden visual cuando el diseño sea complejo."],
            }
        )

    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return package, fragments


def build_human_review(package: dict[str, Any], fragments: list[dict[str, Any]]) -> tuple[str, str]:
    fragment_by_code = {item["code"]: item for item in fragments}
    md: list[str] = [
        "# C019A4-LIB1 — Revisión humana de equivalencia",
        "",
        "Este paquete permite revisar de forma legible la equivalencia entre el PDF fuente aprobado y las versiones normalizadas en Dentia.",
        "",
        "- Resultado inicial de todas las versiones normalizadas: `PENDING`.",
        "- La fuente original se considera aprobada para Colombia y Chile.",
        "- Ninguna versión normalizada queda aprobada automáticamente por este documento.",
        "- Método de extracción: Apple PDFKit vía Swift local, sin OCR.",
        "",
        "## Revisión de variantes Colombia y Chile",
        "",
        "Cada documento tiene variantes independientes `CO / es-CO` y `CL / es-CL`. El contenido clínico base debe permanecer equivalente; las diferencias esperadas son país, locale, identificador y hash normalizado.",
        "",
    ]
    html_parts: list[str] = [
        "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>C019A4-LIB1 Revisión humana</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#0f172a;background:#f8fafc}article{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin:24px 0}pre{white-space:pre-wrap;background:#f1f5f9;border-radius:12px;padding:16px;overflow:auto}.var{color:#047857;font-weight:700}.del{color:#b91c1c}.add{color:#0369a1}.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#fef3c7;color:#92400e;font-weight:700;font-size:12px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.small{font-size:12px;color:#64748b}table{border-collapse:collapse;width:100%}td,th{border:1px solid #e2e8f0;padding:8px;text-align:left}</style></head><body>",
        "<h1>C019A4-LIB1 — Revisión humana de equivalencia</h1>",
        "<p>HTML local, estático, sin recursos externos. Ninguna versión normalizada queda aprobada automáticamente.</p>",
    ]

    for index, document in enumerate(package["documents"], start=1):
        fragment = fragment_by_code[document["code"]]
        co = next(version for version in document["versions"] if version["country_code"] == "CO")
        cl = next(version for version in document["versions"] if version["country_code"] == "CL")
        normalized_body = _content_without_header(co["content"])
        normalized_source, replacements = _normalize_source_for_dentia(fragment["source_text"])
        diff_text = _diff(normalized_source, normalized_body)
        values = _values(fragment["source_text"])
        warning_lines = _review_lines(fragment["source_text"])
        result = "PENDING"
        md.extend(
            [
                f"## {index:02d}. {document['source_title_exact']}",
                "",
                f"- Código: `{document['code']}`",
                f"- Categoría: {document['category']}",
                f"- Páginas fuente: {document['source_page_start']}–{document['source_page_end']}",
                f"- Especialidad: {document.get('specialty_name') or 'General'}",
                f"- Firmante: `{document['signer_scope']}`",
                f"- Resultado: `{result}`",
                f"- Fragmento SHA-256: `{fragment['source_text_sha256']}`",
                "",
                "### Texto fuente relevante",
                "",
                "```text",
                fragment["source_text"],
                "```",
                "",
                "### Texto normalizado CO / es-CO",
                "",
                "```markdown",
                co["content"],
                "```",
                "",
                "### Variables introducidas",
                "",
                ", ".join(f"`{item}`" for item in co.get("variables", [])) or "Sin variables.",
                "",
                "### Líneas eliminadas o sustituidas",
                "",
                "\n".join(f"- {item}" for item in (replacements or ["No se detectaron referencias institucionales sustituidas."])),
                "",
                "### Cambios de formato",
                "",
                "- Transformación a Markdown restringido Dentia.",
                "- Encabezado Dentia agregado con variables institucionales.",
                "- Saltos de página representados como etiquetas `[Página N]`.",
                "",
                "### Diferencias textuales",
                "",
                "```diff",
                diff_text or "Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.",
                "```",
                "",
                "### Valores, porcentajes y plazos detectados",
                "",
                ", ".join(f"`{item}`" for item in values) if values else "No se detectaron valores, porcentajes o plazos explícitos por patrón automático.",
                "",
                "### Riesgos y advertencias detectadas",
                "",
                "\n".join(f"- {item}" for item in warning_lines) if warning_lines else "No se detectaron líneas por palabra clave; revisar texto completo.",
                "",
                "### Referencias institucionales sustituidas",
                "",
                "\n".join(f"- {item}" for item in replacements) if replacements else "No se detectaron referencias institucionales fuente en este fragmento.",
                "",
                "### Revisión de variantes Colombia y Chile",
                "",
                f"- CO: id lógico `{document['code']}-CO`, país `{co['country_code']}`, locale `{co['language_code']}`, hash `{co['normalized_content_sha256']}`.",
                f"- CL: id lógico `{document['code']}-CL`, país `{cl['country_code']}`, locale `{cl['language_code']}`, hash `{cl['normalized_content_sha256']}`.",
                f"- Hashes distintos: {'sí' if co['normalized_content_sha256'] != cl['normalized_content_sha256'] else 'no'}",
                "- Fallback: no se usa; cada variante conserva país y locale propios.",
                "",
                "### Observaciones",
                "",
                "- Pendiente registrar revisión odontológica y jurídica de equivalencia.",
                "- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.",
                "",
            ]
        )
        html_parts.extend(
            [
                "<article>",
                f"<h2>{index:02d}. {html.escape(document['source_title_exact'])}</h2>",
                f"<p><span class='badge'>{result}</span> {html.escape(document['category'])} · {html.escape(document.get('specialty_name') or 'General')} · páginas {document['source_page_start']}–{document['source_page_end']}</p>",
                "<div class='grid'><section><h3>Fuente</h3>",
                f"<pre>{html.escape(fragment['source_text'])}</pre></section><section><h3>Normalizado CO</h3>",
                f"<pre>{html.escape(co['content'])}</pre></section></div>",
                "<h3>Variables</h3>",
                "<p>" + " ".join(f"<span class='var'>{html.escape(item)}</span>" for item in co.get("variables", [])) + "</p>",
                "<h3>Diferencias</h3>",
                f"<pre>{html.escape(diff_text or 'Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.')}</pre>",
                "<h3>CO / CL</h3>",
                f"<table><tr><th>País</th><th>Locale</th><th>Hash</th></tr><tr><td>CO</td><td>{co['language_code']}</td><td>{co['normalized_content_sha256']}</td></tr><tr><td>CL</td><td>{cl['language_code']}</td><td>{cl['normalized_content_sha256']}</td></tr></table>",
                "</article>",
            ]
        )
    html_parts.append("</body></html>")
    return "\n".join(md) + "\n", "\n".join(html_parts) + "\n"


def build_checklist(package: dict[str, Any]) -> str:
    lines = [
        "# C019A4-LIB1 — Checklist de equivalencia normalizada",
        "",
        "Este checklist debe diligenciarse manualmente por documento y país antes de aprobar una versión normalizada.",
        "",
        "No inventar nombres, matrículas ni fechas. La aprobación es independiente por variante CO/CL.",
        "",
        "| # | Código | País | Texto clínico fiel | Riesgos preservados | Advertencias preservadas | Valores preservados | Variables correctas | Títulos/límites correctos | Firmante correcto | Clasificación correcta | País aprobado | Revisión odontológica | Revisión jurídica equivalencia | Revisor | Fecha | Observaciones |",
        "|---|--------|------|---------------------|----------------------|---------------------------|---------------------|---------------------|---------------------------|-------------------|------------------------|---------------|------------------------|-------------------------------|---------|-------|---------------|",
    ]
    row = 1
    for document in package["documents"]:
        for version in document["versions"]:
            lines.append(
                f"| {row} | `{document['code']}` | {version['country_code']} / {version['language_code']} | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |  |  |  |"
            )
            row += 1
    lines.extend(
        [
            "",
            "## Reglas de aprobación",
            "",
            "- Una variante solo puede pasar a `APPROVED` cuando todas las casillas de su fila estén completas.",
            "- La aprobación de CO no aprueba automáticamente CL, y viceversa.",
            "- La fuente original está aprobada; este checklist revisa la equivalencia de la normalización Dentia.",
            "- Si existe duda sobre riesgos, advertencias, valores, garantías, obligaciones o negaciones, marcar `CHANGES_REQUIRED` fuera de sistema y no aprobar.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera paquete humano de equivalencia LIB1.")
    parser.add_argument("--package", default=str(PACKAGE_PATH))
    parser.add_argument("--source-pdf", default=str(default_source_pdf_path()))
    args = parser.parse_args()

    package_path = Path(args.package)
    pdf_path = Path(args.source_pdf)
    package, fragments = update_package_from_pdf(package_path, pdf_path)
    SOURCE_FRAGMENTS_PATH.write_text(json.dumps({"fragments": fragments}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md, html_doc = build_human_review(package, fragments)
    HUMAN_REVIEW_MD_PATH.write_text(md, encoding="utf-8")
    HUMAN_REVIEW_HTML_PATH.write_text(html_doc, encoding="utf-8")
    CHECKLIST_PATH.write_text(build_checklist(package), encoding="utf-8")
    print(json.dumps({"documents": len(package["documents"]), "versions": sum(len(item["versions"]) for item in package["documents"]), "fragments": len(fragments), "method": "Apple PDFKit via Swift local, sin OCR"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
