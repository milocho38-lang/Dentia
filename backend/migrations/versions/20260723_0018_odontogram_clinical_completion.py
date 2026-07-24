"""add clinical completion traceability to odontogram events

Revision ID: 20260723_0018
Revises: 20260723_0017
Create Date: 2026-07-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260723_0018"
down_revision = "20260723_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "odontograma_eventos",
        sa.Column("source_odontogram_event_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "odontograma_eventos",
        sa.Column("source_diagnosis_action", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "odontograma_eventos",
        sa.Column("completion_idempotency_key", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "odontograma_eventos",
        sa.Column(
            "reviewed_for_evolution",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "odontograma_eventos",
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "odontograma_eventos",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_odontograma_eventos_source_event",
        "odontograma_eventos",
        "odontograma_eventos",
        ["source_odontogram_event_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_odontograma_eventos_reviewed_by",
        "odontograma_eventos",
        "usuarios",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_odontograma_eventos_source_event",
        "odontograma_eventos",
        ["source_odontogram_event_id"],
    )
    op.create_index(
        "ix_odontograma_eventos_completion_key",
        "odontograma_eventos",
        ["empresa_id", "completion_idempotency_key"],
    )
    op.create_index(
        "uq_odontograma_eventos_empresa_completion_key",
        "odontograma_eventos",
        ["empresa_id", "completion_idempotency_key"],
        unique=True,
        postgresql_where=sa.text("completion_idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_odontograma_eventos_empresa_completion_key",
        table_name="odontograma_eventos",
    )
    op.drop_index("ix_odontograma_eventos_completion_key", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_source_event", table_name="odontograma_eventos")
    op.drop_constraint(
        "fk_odontograma_eventos_reviewed_by",
        "odontograma_eventos",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_odontograma_eventos_source_event",
        "odontograma_eventos",
        type_="foreignkey",
    )
    op.drop_column("odontograma_eventos", "reviewed_at")
    op.drop_column("odontograma_eventos", "reviewed_by")
    op.drop_column("odontograma_eventos", "reviewed_for_evolution")
    op.drop_column("odontograma_eventos", "completion_idempotency_key")
    op.drop_column("odontograma_eventos", "source_diagnosis_action")
    op.drop_column("odontograma_eventos", "source_odontogram_event_id")
