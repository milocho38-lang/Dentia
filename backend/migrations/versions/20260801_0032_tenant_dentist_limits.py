"""tenant dentist seat limits

Revision ID: 20260801_0032
Revises: 20260801_0031
"""

from alembic import op
import sqlalchemy as sa


revision = "20260801_0032"
down_revision = "20260801_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresas",
        sa.Column("max_active_dentists", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE empresas AS e
        SET max_active_dentists = CASE
            WHEN active_dentists.seats <= 1 THEN 1
            WHEN active_dentists.seats <= 3 THEN 3
            WHEN active_dentists.seats <= 5 THEN 5
            WHEN active_dentists.seats <= 10 THEN 10
            ELSE active_dentists.seats
        END
        FROM (
            SELECT
                e2.id AS empresa_id,
                COUNT(o.id) FILTER (
                    WHERE o.is_active IS TRUE
                      AND o.estado = 'Activo'
                      AND (
                          o.usuario_id IS NULL
                          OR (
                              u.is_active IS TRUE
                              AND u.estado = 'Activo'
                              AND u.empresa_id = e2.id
                          )
                      )
                ) AS seats
            FROM empresas AS e2
            LEFT JOIN odontologos AS o ON o.empresa_id = e2.id
            LEFT JOIN usuarios AS u ON u.id = o.usuario_id
            GROUP BY e2.id
        ) AS active_dentists
        WHERE active_dentists.empresa_id = e.id
        """
    )
    op.alter_column(
        "empresas",
        "max_active_dentists",
        nullable=False,
        server_default="1",
    )
    op.create_check_constraint(
        "ck_empresas_max_active_dentists_positive",
        "empresas",
        "max_active_dentists > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_empresas_max_active_dentists_positive",
        "empresas",
        type_="check",
    )
    op.drop_column("empresas", "max_active_dentists")
