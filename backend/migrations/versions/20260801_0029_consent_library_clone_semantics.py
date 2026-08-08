"""allow multiple editable clones from Dentia library versions

Revision ID: 20260801_0029
Revises: 20260801_0028
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260801_0029"
down_revision = "20260801_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_consent_library_install_company_version_mode",
        "consentimiento_biblioteca_instalaciones",
        type_="unique",
    )
    op.create_index(
        "uq_consent_library_install_exact_company_version",
        "consentimiento_biblioteca_instalaciones",
        ["empresa_id", "library_version_id"],
        unique=True,
        postgresql_where=sa.text("installation_mode = 'EXACT'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_consent_library_install_exact_company_version",
        table_name="consentimiento_biblioteca_instalaciones",
    )
    op.create_unique_constraint(
        "uq_consent_library_install_company_version_mode",
        "consentimiento_biblioteca_instalaciones",
        ["empresa_id", "library_version_id", "installation_mode"],
    )
