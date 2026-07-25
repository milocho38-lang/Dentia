"""add treatment-first odontogram catalog configuration

Revision ID: 20260724_0020
Revises: 20260724_0019
Create Date: 2026-07-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260724_0020"
down_revision = "20260724_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "catalogo_procedimientos",
        sa.Column(
            "odontogram_behavior",
            sa.String(length=40),
            nullable=False,
            server_default="UNCONFIGURED",
        ),
    )
    op.add_column(
        "catalogo_procedimientos",
        sa.Column("odontogram_scope_type", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "catalogo_procedimientos",
        sa.Column(
            "default_performed_catalog_item_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        "odontogram_behavior IN ('UNCONFIGURED', 'NO_CHANGE', 'OPTIONAL_DIAGNOSIS', 'REQUIRES_DIAGNOSIS')",
    )
    op.create_check_constraint(
        "ck_catalogo_proc_odontogram_scope_type",
        "catalogo_procedimientos",
        "odontogram_scope_type IS NULL OR odontogram_scope_type IN ('GENERAL', 'ZONE', 'TOOTH', 'TOOTH_SURFACE')",
    )
    op.create_foreign_key(
        "fk_catalogo_proc_default_performed_catalog_item",
        "catalogo_procedimientos",
        "odontograma_catalogo",
        ["default_performed_catalog_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_catalogo_proc_empresa_odontograma",
        "catalogo_procedimientos",
        ["empresa_id", "odontogram_behavior"],
    )

    op.create_table(
        "catalogo_procedimientos_diagnosticos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("catalogo_procedimiento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontograma_catalog_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["catalogo_procedimiento_id"],
            ["catalogo_procedimientos.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["odontograma_catalog_item_id"],
            ["odontograma_catalogo.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "catalogo_procedimiento_id",
            "odontograma_catalog_item_id",
            name="uq_catalogo_proc_diagnostico_item",
        ),
    )
    op.create_index(
        "ix_catalogo_proc_diag_empresa_proc",
        "catalogo_procedimientos_diagnosticos",
        ["empresa_id", "catalogo_procedimiento_id"],
    )
    op.create_index(
        "ix_catalogo_proc_diag_catalog_item",
        "catalogo_procedimientos_diagnosticos",
        ["odontograma_catalog_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalogo_proc_diag_catalog_item", table_name="catalogo_procedimientos_diagnosticos")
    op.drop_index("ix_catalogo_proc_diag_empresa_proc", table_name="catalogo_procedimientos_diagnosticos")
    op.drop_table("catalogo_procedimientos_diagnosticos")
    op.drop_index("ix_catalogo_proc_empresa_odontograma", table_name="catalogo_procedimientos")
    op.drop_constraint(
        "fk_catalogo_proc_default_performed_catalog_item",
        "catalogo_procedimientos",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_catalogo_proc_odontogram_scope_type",
        "catalogo_procedimientos",
        type_="check",
    )
    op.drop_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        type_="check",
    )
    op.drop_column("catalogo_procedimientos", "default_performed_catalog_item_id")
    op.drop_column("catalogo_procedimientos", "odontogram_scope_type")
    op.drop_column("catalogo_procedimientos", "odontogram_behavior")
