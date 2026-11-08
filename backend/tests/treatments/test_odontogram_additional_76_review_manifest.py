import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "library_data"
    / "procedure_catalog_odontogram_additional_76_review.json"
)
APPROVED_REVIEW_SHA256 = "2e7e16f5128da529a360bf12beecb93e785176352ce32989d04b111498908c48"
EXPECTED_SOURCE_ROWS = {
    6,
    9,
    *range(66, 75),
    *range(179, 193),
    197,
    *range(206, 214),
    *range(222, 227),
    228,
    229,
    231,
    260,
    261,
    267,
    268,
    277,
    278,
    279,
    282,
    283,
    287,
    288,
    289,
    292,
    293,
    *range(302, 306),
    308,
    309,
    310,
    316,
    328,
    478,
    480,
    481,
    482,
    487,
    488,
    489,
    493,
    517,
    518,
    519,
}
READY_RESTORATION_ROWS = {277, 278, 287, 288, 289, 316}
READY_NO_CHANGE_ROWS = {222, 223, 224, 225, 226, 279}
READY_RETREATMENT_ROWS = set(range(206, 214))


def _manifest() -> dict:
    raw = MANIFEST_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == APPROVED_REVIEW_SHA256
    return json.loads(raw)


def test_review_manifest_is_complete_unique_and_not_executable() -> None:
    payload = _manifest()
    records = payload["records"]

    assert payload["artifact_kind"].endswith("NOT_V2")
    assert payload["source_sha256"] == (
        "1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df"
    )
    assert len(records) == 76
    assert {record["source_row"] for record in records} == EXPECTED_SOURCE_ROWS
    assert len({record["name"] for record in records}) == 76
    assert all(record["apply_enabled"] is False for record in records)
    assert payload["execution"] == {
        "connected_to_runtime": False,
        "onboarding_enabled": False,
        "backfill_api_enabled": False,
        "cli_apply_enabled": False,
        "production_authorized": False,
    }


def test_fixed_cop_prices_use_the_approved_one_time_basis() -> None:
    payload = _manifest()
    rate = Decimal(payload["currency_policy"]["clp_to_cop_rate"])

    assert payload["currency_policy"]["runtime_conversion"] is False
    for record in payload["records"]:
        expected = (
            Decimal(record["source_price_clp"]) * rate / Decimal("1000")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("1000")
        assert Decimal(record["fixed_price_cop"]) == expected


def test_resolved_and_implemented_rows_are_classified_without_enabling_apply() -> None:
    records = _manifest()["records"]
    restoration_rows = {
        record["source_row"]
        for record in records
        if record["preparation_status"] == "READY_EXISTING_RESTORATION_FLOW"
    }
    no_change_rows = {
        record["source_row"]
        for record in records
        if record["preparation_status"] == "READY_CATALOG_NO_CHANGE"
    }
    retreatment_rows = {
        record["source_row"]
        for record in records
        if record["preparation_status"] == "READY_ENGINEERING_RETREATMENT"
    }

    assert restoration_rows == READY_RESTORATION_ROWS
    assert no_change_rows == READY_NO_CHANGE_ROWS
    assert retreatment_rows == READY_RETREATMENT_ROWS
    for record in records:
        if record["source_row"] in READY_RESTORATION_ROWS:
            assert record["odontogram_behavior"] == "REQUIRES_DIAGNOSIS"
            assert record["suggested_scope_type"] == "TOOTH_SURFACE"
            assert record["allowed_diagnosis_codes"] == [
                "FIND_CARIES",
                "FIND_FRACTURE",
            ]
            assert record["default_performed_code"] == "DONE_RESIN"
        elif record["source_row"] in READY_NO_CHANGE_ROWS:
            assert record["odontogram_behavior"] == "NO_CHANGE"
            assert record["default_performed_code"] is None
        elif record["source_row"] in READY_RETREATMENT_ROWS:
            assert record["suggested_scope_type"] == "TOOTH"
            assert record["allowed_diagnosis_codes"] == ["FIND_ENDO_DEFECTIVE"]
            assert record["default_performed_code"] == "DONE_ENDO"
        else:
            assert record["source_row"] in {197, 519} or not record[
                "preparation_status"
            ].startswith("READY_")


def test_only_repair_veneer_correspondence_stays_source_blocked() -> None:
    by_row = {record["source_row"]: record for record in _manifest()["records"]}

    assert by_row[328]["preparation_status"] == (
        "SOURCE_RULE_PENDING_SPECIFIC_CORRESPONDENCE"
    )
    assert by_row[197]["preparation_status"] == "READY_ENGINEERING_PULPOTOMY"
    assert by_row[519]["preparation_status"] == "READY_ENGINEERING_IMPLANT_CROWN"
