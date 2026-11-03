from decimal import Decimal
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.services.procedure_catalog_seed_service import (
    CatalogConversion,
    ProcedureCatalogSeedError,
    company_currency,
    planned_catalog_rows,
    seed_initial_procedure_catalog,
)


REFERENCE = CatalogConversion(
    Decimal("3.2126"),
    "XE https://www.xe.com/es/currencyconverter/convert/?Amount=1&From=CLP&To=COP",
    "2026-11-02T09:47:00Z",
    is_reference=True,
    allow_reference=True,
)
REFERENCE_NOW = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return list(self.values)


class FakeResult:
    def __init__(self, count): self.count = count
    def scalars(self): return FakeScalars(range(self.count))


class FakeSession:
    def __init__(self, inserted=173):
        self.inserted = inserted
        self.added = []
        self.flushed = False

    def scalars(self, _statement):
        return FakeScalars(())

    def execute(self, _statement):
        return FakeResult(self.inserted)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flushed = True


def company(country):
    return Company(id=uuid4(), name="Clínica", slug=f"clinic-{uuid4()}", country=country)


def test_manifest_is_exactly_173_unique_no_change_candidates():
    payload, rows = planned_catalog_rows("Chile", CatalogConversion())
    assert payload["source_sha256"] == "1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df"
    assert len(rows) == 173
    assert len({row["normalized_name"] for row in rows}) == 173
    assert {row["suggested_scope_type"] for row in rows} <= {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}
    review = json.loads((Path(__file__).resolve().parents[2] / "app/library_data/procedure_catalog_excluded_review.json").read_text())
    assert len(review["items"]) == 311
    assert not ({row["source_row"] for row in rows} & {row["source_row"] for row in review["items"]})


def test_chile_keeps_clp_without_conversion():
    _, rows = planned_catalog_rows("Chile", CatalogConversion())
    assert all(row["price_currency"] == "CLP" for row in rows)
    assert all(row["suggested_value"] == Decimal(row["source_price_clp"]) for row in rows)
    assert all("clp_to_cop_rate" not in row["price_provenance"] for row in rows)


def test_colombia_reference_conversion_rounds_to_nearest_thousand_and_is_traced():
    _, rows = planned_catalog_rows("Colombia", REFERENCE, REFERENCE_NOW)
    assert all(row["price_currency"] == "COP" for row in rows)
    assert all(row["suggested_value"] % 1000 == 0 for row in rows)
    assert all(row["price_provenance"]["clp_to_cop_rate"] == "3.2126" for row in rows)
    assert all(row["price_provenance"]["rate_observed_at_utc"] == "2026-11-02T09:47:00Z" for row in rows)


def test_reference_rate_is_blocked_without_explicit_test_override():
    conversion = CatalogConversion(Decimal("3.2126"), "XE", "2026-11-02T09:47:00Z", is_reference=True)
    with pytest.raises(ProcedureCatalogSeedError, match="referencia"):
        planned_catalog_rows("Colombia", conversion, REFERENCE_NOW)
    equivalent = CatalogConversion(Decimal("3.2126"), "another label", "2026-11-02T09:47:00+00:00")
    with pytest.raises(ProcedureCatalogSeedError, match="referencia"):
        planned_catalog_rows("Colombia", equivalent, REFERENCE_NOW)


@pytest.mark.parametrize("observed", [
    "2026-11-02T09:47:00", "2026-11-02T09:47:00-03:00",
    "2026-11-02T10:01:00Z", "2026-11-01T09:59:59Z",
])
def test_rate_rejects_missing_utc_offset_non_utc_future_and_stale(observed):
    conversion = CatalogConversion(Decimal("3.2"), "source", observed)
    with pytest.raises(ProcedureCatalogSeedError):
        planned_catalog_rows("Colombia", conversion, REFERENCE_NOW)


@pytest.mark.parametrize("conversion", [CatalogConversion(), CatalogConversion(Decimal("3.2")),
    CatalogConversion(Decimal("3.2"), "XE", None)])
def test_colombia_requires_complete_rate_trace(conversion):
    with pytest.raises(ProcedureCatalogSeedError):
        planned_catalog_rows("Colombia", conversion, REFERENCE_NOW)


@pytest.mark.parametrize("country", [None, "", "Perú"])
def test_unsupported_or_missing_country_is_rejected(country):
    with pytest.raises(ProcedureCatalogSeedError, match="País"):
        company_currency(country)


def test_new_company_inserts_all_items_without_commit():
    session = FakeSession()
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4(), CatalogConversion())
    audits = [row for row in session.added if isinstance(row, AuditEvent)]
    assert result.inserted == 173 and result.skipped_collisions == 0
    assert len(audits) == 1 and session.flushed


def test_existing_company_skips_collision_and_never_updates_existing_price():
    session = FakeSession(inserted=172)
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4(), CatalogConversion())
    assert result.inserted == 172 and result.skipped_collisions == 1


def test_second_run_is_idempotent():
    session = FakeSession(inserted=0)
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4(), CatalogConversion())
    assert result.inserted == 0 and result.skipped_collisions == 173
