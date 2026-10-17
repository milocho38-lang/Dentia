from pathlib import Path

import pytest

from app.services import clinical_file_service as service


def test_detects_real_content_instead_of_declared_extension():
    assert service.detect_mime(b"%PDF-1.7 synthetic") == "application/pdf"
    assert service.detect_mime(b"plain text named xray.pdf") is None


def test_normalizes_untrusted_original_filename():
    assert service.safe_original_name("../../patient/xray.pdf") == "xray.pdf"
    assert service.safe_original_name("..\\..\\exam.png") == "exam.png"


def test_rejects_storage_path_traversal(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(service, "_root", lambda: tmp_path.resolve())
    with pytest.raises(service.ClinicalFileError):
        service.resolve_storage_key("../outside.pdf")


def test_accepts_tenant_scoped_storage_key(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(service, "_root", lambda: tmp_path.resolve())
    assert service.resolve_storage_key("company_a/patients/patient_b/file.pdf") == (tmp_path / "company_a/patients/patient_b/file.pdf").resolve()
