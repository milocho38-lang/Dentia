import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.treatment import ProcedureCatalogItem
CATALOG_PATH = Path(__file__).resolve().parents[1] / "library_data" / "procedure_catalog_initial_173.json"
APPROVED_PAYLOAD_SHA256 = "9ba8bf0c2ddaa2524ce272ec5a7c19b47a0fbede704fb47be05d1ca7798b8d13"
APPROVED_SCOPES = {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}


class ProcedureCatalogSeedError(RuntimeError):
    pass


@dataclass(frozen=True)
class CatalogSeedResult:
    inserted: int
    skipped_collisions: int
    currency: str
    catalog_version: str


def normalize_catalog_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def optional_company_currency(country: str | None) -> str | None:
    normalized = (country or "").strip().casefold()
    if normalized in {"chile", "cl"}:
        return "CLP"
    if normalized in {"colombia", "co"}:
        return "COP"
    return None


def company_currency(country: str | None) -> str:
    currency = optional_company_currency(country)
    if currency:
        return currency
    raise ProcedureCatalogSeedError(f"País sin moneda de catálogo aprobada: {country!r}.")


def record_unsupported_country_skip(session: Session, company: Company, actor_id: UUID | None) -> None:
    session.add(AuditEvent(
        company_id=company.id,
        user_id=actor_id,
        entity="procedure_catalog_seed",
        entity_id=company.id,
        action="PROCEDURE_CATALOG_SEED_SKIPPED",
        result="SKIPPED",
        detail={
            "reason": "UNSUPPORTED_OR_MISSING_COUNTRY",
            "country": company.country,
            "display_currency": "moneda local",
        },
    ))
    session.flush()


def _load_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if len(payload.get("items", [])) != 173:
        raise ProcedureCatalogSeedError("El lote inicial debe contener exactamente 173 filas.")
    payload_digest = hashlib.sha256(json.dumps(
        {key: payload.get(key) for key in (
            "catalog_version", "source_sha256", "cop_price_basis", "items"
        )},
        ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if payload_digest != APPROVED_PAYLOAD_SHA256:
        raise ProcedureCatalogSeedError("El lote inicial no coincide con el manifiesto aprobado.")
    names = [normalize_catalog_name(row["name"]) for row in payload["items"]]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote inicial contiene nombres normalizados duplicados.")
    for row in payload["items"]:
        try:
            clp = Decimal(row["source_price_clp"])
            cop = Decimal(row["suggested_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError("El lote aprobado contiene un precio inválido.") from exc
        if clp < 0 or cop < 0 or cop % 1000:
            raise ProcedureCatalogSeedError("El lote aprobado contiene un precio fuera de regla.")
        if row.get("suggested_scope_type") not in APPROVED_SCOPES:
            raise ProcedureCatalogSeedError("El lote aprobado contiene un alcance inválido.")
    return payload


def planned_catalog_rows(country: str | None) -> tuple[dict, list[dict]]:
    payload = _load_catalog()
    currency = company_currency(country)
    basis = payload.get("cop_price_basis") or {}
    planned = []
    for source in payload["items"]:
        try:
            clp = Decimal(source["source_price_clp"])
            cop = Decimal(source["suggested_price_cop"])
        except (InvalidOperation, KeyError) as exc:
            raise ProcedureCatalogSeedError("Precio inválido en el lote aprobado.") from exc
        value = clp if currency == "CLP" else cop
        provenance = {
            "catalog_version": payload["catalog_version"], "source_sha256": payload["source_sha256"],
            "approved_payload_sha256": APPROVED_PAYLOAD_SHA256,
            "source_row": source["source_row"], "source_currency": "CLP", "source_price": str(clp),
            "generated_currency": currency, "generated_value": str(value),
            "currency_role": "IMPORT_ORIGIN_NOT_CURRENT_DISPLAY_CURRENCY",
        }
        if currency == "COP":
            provenance.update({"clp_to_cop_rate": basis.get("clp_to_cop_rate"),
                "rate_source": basis.get("rate_source"),
                "rate_observed_at_utc": basis.get("rate_observed_at_utc"),
                "rounding": basis.get("rounding")})
        planned.append({**source, "normalized_name": normalize_catalog_name(source["name"]),
                        "suggested_value": value, "price_currency": currency,
                        "price_provenance": provenance})
    return payload, planned


def seed_initial_procedure_catalog(session: Session, company: Company, actor_id: UUID | None) -> CatalogSeedResult:
    payload, rows = planned_catalog_rows(company.country)
    values = [{"company_id": company.id, "name": row["name"],
        "normalized_name": row["normalized_name"], "suggested_value": row["suggested_value"],
        "price_currency": row["price_currency"], "price_provenance": row["price_provenance"],
        "suggested_scope_type": row["suggested_scope_type"], "odontogram_behavior": "NO_CHANGE",
        "is_active": True, "created_by": actor_id} for row in rows]
    statement = pg_insert(ProcedureCatalogItem).values(values).on_conflict_do_nothing(
        constraint="uq_catalogo_proc_empresa_nombre_normalizado"
    ).returning(ProcedureCatalogItem.normalized_name)
    inserted = len(session.execute(statement).scalars().all())
    skipped = len(rows) - inserted
    currency = company_currency(company.country)
    session.add(AuditEvent(company_id=company.id, user_id=actor_id,
        entity="procedure_catalog_seed", entity_id=company.id,
        action="PROCEDURE_CATALOG_SEEDED", result="SUCCESS",
        detail={"catalog_version": payload["catalog_version"], "source_sha256": payload["source_sha256"],
                "approved_payload_sha256": APPROVED_PAYLOAD_SHA256,
                "inserted": inserted, "skipped_collisions": skipped, "currency": currency}))
    session.flush()
    return CatalogSeedResult(inserted, skipped, currency, payload["catalog_version"])
