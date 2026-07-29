#!/usr/bin/env python3
"""Semantic document inventory for Dentia backups.

This utility intentionally stores only operational metadata:
entity type, record identifiers, status, logical path, expected relative
storage path, expected SHA-256, optional file size and validation result.
It never stores clinical narrative content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


HEADER = [
    "entity_type",
    "record_id",
    "empresa_id",
    "status",
    "stored_path",
    "expected_storage_path",
    "expected_sha256",
    "file_size_bytes",
    "finalized_at",
    "validation_result",
    "validation_detail",
]

QUERY = r"""
SELECT *
FROM (
  SELECT
    'clinical_document' AS entity_type,
    id::text AS record_id,
    empresa_id::text AS empresa_id,
    estado AS status,
    COALESCE(pdf_storage_path, '') AS stored_path,
    CASE WHEN pdf_storage_path IS NULL OR pdf_storage_path = ''
      THEN ''
      ELSE 'backend/storage/clinical_documents/' || pdf_storage_path
    END AS expected_storage_path,
    COALESCE(pdf_sha256, '') AS expected_sha256,
    COALESCE(finalized_at::text, '') AS finalized_at
  FROM documentos_clinicos
  WHERE estado IN ('FINALIZED', 'VOIDED')
  UNION ALL
  SELECT
    'prescription' AS entity_type,
    id::text AS record_id,
    empresa_id::text AS empresa_id,
    estado AS status,
    COALESCE(pdf_storage_path, '') AS stored_path,
    CASE WHEN pdf_storage_path IS NULL OR pdf_storage_path = ''
      THEN ''
      ELSE 'backend/storage/prescriptions/' || pdf_storage_path
    END AS expected_storage_path,
    COALESCE(pdf_sha256, '') AS expected_sha256,
    COALESCE(finalized_at::text, '') AS finalized_at
  FROM recetas
  WHERE estado IN ('FINALIZED', 'VOIDED')
) AS documents
ORDER BY entity_type, empresa_id, record_id;
"""


@dataclass
class InventoryRow:
    entity_type: str
    record_id: str
    empresa_id: str
    status: str
    stored_path: str
    expected_storage_path: str
    expected_sha256: str
    file_size_bytes: str = ""
    finalized_at: str = ""
    validation_result: str = ""
    validation_detail: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "InventoryRow":
        return cls(**{key: data.get(key, "") for key in HEADER})

    def as_dict(self) -> dict[str, str]:
        return {key: str(getattr(self, key)) for key in HEADER}


def fail(message: str) -> None:
    print(f"[dentia][ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_expected_path(path: str) -> None:
    if not path:
        fail("inventory row has empty expected_storage_path")
    posix = PurePosixPath(path)
    if posix.is_absolute():
        fail(f"absolute storage path is not allowed: {path}")
    if any(part in {"", ".", ".."} for part in posix.parts):
        fail(f"unsafe storage path is not allowed: {path}")
    if not path.startswith("backend/storage/"):
        fail(f"path is outside allowed storage prefix: {path}")


def storage_relative_path(expected_storage_path: str) -> Path:
    validate_expected_path(expected_storage_path)
    prefix = PurePosixPath("backend/storage")
    relative = PurePosixPath(expected_storage_path).relative_to(prefix)
    return Path(*relative.parts)


def query_documents(args: argparse.Namespace) -> list[InventoryRow]:
    command = [
        "docker",
        "exec",
        args.db_container,
        "psql",
        "-U",
        args.db_user,
        "-d",
        args.db_name,
        "-X",
        "-A",
        "-F",
        "\t",
        "-t",
        "-c",
        QUERY,
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"psql query failed: {result.stderr.strip()}")
    rows: list[InventoryRow] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 8:
            fail(f"unexpected psql row shape: {line!r}")
        rows.append(
            InventoryRow(
                entity_type=parts[0],
                record_id=parts[1],
                empresa_id=parts[2],
                status=parts[3],
                stored_path=parts[4],
                expected_storage_path=parts[5],
                expected_sha256=parts[6],
                finalized_at=parts[7],
            )
        )
    return rows


def load_inventory(path: Path) -> list[InventoryRow]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames != HEADER:
            fail(f"invalid inventory header in {path}")
        return [InventoryRow.from_dict(row) for row in reader]


def write_inventory(path: Path, rows: list[InventoryRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def validate_against_storage(rows: list[InventoryRow], storage_root: Path) -> dict[str, int]:
    storage_root = storage_root.resolve()
    metrics = {
        "records_reviewed": len(rows),
        "files_required": 0,
        "files_found": 0,
        "missing": 0,
        "hash_matches": 0,
        "hash_mismatches": 0,
        "invalid_paths": 0,
    }
    seen: set[str] = set()
    for row in rows:
        row.validation_result = "PENDING"
        row.validation_detail = ""
        if not row.stored_path or not row.expected_sha256:
            metrics["missing"] += 1
            row.validation_result = "ERROR"
            row.validation_detail = "finalized_or_voided_record_missing_pdf_path_or_hash"
            continue
        try:
            validate_expected_path(row.expected_storage_path)
        except SystemExit:
            metrics["invalid_paths"] += 1
            row.validation_result = "ERROR"
            row.validation_detail = "invalid_path"
            continue
        if row.expected_storage_path in seen:
            row.validation_result = "ERROR"
            row.validation_detail = "duplicate_expected_storage_path"
            metrics["invalid_paths"] += 1
            continue
        seen.add(row.expected_storage_path)
        metrics["files_required"] += 1
        file_path = (storage_root / storage_relative_path(row.expected_storage_path)).resolve()
        try:
            file_path.relative_to(storage_root)
        except ValueError:
            row.validation_result = "ERROR"
            row.validation_detail = "path_escape"
            metrics["invalid_paths"] += 1
            continue
        if file_path.is_symlink():
            row.validation_result = "ERROR"
            row.validation_detail = "symlink_not_allowed"
            metrics["invalid_paths"] += 1
            continue
        if not file_path.is_file():
            row.validation_result = "ERROR"
            row.validation_detail = "missing_file"
            metrics["missing"] += 1
            continue
        metrics["files_found"] += 1
        row.file_size_bytes = str(file_path.stat().st_size)
        actual_sha = sha256_file(file_path)
        if actual_sha != row.expected_sha256:
            row.validation_result = "ERROR"
            row.validation_detail = "hash_mismatch"
            metrics["hash_mismatches"] += 1
            continue
        row.validation_result = "OK"
        row.validation_detail = "hash_match"
        metrics["hash_matches"] += 1
    return metrics


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        names: set[str] = set()
        for member in members:
            name = member.name
            if name in names:
                fail(f"duplicate path in storage archive: {name}")
            names.add(name)
            path = PurePosixPath(name)
            if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
                fail(f"unsafe path in storage archive: {name}")
            target = (destination / Path(*path.parts)).resolve()
            try:
                target.relative_to(destination)
            except ValueError:
                fail(f"archive member escapes destination: {name}")
            if member.issym() or member.islnk():
                fail(f"links are not allowed in storage archive: {name}")
        tar.extractall(destination, members=members)


def print_metrics(metrics: dict[str, int]) -> None:
    for key in sorted(metrics):
        print(f"{key}={metrics[key]}")


def cmd_collect(args: argparse.Namespace) -> int:
    rows = query_documents(args)
    metrics = validate_against_storage(rows, Path(args.storage_root))
    write_inventory(Path(args.output), rows)
    Path(args.metrics_output).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_metrics(metrics)
    if metrics["missing"] or metrics["hash_mismatches"] or metrics["invalid_paths"]:
        return 1
    return 0


def cmd_verify_storage(args: argparse.Namespace) -> int:
    rows = load_inventory(Path(args.inventory))
    metrics = validate_against_storage(rows, Path(args.storage_root))
    if args.output:
        write_inventory(Path(args.output), rows)
    if args.metrics_output:
        Path(args.metrics_output).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_metrics(metrics)
    if metrics["missing"] or metrics["hash_mismatches"] or metrics["invalid_paths"]:
        return 1
    return 0


def cmd_verify_archive(args: argparse.Namespace) -> int:
    rows = load_inventory(Path(args.inventory))
    temp_dir = Path(tempfile.mkdtemp(prefix="dentia_storage_verify_"))
    try:
        safe_extract_tar(Path(args.archive), temp_dir)
        storage_root = temp_dir / "backend" / "storage"
        if not storage_root.exists():
            # Empty backups created before any storage exists still need a root for
            # inventories with zero rows. If rows exist, validation will fail.
            storage_root.mkdir(parents=True, exist_ok=True)
        metrics = validate_against_storage(rows, storage_root)
        if args.metrics_output:
            Path(args.metrics_output).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print_metrics(metrics)
        if metrics["missing"] or metrics["hash_mismatches"] or metrics["invalid_paths"]:
            return 1
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dentia semantic document inventory validator.")
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Query PostgreSQL and validate host storage.")
    collect.add_argument("--db-container", required=True)
    collect.add_argument("--db-user", required=True)
    collect.add_argument("--db-name", required=True)
    collect.add_argument("--storage-root", required=True)
    collect.add_argument("--output", required=True)
    collect.add_argument("--metrics-output", required=True)
    collect.set_defaults(func=cmd_collect)

    verify_storage = sub.add_parser("verify-storage", help="Validate an inventory against an extracted storage root.")
    verify_storage.add_argument("--inventory", required=True)
    verify_storage.add_argument("--storage-root", required=True)
    verify_storage.add_argument("--output")
    verify_storage.add_argument("--metrics-output")
    verify_storage.set_defaults(func=cmd_verify_storage)

    verify_archive = sub.add_parser("verify-archive", help="Validate an inventory against storage.tar.gz.")
    verify_archive.add_argument("--inventory", required=True)
    verify_archive.add_argument("--archive", required=True)
    verify_archive.add_argument("--metrics-output")
    verify_archive.set_defaults(func=cmd_verify_archive)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
