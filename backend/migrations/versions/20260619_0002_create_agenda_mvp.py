"""create agenda mvp

Revision ID: 20260619_0002
Revises: 03137f3bb487
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260619_0002"
down_revision: str | Sequence[str] | None = "03137f3bb487"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pacientes",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("nombres", sa.String(length=150), nullable=False),
        sa.Column("apellidos", sa.String(length=150), nullable=False),
        sa.Column("documento", sa.String(length=50), nullable=False),
        sa.Column("celular", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "empresa_id",
            "documento",
            name="uq_pacientes_empresa_documento",
        ),
    )
    op.create_index("ix_pacientes_empresa_id", "pacientes", ["empresa_id"])

    op.create_table(
        "odontologos",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column(
            "estado",
            sa.String(length=20),
            server_default="Activo",
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
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
            ["usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "empresa_id",
            "usuario_id",
            name="uq_odontologos_empresa_usuario",
        ),
    )
    op.create_index("ix_odontologos_empresa_id", "odontologos", ["empresa_id"])
    op.create_index("ix_odontologos_usuario_id", "odontologos", ["usuario_id"])

    op.create_table(
        "tipos_cita",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("duracion_sugerida_minutos", sa.Integer(), nullable=False),
        sa.Column(
            "permite_sobrecupo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
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
        sa.CheckConstraint(
            "duracion_sugerida_minutos > 0",
            name="ck_tipos_cita_duracion_sugerida_positiva",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"], ["empresas.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "empresa_id", "nombre", name="uq_tipos_cita_empresa_nombre"
        ),
    )
    op.create_index("ix_tipos_cita_empresa_id", "tipos_cita", ["empresa_id"])

    op.create_table(
        "odontologo_sedes",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("odontologo_id", sa.UUID(), nullable=False),
        sa.Column("sede_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
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
            ["odontologo_id"], ["odontologos.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sede_id"], ["sedes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "odontologo_id",
            "sede_id",
            name="uq_odontologo_sedes_odontologo_sede",
        ),
    )
    op.create_index(
        "ix_odontologo_sedes_empresa_id", "odontologo_sedes", ["empresa_id"]
    )
    op.create_index(
        "ix_odontologo_sedes_odontologo_id",
        "odontologo_sedes",
        ["odontologo_id"],
    )
    op.create_index(
        "ix_odontologo_sedes_sede_id", "odontologo_sedes", ["sede_id"]
    )

    op.create_table(
        "citas",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("paciente_id", sa.UUID(), nullable=False),
        sa.Column("odontologo_id", sa.UUID(), nullable=False),
        sa.Column("sede_id", sa.UUID(), nullable=False),
        sa.Column("tipo_cita_id", sa.UUID(), nullable=False),
        sa.Column("cita_origen_id", sa.UUID(), nullable=True),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motivo", sa.String(length=300), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=30),
            server_default="Programada",
            nullable=False,
        ),
        sa.Column(
            "es_sobrecupo",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "justificacion_sobrecupo", sa.String(length=300), nullable=True
        ),
        sa.Column("medio_confirmacion", sa.String(length=20), nullable=True),
        sa.Column("confirmada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmada_por", sa.UUID(), nullable=True),
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
        sa.CheckConstraint(
            "fin > inicio", name="ck_citas_fin_posterior_inicio"
        ),
        sa.ForeignKeyConstraint(
            ["cita_origen_id"], ["citas.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["confirmada_por"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"], ["empresas.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["sede_id"], ["sedes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tipo_cita_id"], ["tipos_cita.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "empresa_id",
        "paciente_id",
        "odontologo_id",
        "sede_id",
        "tipo_cita_id",
        "cita_origen_id",
        "estado",
    ):
        op.create_index(f"ix_citas_{column}", "citas", [column])
    op.create_index(
        "ix_citas_odontologo_inicio_fin",
        "citas",
        ["odontologo_id", "inicio", "fin"],
    )
    op.create_index(
        "ix_citas_paciente_inicio_fin",
        "citas",
        ["paciente_id", "inicio", "fin"],
    )
    op.create_index(
        "ix_citas_empresa_inicio", "citas", ["empresa_id", "inicio"]
    )

    op.create_table(
        "cita_historial",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("cita_id", sa.UUID(), nullable=False),
        sa.Column("cita_relacionada_id", sa.UUID(), nullable=True),
        sa.Column("estado_anterior", sa.String(length=30), nullable=True),
        sa.Column("estado_nuevo", sa.String(length=30), nullable=False),
        sa.Column(
            "inicio_anterior", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("inicio_nuevo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo", sa.String(length=300), nullable=True),
        sa.Column("usuario_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["cita_id"], ["citas.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["cita_relacionada_id"], ["citas.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"], ["empresas.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cita_historial_empresa_id", "cita_historial", ["empresa_id"]
    )
    op.create_index(
        "ix_cita_historial_cita_id", "cita_historial", ["cita_id"]
    )
    op.create_index(
        "ix_cita_historial_cita_fecha",
        "cita_historial",
        ["cita_id", "created_at"],
    )

    op.execute(
        """
        INSERT INTO tipos_cita (
            id, empresa_id, nombre, duracion_sugerida_minutos,
            permite_sobrecupo, created_by
        )
        SELECT gen_random_uuid(), e.id, seed.nombre, seed.duracion, true, e.created_by
        FROM empresas e
        CROSS JOIN (
            VALUES
                ('Valoración', 30),
                ('Control', 30),
                ('Limpieza', 45),
                ('Tratamiento', 60),
                ('Urgencia', 30),
                ('Retiro de puntos', 15),
                ('Impresión', 15)
        ) AS seed(nombre, duracion)
        ON CONFLICT (empresa_id, nombre) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO odontologos (
            id, empresa_id, usuario_id, nombre, estado, created_by
        )
        SELECT gen_random_uuid(), u.empresa_id, u.id, u.nombre, 'Activo', u.id
        FROM usuarios u
        JOIN usuario_roles ur
          ON ur.usuario_id = u.id AND ur.is_active = true
        JOIN roles r
          ON r.id = ur.rol_id
         AND r.code = 'ADMINISTRATOR'
         AND r.is_active = true
        WHERE u.is_active = true
          AND u.estado = 'Activo'
        ON CONFLICT (empresa_id, usuario_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO odontologo_sedes (
            id, empresa_id, odontologo_id, sede_id, created_by
        )
        SELECT gen_random_uuid(), o.empresa_id, o.id, us.sede_id, o.usuario_id
        FROM odontologos o
        JOIN usuario_sedes us
          ON us.usuario_id = o.usuario_id AND us.is_active = true
        ON CONFLICT (odontologo_id, sede_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("cita_historial")
    op.drop_table("citas")
    op.drop_table("odontologo_sedes")
    op.drop_table("tipos_cita")
    op.drop_table("odontologos")
    op.drop_table("pacientes")
