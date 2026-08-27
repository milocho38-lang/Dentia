"""add immutable payment receipt balance snapshot

Revision ID: 20260801_0034
Revises: 20260801_0033
"""

from alembic import op
import sqlalchemy as sa


revision = "20260801_0034"
down_revision = "20260801_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pagos_tratamiento",
        sa.Column(
            "mostrar_saldo_pendiente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "pagos_tratamiento",
        sa.Column("saldo_pendiente_snapshot", sa.Numeric(14, 2), nullable=True),
    )
    op.create_check_constraint(
        "ck_pagos_saldo_pendiente_snapshot_no_negativo",
        "pagos_tratamiento",
        "saldo_pendiente_snapshot IS NULL OR saldo_pendiente_snapshot >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_pagos_saldo_pendiente_snapshot_no_negativo",
        "pagos_tratamiento",
        type_="check",
    )
    op.drop_column("pagos_tratamiento", "saldo_pendiente_snapshot")
    op.drop_column("pagos_tratamiento", "mostrar_saldo_pendiente")
