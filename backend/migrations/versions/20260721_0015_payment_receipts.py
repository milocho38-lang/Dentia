"""add payment receipts

Revision ID: 20260721_0015
Revises: 20260714_0014
Create Date: 2026-07-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260721_0015"
down_revision = "20260714_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresas",
        sa.Column(
            "titulo_comprobante_pago",
            sa.String(length=120),
            nullable=False,
            server_default="COMPROBANTE DE PAGO",
        ),
    )
    op.add_column(
        "pagos_tratamiento",
        sa.Column("comprobante_consecutivo", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pagos_tratamiento",
        sa.Column("comprobante_numero", sa.String(length=30), nullable=True),
    )

    op.execute(
        """
        WITH numbered AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY empresa_id
                    ORDER BY fecha_pago, created_at, id
                ) AS seq
            FROM pagos_tratamiento
        )
        UPDATE pagos_tratamiento p
        SET
            comprobante_consecutivo = numbered.seq,
            comprobante_numero = 'CP-' || LPAD(numbered.seq::text, 6, '0')
        FROM numbered
        WHERE p.id = numbered.id
        """
    )

    op.alter_column(
        "pagos_tratamiento",
        "comprobante_consecutivo",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "pagos_tratamiento",
        "comprobante_numero",
        existing_type=sa.String(length=30),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_pagos_empresa_comprobante_consecutivo",
        "pagos_tratamiento",
        ["empresa_id", "comprobante_consecutivo"],
    )
    op.create_unique_constraint(
        "uq_pagos_empresa_comprobante_numero",
        "pagos_tratamiento",
        ["empresa_id", "comprobante_numero"],
    )

    op.create_table(
        "pagos_tratamiento_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pago_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procedimiento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pago_id"], ["pagos_tratamiento.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["procedimiento_id"], ["tratamiento_procedimientos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pago_id", "procedimiento_id", name="uq_pagos_proc_pago_procedimiento"),
    )
    op.create_index(
        "ix_pagos_proc_empresa_pago",
        "pagos_tratamiento_procedimientos",
        ["empresa_id", "pago_id"],
    )
    op.create_index(
        "ix_pagos_proc_empresa_procedimiento",
        "pagos_tratamiento_procedimientos",
        ["empresa_id", "procedimiento_id"],
    )
    op.create_index(
        "ix_pagos_tratamiento_procedimientos_empresa_id",
        "pagos_tratamiento_procedimientos",
        ["empresa_id"],
    )
    op.create_index(
        "ix_pagos_tratamiento_procedimientos_pago_id",
        "pagos_tratamiento_procedimientos",
        ["pago_id"],
    )
    op.create_index(
        "ix_pagos_tratamiento_procedimientos_procedimiento_id",
        "pagos_tratamiento_procedimientos",
        ["procedimiento_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pagos_tratamiento_procedimientos_procedimiento_id", table_name="pagos_tratamiento_procedimientos")
    op.drop_index("ix_pagos_tratamiento_procedimientos_pago_id", table_name="pagos_tratamiento_procedimientos")
    op.drop_index("ix_pagos_tratamiento_procedimientos_empresa_id", table_name="pagos_tratamiento_procedimientos")
    op.drop_index("ix_pagos_proc_empresa_procedimiento", table_name="pagos_tratamiento_procedimientos")
    op.drop_index("ix_pagos_proc_empresa_pago", table_name="pagos_tratamiento_procedimientos")
    op.drop_table("pagos_tratamiento_procedimientos")
    op.drop_constraint("uq_pagos_empresa_comprobante_numero", "pagos_tratamiento", type_="unique")
    op.drop_constraint("uq_pagos_empresa_comprobante_consecutivo", "pagos_tratamiento", type_="unique")
    op.drop_column("pagos_tratamiento", "comprobante_numero")
    op.drop_column("pagos_tratamiento", "comprobante_consecutivo")
    op.drop_column("empresas", "titulo_comprobante_pago")
