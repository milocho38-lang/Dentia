"""track per-procedure odontogram integration opt-out

Revision ID: 20261111_0058
Revises: 20261111_0057
"""

from alembic import op
import sqlalchemy as sa


revision = "20261111_0058"
down_revision = "20261111_0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column(
            "odontograma_integracion_omitida",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    opted_out = op.get_bind().scalar(
        sa.text(
            "SELECT count(*) FROM tratamiento_procedimientos "
            "WHERE odontograma_integracion_omitida IS TRUE"
        )
    )
    if opted_out:
        raise RuntimeError(
            "Downgrade blocked: odontogram opt-out decisions exist. "
            "Use a forward recovery or a code-only rollback compatible with revision 0058."
        )
    op.drop_column("tratamiento_procedimientos", "odontograma_integracion_omitida")
