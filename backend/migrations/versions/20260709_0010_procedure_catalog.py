"""add procedure catalog

Revision ID: 20260709_0010
Revises: 20260709_0009
Create Date: 2026-07-09 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260709_0010"
down_revision: Union[str, None] = "20260709_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = (
    (
        "procedure_catalog.view",
        "Ver catálogo de procedimientos",
        "treatments",
        "Consultar el catálogo de procedimientos de la empresa.",
    ),
    (
        "procedure_catalog.manage",
        "Administrar catálogo de procedimientos",
        "treatments",
        "Crear, editar, activar e inactivar procedimientos del catálogo.",
    ),
)


def upgrade() -> None:
    op.create_table(
        "catalogo_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("nombre_normalizado", sa.String(length=220), nullable=False),
        sa.Column("categoria", sa.String(length=120), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("valor_sugerido", sa.Numeric(14, 2), nullable=True),
        sa.Column("tipo_alcance_sugerido", sa.String(length=30), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("valor_sugerido IS NULL OR valor_sugerido >= 0", name="ck_catalogo_proc_valor_no_negativo"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_catalogo_proc_empresa_activo", "catalogo_procedimientos", ["empresa_id", "activo"])
    op.create_index("ix_catalogo_proc_empresa_categoria", "catalogo_procedimientos", ["empresa_id", "categoria"])
    op.create_index("ix_catalogo_proc_empresa_id", "catalogo_procedimientos", ["empresa_id"])
    op.create_unique_constraint(
        "uq_catalogo_proc_empresa_nombre_normalizado",
        "catalogo_procedimientos",
        ["empresa_id", "nombre_normalizado"],
    )

    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("catalogo_procedimiento_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_trat_proc_catalogo_proc",
        "tratamiento_procedimientos",
        "catalogo_procedimientos",
        ["catalogo_procedimiento_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_proc_catalogo", "tratamiento_procedimientos", ["catalogo_procedimiento_id"])

    for code, name, module, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active)
                VALUES (gen_random_uuid(), :code, :name, :module, :description, true)
                ON CONFLICT (code) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true
                """
            ).bindparams(
                code=code,
                name=name,
                module=module,
                description=description,
            )
        )

    op.execute(
        """
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
        FROM roles r
        JOIN permisos p ON p.code IN ('procedure_catalog.view', 'procedure_catalog.manage')
        WHERE r.code IN ('ADMINISTRATOR', 'DENTIST_ADMIN')
          AND NOT EXISTS (
              SELECT 1
              FROM rol_permisos rp
              WHERE rp.rol_id = r.id
                AND rp.permiso_id = p.id
          )
        """
    )
    op.execute(
        """
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
        FROM roles r
        JOIN permisos p ON p.code = 'procedure_catalog.view'
        WHERE r.code IN ('DENTIST', 'SECRETARY')
          AND NOT EXISTS (
              SELECT 1
              FROM rol_permisos rp
              WHERE rp.rol_id = r.id
                AND rp.permiso_id = p.id
          )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_proc_catalogo", table_name="tratamiento_procedimientos")
    op.drop_constraint(
        "fk_trat_proc_catalogo_proc",
        "tratamiento_procedimientos",
        type_="foreignkey",
    )
    op.drop_column("tratamiento_procedimientos", "catalogo_procedimiento_id")
    op.drop_constraint("uq_catalogo_proc_empresa_nombre_normalizado", "catalogo_procedimientos", type_="unique")
    op.drop_index("ix_catalogo_proc_empresa_id", table_name="catalogo_procedimientos")
    op.drop_index("ix_catalogo_proc_empresa_categoria", table_name="catalogo_procedimientos")
    op.drop_index("ix_catalogo_proc_empresa_activo", table_name="catalogo_procedimientos")
    op.drop_table("catalogo_procedimientos")

    op.execute(
        """
        DELETE FROM rol_permisos
        WHERE permiso_id IN (
            SELECT id FROM permisos
            WHERE code IN ('procedure_catalog.view', 'procedure_catalog.manage')
        )
        """
    )
    op.execute(
        """
        DELETE FROM permisos
        WHERE code IN ('procedure_catalog.view', 'procedure_catalog.manage')
        """
    )
