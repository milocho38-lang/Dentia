"""add explicit veneer planning and result codes

Revision ID: 20261108_0056
Revises: 20261108_0055
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261108_0056"
down_revision = "20261108_0055"
branch_labels = None
depends_on = None


CATALOG_ROWS = (
    ("PLAN_VENEER", "Carilla planificada", "PLANNED_PROCEDURE", "#dc2626"),
    ("DONE_VENEER", "Carilla realizada", "PERFORMED_PROCEDURE", "#2563eb"),
)


def upgrade() -> None:
    statement = sa.text("""
        INSERT INTO odontograma_catalogo (
            id, empresa_id, codigo, nombre, tipo, categoria, descripcion,
            color, pattern, symbol, allowed_scopes, allowed_surfaces,
            is_active, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), NULL, :code, :name, :type, 'Tratamiento',
            'Código clínico explícito del lote estético cuatro; carga deshabilitada.',
            :color, 'veneer', 'V', :scopes, NULL, true, now(), now()
        )
        ON CONFLICT (codigo) WHERE empresa_id IS NULL DO NOTHING
    """)
    for code, name, item_type, color in CATALOG_ROWS:
        op.execute(statement.bindparams(
            sa.bindparam("code", value=code),
            sa.bindparam("name", value=name),
            sa.bindparam("type", value=item_type),
            sa.bindparam("color", value=color),
            sa.bindparam("scopes", value=["TOOTH"], type_=postgresql.JSONB()),
        ))


def downgrade() -> None:
    # Aditiva: los códigos pueden estar referenciados por historia clínica.
    pass
