"""add safe tenant document font selection

Revision ID: 20260801_0033
Revises: 20260801_0032
"""

from alembic import op
import sqlalchemy as sa


revision = "20260801_0033"
down_revision = "20260801_0032"
branch_labels = None
depends_on = None


FONT_CODES = (
    "HELVETICA",
    "ARIAL_COMPATIBLE",
    "TIMES_COMPATIBLE",
    "GEORGIA_COMPATIBLE",
    "VERDANA_COMPATIBLE",
    "TREBUCHET_COMPATIBLE",
)


def upgrade() -> None:
    op.add_column(
        "empresas",
        sa.Column(
            "document_font_family",
            sa.String(length=40),
            nullable=False,
            server_default="HELVETICA",
        ),
    )
    allowed = ", ".join(f"'{code}'" for code in FONT_CODES)
    op.create_check_constraint(
        "ck_empresas_document_font_family",
        "empresas",
        f"document_font_family IN ({allowed})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_empresas_document_font_family", "empresas", type_="check")
    op.drop_column("empresas", "document_font_family")
