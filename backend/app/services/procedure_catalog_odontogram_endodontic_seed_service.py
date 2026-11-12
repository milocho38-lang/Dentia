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


CATALOG_PATH = Path(__file__).resolve().parents[1] / "library_data" / "procedure_catalog_odontogram_endodontic_18_draft.json"
APPROVED_FILE_SHA256 = "0667a9b55cd8e9937f4d6093b69d841fe0f18ecdf08496cbacb422be6c0fec05"
EXPECTED_ROWS = set(range(179, 193)) | {282, 283, 292, 293}
PRIMARY_ROWS = {282, 283, 292, 293}
EXPECTED_CODES = {"PLAN_ENDO", "DONE_ENDO", "FIND_CARIES", "FIND_FRACTURE"}


@dataclass(frozen=True)
class EndodonticCatalogDryRunResult:
    would_insert: int
    collisions: tuple[dict, ...]
    currency: str
    catalog_version: str


@dataclass(frozen=True)
class EndodonticCatalogSeedResult:
    inserted: int
    skipped_collisions: int
    currency: str
    catalog_version: str


def _load_batch() -> dict:
    raw = CATALOG_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != APPROVED_FILE_SHA256:
        raise ProcedureCatalogSeedError("El lote endodóntico 18 no coincide con el manifiesto revisado.")
    payload = json.loads(raw)
    items = payload.get("items", [])
    if len(items) != 18 or {item.get("source_row") for item in items} != EXPECTED_ROWS:
        raise ProcedureCatalogSeedError("El lote endodóntico debe contener las dieciocho filas esperadas.")
    names = [normalize_catalog_name(item["name"]) for item in items]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote endodóntico contiene nombres duplicados.")
    for item in items:
        try:
            clp = Decimal(item["source_price_clp"])
            cop = Decimal(item["fixed_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError("El lote endodóntico contiene un precio inválido.") from exc
        allowed = item.get("optional_diagnosis_codes")
        expected_allowed = ["FIND_CARIES", "FIND_FRACTURE"]
        if (
            clp < 0
            or cop < 0
            or cop % 1000
            or item.get("suggested_scope_type") != "TOOTH"
            or item.get("odontogram_behavior") != "PLANNED_RESULT"
            or (item.get("planned_code"), item.get("default_performed_code")) != ("PLAN_ENDO", "DONE_ENDO")
            or allowed != expected_allowed
            or item.get("required_dentition")
            != ("PRIMARY" if item["source_row"] in PRIMARY_ROWS else None)
        ):
            raise ProcedureCatalogSeedError(f"La fila {item['source_row']} contiene una regla endodóntica inesperada.")
    return payload


def preview_odontogram_endodontic_catalog(session: Session, company: Company) -> EndodonticCatalogDryRunResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    source_by_name = {normalize_catalog_name(item["name"]): item for item in payload["items"]}
    existing = session.execute(
        select(ProcedureCatalogItem.id, ProcedureCatalogItem.name, ProcedureCatalogItem.normalized_name, ProcedureCatalogItem.suggested_value).where(
            ProcedureCatalogItem.company_id == company.id,
            ProcedureCatalogItem.normalized_name.in_(source_by_name),
        )
    ).all()
    collisions = tuple(
        {
            "existing_id": str(row.id),
            "existing_name": row.name,
            "existing_value": str(row.suggested_value) if row.suggested_value is not None else None,
            "source_row": source_by_name[row.normalized_name]["source_row"],
            "source_name": source_by_name[row.normalized_name]["name"],
        }
        for row in existing
    )
    return EndodonticCatalogDryRunResult(
        would_insert=18 - len(collisions),
        collisions=collisions,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )


def seed_odontogram_endodontic_catalog(
    session: Session, company: Company, actor_id: UUID | None
) -> EndodonticCatalogSeedResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    clinical = {
        item.code: item
        for item in session.scalars(
            select(OdontogramCatalogItem).where(
                OdontogramCatalogItem.company_id.is_(None),
                OdontogramCatalogItem.code.in_(EXPECTED_CODES),
                OdontogramCatalogItem.is_active.is_(True),
            )
        )
    }
    if set(clinical) != EXPECTED_CODES:
        raise ProcedureCatalogSeedError("Faltan símbolos globales requeridos por el lote endodóntico.")

    values = []
    source_by_name = {}
    for source in payload["items"]:
        value = Decimal(source["source_price_clp"] if currency == "CLP" else source["fixed_price_cop"])
        normalized = normalize_catalog_name(source["name"])
        source_by_name[normalized] = source
        values.append(
            {
                "company_id": company.id,
                "name": source["name"],
                "normalized_name": normalized,
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
                    "required_dentition": source.get("required_dentition"),
                },
                "suggested_scope_type": "TOOTH",
                "odontogram_behavior": "PLANNED_RESULT",
                "odontogram_scope_type": "TOOTH",
                "default_performed_catalog_item_id": clinical["DONE_ENDO"].id,
                "is_active": True,
                "created_by": actor_id,
            }
        )
    inserted_rows = session.execute(
        pg_insert(ProcedureCatalogItem)
        .values(values)
        .on_conflict_do_nothing(constraint="uq_catalogo_proc_empresa_nombre_normalizado")
        .returning(ProcedureCatalogItem.id, ProcedureCatalogItem.normalized_name)
    ).all()
    inserted_by_name = {row.normalized_name: row.id for row in inserted_rows}
    diagnostic_links = []
    for normalized, procedure_id in inserted_by_name.items():
        for code in source_by_name[normalized]["optional_diagnosis_codes"]:
            diagnostic_links.append(
                {
                    "company_id": company.id,
                    "procedure_catalog_id": procedure_id,
                    "odontogram_catalog_item_id": clinical[code].id,
                    "is_active": True,
                }
            )
    if diagnostic_links:
        session.execute(
            pg_insert(ProcedureCatalogDiagnosis)
            .values(diagnostic_links)
            .on_conflict_do_nothing(constraint="uq_catalogo_proc_diagnostico_item")
        )
    skipped = len(values) - len(inserted_rows)
    session.add(
        AuditEvent(
            company_id=company.id,
            user_id=actor_id,
            entity="procedure_catalog_seed",
            entity_id=company.id,
            action="PROCEDURE_CATALOG_ODONTOGRAM_ENDODONTIC_18_DRAFT_SEEDED",
            result="SUCCESS",
            detail={
                "catalog_version": payload["catalog_version"],
                "approved_file_sha256": APPROVED_FILE_SHA256,
                "inserted": len(inserted_rows),
                "skipped_collisions": skipped,
                "currency": currency,
                "connected_to_runtime": False,
            },
        )
    )
    session.flush()
    return EndodonticCatalogSeedResult(
        inserted=len(inserted_rows),
        skipped_collisions=skipped,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )
