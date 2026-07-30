from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.utils.clinical_dates import (
    FALLBACK_TIMEZONE,
    clinical_date_or_local_default,
    effective_timezone,
    local_clinical_date,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_local_clinical_date_uses_bogota_company_timezone() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    now = datetime(2026, 7, 30, 2, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, None, now=now).isoformat() == "2026-07-29"


def test_local_clinical_date_uses_santiago_site_timezone() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    site = SimpleNamespace(timezone="America/Santiago")
    now = datetime(2026, 7, 30, 2, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, site, now=now).isoformat() == "2026-07-29"


def test_santiago_standard_time_boundary() -> None:
    company = SimpleNamespace(timezone="America/Santiago")
    now = datetime(2026, 7, 30, 3, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, None, now=now).isoformat() == "2026-07-29"


def test_santiago_dst_boundary() -> None:
    company = SimpleNamespace(timezone="America/Santiago")
    now = datetime(2026, 12, 30, 3, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, None, now=now).isoformat() == "2026-12-30"


def test_server_utc_next_day_still_previous_day_in_colombia() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    now = datetime(2026, 1, 1, 2, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, None, now=now).isoformat() == "2025-12-31"


def test_utc_still_previous_day_in_chile() -> None:
    company = SimpleNamespace(timezone="America/Santiago")
    now = datetime(2026, 7, 30, 2, 30, tzinfo=timezone.utc)

    assert local_clinical_date(company, None, now=now).isoformat() == "2026-07-29"


def test_local_clinical_date_respects_aware_reference_datetime() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    now = datetime(2026, 7, 29, 23, 30, tzinfo=ZoneInfo("America/Bogota"))

    assert local_clinical_date(company, None, now=now).isoformat() == "2026-07-29"


def test_site_timezone_overrides_company_timezone() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    site = SimpleNamespace(timezone="America/Santiago")

    assert effective_timezone(company, site) == "America/Santiago"


def test_company_timezone_used_when_site_has_no_timezone() -> None:
    company = SimpleNamespace(timezone="America/Santiago")
    site = SimpleNamespace(timezone=None)

    assert effective_timezone(company, site) == "America/Santiago"


def test_invalid_timezone_falls_back_to_bogota() -> None:
    company = SimpleNamespace(timezone="Mars/Olympus")

    assert effective_timezone(company, None) == FALLBACK_TIMEZONE


def test_explicit_clinical_date_is_respected() -> None:
    company = SimpleNamespace(timezone="America/Bogota")
    explicit = date(2026, 7, 15)
    now = datetime(2026, 7, 30, 2, 30, tzinfo=timezone.utc)

    assert clinical_date_or_local_default(explicit, company, None, now=now) == explicit


def test_duplicate_prescription_uses_timezone_helper() -> None:
    source = (BACKEND_ROOT / "app/services/prescription_service.py").read_text(encoding="utf-8")

    assert "clinical_date=local_clinical_date(company, site)" in source
    assert "clinical_date=date.today()" not in source


def test_duplicate_clinical_document_uses_timezone_helper() -> None:
    source = (BACKEND_ROOT / "app/services/clinical_document_service.py").read_text(encoding="utf-8")

    assert "clinical_date=local_clinical_date(company, site)" in source
    assert "clinical_date=date.today()" not in source


def test_void_audit_timestamps_remain_utc() -> None:
    prescription = (BACKEND_ROOT / "app/services/prescription_service.py").read_text(encoding="utf-8")
    document = (BACKEND_ROOT / "app/services/clinical_document_service.py").read_text(encoding="utf-8")

    assert "prescription.voided_at = datetime.now(timezone.utc)" in prescription
    assert "document.voided_at = datetime.now(timezone.utc)" in document
