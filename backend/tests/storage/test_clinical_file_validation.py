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


@pytest.mark.parametrize("value", ["invalid", "0", "104857601"])
def test_rejects_invalid_max_size_configuration(monkeypatch, value: str):
    monkeypatch.setenv("CLINICAL_FILE_MAX_BYTES", value)
    with pytest.raises(RuntimeError, match="CLINICAL_FILE_MAX_BYTES"):
        service.configured_max_size()


def test_accepts_default_max_size(monkeypatch):
    monkeypatch.delenv("CLINICAL_FILE_MAX_BYTES", raising=False)
    assert service.configured_max_size() == 25 * 1024 * 1024


def test_production_rejects_lexical_storage_traversal(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CLINICAL_FILE_STORAGE_DIR", "/app/storage/../tmp/clinical_files")
    with pytest.raises(RuntimeError, match="exactly /app/storage/clinical_files"):
        service._root()


def test_production_rejects_symlinked_storage_root(monkeypatch):
    original_resolve = Path.resolve

    def resolve_with_symlink(self: Path, *args, **kwargs):
        if self == Path("/app/storage/clinical_files"):
            return Path("/tmp/escaped-clinical-files")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_symlink)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CLINICAL_FILE_STORAGE_DIR", "/app/storage/clinical_files")
    with pytest.raises(RuntimeError, match="must not traverse symlinks"):
        service._root()
