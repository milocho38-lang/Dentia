"""Explicit administrative CLI for the Aurora demo tenant."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import getpass
import json
import os
import sys
from uuid import UUID

from sqlalchemy.orm import Session

from app.database.session import engine
from app.services.demo_tenant_service import (
    DATASET_VERSION,
    DEMO_COMPANY_NAME,
    DEMO_COMPANY_SLUG,
    DemoStorageTransaction,
    DemoTenantError,
    DemoTenantOrchestrator,
    database_target,
    is_production_target,
    require_platform_actor,
)


def _uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("UUID inválido") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Administra el tenant demo seguro de Dentia.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="Muestra el plan sin mutar datos.")
    plan.add_argument("--operation", choices=["create", "update", "reset"], default="create")
    plan.add_argument("--company-id", type=_uuid)
    status = subparsers.add_parser("status", help="Inspecciona un tenant sin mutarlo.")
    status.add_argument("--company-id", required=True, type=_uuid)
    for command in ("create", "update", "reset"):
        item = subparsers.add_parser(command)
        item.add_argument("--dataset", choices=[DATASET_VERSION], default=DATASET_VERSION)
        item.add_argument("--company-id", type=_uuid, required=command != "create")
        item.add_argument("--actor-user-id", type=_uuid, required=True)
        item.add_argument("--apply", action="store_true", help="Aplica; sin esta opción es dry-run.")
        item.add_argument("--confirm-database-target")
        item.add_argument("--anchor-date", type=date.fromisoformat)
        item.add_argument("--confirm-environment")
        item.add_argument("--confirm-tenant")
        if command == "reset":
            item.add_argument("--backup-reference")
            item.add_argument("--confirm-reset")
    return parser


def _json(value) -> None:
    print(json.dumps(asdict(value), ensure_ascii=False, indent=2, default=str))


def _require_production_confirmation(args: argparse.Namespace) -> None:
    if args.command == "reset":
        expected = f"RESET CLINICA DENTAL AURORA {args.company_id}"
        if args.confirm_reset != expected:
            raise DemoTenantError("La frase inequívoca de reset no coincide.")
    if not is_production_target():
        return
    if args.confirm_environment != "PRODUCTION":
        raise DemoTenantError("Producción requiere --confirm-environment PRODUCTION.")
    expected_tenant = str(args.company_id) if args.company_id else "CREATE"
    if args.confirm_tenant != expected_tenant:
        raise DemoTenantError(f"Producción requiere --confirm-tenant {expected_tenant}.")
    if args.command == "reset":
        if not args.backup_reference:
            raise DemoTenantError("Reset productivo requiere --backup-reference.")


def _require_apply_confirmation(args: argparse.Namespace) -> None:
    expected = database_target()
    if args.confirm_database_target != expected:
        raise DemoTenantError(
            f"Confirma el destino saneado con --confirm-database-target {expected}."
        )
    _require_production_confirmation(args)


def _secret(name: str, prompt: str, *, required: bool) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if not required:
        return None
    if not sys.stdin.isatty():
        if required:
            raise DemoTenantError(f"Falta el secreto {name}.")
        return None
    value = getpass.getpass(prompt).strip()
    if required and not value:
        raise DemoTenantError(f"Falta el secreto {name}.")
    return value or None


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command in {"create", "update", "reset"} and not args.apply:
        with Session(engine) as session:
            _json(DemoTenantOrchestrator(session).plan(args.command, args.company_id, apply=False))
        return 0
    if args.command == "plan":
        with Session(engine) as session:
            _json(DemoTenantOrchestrator(session).plan(args.operation, args.company_id, apply=False))
        return 0
    if args.command == "status":
        with Session(engine) as session:
            _json(DemoTenantOrchestrator(session).status(args.company_id))
        return 0

    _require_apply_confirmation(args)
    sink_recipient = _secret(
        "DENTIA_DEMO_EMAIL_SINK_RECIPIENT",
        "Destinatario interno controlado del sink demo: ",
        required=True,
    )
    admin_email = os.getenv("DENTIA_DEMO_ADMIN_EMAIL", "valentina@aurora.demo.invalid")
    admin_password = _secret(
        "DENTIA_DEMO_ADMIN_PASSWORD",
        "Contraseña administrada para la cuenta demo: ",
        required=args.command == "create",
    )

    storage: DemoStorageTransaction | None = None
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    database_committed = False
    try:
        actor = require_platform_actor(session, args.actor_user_id)
        orchestrator = DemoTenantOrchestrator(session)
        if args.command == "create":
            result = orchestrator.create(
                actor,
                admin_email=admin_email,
                admin_password=admin_password,
                sink_recipient=sink_recipient,
                anchor=args.anchor_date,
            )
            storage = orchestrator.storage_transaction
        elif args.command == "update":
            storage = DemoStorageTransaction(args.company_id)
            storage.snapshot()
            result = orchestrator.update(
                actor,
                args.company_id,
                admin_password=admin_password,
                sink_recipient=sink_recipient,
                anchor=args.anchor_date,
            )
        else:
            storage = DemoStorageTransaction(args.company_id)
            storage.snapshot()
            storage.quarantine()
            result, deleted = orchestrator.reset(
                actor,
                args.company_id,
                sink_recipient=sink_recipient,
                anchor=args.anchor_date,
            )
        transaction.commit()
        database_committed = True
        if storage:
            storage.commit()
        _json(result)
        if args.command == "reset":
            print(json.dumps({"deleted": deleted}, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        if storage is None and "orchestrator" in locals():
            storage = orchestrator.storage_transaction
        if transaction.is_active:
            transaction.rollback()
        if storage and not database_committed:
            storage.rollback()
        raise
    finally:
        session.close()
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DemoTenantError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
