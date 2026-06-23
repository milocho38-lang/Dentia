"""expand company and sites management

Revision ID: 20260621_0005
Revises: 20260619_0004
Create Date: 2026-06-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260621_0005"
down_revision: str | Sequence[str] | None = "20260619_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresas", sa.Column("tipo_empresa", sa.String(50), nullable=True)
    )
    op.add_column("empresas", sa.Column("nit", sa.String(50), nullable=True))
    op.add_column(
        "empresas",
        sa.Column("nit_normalizado", sa.String(50), nullable=True),
    )
    op.add_column(
        "empresas", sa.Column("telefono", sa.String(50), nullable=True)
    )
    op.add_column(
        "empresas", sa.Column("correo", sa.String(200), nullable=True)
    )
    op.add_column(
        "empresas", sa.Column("direccion", sa.String(300), nullable=True)
    )
    op.add_column(
        "empresas", sa.Column("ciudad", sa.String(100), nullable=True)
    )
    op.add_column(
        "empresas",
        sa.Column(
            "zona_horaria",
            sa.String(100),
            server_default="America/Bogota",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_empresas_nit_normalizado",
        "empresas",
        ["nit_normalizado"],
        unique=False,
    )

    op.add_column(
        "sedes",
        sa.Column("nombre_normalizado", sa.String(150), nullable=True),
    )
    op.add_column(
        "sedes", sa.Column("direccion", sa.String(300), nullable=True)
    )
    op.add_column(
        "sedes", sa.Column("ciudad", sa.String(100), nullable=True)
    )
    op.add_column(
        "sedes", sa.Column("telefono", sa.String(50), nullable=True)
    )
    op.add_column(
        "sedes", sa.Column("zona_horaria", sa.String(100), nullable=True)
    )
    op.execute(
        """
        WITH normalized AS (
            SELECT
                id,
                translate(
                    lower(regexp_replace(trim(nombre), '\\s+', ' ', 'g')),
                    'áéíóúüñ',
                    'aeiouun'
                ) AS base_name,
                row_number() OVER (
                    PARTITION BY empresa_id, translate(
                        lower(regexp_replace(trim(nombre), '\\s+', ' ', 'g')),
                        'áéíóúüñ',
                        'aeiouun'
                    )
                    ORDER BY created_at, id
                ) AS duplicate_number
            FROM sedes
        )
        UPDATE sedes AS site
        SET
            nombre_normalizado = CASE
                WHEN normalized.duplicate_number = 1
                    THEN normalized.base_name
                ELSE normalized.base_name || '-' || left(site.id::text, 8)
            END,
            direccion = COALESCE(NULLIF(trim(site.direccion), ''), 'Por completar'),
            ciudad = COALESCE(NULLIF(trim(site.ciudad), ''), 'Por completar')
        FROM normalized
        WHERE normalized.id = site.id
        """
    )
    op.alter_column("sedes", "nombre_normalizado", nullable=False)
    op.alter_column("sedes", "direccion", nullable=False)
    op.alter_column("sedes", "ciudad", nullable=False)
    op.drop_constraint(
        "uq_sedes_empresa_nombre", "sedes", type_="unique"
    )
    op.create_unique_constraint(
        "uq_sedes_empresa_nombre_normalizado",
        "sedes",
        ["empresa_id", "nombre_normalizado"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_sedes_empresa_nombre_normalizado", "sedes", type_="unique"
    )
    op.create_unique_constraint(
        "uq_sedes_empresa_nombre", "sedes", ["empresa_id", "nombre"]
    )
    op.drop_column("sedes", "zona_horaria")
    op.drop_column("sedes", "telefono")
    op.drop_column("sedes", "ciudad")
    op.drop_column("sedes", "direccion")
    op.drop_column("sedes", "nombre_normalizado")

    op.drop_index("ix_empresas_nit_normalizado", table_name="empresas")
    op.drop_column("empresas", "zona_horaria")
    op.drop_column("empresas", "ciudad")
    op.drop_column("empresas", "direccion")
    op.drop_column("empresas", "correo")
    op.drop_column("empresas", "telefono")
    op.drop_column("empresas", "nit_normalizado")
    op.drop_column("empresas", "nit")
    op.drop_column("empresas", "tipo_empresa")
