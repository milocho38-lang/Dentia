#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


def main() -> int:
    sys.path.insert(0, str(BACKEND_ROOT))
    os.environ.setdefault("APP_ENV", "test")

    from app.main import create_app  # noqa: PLC0415
    from tests.route_security_registry import (  # noqa: PLC0415
        RiskLevel,
        TestStatus,
        build_route_security_registry,
        route_security_metrics,
    )

    entries = build_route_security_registry(create_app())
    metrics = route_security_metrics(entries)
    by_module: dict[str, dict[str, int]] = {}
    for entry in entries:
        bucket = by_module.setdefault(
            entry.module,
            {"total": 0, "critical": 0, "db_backed": 0, "pending": 0},
        )
        bucket["total"] += 1
        bucket["critical"] += int(entry.risk == RiskLevel.CRITICAL)
        bucket["db_backed"] += int(entry.test_status == TestStatus.DB_BACKED)
        bucket["pending"] += int(entry.test_status == TestStatus.PENDING)

    payload = {
        "route_security_metrics": metrics,
        "modules": dict(sorted(by_module.items())),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if metrics["pending"] != 0:
        return 1
    if metrics["downloads"] != metrics["downloads_db_backed"]:
        return 1
    if metrics["critical_mutations"] != metrics["critical_mutations_db_backed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
