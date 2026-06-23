"""expand patients mvp

Revision ID: 20260619_0003
Revises: 20260619_0002
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260619_0003"
down_revision: str | Sequence[str] | None = "20260619_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_pacientes_empresa_documento",
        "pacientes",
        type_="unique",
    )
    op.alter_column("pacientes", "documento", nullable=True)
    op.add_column(
        "pacientes",
        sa.Column(
            "tipo_documento",
            sa.String(length=20),
            server_default="Otro",
            nullable=False,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column("documento_normalizado", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "celular_normalizado",
            sa.String(length=50),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("sexo", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("correo", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("correo_normalizado", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("telefono_alternativo", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("direccion", sa.String(length=300), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("ciudad", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column("departamento", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "contacto_emergencia_nombre",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "contacto_emergencia_celular",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column("observaciones_administrativas", sa.Text(), nullable=True),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "estado",
            sa.String(length=20),
            server_default="Activo",
            nullable=False,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "perfil_completo",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column(
            "texto_busqueda",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "pacientes",
        sa.Column("updated_by", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_pacientes_updated_by_usuarios",
        "pacientes",
        "usuarios",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE pacientes
        SET
            tipo_documento = 'Otro',
            documento_normalizado = upper(regexp_replace(documento, '[^0-9A-Za-z]', '', 'g')),
            celular_normalizado = regexp_replace(celular, '[^0-9]', '', 'g'),
            texto_busqueda = lower(
                concat_ws(
                    ' ',
                    nombres,
                    apellidos,
                    documento,
                    regexp_replace(celular, '[^0-9]', '', 'g')
                )
            ),
            perfil_completo = false,
            updated_by = created_by
        """
    )
    op.create_index(
        "uq_pacientes_empresa_tipo_documento_normalizado",
        "pacientes",
        ["empresa_id", "tipo_documento", "documento_normalizado"],
        unique=True,
        postgresql_where=sa.text(
            "tipo_documento <> 'Sin documento' "
            "AND documento_normalizado IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_pacientes_empresa_busqueda",
        "pacientes",
        ["empresa_id", "texto_busqueda"],
    )
    op.create_index(
        "ix_pacientes_estado",
        "pacientes",
        ["estado"],
    )

    op.create_table(
        "responsables_paciente",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("paciente_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("tipo_documento", sa.String(length=20), nullable=False),
        sa.Column("documento", sa.String(length=50), nullable=True),
        sa.Column("documento_normalizado", sa.String(length=50), nullable=True),
        sa.Column("parentesco", sa.String(length=100), nullable=False),
        sa.Column("celular", sa.String(length=50), nullable=False),
        sa.Column("correo", sa.String(length=200), nullable=True),
        sa.Column(
            "es_responsable_principal",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"], ["empresas.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["paciente_id"], ["pacientes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_responsables_paciente_empresa_id",
        "responsables_paciente",
        ["empresa_id"],
    )
    op.create_index(
        "ix_responsables_paciente_paciente_id",
        "responsables_paciente",
        ["paciente_id"],
    )
    op.create_index(
        "uq_responsables_paciente_principal_activo",
        "responsables_paciente",
        ["paciente_id"],
        unique=True,
        postgresql_where=sa.text(
            "es_responsable_principal = true AND is_active = true"
        ),
    )

    op.execute(
        """
        INSERT INTO permisos (
            id, code, nombre, descripcion, modulo, is_active
        )
        SELECT
            gen_random_uuid(),
            'patients.deactivate',
            'Desactivar pacientes',
            'Desactivar y reactivar pacientes con validación de agenda.',
            'patients',
            true
        WHERE EXISTS (SELECT 1 FROM empresas)
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO rol_permisos (
            id, empresa_id, rol_id, permiso_id, created_by, is_active
        )
        SELECT
            gen_random_uuid(),
            r.empresa_id,
            r.id,
            p.id,
            r.created_by,
            true
        FROM roles r
        JOIN permisos p ON p.code = 'patients.deactivate'
        WHERE r.code IN ('ADMINISTRATOR', 'DENTIST_ADMIN')
        ON CONFLICT (rol_id, permiso_id) DO UPDATE SET is_active = true
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rol_permisos
        WHERE permiso_id = (
            SELECT id FROM permisos WHERE code = 'patients.deactivate'
        )
        """
    )
    op.execute("DELETE FROM permisos WHERE code = 'patients.deactivate'")
    op.drop_table("responsables_paciente")
    op.drop_index("ix_pacientes_estado", table_name="pacientes")
    op.drop_index(
        "ix_pacientes_empresa_busqueda",
        table_name="pacientes",
    )
    op.drop_index(
        "uq_pacientes_empresa_tipo_documento_normalizado",
        table_name="pacientes",
    )
    op.drop_constraint(
        "fk_pacientes_updated_by_usuarios",
        "pacientes",
        type_="foreignkey",
    )
    for column in (
        "updated_by",
        "texto_busqueda",
        "perfil_completo",
        "estado",
        "observaciones_administrativas",
        "contacto_emergencia_celular",
        "contacto_emergencia_nombre",
        "departamento",
        "ciudad",
        "direccion",
        "telefono_alternativo",
        "correo_normalizado",
        "correo",
        "sexo",
        "fecha_nacimiento",
        "celular_normalizado",
        "documento_normalizado",
        "tipo_documento",
    ):
        op.drop_column("pacientes", column)
    op.alter_column("pacientes", "documento", nullable=False)
    op.create_unique_constraint(
        "uq_pacientes_empresa_documento",
        "pacientes",
        ["empresa_id", "documento"],
    )
