"""add dental scope to treatment procedures

Revision ID: 20260709_0008
Revises: 20260702_0007
Create Date: 2026-07-09 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260709_0008"
down_revision: str | None = "20260702_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("tipo_alcance", sa.String(length=30), server_default="GENERAL", nullable=False),
    )
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("zona", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("caras", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "presupuesto_detalle",
        sa.Column("tipo_alcance", sa.String(length=30), server_default="GENERAL", nullable=False),
    )
    op.add_column(
        "presupuesto_detalle",
        sa.Column("zona", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "presupuesto_detalle",
        sa.Column("pieza_dental", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "presupuesto_detalle",
        sa.Column("caras", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("presupuesto_detalle", "caras")
    op.drop_column("presupuesto_detalle", "pieza_dental")
    op.drop_column("presupuesto_detalle", "zona")
    op.drop_column("presupuesto_detalle", "tipo_alcance")

    op.drop_column("tratamiento_procedimientos", "caras")
    op.drop_column("tratamiento_procedimientos", "zona")
    op.drop_column("tratamiento_procedimientos", "tipo_alcance")
