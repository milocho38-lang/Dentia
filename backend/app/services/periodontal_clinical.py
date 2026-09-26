from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


PERMANENT_FDI_ORDER = (
    18, 17, 16, 15, 14, 13, 12, 11,
    21, 22, 23, 24, 25, 26, 27, 28,
    48, 47, 46, 45, 44, 43, 42, 41,
    31, 32, 33, 34, 35, 36, 37, 38,
)
PERMANENT_FDI = frozenset(PERMANENT_FDI_ORDER)
MOLAR_FDI = frozenset({18, 17, 16, 26, 27, 28, 48, 47, 46, 36, 37, 38})
SITE_CODES = (
    "BUCCAL_DISTAL",
    "BUCCAL_MID",
    "BUCCAL_MESIAL",
    "LINGUAL_DISTAL",
    "LINGUAL_MID",
    "LINGUAL_MESIAL",
)
SITE_CODE_SET = frozenset(SITE_CODES)


def calculate_cal(probing_depth_mm: int | None, gingival_margin_mm: int | None) -> int | None:
    if probing_depth_mm is None or gingival_margin_mm is None:
        return None
    return probing_depth_mm - gingival_margin_mm


def is_periodontal_pocket(probing_depth_mm: int | None) -> bool:
    return probing_depth_mm is not None and probing_depth_mm >= 4


def _index(values: Iterable[bool | None]) -> dict[str, int | float | None]:
    measured = [value for value in values if value is not None]
    positives = sum(value is True for value in measured)
    return {
        "positive_sites": positives,
        "evaluated_sites": len(measured),
        "percentage": round(positives * 100 / len(measured), 2) if measured else None,
    }


def calculate_periodontal_aggregates(
    teeth: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, int | float | bool | None]]:
    eligible_sites = 0
    evaluated_sites = 0
    bleeding_values: list[bool | None] = []
    plaque_values: list[bool | None] = []

    for tooth in teeth:
        if tooth["state"] == "ABSENT":
            continue
        eligible_sites += len(SITE_CODES)
        sites_by_code = {site["site_code"]: site for site in tooth.get("sites", [])}
        for site_code in SITE_CODES:
            site = sites_by_code.get(site_code)
            if site is None:
                continue
            if site.get("probing_depth_mm") is not None and site.get("gingival_margin_mm") is not None:
                evaluated_sites += 1
            bleeding_values.append(site.get("bleeding_on_probing"))
            plaque_values.append(site.get("plaque"))

    return {
        "coverage": {
            "eligible_sites": eligible_sites,
            "evaluated_sites": evaluated_sites,
            "incomplete": evaluated_sites < eligible_sites,
        },
        "indices": {
            "bop": _index(bleeding_values),
            "plaque": _index(plaque_values),
        },
    }
