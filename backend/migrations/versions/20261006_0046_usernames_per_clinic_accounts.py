"""add global usernames and scope contact email per company.

Rollout invariants:
- Existing account UUIDs, password hashes, roles, sessions and audit history are
  untouched; only the two username columns and uniqueness constraints change.
- Existing logins remain valid because username is backfilled from the already
  normalized, globally unique contact email.
- A downgrade is intentionally fail-closed once contact email is shared across
  companies. Operators must resolve those duplicates explicitly before retrying;
  this migration never deletes or merges accounts.

Revision ID: 20261006_0046
Revises: 20260926_0045
Create Date: 2026-10-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20261006_0046"
down_revision: str | Sequence[str] | None = "20260926_0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("username", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("username_normalizado", sa.String(length=320), nullable=True),
    )
    op.execute(
        """
        UPDATE usuarios
        SET username = correo_normalizado,
            username_normalizado = correo_normalizado
        """
    )
    op.alter_column("usuarios", "username", nullable=False)
    op.alter_column("usuarios", "username_normalizado", nullable=False)
    op.drop_constraint(
        "uq_usuarios_correo_normalizado",
        "usuarios",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_usuarios_username_normalizado",
        "usuarios",
        ["username_normalizado"],
    )
    op.create_unique_constraint(
        "uq_usuarios_empresa_correo_normalizado",
        "usuarios",
        ["empresa_id", "correo_normalizado"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    duplicate = connection.execute(
        sa.text(
            """
            SELECT correo_normalizado, count(*)
            FROM usuarios
            GROUP BY correo_normalizado
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate is not None:
        raise RuntimeError(
            "Downgrade bloqueado: existen correos compartidos entre clínicas. "
            "No se eliminarán ni fusionarán cuentas para restaurar la unicidad global."
        )

    op.drop_constraint(
        "uq_usuarios_empresa_correo_normalizado",
        "usuarios",
        type_="unique",
    )
    op.drop_constraint(
        "uq_usuarios_username_normalizado",
        "usuarios",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_usuarios_correo_normalizado",
        "usuarios",
        ["correo_normalizado"],
    )
    op.drop_column("usuarios", "username_normalizado")
    op.drop_column("usuarios", "username")
