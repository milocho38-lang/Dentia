"""add existing veneer odontogram finding

Revision ID: 20261021_0051
Revises: 20261017_0050
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261021_0051"
down_revision = "20261017_0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO odontograma_catalogo (
                id, empresa_id, codigo, nombre, tipo, categoria, descripcion,
                color, pattern, symbol, allowed_scopes, allowed_surfaces,
                is_active, created_at, updated_at
            )
            VALUES (
                gen_random_uuid(), NULL, :code, :name, 'FINDING', 'Hallazgo', :description,
                :color, 'solid', :symbol, :scopes, NULL,
                true, now(), now()
            )
            ON CONFLICT (codigo) WHERE empresa_id IS NULL DO NOTHING
            """
        ).bindparams(
            sa.bindparam("code", value="FIND_VENEER"),
            sa.bindparam("name", value="Carilla existente"),
            sa.bindparam("description", value="Carilla dental previa existente."),
            sa.bindparam("color", value="#2563eb"),
            sa.bindparam("symbol", value="Ve"),
            sa.bindparam("scopes", value=["TOOTH"], type_=postgresql.JSONB()),
        )
    )


def downgrade() -> None:
    # Catalog entries can already be referenced by immutable clinical history,
    # and a matching code may have predated this revision. Downgrade is therefore
    # intentionally non-destructive; the additive catalog row remains valid.
    pass
