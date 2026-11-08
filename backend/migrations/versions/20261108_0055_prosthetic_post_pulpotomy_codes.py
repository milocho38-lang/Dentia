"""add explicit post and pulpotomy clinical codes

Revision ID: 20261108_0055
Revises: 20261108_0054
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261108_0055"
down_revision = "20261108_0054"
branch_labels = None
depends_on = None


CATALOG_ROWS = (
    ("PLAN_POST", "Perno planificado", "PLANNED_PROCEDURE", "#dc2626", "post", "P|"),
    ("DONE_POST", "Perno realizado", "PERFORMED_PROCEDURE", "#2563eb", "post", "P|"),
    ("DONE_PULPOTOMY", "Pulpotomía realizada", "PERFORMED_PROCEDURE", "#2563eb", "occlusal-ring", "Po"),
)


def upgrade() -> None:
    statement = sa.text(
        """
        INSERT INTO odontograma_catalogo (
            id, empresa_id, codigo, nombre, tipo, categoria, descripcion,
            color, pattern, symbol, allowed_scopes, allowed_surfaces,
            is_active, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), NULL, :code, :name, :type, 'Tratamiento', :description,
            :color, :pattern, :symbol, :scopes, :surfaces,
            true, now(), now()
        )
        ON CONFLICT (codigo) WHERE empresa_id IS NULL DO NOTHING
        """
    )
    for code, name, item_type, color, pattern, symbol in CATALOG_ROWS:
        op.execute(statement.bindparams(
            sa.bindparam("code", value=code),
            sa.bindparam("name", value=name),
            sa.bindparam("type", value=item_type),
            sa.bindparam("description", value="Código clínico explícito del lote protésico nueve; carga deshabilitada."),
            sa.bindparam("color", value=color),
            sa.bindparam("pattern", value=pattern),
            sa.bindparam("symbol", value=symbol),
            sa.bindparam("scopes", value=["TOOTH"], type_=postgresql.JSONB()),
            sa.bindparam("surfaces", value=["OCCLUSAL"] if code == "DONE_PULPOTOMY" else None, type_=postgresql.JSONB()),
        ))


def downgrade() -> None:
    # Aditiva: estos códigos pueden quedar referenciados por historia clínica.
    pass
