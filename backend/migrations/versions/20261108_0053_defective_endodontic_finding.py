"""add defective prior endodontic finding

Revision ID: 20261108_0053
Revises: 20261102_0052
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261108_0053"
down_revision = "20261102_0052"
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
                :color, 'zigzag', :symbol, :scopes, NULL,
                true, now(), now()
            )
            ON CONFLICT (codigo) WHERE empresa_id IS NULL DO NOTHING
            """
        ).bindparams(
            sa.bindparam("code", value="FIND_ENDO_DEFECTIVE"),
            sa.bindparam("name", value="Endodoncia previa en mal estado"),
            sa.bindparam(
                "description",
                value=(
                    "Marcador explícito de una endodoncia previa defectuosa; "
                    "debe existir antes de vincular un retratamiento."
                ),
            ),
            sa.bindparam("color", value="#2563eb"),
            sa.bindparam("symbol", value="En~"),
            sa.bindparam("scopes", value=["TOOTH"], type_=postgresql.JSONB()),
        )
    )


def downgrade() -> None:
    # El hallazgo puede quedar referenciado por historia clínica inmutable.
    # El downgrade de esquema es aditivo y deliberadamente no destructivo.
    pass
