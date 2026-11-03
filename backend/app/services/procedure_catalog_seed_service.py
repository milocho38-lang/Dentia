import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.treatment import ProcedureCatalogItem
from app.core.config import settings


CATALOG_PATH = Path(__file__).resolve().parents[1] / "library_data" / "procedure_catalog_initial_173.json"
THOUSAND = Decimal("1000")
TEST_REFERENCE_RATE = Decimal("3.2126")
TEST_REFERENCE_OBSERVED_AT = "2026-11-02T09:47:00Z"


class ProcedureCatalogSeedError(RuntimeError):
    pass


@dataclass(frozen=True)
class CatalogConversion:
    clp_to_cop_rate: Decimal | None = None
    source: str | None = None
    observed_at_utc: str | None = None
    is_reference: bool = False
    allow_reference: bool = False


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


def conversion_from_settings() -> CatalogConversion:
    try:
        rate = Decimal(settings.procedure_catalog_clp_to_cop_rate) if settings.procedure_catalog_clp_to_cop_rate else None
    except InvalidOperation as exc:
        raise ProcedureCatalogSeedError("La tasa CLP/COP configurada no es decimal válida.") from exc
    return CatalogConversion(rate, settings.procedure_catalog_rate_source,
        settings.procedure_catalog_rate_observed_at_utc,
        settings.procedure_catalog_rate_is_reference, False)


def _load_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if len(payload.get("items", [])) != 173:
        raise ProcedureCatalogSeedError("El lote inicial debe contener exactamente 173 filas.")
    names = [normalize_catalog_name(row["name"]) for row in payload["items"]]
    if len(names) != len(set(names)):
        raise ProcedureCatalogSeedError("El lote inicial contiene nombres normalizados duplicados.")
    return payload


def _cop_value(clp: Decimal, conversion: CatalogConversion, now: datetime | None = None) -> Decimal:
    if not conversion.clp_to_cop_rate or conversion.clp_to_cop_rate <= 0:
        raise ProcedureCatalogSeedError("La carga COP requiere una tasa CLP/COP positiva.")
    if not conversion.source or not conversion.observed_at_utc:
        raise ProcedureCatalogSeedError("La carga COP requiere fuente y fecha UTC de la tasa.")
    try:
        observed = datetime.fromisoformat(conversion.observed_at_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProcedureCatalogSeedError("La fecha de la tasa no es ISO-8601 válida.") from exc
    if observed.tzinfo is None or observed.utcoffset() != timedelta(0):
        raise ProcedureCatalogSeedError("La fecha de la tasa debe incluir offset UTC +00:00 o Z.")
    current = now or datetime.now(timezone.utc)
    if observed > current:
        raise ProcedureCatalogSeedError("La fecha de la tasa no puede estar en el futuro.")
    if current - observed > timedelta(hours=24):
        raise ProcedureCatalogSeedError("La tasa tiene más de 24 horas y debe renovarse.")
    test_reference_instant = datetime.fromisoformat(TEST_REFERENCE_OBSERVED_AT.replace("Z", "+00:00"))
    known_test_reference = conversion.clp_to_cop_rate == TEST_REFERENCE_RATE and observed == test_reference_instant
    if (conversion.is_reference or known_test_reference) and not conversion.allow_reference:
        raise ProcedureCatalogSeedError("La tasa marcada como referencia no puede usarse para una carga real.")
    return (clp * conversion.clp_to_cop_rate / THOUSAND).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ) * THOUSAND


def planned_catalog_rows(country: str | None, conversion: CatalogConversion,
                         now: datetime | None = None) -> tuple[dict, list[dict]]:
    payload = _load_catalog()
    currency = company_currency(country)
    planned = []
    for source in payload["items"]:
        try:
            clp = Decimal(source["source_price_clp"])
        except InvalidOperation as exc:
            raise ProcedureCatalogSeedError("Precio CLP inválido en el lote.") from exc
        value = clp if currency == "CLP" else _cop_value(clp, conversion, now)
        provenance = {
            "catalog_version": payload["catalog_version"], "source_sha256": payload["source_sha256"],
            "source_row": source["source_row"], "source_currency": "CLP", "source_price": str(clp),
            "generated_currency": currency, "generated_value": str(value),
            "currency_role": "IMPORT_ORIGIN_NOT_CURRENT_DISPLAY_CURRENCY",
        }
        if currency == "COP":
            provenance.update({"clp_to_cop_rate": str(conversion.clp_to_cop_rate),
                "rate_source": conversion.source, "rate_observed_at_utc": conversion.observed_at_utc,
                "rounding": "NEAREST_1000_COP_HALF_UP"})
        planned.append({**source, "normalized_name": normalize_catalog_name(source["name"]),
                        "suggested_value": value, "price_currency": currency,
                        "price_provenance": provenance})
    return payload, planned


def seed_initial_procedure_catalog(session: Session, company: Company, actor_id: UUID,
                                   conversion: CatalogConversion) -> CatalogSeedResult:
    payload, rows = planned_catalog_rows(company.country, conversion)
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
                "inserted": inserted, "skipped_collisions": skipped, "currency": currency}))
    session.flush()
    return CatalogSeedResult(inserted, skipped, currency, payload["catalog_version"])
