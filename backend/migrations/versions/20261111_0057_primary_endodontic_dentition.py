"""mark temporal endodontic catalog rows as primary dentition

Revision ID: 20261111_0057
Revises: 20261108_0056
"""

from alembic import op
import sqlalchemy as sa


revision = "20261111_0057"
down_revision = "20261108_0056"
branch_labels = None
depends_on = None


CATALOG_VERSION = "KIMBERLY-2026-11-08-ODONTOGRAM-ENDODONTIC-18-DRAFT"
PRIMARY_SOURCE_ROWS = (282, 283, 292, 293)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE catalogo_procedimientos
            SET procedencia_precio = jsonb_set(
                COALESCE(procedencia_precio, '{}'::jsonb),
                '{required_dentition}',
                '"PRIMARY"'::jsonb,
                true
            )
            WHERE procedencia_precio->>'catalog_version' = :catalog_version
              AND (procedencia_precio->>'source_row')::integer IN :source_rows
            """
        ).bindparams(
            sa.bindparam("catalog_version", value=CATALOG_VERSION),
            sa.bindparam("source_rows", value=PRIMARY_SOURCE_ROWS, expanding=True),
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE catalogo_procedimientos
            SET procedencia_precio = procedencia_precio - 'required_dentition'
            WHERE procedencia_precio->>'catalog_version' = :catalog_version
              AND (procedencia_precio->>'source_row')::integer IN :source_rows
              AND procedencia_precio->>'required_dentition' = 'PRIMARY'
            """
        ).bindparams(
            sa.bindparam("catalog_version", value=CATALOG_VERSION),
            sa.bindparam("source_rows", value=PRIMARY_SOURCE_ROWS, expanding=True),
        )
    )
