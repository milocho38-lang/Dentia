"""add catalog price currency and provenance

Revision ID: 20261102_0052
Revises: 20261021_0051
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261102_0052"
down_revision = "20261021_0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalogo_procedimientos", sa.Column("moneda_valor", sa.String(3), nullable=True))
    op.add_column("catalogo_procedimientos", sa.Column("procedencia_precio", postgresql.JSONB(), nullable=True))
    op.execute("""
        UPDATE catalogo_procedimientos AS cp
        SET moneda_valor = CASE
            WHEN lower(trim(coalesce(e.pais, ''))) IN ('chile', 'cl') THEN 'CLP'
            WHEN lower(trim(coalesce(e.pais, ''))) IN ('colombia', 'co') THEN 'COP'
            ELSE NULL
        END
        FROM empresas AS e WHERE e.id = cp.empresa_id
    """)


def downgrade() -> None:
    op.drop_column("catalogo_procedimientos", "procedencia_precio")
    op.drop_column("catalogo_procedimientos", "moneda_valor")
