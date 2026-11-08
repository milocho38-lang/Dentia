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
from app.models.treatment import ProcedureCatalogItem
from app.services.procedure_catalog_seed_service import (
    ProcedureCatalogSeedError,
    company_currency,
    normalize_catalog_name,
)


CATALOG_PATH = Path(__file__).resolve().parents[1] / "library_data" / "procedure_catalog_odontogram_planned_13_draft.json"
APPROVED_FILE_SHA256 = "5f572ef984cb79997b2fd74ae18e52a509fc250febdc067d8d030a3a9845d5c3"
EXPECTED_ROWS = {6, 231, 260, 261, 305, 308, 309, 310, 480, 481, 493, 517, 518}
EXPECTED_CODES = {"PLAN_CROWN", "DONE_CROWN", "PLAN_IMPLANT", "DONE_IMPLANT"}


@dataclass(frozen=True)
class PlannedCatalogDryRunResult:
    would_insert: int
    collisions: tuple[dict, ...]
    currency: str
    catalog_version: str


@dataclass(frozen=True)
class PlannedCatalogSeedResult:
    inserted: int
    skipped_collisions: int
    currency: str
    catalog_version: str


def _load_batch() -> dict:
    raw = CATALOG_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != APPROVED_FILE_SHA256:
        raise ProcedureCatalogSeedError("El lote planificado 13 no coincide con el manifiesto revisado.")
    payload = json.loads(raw)
    items = payload.get("items", [])
    if len(items) != 13 or {item.get("source_row") for item in items} != EXPECTED_ROWS:
        raise ProcedureCatalogSeedError("El lote planificado debe contener las trece filas esperadas.")
    names = [normalize_catalog_name(item["name"]) for item in items]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote planificado contiene nombres duplicados.")
    for item in items:
        try:
            clp = Decimal(item["source_price_clp"])
            cop = Decimal(item["fixed_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError("El lote planificado contiene un precio inválido.") from exc
        expected_pair = (
            ("PLAN_IMPLANT", "DONE_IMPLANT")
            if item["source_row"] == 231
            else ("PLAN_CROWN", "DONE_CROWN")
        )
        if (
            clp < 0 or cop < 0 or cop % 1000
            or item["suggested_scope_type"] != "TOOTH"
            or item["odontogram_behavior"] != "PLANNED_RESULT"
            or (item["planned_code"], item["default_performed_code"]) != expected_pair
        ):
            raise ProcedureCatalogSeedError(
                f"La fila {item['source_row']} contiene una regla planificada inesperada."
            )
    return payload


def preview_odontogram_planned_catalog(session: Session, company: Company) -> PlannedCatalogDryRunResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    source_by_name = {normalize_catalog_name(item["name"]): item for item in payload["items"]}
    existing = session.execute(
        select(
            ProcedureCatalogItem.id,
            ProcedureCatalogItem.name,
            ProcedureCatalogItem.normalized_name,
            ProcedureCatalogItem.suggested_value,
        ).where(
            ProcedureCatalogItem.company_id == company.id,
            ProcedureCatalogItem.normalized_name.in_(source_by_name),
        )
    ).all()
    collisions = tuple({
        "existing_id": str(row.id),
        "existing_name": row.name,
        "existing_value": str(row.suggested_value) if row.suggested_value is not None else None,
        "source_row": source_by_name[row.normalized_name]["source_row"],
        "source_name": source_by_name[row.normalized_name]["name"],
    } for row in existing)
    return PlannedCatalogDryRunResult(
        would_insert=len(payload["items"]) - len(collisions),
        collisions=collisions,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )


def seed_odontogram_planned_catalog(
    session: Session, company: Company, actor_id: UUID | None
) -> PlannedCatalogSeedResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    clinical = {item.code: item for item in session.scalars(
        select(OdontogramCatalogItem).where(
            OdontogramCatalogItem.company_id.is_(None),
            OdontogramCatalogItem.code.in_(EXPECTED_CODES),
            OdontogramCatalogItem.is_active.is_(True),
        )
    )}
    if set(clinical) != EXPECTED_CODES:
        raise ProcedureCatalogSeedError("Faltan símbolos globales requeridos por el lote planificado.")
    values = []
    for source in payload["items"]:
        value = Decimal(source["source_price_clp"] if currency == "CLP" else source["fixed_price_cop"])
        values.append({
            "company_id": company.id,
            "name": source["name"],
            "normalized_name": normalize_catalog_name(source["name"]),
            "suggested_value": value,
            "price_currency": currency,
            "price_provenance": {
                "catalog_version": payload["catalog_version"],
                "source_sha256": payload["source_sha256"],
                "approved_file_sha256": APPROVED_FILE_SHA256,
                "source_row": source["source_row"],
                "source_currency": "CLP",
                "source_price": source["source_price_clp"],
                "generated_currency": currency,
                "generated_value": str(value),
                "clp_to_cop_rate": payload["currency_policy"]["clp_to_cop_rate"],
                "runtime_conversion": False,
            },
            "suggested_scope_type": "TOOTH",
            "odontogram_behavior": "PLANNED_RESULT",
            "odontogram_scope_type": "TOOTH",
            "default_performed_catalog_item_id": clinical[source["default_performed_code"]].id,
            "is_active": True,
            "created_by": actor_id,
        })
    inserted = session.execute(
        pg_insert(ProcedureCatalogItem).values(values).on_conflict_do_nothing(
            constraint="uq_catalogo_proc_empresa_nombre_normalizado"
        ).returning(ProcedureCatalogItem.id)
    ).all()
    skipped = len(values) - len(inserted)
    session.add(AuditEvent(
        company_id=company.id,
        user_id=actor_id,
        entity="procedure_catalog_seed",
        entity_id=company.id,
        action="PROCEDURE_CATALOG_ODONTOGRAM_PLANNED_13_DRAFT_SEEDED",
        result="SUCCESS",
        detail={
            "catalog_version": payload["catalog_version"],
            "approved_file_sha256": APPROVED_FILE_SHA256,
            "inserted": len(inserted),
            "skipped_collisions": skipped,
            "currency": currency,
            "connected_to_runtime": False,
        },
    ))
    session.flush()
    return PlannedCatalogSeedResult(
        inserted=len(inserted),
        skipped_collisions=skipped,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )
