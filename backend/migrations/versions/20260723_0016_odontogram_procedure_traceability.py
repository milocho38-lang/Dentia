"""add odontogram to planned procedure traceability

Revision ID: 20260723_0016
Revises: 20260721_0015
Create Date: 2026-07-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260723_0016"
down_revision = "20260721_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column(
            "odontograma_evento_origen_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("odontograma_idempotency_key", sa.String(length=120), nullable=True),
    )
    op.create_foreign_key(
        "fk_proc_odontograma_evento_origen",
        "tratamiento_procedimientos",
        "odontograma_eventos",
        ["odontograma_evento_origen_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_proc_odontograma_evento_origen",
        "tratamiento_procedimientos",
        ["odontograma_evento_origen_id"],
    )
    op.create_index(
        "ix_proc_empresa_odontograma_evento_origen",
        "tratamiento_procedimientos",
        ["empresa_id", "odontograma_evento_origen_id"],
    )
    op.create_index(
        "uq_proc_empresa_odontograma_idempotency_key",
        "tratamiento_procedimientos",
        ["empresa_id", "odontograma_idempotency_key"],
        unique=True,
        postgresql_where=sa.text("odontograma_idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_proc_empresa_odontograma_idempotency_key",
        table_name="tratamiento_procedimientos",
    )
    op.drop_index(
        "ix_proc_empresa_odontograma_evento_origen",
        table_name="tratamiento_procedimientos",
    )
    op.drop_index(
        "ix_proc_odontograma_evento_origen",
        table_name="tratamiento_procedimientos",
    )
    op.drop_constraint(
        "fk_proc_odontograma_evento_origen",
        "tratamiento_procedimientos",
        type_="foreignkey",
    )
    op.drop_column("tratamiento_procedimientos", "odontograma_idempotency_key")
    op.drop_column("tratamiento_procedimientos", "odontograma_evento_origen_id")
