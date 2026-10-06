from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.models.audit_event import AuditEvent


PREVIOUS_REVISION = "20260926_0045"
USERNAME_REVISION = "20261006_0046"
IMPORT_REVISION = "20261006_0047"


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    return Config(str(backend_root / "alembic.ini"))


def _snapshot(connection, user_id):
    user = connection.execute(
        text(
            """
            SELECT id, empresa_id, correo, correo_normalizado, password_hash,
                   auth_version, estado
            FROM usuarios
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().one()
    roles = connection.execute(
        text(
            """
            SELECT id, empresa_id, usuario_id, rol_id, is_active
            FROM usuario_roles
            WHERE usuario_id = :user_id
            ORDER BY id
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    sessions = connection.execute(
        text(
            """
            SELECT id, empresa_id, usuario_id, refresh_token_hash,
                   token_family_id, rotation_counter, revoked_at
            FROM auth_sessions
            WHERE usuario_id = :user_id
            ORDER BY id
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    audits = connection.execute(
        text(
            """
            SELECT id, empresa_id, usuario_id, session_id, entidad,
                   entidad_id, accion, resultado, detalle
            FROM auditoria_eventos
            WHERE usuario_id = :user_id
            ORDER BY id
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return {
        "user": dict(user),
        "roles": [dict(row) for row in roles],
        "sessions": [dict(row) for row in sessions],
        "audits": [dict(row) for row in audits],
    }


def test_username_migration_preserves_security_identity_and_downgrade_fails_closed(
    db_session, security_world
) -> None:
    user = security_world.tenant_a.admin.user
    other_company_user = security_world.tenant_b.admin.user
    auth_session = db_session.execute(
        text(
            "SELECT id FROM auth_sessions WHERE usuario_id = :user_id ORDER BY id LIMIT 1"
        ),
        {"user_id": user.id},
    ).scalar_one()
    audit = AuditEvent(
        company_id=user.company_id,
        user_id=user.id,
        session_id=auth_session,
        entity="user",
        entity_id=user.id,
        action="USERNAME_MIGRATION_SENTINEL",
        result="SUCCESS",
        detail={"preserve": True},
        ip_address="127.0.0.1",
        user_agent="username-migration-test",
    )
    db_session.add(audit)
    db_session.commit()
    engine = db_session.get_bind()
    with engine.connect() as connection:
        before = _snapshot(connection, user.id)

    db_session.close()
    config = _alembic_config()
    command.downgrade(config, PREVIOUS_REVISION)
    with engine.connect() as connection:
        columns = set(
            connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'usuarios'
                    """
                )
            ).scalars()
        )
        assert "username" not in columns
        assert "username_normalizado" not in columns
        assert _snapshot(connection, user.id) == before

    command.upgrade(config, USERNAME_REVISION)
    with engine.connect() as connection:
        after = _snapshot(connection, user.id)
        migrated_names = connection.execute(
            text(
                """
                SELECT username, username_normalizado
                FROM usuarios
                WHERE id = :user_id
                """
            ),
            {"user_id": user.id},
        ).one()
        assert after == before
        assert migrated_names.username == before["user"]["correo_normalizado"]
        assert migrated_names.username_normalizado == before["user"]["correo_normalizado"]

    shared_email = "migration-shared@example.test"
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE usuarios
                SET correo = :email, correo_normalizado = :email
                WHERE id IN (:user_id, :other_user_id)
                """
            ),
            {
                "email": shared_email,
                "user_id": user.id,
                "other_user_id": other_company_user.id,
            },
        )

    with pytest.raises(RuntimeError, match="Downgrade bloqueado"):
        command.downgrade(config, PREVIOUS_REVISION)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == USERNAME_REVISION
        rows = connection.execute(
            text(
                """
                SELECT id, empresa_id, correo_normalizado
                FROM usuarios
                WHERE id IN (:user_id, :other_user_id)
                ORDER BY id
                """
            ),
            {"user_id": user.id, "other_user_id": other_company_user.id},
        ).mappings().all()
        assert len(rows) == 2
        assert rows[0]["id"] != rows[1]["id"]
        assert rows[0]["empresa_id"] != rows[1]["empresa_id"]
        assert {row["correo_normalizado"] for row in rows} == {shared_email}

    # Leave the shared test database at the actual application head for tests
    # that run after this focused historical migration assertion.
    command.upgrade(config, IMPORT_REVISION)
