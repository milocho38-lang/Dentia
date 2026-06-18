import argparse
import getpass
import sys

from app.database.session import SessionLocal
from app.services.bootstrap_service import (
    BootstrapError,
    BootstrapInput,
    bootstrap_installation,
    ensure_bootstrap_available,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inicializa una instalación local vacía de Dentia.",
    )
    parser.add_argument("--company-name", help="Nombre de la empresa inicial.")
    parser.add_argument("--company-slug", help="Slug técnico de la empresa.")
    parser.add_argument("--site-name", help="Nombre de la sede principal.")
    parser.add_argument("--admin-name", help="Nombre del administrador inicial.")
    parser.add_argument("--admin-email", help="Correo del administrador inicial.")
    return parser


def prompt_if_missing(value: str | None, label: str) -> str:
    if value:
        return value
    return input(f"{label}: ").strip()


def prompt_password() -> str:
    password = getpass.getpass("Contraseña del administrador: ")
    confirmation = getpass.getpass("Confirmar contraseña: ")
    if password != confirmation:
        raise BootstrapError("Las contraseñas no coinciden.")
    return password


def main() -> int:
    args = build_parser().parse_args()

    try:
        with SessionLocal() as session:
            ensure_bootstrap_available(session)

        data = BootstrapInput(
            company_name=prompt_if_missing(
                args.company_name,
                "Nombre de la empresa",
            ),
            company_slug=prompt_if_missing(
                args.company_slug,
                "Slug de la empresa",
            ),
            site_name=prompt_if_missing(
                args.site_name,
                "Nombre de la sede principal",
            ),
            admin_name=prompt_if_missing(
                args.admin_name,
                "Nombre del administrador",
            ),
            admin_email=prompt_if_missing(
                args.admin_email,
                "Correo del administrador",
            ),
            admin_password=prompt_password(),
        )

        with SessionLocal() as session:
            result = bootstrap_installation(session, data)
    except BootstrapError as exc:
        print(f"Bootstrap cancelado: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "Bootstrap fallido. No se aplicaron cambios.",
            file=sys.stderr,
        )
        raise

    print("Instalación inicial completada.")
    print(f"Empresa: {result.company_id}")
    print(f"Sede principal: {result.site_id}")
    print(f"Administrador: {result.admin_user_id}")
    print(f"Roles creados: {result.role_count}")
    print(f"Permisos creados: {result.permission_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
