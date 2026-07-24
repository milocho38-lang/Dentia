"""add budget versioning traceability

Revision ID: 20260723_0017
Revises: 20260723_0016
Create Date: 2026-07-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260723_0017"
down_revision = "20260723_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "presupuestos",
        sa.Column("budget_series_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "presupuestos",
        sa.Column("previous_budget_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "presupuestos",
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "presupuestos",
        sa.Column(
            "es_version_vigente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "presupuestos",
        sa.Column("motivo_version", sa.Text(), nullable=True),
    )
    op.add_column(
        "presupuestos",
        sa.Column("budget_idempotency_key", sa.String(length=120), nullable=True),
    )

    op.execute("UPDATE presupuestos SET budget_series_id = id WHERE budget_series_id IS NULL")
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY empresa_id, budget_series_id
                    ORDER BY version DESC, aprobado_at DESC NULLS LAST, fecha_emision DESC
                ) AS rn
            FROM presupuestos
            WHERE estado = 'Aprobado'
        )
        UPDATE presupuestos p
        SET es_version_vigente = true
        FROM ranked
        WHERE p.id = ranked.id AND ranked.rn = 1
        """
    )

    op.alter_column("presupuestos", "budget_series_id", nullable=False)
    op.drop_constraint(
        "uq_presupuestos_empresa_tratamiento_version",
        "presupuestos",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_presupuestos_empresa_series_version",
        "presupuestos",
        ["empresa_id", "budget_series_id", "version"],
    )
    op.create_foreign_key(
        "fk_presupuestos_series",
        "presupuestos",
        "presupuestos",
        ["budget_series_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_presupuestos_previous",
        "presupuestos",
        "presupuestos",
        ["previous_budget_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_presupuestos_superseded_by",
        "presupuestos",
        "presupuestos",
        ["superseded_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_presupuestos_empresa_series",
        "presupuestos",
        ["empresa_id", "budget_series_id"],
    )
    op.create_index(
        "ix_presupuestos_budget_series_id",
        "presupuestos",
        ["budget_series_id"],
    )
    op.create_index("ix_presupuestos_previous", "presupuestos", ["previous_budget_id"])
    op.create_index("ix_presupuestos_superseded_by", "presupuestos", ["superseded_by_id"])
    op.create_index(
        "uq_presupuestos_empresa_idempotency_key",
        "presupuestos",
        ["empresa_id", "budget_idempotency_key"],
        unique=True,
        postgresql_where=sa.text("budget_idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "uq_presupuestos_current_approved_series",
        "presupuestos",
        ["empresa_id", "budget_series_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'Aprobado' AND es_version_vigente = true"),
    )
    op.create_index(
        "uq_presupuesto_detalle_presupuesto_procedimiento",
        "presupuesto_detalle",
        ["presupuesto_id", "procedimiento_id"],
        unique=True,
        postgresql_where=sa.text("procedimiento_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_presupuesto_detalle_presupuesto_procedimiento",
        table_name="presupuesto_detalle",
    )
    op.drop_index("uq_presupuestos_current_approved_series", table_name="presupuestos")
    op.drop_index("uq_presupuestos_empresa_idempotency_key", table_name="presupuestos")
    op.drop_index("ix_presupuestos_superseded_by", table_name="presupuestos")
    op.drop_index("ix_presupuestos_previous", table_name="presupuestos")
    op.execute("DROP INDEX IF EXISTS ix_presupuestos_budget_series_id")
    op.drop_index("ix_presupuestos_empresa_series", table_name="presupuestos")
    op.drop_constraint("fk_presupuestos_superseded_by", "presupuestos", type_="foreignkey")
    op.drop_constraint("fk_presupuestos_previous", "presupuestos", type_="foreignkey")
    op.drop_constraint("fk_presupuestos_series", "presupuestos", type_="foreignkey")
    op.drop_constraint("uq_presupuestos_empresa_series_version", "presupuestos", type_="unique")
    op.create_unique_constraint(
        "uq_presupuestos_empresa_tratamiento_version",
        "presupuestos",
        ["empresa_id", "tratamiento_id", "version"],
    )
    op.drop_column("presupuestos", "budget_idempotency_key")
    op.drop_column("presupuestos", "motivo_version")
    op.drop_column("presupuestos", "es_version_vigente")
    op.drop_column("presupuestos", "superseded_by_id")
    op.drop_column("presupuestos", "previous_budget_id")
    op.drop_column("presupuestos", "budget_series_id")
