"""add optional periodontogram evolution link

Revision ID: 20260923_0044
Revises: 20260923_0043
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260923_0044"
down_revision = "20260923_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "periodontal_exams",
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_periodontal_exams_evolution",
        "periodontal_exams",
        "evoluciones_clinicas",
        ["evolucion_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_periodontal_exams_evolution_link",
        "periodontal_exams",
        ["empresa_id", "paciente_id", "evolucion_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_periodontal_exams_evolution_link",
        table_name="periodontal_exams",
    )
    op.drop_constraint(
        "fk_periodontal_exams_evolution",
        "periodontal_exams",
        type_="foreignkey",
    )
    op.drop_column("periodontal_exams", "evolucion_id")
