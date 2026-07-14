"""create clinical evolutions and timeline

Revision ID: 20260709_0012
Revises: 20260709_0011
Create Date: 2026-07-09 00:12:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260709_0012"
down_revision: Union[str, None] = "20260709_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = (
    (
        "clinical_evolutions.view",
        "Ver evoluciones clínicas",
        "clinical",
        "Consultar evoluciones clínicas autorizadas.",
    ),
    (
        "clinical_evolutions.create",
        "Crear evoluciones clínicas",
        "clinical",
        "Crear borradores de evolución clínica.",
    ),
    (
        "clinical_evolutions.update_draft",
        "Actualizar borrador de evolución",
        "clinical",
        "Editar borradores de evolución clínica.",
    ),
    (
        "clinical_evolutions.sign",
        "Firmar evoluciones clínicas",
        "clinical",
        "Firmar y cerrar evoluciones clínicas.",
    ),
    (
        "clinical_evolutions.add_addendum",
        "Agregar adendas clínicas",
        "clinical",
        "Agregar adendas a evoluciones clínicas firmadas.",
    ),
    (
        "clinical_timeline.view",
        "Ver línea de tiempo clínica",
        "clinical",
        "Consultar la línea de tiempo clínica del paciente.",
    ),
)


def _upsert_permissions() -> None:
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


def _assign_permissions() -> None:
    clinical_codes = tuple(code for code, *_ in PERMISSIONS)
    op.execute(
        sa.text(
            """
            INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
            SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
            FROM roles r
            JOIN permisos p ON p.code = ANY(:codes)
            WHERE r.code IN ('DENTIST', 'DENTIST_ADMIN')
              AND NOT EXISTS (
                  SELECT 1 FROM rol_permisos rp
                  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
              )
            """
        ).bindparams(sa.bindparam("codes", clinical_codes, type_=postgresql.ARRAY(sa.String())))
    )


def upgrade() -> None:
    op.create_table(
        "evoluciones_clinicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha_atencion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zona_horaria", sa.String(length=100), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("subjetivo", sa.Text(), nullable=True),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("evaluacion", sa.Text(), nullable=True),
        sa.Column("procedimiento_realizado", sa.Text(), nullable=True),
        sa.Column("anestesia", sa.Text(), nullable=True),
        sa.Column("materiales", sa.Text(), nullable=True),
        sa.Column("medicamentos_administrados", sa.Text(), nullable=True),
        sa.Column("hallazgos", sa.Text(), nullable=True),
        sa.Column("complicaciones", sa.Text(), nullable=True),
        sa.Column("indicaciones", sa.Text(), nullable=True),
        sa.Column("recomendaciones", sa.Text(), nullable=True),
        sa.Column("proximo_control_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proximo_control_motivo", sa.Text(), nullable=True),
        sa.Column("seguimiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=40), server_default="DRAFT", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("hash_contenido", sa.String(length=128), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_evoluciones_clinicas_version_positive"),
        sa.CheckConstraint(
            "estado IN ('DRAFT', 'SIGNED', 'VOIDED_BY_COMPENSATING_RECORD')",
            name="ck_evoluciones_clinicas_estado",
        ),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seguimiento_id"], ["seguimientos_paciente.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["signed_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "cita_id", name="uq_evoluciones_clinicas_empresa_cita_principal"),
    )
    op.create_index("ix_evoluciones_empresa_cita", "evoluciones_clinicas", ["empresa_id", "cita_id"])
    op.create_index("ix_evoluciones_empresa_estado", "evoluciones_clinicas", ["empresa_id", "estado"])
    op.create_index("ix_evoluciones_empresa_historia", "evoluciones_clinicas", ["empresa_id", "historia_clinica_id"])
    op.create_index("ix_evoluciones_empresa_odontologo", "evoluciones_clinicas", ["empresa_id", "odontologo_id"])
    op.create_index("ix_evoluciones_empresa_paciente_fecha", "evoluciones_clinicas", ["empresa_id", "paciente_id", "fecha_atencion"])
    op.create_index("ix_evoluciones_empresa_sede", "evoluciones_clinicas", ["empresa_id", "sede_id"])
    op.create_index("ix_evoluciones_clinicas_cita_id", "evoluciones_clinicas", ["cita_id"])
    op.create_index("ix_evoluciones_clinicas_empresa_id", "evoluciones_clinicas", ["empresa_id"])
    op.create_index("ix_evoluciones_clinicas_historia_clinica_id", "evoluciones_clinicas", ["historia_clinica_id"])
    op.create_index("ix_evoluciones_clinicas_odontologo_id", "evoluciones_clinicas", ["odontologo_id"])
    op.create_index("ix_evoluciones_clinicas_paciente_id", "evoluciones_clinicas", ["paciente_id"])
    op.create_index("ix_evoluciones_clinicas_sede_id", "evoluciones_clinicas", ["sede_id"])
    op.create_index("ix_evoluciones_clinicas_seguimiento_id", "evoluciones_clinicas", ["seguimiento_id"])
    op.create_index("ix_evoluciones_clinicas_tratamiento_id", "evoluciones_clinicas", ["tratamiento_id"])

    op.create_table(
        "evoluciones_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("procedimiento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "accion IN ('PLANNED', 'PERFORMED', 'REVIEWED', 'SUSPENDED')",
            name="ck_evoluciones_proc_accion",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evolucion_id"], ["evoluciones_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["procedimiento_id"], ["tratamiento_procedimientos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evoluciones_proc_evolucion", "evoluciones_procedimientos", ["evolucion_id"])
    op.create_index("ix_evoluciones_proc_procedimiento", "evoluciones_procedimientos", ["procedimiento_id"])
    op.create_index("ix_evoluciones_procedimientos_empresa_id", "evoluciones_procedimientos", ["empresa_id"])

    op.create_table(
        "evoluciones_adendas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hash_contenido", sa.String(length=128), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evolucion_id"], ["evoluciones_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evoluciones_adendas_evolucion", "evoluciones_adendas", ["evolucion_id"])
    op.create_index("ix_evoluciones_adendas_paciente", "evoluciones_adendas", ["empresa_id", "paciente_id"])
    op.create_index("ix_evoluciones_adendas_empresa_id", "evoluciones_adendas", ["empresa_id"])
    op.create_index("ix_evoluciones_adendas_paciente_id", "evoluciones_adendas", ["paciente_id"])

    op.create_table(
        "historia_clinica_eventos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_evento", sa.String(length=80), nullable=False),
        sa.Column("entidad_tipo", sa.String(length=80), nullable=False),
        sa.Column("entidad_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("titulo", sa.String(length=250), nullable=False),
        sa.Column("descripcion_resumen", sa.Text(), nullable=True),
        sa.Column("fecha_clinica", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historia_eventos_historia", "historia_clinica_eventos", ["historia_clinica_id"])
    op.create_index("ix_historia_eventos_paciente_fecha", "historia_clinica_eventos", ["empresa_id", "paciente_id", "fecha_clinica"])
    op.create_index("ix_historia_eventos_tipo", "historia_clinica_eventos", ["empresa_id", "tipo_evento"])
    op.create_index("ix_historia_clinica_eventos_empresa_id", "historia_clinica_eventos", ["empresa_id"])
    op.create_index("ix_historia_clinica_eventos_paciente_id", "historia_clinica_eventos", ["paciente_id"])

    _upsert_permissions()
    _assign_permissions()


def downgrade() -> None:
    op.drop_index("ix_historia_clinica_eventos_empresa_id", table_name="historia_clinica_eventos")
    op.drop_index("ix_historia_clinica_eventos_paciente_id", table_name="historia_clinica_eventos")
    op.drop_index("ix_historia_eventos_tipo", table_name="historia_clinica_eventos")
    op.drop_index("ix_historia_eventos_paciente_fecha", table_name="historia_clinica_eventos")
    op.drop_index("ix_historia_eventos_historia", table_name="historia_clinica_eventos")
    op.drop_table("historia_clinica_eventos")

    op.drop_index("ix_evoluciones_adendas_empresa_id", table_name="evoluciones_adendas")
    op.drop_index("ix_evoluciones_adendas_paciente_id", table_name="evoluciones_adendas")
    op.drop_index("ix_evoluciones_adendas_paciente", table_name="evoluciones_adendas")
    op.drop_index("ix_evoluciones_adendas_evolucion", table_name="evoluciones_adendas")
    op.drop_table("evoluciones_adendas")

    op.drop_index("ix_evoluciones_procedimientos_empresa_id", table_name="evoluciones_procedimientos")
    op.drop_index("ix_evoluciones_proc_procedimiento", table_name="evoluciones_procedimientos")
    op.drop_index("ix_evoluciones_proc_evolucion", table_name="evoluciones_procedimientos")
    op.drop_table("evoluciones_procedimientos")

    op.drop_index("ix_evoluciones_empresa_sede", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_tratamiento_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_seguimiento_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_sede_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_paciente_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_odontologo_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_historia_clinica_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_empresa_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_clinicas_cita_id", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_empresa_paciente_fecha", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_empresa_odontologo", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_empresa_historia", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_empresa_estado", table_name="evoluciones_clinicas")
    op.drop_index("ix_evoluciones_empresa_cita", table_name="evoluciones_clinicas")
    op.drop_table("evoluciones_clinicas")
