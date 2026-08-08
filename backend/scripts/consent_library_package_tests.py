from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "app" / "library_data" / "consents" / "v1" / "documents.json"
SOURCE_HASH = "5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c"


def main() -> None:
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    documents = payload["documents"]
    versions = [version for document in documents for version in document["versions"]]
    assert payload["source_file_sha256"] == SOURCE_HASH
    assert len(documents) == 35
    assert len(versions) == 70
    assert {version["country_code"] for version in versions} == {"CO", "CL"}
    assert all(version["language_code"] == f"es-{version['country_code']}" for version in versions)
    assert all("Clínica Dental Seis" not in version["content"] for version in versions)
    assert all("DENTAL SEIS" not in version["content"].upper() for version in versions)
    assert all("{{company.name}}" in version["content"] for version in versions)
    special = [document for document in documents if document["document_type"] != "INFORMED_CONSENT" or document["signer_scope"] != "ADULT_SELF"]
    assert special
    assert all(all(version["publication_status"] == "READY_FOR_REVIEW" for version in document["versions"]) for document in special)
    assert all(version["legal_review_status"] == "PENDING_EQUIVALENCE_REVIEW" for version in versions)
    assert all(version["clinical_review_status"] == "PENDING_EQUIVALENCE_REVIEW" for version in versions)
    assert any(document["document_type"] == "INFORMED_CONSENT" and document["signer_scope"] == "ADULT_SELF" for document in documents)
    print(json.dumps({"ok": True, "documents": len(documents), "versions": len(versions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
