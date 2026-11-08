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
from app.services.procedure_catalog_seed_service import ProcedureCatalogSeedError, company_currency, normalize_catalog_name


CATALOG_PATH = Path(__file__).resolve().parents[1] / "library_data" / "procedure_catalog_odontogram_resin_8.json"
APPROVED_FILE_SHA256 = "b03b322654d0168e9c9930c0cb2d1f9f18189a8e0cc6d05c9d64670ee3bedef2"
EXPECTED_CODES = {"FIND_CARIES", "FIND_FRACTURE", "DONE_RESIN"}


@dataclass(frozen=True)
class OdontogramCatalogSeedResult:
    inserted: int
    skipped_collisions: int
    diagnosis_links: int
    currency: str
    catalog_version: str


@dataclass(frozen=True)
class OdontogramCatalogDryRunResult:
    would_insert: int
    collisions: tuple[dict, ...]
    currency: str
    catalog_version: str


def _load_batch() -> dict:
    raw = CATALOG_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != APPROVED_FILE_SHA256:
        raise ProcedureCatalogSeedError("El lote de resinas no coincide con el manifiesto revisado.")
    payload = json.loads(raw)
    items = payload.get("items", [])
    if len(items) != 8 or len({row["source_row"] for row in items}) != 8:
        raise ProcedureCatalogSeedError("El lote de resinas debe contener ocho filas fuente únicas.")
    names = [normalize_catalog_name(row["name"]) for row in items]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote de resinas contiene nombres duplicados.")
    for row in items:
        try:
            clp, cop = Decimal(row["source_price_clp"]), Decimal(row["suggested_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError("El lote de resinas contiene un precio inválido.") from exc
        codes = set(row.get("allowed_diagnosis_codes", [])) | {row.get("default_performed_code")}
        if (
            clp < 0 or cop < 0 or cop % 1000
            or row.get("source_note") != "por caries o fractura"
            or row.get("source_scope") != "por diente y cara"
            or row.get("suggested_scope_type") != "TOOTH_SURFACE"
            or row.get("odontogram_behavior") != "REQUIRES_DIAGNOSIS"
            or codes != EXPECTED_CODES
        ):
            raise ProcedureCatalogSeedError("El lote de resinas contiene una regla clínica o monetaria inesperada.")
    return payload


def preview_odontogram_resin_catalog(session: Session, company: Company) -> OdontogramCatalogDryRunResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    normalized_to_source = {
        normalize_catalog_name(item["name"]): item for item in payload["items"]
    }
    existing = session.execute(select(
        ProcedureCatalogItem.id,
        ProcedureCatalogItem.name,
        ProcedureCatalogItem.normalized_name,
        ProcedureCatalogItem.suggested_value,
    ).where(
        ProcedureCatalogItem.company_id == company.id,
        ProcedureCatalogItem.normalized_name.in_(normalized_to_source),
    )).all()
    collisions = tuple({
        "existing_id": str(row.id),
        "existing_name": row.name,
        "existing_value": str(row.suggested_value) if row.suggested_value is not None else None,
        "source_row": normalized_to_source[row.normalized_name]["source_row"],
        "source_name": normalized_to_source[row.normalized_name]["name"],
    } for row in existing)
    return OdontogramCatalogDryRunResult(
        would_insert=len(payload["items"]) - len(collisions),
        collisions=collisions,
        currency=currency,
        catalog_version=payload["catalog_version"],
    )


def seed_odontogram_resin_catalog(
    session: Session,
    company: Company,
    actor_id: UUID | None,
    *,
    operator_session_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> OdontogramCatalogSeedResult:
    payload = _load_batch()
    currency = company_currency(company.country)
    clinical_items = {item.code: item for item in session.scalars(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.company_id.is_(None),
        OdontogramCatalogItem.code.in_(EXPECTED_CODES),
        OdontogramCatalogItem.is_active.is_(True),
    ))}
    if set(clinical_items) != EXPECTED_CODES:
        raise ProcedureCatalogSeedError("Faltan elementos clínicos globales requeridos por el lote de resinas.")
    if clinical_items["DONE_RESIN"].type != "PERFORMED_PROCEDURE" or any(
        clinical_items[code].type not in {"FINDING", "DIAGNOSIS"} for code in ("FIND_CARIES", "FIND_FRACTURE")
    ):
        raise ProcedureCatalogSeedError("Los elementos clínicos requeridos no tienen el tipo esperado.")

    values = []
    for source in payload["items"]:
        value = Decimal(source["source_price_clp"] if currency == "CLP" else source["suggested_price_cop"])
        provenance = {
            "catalog_version": payload["catalog_version"], "source_sha256": payload["source_sha256"],
            "approved_file_sha256": APPROVED_FILE_SHA256, "source_row": source["source_row"],
            "source_currency": "CLP", "source_price": source["source_price_clp"],
            "generated_currency": currency, "generated_value": str(value),
            "currency_role": "IMPORT_ORIGIN_NOT_CURRENT_DISPLAY_CURRENCY",
            "source_verification": payload["source_verification"],
        }
        if currency == "COP": provenance.update(payload["cop_price_basis"])
        values.append({
            "company_id": company.id, "name": source["name"], "normalized_name": normalize_catalog_name(source["name"]),
            "suggested_value": value, "price_currency": currency, "price_provenance": provenance,
            "suggested_scope_type": "TOOTH_SURFACE", "odontogram_behavior": "REQUIRES_DIAGNOSIS",
            "odontogram_scope_type": "TOOTH_SURFACE",
            "default_performed_catalog_item_id": clinical_items["DONE_RESIN"].id,
            "is_active": True, "created_by": actor_id,
        })
    inserted_ids = session.execute(pg_insert(ProcedureCatalogItem).values(values).on_conflict_do_nothing(
        constraint="uq_catalogo_proc_empresa_nombre_normalizado"
    ).returning(ProcedureCatalogItem.id)).scalars().all()
    links = [{"company_id": company.id, "procedure_catalog_id": procedure_id,
              "odontogram_catalog_item_id": clinical_items[code].id, "is_active": True}
             for procedure_id in inserted_ids for code in ("FIND_CARIES", "FIND_FRACTURE")]
    if links: session.execute(pg_insert(ProcedureCatalogDiagnosis).values(links))
    skipped = len(values) - len(inserted_ids)
    session.add(AuditEvent(
        company_id=company.id, user_id=actor_id, session_id=operator_session_id,
        entity="procedure_catalog_seed", entity_id=company.id,
        action="PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED", result="SUCCESS",
        detail={"catalog_version": payload["catalog_version"], "source_sha256": payload["source_sha256"],
                "approved_file_sha256": APPROVED_FILE_SHA256, "inserted": len(inserted_ids),
                "skipped_collisions": skipped, "diagnosis_links": len(links), "currency": currency,
                "authenticated_operator": operator_session_id is not None},
        ip_address=ip_address,
        user_agent=user_agent,
    ))
    session.flush()
    return OdontogramCatalogSeedResult(len(inserted_ids), skipped, len(links), currency, payload["catalog_version"])
