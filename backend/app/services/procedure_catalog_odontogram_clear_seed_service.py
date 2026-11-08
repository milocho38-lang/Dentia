import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.odontogram import OdontogramCatalogItem
from app.models.treatment import ProcedureCatalogDiagnosis, ProcedureCatalogItem
from app.services.procedure_catalog_seed_service import (
    ProcedureCatalogSeedError,
    company_currency,
    normalize_catalog_name,
)


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "library_data"
    / "procedure_catalog_odontogram_clear_20_draft.json"
)
APPROVED_FILE_SHA256 = "1b7894dfb23e3c72f5728aa8404e6c0b35e88e0e71134cdb06bf613feb7c2c8f"
EXPECTED_ROWS = {
    *range(206, 214),
    *range(222, 227),
    277,
    278,
    279,
    287,
    288,
    289,
    316,
}
EXPECTED_CODES = {
    "FIND_CARIES",
    "FIND_FRACTURE",
    "FIND_ENDO_DEFECTIVE",
    "DONE_RESIN",
    "DONE_ENDO",
}


@dataclass(frozen=True)
class ClearCatalogSeedResult:
    inserted: int
    skipped_collisions: int
    diagnosis_links: int
    currency: str
    catalog_version: str


@dataclass(frozen=True)
class ClearCatalogDryRunResult:
    would_insert: int
    collisions: tuple[dict, ...]
    currency: str
    catalog_version: str


def _load_batch() -> dict:
    raw = CATALOG_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != APPROVED_FILE_SHA256:
        raise ProcedureCatalogSeedError(
            "El lote clínico claro no coincide con el manifiesto revisado."
        )
    payload = json.loads(raw)
    items = payload.get("items", [])
    if len(items) != 20 or {item.get("source_row") for item in items} != EXPECTED_ROWS:
        raise ProcedureCatalogSeedError(
            "El lote clínico claro debe contener las veinte filas fuente esperadas."
        )
    names = [normalize_catalog_name(item["name"]) for item in items]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote clínico claro contiene nombres duplicados.")
    for item in items:
        try:
            clp = Decimal(item["source_price_clp"])
            cop = Decimal(item["fixed_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError(
                "El lote clínico claro contiene un precio inválido."
            ) from exc
        if clp < 0 or cop < 0 or cop % 1000:
            raise ProcedureCatalogSeedError(
                "El lote clínico claro contiene un precio monetario inesperado."
            )
        row = item["source_row"]
        if row in range(206, 214):
            valid = (
                item["suggested_scope_type"] == "TOOTH"
                and item["odontogram_behavior"] == "REQUIRES_DIAGNOSIS"
                and item["allowed_diagnosis_codes"] == ["FIND_ENDO_DEFECTIVE"]
                and item["default_performed_code"] == "DONE_ENDO"
                and item["requires_existing_diagnosis"] is True
            )
        elif row in range(222, 227):
            valid = (
                item["suggested_scope_type"] == "GENERAL"
                and item["odontogram_behavior"] == "NO_CHANGE"
                and not item["allowed_diagnosis_codes"]
                and item["default_performed_code"] is None
            )
        elif row == 279:
            valid = (
                item["suggested_scope_type"] == "TOOTH_SURFACE"
                and item["odontogram_behavior"] == "NO_CHANGE"
                and not item["allowed_diagnosis_codes"]
                and item["default_performed_code"] is None
            )
        else:
            valid = (
                item["suggested_scope_type"] == "TOOTH_SURFACE"
                and item["odontogram_behavior"] == "REQUIRES_DIAGNOSIS"
                and item["allowed_diagnosis_codes"]
                == ["FIND_CARIES", "FIND_FRACTURE"]
                and item["default_performed_code"] == "DONE_RESIN"
            )
        if not valid:
            raise ProcedureCatalogSeedError(
                f"La fila {row} contiene una regla clínica inesperada."
            )
    return payload


def preview_odontogram_clear_catalog(
    session: Session, company: Company
) -> ClearCatalogDryRunResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    normalized_to_source = {
        normalize_catalog_name(item["name"]): item for item in payload["items"]
    }
    existing = session.execute(
        select(
            ProcedureCatalogItem.id,
            ProcedureCatalogItem.name,
            ProcedureCatalogItem.normalized_name,
            ProcedureCatalogItem.suggested_value,
        ).where(
            ProcedureCatalogItem.company_id == company.id,
            ProcedureCatalogItem.normalized_name.in_(normalized_to_source),
        )
    ).all()
    collisions = tuple(
        {
            "existing_id": str(row.id),
            "existing_name": row.name,
            "existing_value": (
                str(row.suggested_value) if row.suggested_value is not None else None
            ),
            "source_row": normalized_to_source[row.normalized_name]["source_row"],
            "source_name": normalized_to_source[row.normalized_name]["name"],
        }
        for row in existing
    )
    return ClearCatalogDryRunResult(
        would_insert=len(payload["items"]) - len(collisions),
        collisions=collisions,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )


def seed_odontogram_clear_catalog(
    session: Session,
    company: Company,
    actor_id: UUID | None,
) -> ClearCatalogSeedResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    clinical_items = {
        item.code: item
        for item in session.scalars(
            select(OdontogramCatalogItem).where(
                OdontogramCatalogItem.company_id.is_(None),
                OdontogramCatalogItem.code.in_(EXPECTED_CODES),
                OdontogramCatalogItem.is_active.is_(True),
            )
        )
    }
    if set(clinical_items) != EXPECTED_CODES:
        raise ProcedureCatalogSeedError(
            "Faltan elementos clínicos globales requeridos por el lote claro."
        )
    values = []
    source_by_name = {}
    for source in payload["items"]:
        normalized_name = normalize_catalog_name(source["name"])
        source_by_name[normalized_name] = source
        value = Decimal(
            source["source_price_clp"]
            if currency == "CLP"
            else source["fixed_price_cop"]
        )
        provenance = {
            "catalog_version": payload["catalog_version"],
            "source_sha256": payload["source_sha256"],
            "approved_file_sha256": APPROVED_FILE_SHA256,
            "source_row": source["source_row"],
            "source_currency": "CLP",
            "source_price": source["source_price_clp"],
            "generated_currency": currency,
            "generated_value": str(value),
            "currency_role": "IMPORT_ORIGIN_NOT_CURRENT_DISPLAY_CURRENCY",
            "runtime_conversion": False,
        }
        values.append(
            {
                "company_id": company.id,
                "name": source["name"],
                "normalized_name": normalized_name,
                "suggested_value": value,
                "price_currency": currency,
                "price_provenance": provenance,
                "suggested_scope_type": source["suggested_scope_type"],
                "odontogram_behavior": source["odontogram_behavior"],
                "odontogram_scope_type": (
                    source["suggested_scope_type"]
                    if source["odontogram_behavior"] == "REQUIRES_DIAGNOSIS"
                    else None
                ),
                "default_performed_catalog_item_id": (
                    clinical_items[source["default_performed_code"]].id
                    if source["default_performed_code"]
                    else None
                ),
                "is_active": True,
                "created_by": actor_id,
            }
        )
    inserted = session.execute(
        pg_insert(ProcedureCatalogItem)
        .values(values)
        .on_conflict_do_nothing(
            constraint="uq_catalogo_proc_empresa_nombre_normalizado"
        )
        .returning(ProcedureCatalogItem.id, ProcedureCatalogItem.normalized_name)
    ).all()
    links = []
    for procedure_id, normalized_name in inserted:
        source = source_by_name[normalized_name]
        for code in source["allowed_diagnosis_codes"]:
            links.append(
                {
                    "company_id": company.id,
                    "procedure_catalog_id": procedure_id,
                    "odontogram_catalog_item_id": clinical_items[code].id,
                    "is_active": True,
                }
            )
    if links:
        session.execute(pg_insert(ProcedureCatalogDiagnosis).values(links))
    skipped = len(values) - len(inserted)
    session.add(
        AuditEvent(
            company_id=company.id,
            user_id=actor_id,
            entity="procedure_catalog_seed",
            entity_id=company.id,
            action="PROCEDURE_CATALOG_ODONTOGRAM_CLEAR_DRAFT_SEEDED",
            result="SUCCESS",
            detail={
                "catalog_version": payload["catalog_version"],
                "source_sha256": payload["source_sha256"],
                "approved_file_sha256": APPROVED_FILE_SHA256,
                "inserted": len(inserted),
                "skipped_collisions": skipped,
                "diagnosis_links": len(links),
                "currency": currency,
                "connected_to_runtime": False,
            },
        )
    )
    session.flush()
    return ClearCatalogSeedResult(
        inserted=len(inserted),
        skipped_collisions=skipped,
        diagnosis_links=len(links),
        currency=currency,
        catalog_version=payload["catalog_version"],
    )
