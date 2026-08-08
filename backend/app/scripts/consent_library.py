from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.database.session import SessionLocal
from app.models.consent_template import ConsentLibraryVersion, ConsentTemplateVersion
from app.services.consent_library_normalization import validate_patient_facing_content
from app.services.consent_library_service import build_equivalence_report, import_library_package, load_library_package


def main() -> None:
    parser = argparse.ArgumentParser(description="Biblioteca oficial Dentia de documentos odontológicos")
    parser.add_argument("command", choices=["validate", "dry-run", "import", "reimport", "equivalence-report", "report", "verify-installed-content"], help="Acción a ejecutar")
    parser.add_argument("--path", default=None, help="Ruta opcional del paquete JSON canónico")
    parser.add_argument("--source-pdf", default=None, help="Ruta opcional del PDF fuente para validar SHA-256")
    parser.add_argument("--output", default=None, help="Ruta opcional de salida JSON")
    args = parser.parse_args()
    package_path = Path(args.path) if args.path else None

    source_pdf_path = Path(args.source_pdf) if args.source_pdf else None
    if args.command == "validate":
        payload = load_library_package(package_path, source_pdf_path=source_pdf_path) if package_path else load_library_package(source_pdf_path=source_pdf_path)
        print(json.dumps({"ok": True, "documents": len(payload.get("documents", [])), "source_sha256": payload.get("source_file_sha256"), "source_pdf_verification": payload.get("source_pdf_verification")}, ensure_ascii=False, indent=2))
        return
    if args.command in {"equivalence-report", "report"}:
        report = build_equivalence_report(package_path) if package_path else build_equivalence_report()
        serialized = json.dumps(report, ensure_ascii=False, indent=2, default=str)
        if args.output:
            Path(args.output).write_text(serialized + "\n", encoding="utf-8")
        print(serialized)
        return

    with SessionLocal() as session:
        if args.command == "verify-installed-content":
            rows = list(session.query(ConsentTemplateVersion).filter(ConsentTemplateVersion.source_library_version_id.isnot(None)).all())
            failures = []
            skipped_legacy = []
            for row in rows:
                library_version = session.get(ConsentLibraryVersion, row.source_library_version_id)
                notes = library_version.transformation_notes if library_version else []
                if "normalization_schema_version=LIB1_NORM_V2" not in (notes or []):
                    skipped_legacy.append(str(row.id))
                    continue
                validation = validate_patient_facing_content(row.content, allowed_variables=None, document_type="PROCEDURE_CONSENT", signer_compatibility="ADULT_SELF", normalized_hash=row.content_sha256)
                if validation.status == "BLOCKED":
                    failures.append({"version_id": str(row.id), "template_id": str(row.template_id), "blockers": validation.blockers})
            result = {"installed_versions_seen": len(rows), "installed_versions_checked": len(rows) - len(skipped_legacy), "legacy_versions_skipped": len(skipped_legacy), "failures": failures, "ok": not failures}
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            if failures:
                raise SystemExit(1)
            return
        result = import_library_package(session, path=package_path, dry_run=args.command == "dry-run", source_pdf_path=source_pdf_path) if package_path else import_library_package(session, dry_run=args.command == "dry-run", source_pdf_path=source_pdf_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
