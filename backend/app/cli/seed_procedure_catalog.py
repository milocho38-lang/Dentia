import argparse
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.services.procedure_catalog_seed_service import (
    CatalogConversion,
    ProcedureCatalogSeedError,
    company_currency,
    seed_initial_procedure_catalog,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Precarga idempotente del catálogo inicial por empresa.")
    parser.add_argument("--company-id", required=True, type=UUID)
    parser.add_argument("--actor-id", required=True, type=UUID)
    parser.add_argument("--clp-cop-rate", type=Decimal)
    parser.add_argument("--rate-source")
    parser.add_argument("--rate-observed-at-utc")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as session:
        company = session.scalar(select(Company).where(Company.id == args.company_id).with_for_update())
        actor = session.scalar(select(User).where(User.id == args.actor_id, User.company_id == args.company_id))
        if company is None or actor is None:
            raise SystemExit("Empresa o actor empresarial no encontrado.")
        try:
            company_currency(company.country)
            result = seed_initial_procedure_catalog(session, company, actor.id,
                CatalogConversion(args.clp_cop_rate, args.rate_source, args.rate_observed_at_utc))
        except ProcedureCatalogSeedError as exc:
            raise SystemExit(
                f"Carga omitida: {exc} Configure explícitamente Chile o Colombia; "
                "no se infiere moneda para un país ausente o no soportado."
            ) from exc
        print(f"insertados={result.inserted} colisiones={result.skipped_collisions} moneda={result.currency}")
        if args.dry_run:
            session.rollback()
            print("dry-run: transacción revertida")
        else:
            session.commit()


if __name__ == "__main__":
    main()
