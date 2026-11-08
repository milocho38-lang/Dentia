import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.services.procedure_catalog_odontogram_clear_seed_service import (
    APPROVED_FILE_SHA256 as CLEAR_SHA256,
    preview_odontogram_clear_catalog,
    seed_odontogram_clear_catalog,
)
from app.services.procedure_catalog_odontogram_endodontic_seed_service import (
    APPROVED_FILE_SHA256 as ENDODONTIC_SHA256,
    preview_odontogram_endodontic_catalog,
    seed_odontogram_endodontic_catalog,
)
from app.services.procedure_catalog_odontogram_esthetic_seed_service import (
    APPROVED_FILE_SHA256 as ESTHETIC_SHA256,
    preview_odontogram_esthetic_catalog,
    seed_odontogram_esthetic_catalog,
)
from app.services.procedure_catalog_odontogram_extraction_seed_service import (
    APPROVED_FILE_SHA256 as EXTRACTION_SHA256,
    preview_odontogram_extraction_catalog,
    seed_odontogram_extraction_catalog,
)
from app.services.procedure_catalog_odontogram_planned_seed_service import (
    APPROVED_FILE_SHA256 as PLANNED_SHA256,
    preview_odontogram_planned_catalog,
    seed_odontogram_planned_catalog,
)
from app.services.procedure_catalog_odontogram_prosthetic_seed_service import (
    APPROVED_FILE_SHA256 as PROSTHETIC_SHA256,
    preview_odontogram_planned_catalog as preview_odontogram_prosthetic_catalog,
    seed_odontogram_planned_catalog as seed_odontogram_prosthetic_catalog,
)
from app.services.procedure_catalog_odontogram_seed_service import (
    APPROVED_FILE_SHA256 as RESIN_SHA256,
    preview_odontogram_resin_catalog,
    seed_odontogram_resin_catalog,
)


CONSOLIDATED_CATALOG_VERSION = "dentia-odontogram-clinical-83-v1"
_COMPONENT_MANIFESTS = {
    "clear_20": CLEAR_SHA256,
    "endodontic_18": ENDODONTIC_SHA256,
    "esthetic_4": ESTHETIC_SHA256,
    "extraction_11": EXTRACTION_SHA256,
    "planned_13": PLANNED_SHA256,
    "prosthetic_9": PROSTHETIC_SHA256,
    "resin_8": RESIN_SHA256,
}
CONSOLIDATED_MANIFEST_SHA256 = hashlib.sha256(
    json.dumps(
        {"catalog_version": CONSOLIDATED_CATALOG_VERSION, "components": _COMPONENT_MANIFESTS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()


@dataclass(frozen=True)
class ConsolidatedCatalogDryRunResult:
    would_insert: int
    collisions: tuple[dict, ...]
    currency: str
    catalog_version: str = CONSOLIDATED_CATALOG_VERSION


@dataclass(frozen=True)
class ConsolidatedCatalogSeedResult:
    inserted: int
    skipped_collisions: int
    diagnosis_links: int
    currency: str
    catalog_version: str = CONSOLIDATED_CATALOG_VERSION


def preview_odontogram_consolidated_catalog(
    session: Session, company: Company
) -> ConsolidatedCatalogDryRunResult:
    previews = (
        preview_odontogram_resin_catalog(session, company),
        preview_odontogram_clear_catalog(session, company),
        preview_odontogram_planned_catalog(session, company),
        preview_odontogram_endodontic_catalog(session, company),
        preview_odontogram_prosthetic_catalog(session, company),
        preview_odontogram_extraction_catalog(session, company),
        preview_odontogram_esthetic_catalog(session, company),
    )
    currencies = {item.currency for item in previews}
    if len(currencies) != 1:
        raise RuntimeError("Los componentes del catálogo clínico no coinciden en moneda.")
    return ConsolidatedCatalogDryRunResult(
        would_insert=sum(item.would_insert for item in previews),
        collisions=tuple(collision for item in previews for collision in item.collisions),
        currency=currencies.pop(),
    )


def seed_odontogram_consolidated_catalog(
    session: Session,
    company: Company,
    actor_id: UUID | None,
    *,
    operator_session_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ConsolidatedCatalogSeedResult:
    results = (
        seed_odontogram_resin_catalog(
            session,
            company,
            actor_id,
            operator_session_id=operator_session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        ),
        seed_odontogram_clear_catalog(session, company, actor_id),
        seed_odontogram_planned_catalog(session, company, actor_id),
        seed_odontogram_endodontic_catalog(session, company, actor_id),
        seed_odontogram_prosthetic_catalog(session, company, actor_id),
        seed_odontogram_extraction_catalog(session, company, actor_id),
        seed_odontogram_esthetic_catalog(session, company, actor_id),
    )
    currencies = {item.currency for item in results}
    if len(currencies) != 1:
        raise RuntimeError("Los componentes del catálogo clínico no coinciden en moneda.")
    inserted = sum(item.inserted for item in results)
    skipped = sum(item.skipped_collisions for item in results)
    diagnosis_links = sum(getattr(item, "diagnosis_links", 0) for item in results)
    currency = currencies.pop()
    session.add(
        AuditEvent(
            company_id=company.id,
            user_id=actor_id,
            session_id=operator_session_id,
            entity="procedure_catalog_seed",
            entity_id=company.id,
            action="PROCEDURE_CATALOG_ODONTOGRAM_CONSOLIDATED_SEEDED",
            result="SUCCESS",
            detail={
                "catalog_version": CONSOLIDATED_CATALOG_VERSION,
                "manifest_sha256": CONSOLIDATED_MANIFEST_SHA256,
                "component_manifests": _COMPONENT_MANIFESTS,
                "inserted": inserted,
                "skipped_collisions": skipped,
                "diagnosis_links": diagnosis_links,
                "currency": currency,
                "authenticated_operator": operator_session_id is not None,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
    session.flush()
    return ConsolidatedCatalogSeedResult(inserted, skipped, diagnosis_links, currency)
