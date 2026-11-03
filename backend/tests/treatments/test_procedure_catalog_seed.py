from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.services import procedure_catalog_seed_service as catalog_service
from app.services.procedure_catalog_seed_service import (
    ProcedureCatalogSeedError,
    company_currency,
    planned_catalog_rows,
    seed_initial_procedure_catalog,
)


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
        self.executed = False

    def scalars(self, _statement):
        return FakeScalars(())

    def execute(self, _statement):
        self.executed = True
        return FakeResult(self.inserted)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flushed = True


def company(country):
    return Company(id=uuid4(), name="Clínica", slug=f"clinic-{uuid4()}", country=country)


def test_manifest_is_exactly_173_unique_no_change_candidates():
    payload, rows = planned_catalog_rows("Chile")
    assert payload["source_sha256"] == "1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df"
    assert len(rows) == 173
    assert len({row["normalized_name"] for row in rows}) == 173
    assert {row["suggested_scope_type"] for row in rows} <= {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}
    review = json.loads((Path(__file__).resolve().parents[2] / "app/library_data/procedure_catalog_excluded_review.json").read_text())
    assert len(review["items"]) == 311
    assert not ({row["source_row"] for row in rows} & {row["source_row"] for row in review["items"]})


def test_chile_keeps_clp_without_conversion():
    _, rows = planned_catalog_rows("Chile")
    assert all(row["price_currency"] == "CLP" for row in rows)
    assert all(row["suggested_value"] == Decimal(row["source_price_clp"]) for row in rows)
    assert all("clp_to_cop_rate" not in row["price_provenance"] for row in rows)


def test_colombia_uses_approved_fixed_prices_and_historical_basis():
    payload, rows = planned_catalog_rows("Colombia")
    assert all(row["price_currency"] == "COP" for row in rows)
    assert all(row["suggested_value"] % 1000 == 0 for row in rows)
    assert all(row["price_provenance"]["clp_to_cop_rate"] == "3.291243" for row in rows)
    assert all(row["price_provenance"]["rate_observed_at_utc"] == "2026-11-03T03:33:00Z" for row in rows)
    assert all(
        row["price_provenance"]["approved_payload_sha256"] == catalog_service.APPROVED_PAYLOAD_SHA256
        for row in rows
    )
    for source, row in zip(payload["items"], rows, strict=True):
        expected = (Decimal(source["source_price_clp"]) * Decimal("3.291243") / 1000).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * 1000
        assert Decimal(source["suggested_price_cop"]) == expected == row["suggested_value"]


def test_fixed_colombia_catalog_does_not_depend_on_current_date_or_settings():
    first = planned_catalog_rows("Colombia")[1]
    second = planned_catalog_rows("Colombia")[1]
    assert [(row["source_row"], row["suggested_value"]) for row in first] == [
        (row["source_row"], row["suggested_value"]) for row in second
    ]


def test_invalid_manifest_fails_before_any_database_mutation(tmp_path, monkeypatch):
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["items"][0]["suggested_price_cop"] = "999000"
    invalid = tmp_path / "invalid-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)
    session = FakeSession()

    with pytest.raises(ProcedureCatalogSeedError, match="manifiesto aprobado"):
        seed_initial_procedure_catalog(session, company("Colombia"), uuid4())

    assert not session.executed
    assert session.added == []
    assert not session.flushed


@pytest.mark.parametrize(("field", "value"), [
    ("catalog_version", "UNAPPROVED-VERSION"),
    ("source_sha256", "0" * 64),
])
def test_manifest_identity_fields_are_covered_by_approved_hash(field, value, tmp_path, monkeypatch):
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload[field] = value
    invalid = tmp_path / f"invalid-{field}.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)

    with pytest.raises(ProcedureCatalogSeedError, match="manifiesto aprobado"):
        planned_catalog_rows("Chile")


@pytest.mark.parametrize("country", [None, "", "Perú"])
def test_unsupported_or_missing_country_is_rejected(country):
    with pytest.raises(ProcedureCatalogSeedError, match="País"):
        company_currency(country)


def test_new_company_inserts_all_items_without_commit():
    session = FakeSession()
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4())
    audits = [row for row in session.added if isinstance(row, AuditEvent)]
    assert result.inserted == 173 and result.skipped_collisions == 0
    assert len(audits) == 1 and session.flushed


def test_existing_company_skips_collision_and_never_updates_existing_price():
    session = FakeSession(inserted=172)
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4())
    assert result.inserted == 172 and result.skipped_collisions == 1


def test_second_run_is_idempotent():
    session = FakeSession(inserted=0)
    result = seed_initial_procedure_catalog(session, company("Chile"), uuid4())
    assert result.inserted == 0 and result.skipped_collisions == 173
