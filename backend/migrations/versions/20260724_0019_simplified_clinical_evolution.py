"""add simplified clinical evolution narrative

Revision ID: 20260724_0019
Revises: 20260723_0018
Create Date: 2026-07-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260724_0019"
down_revision = "20260723_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evoluciones_clinicas",
        sa.Column("texto_evolucion", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evoluciones_clinicas", "texto_evolucion")
