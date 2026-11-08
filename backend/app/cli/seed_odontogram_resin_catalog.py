import argparse
from uuid import UUID

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.services.procedure_catalog_odontogram_seed_service import (
    preview_odontogram_resin_catalog,
    seed_odontogram_resin_catalog,
)
from app.services.procedure_catalog_seed_service import ProcedureCatalogSeedError


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run o backfill idempotente del lote clínico de ocho resinas."
    )
    parser.add_argument("--company-id", required=True, type=UUID)
    parser.add_argument("--actor-id", required=True, type=UUID)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Deshabilitado: se conserva para rechazar explícitamente intentos de escritura.",
    )
    args = parser.parse_args()
    with SessionLocal() as session:
        company = session.scalar(
            select(Company).where(Company.id == args.company_id).with_for_update()
        )
        actor = session.scalar(select(User).where(
            User.id == args.actor_id,
            User.company_id == args.company_id,
            User.status == "Activo",
        ))
        if company is None or actor is None:
            raise SystemExit("Empresa o actor empresarial activo no encontrado.")
        try:
            preview = preview_odontogram_resin_catalog(session, company)
            print(
                f"dry-run moneda={preview.currency} insertar={preview.would_insert} "
                f"colisiones={len(preview.collisions)} version={preview.catalog_version}"
            )
            for collision in preview.collisions:
                print(
                    "colision "
                    f"fila={collision['source_row']} existente_id={collision['existing_id']} "
                    f"nombre={collision['existing_name']!r} valor={collision['existing_value']}"
                )
            if not args.apply:
                session.rollback()
                print("dry-run: sin escrituras ni auditoría")
                return
            session.rollback()
            raise SystemExit(
                "Aplicación deshabilitada: --actor-id no autentica la identidad real del operador. "
                "Use únicamente dry-run hasta disponer de una ejecución autenticada y autorizada."
            )
        except ProcedureCatalogSeedError as exc:
            session.rollback()
            raise SystemExit(f"Carga omitida sin cambios: {exc}") from exc


if __name__ == "__main__":
    main()
