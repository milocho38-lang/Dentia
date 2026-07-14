"""create clinical records base

Revision ID: 20260709_0011
Revises: 20260709_0010
Create Date: 2026-07-09 00:11:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260709_0011"
down_revision: Union[str, None] = "20260709_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = (
    (
        "clinical_records.view",
        "Ver resumen clínico",
        "clinical",
        "Consultar existencia de historia y alertas clínicas operativas.",
    ),
    (
        "clinical_records.create",
        "Abrir historia clínica",
        "clinical",
        "Crear la historia clínica longitudinal de un paciente.",
    ),
    (
        "clinical_records.update_draft",
        "Actualizar borrador clínico",
        "clinical",
        "Modificar información clínica base antes de evoluciones firmadas.",
    ),
    (
        "clinical_records.view_sensitive",
        "Ver detalle clínico sensible",
        "clinical",
        "Consultar antecedentes, alergias, medicamentos y contenido clínico sensible.",
    ),
    (
        "clinical_records.audit",
        "Auditar historia clínica",
        "clinical",
        "Consultar trazabilidad clínica autorizada.",
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
    op.execute(
        """
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
        FROM roles r
        JOIN permisos p ON p.code IN (
            'clinical_records.view',
            'clinical_records.create',
            'clinical_records.update_draft',
            'clinical_records.view_sensitive',
            'clinical_records.audit'
        )
        WHERE r.code = 'DENTIST_ADMIN'
          AND NOT EXISTS (
              SELECT 1 FROM rol_permisos rp
              WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
          )
        """
    )
    op.execute(
        """
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
        FROM roles r
        JOIN permisos p ON p.code IN (
            'clinical_records.view',
            'clinical_records.create',
            'clinical_records.update_draft',
            'clinical_records.view_sensitive'
        )
        WHERE r.code = 'DENTIST'
          AND NOT EXISTS (
              SELECT 1 FROM rol_permisos rp
              WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
          )
        """
    )
    op.execute(
        """
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
        FROM roles r
        JOIN permisos p ON p.code = 'clinical_records.view'
        WHERE r.code IN ('SECRETARY', 'ADMINISTRATOR')
          AND NOT EXISTS (
              SELECT 1 FROM rol_permisos rp
              WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
          )
        """
    )


def upgrade() -> None:
    op.create_table(
        "historias_clinicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="ACTIVA", nullable=False),
        sa.Column("fecha_apertura", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sede_apertura_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("odontologo_apertura_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("motivo_consulta", sa.Text(), nullable=True),
        sa.Column("situacion_actual", sa.Text(), nullable=True),
        sa.Column("inicio_situacion", sa.String(length=200), nullable=True),
        sa.Column("evolucion_situacion", sa.Text(), nullable=True),
        sa.Column("sintomas", sa.Text(), nullable=True),
        sa.Column("tratamientos_previos", sa.Text(), nullable=True),
        sa.Column("informante_tipo", sa.String(length=50), nullable=True),
        sa.Column("informante_nombre", sa.String(length=200), nullable=True),
        sa.Column("informante_parentesco", sa.String(length=100), nullable=True),
        sa.Column("informante_documento", sa.String(length=80), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("habitos", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("antecedentes_odontologicos", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("estado_alergias", sa.String(length=40), server_default="NO_CONFIRMADA", nullable=False),
        sa.Column("estado_antecedentes", sa.String(length=40), server_default="NO_CONFIRMADO", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_historias_clinicas_version_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_apertura_id"], ["odontologos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_apertura_id"], ["sedes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "paciente_id", name="uq_historias_clinicas_empresa_paciente"),
    )
    op.create_index("ix_historias_clinicas_empresa_id", "historias_clinicas", ["empresa_id"])
    op.create_index("ix_historias_clinicas_empresa_estado", "historias_clinicas", ["empresa_id", "estado"])
    op.create_index("ix_historias_clinicas_paciente", "historias_clinicas", ["paciente_id"])
    op.create_index("ix_historias_clinicas_paciente_id", "historias_clinicas", ["paciente_id"])
    op.create_index("ix_historias_clinicas_sede_apertura_id", "historias_clinicas", ["sede_apertura_id"])
    op.create_index("ix_historias_clinicas_odontologo_apertura_id", "historias_clinicas", ["odontologo_apertura_id"])

    op.create_table(
        "historias_clinicas_antecedentes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(length=120), nullable=False),
        sa.Column("presente", sa.String(length=20), server_default="DESCONOCIDO", nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("severidad", sa.String(length=40), nullable=True),
        sa.Column("estado", sa.String(length=40), server_default="activo", nullable=False),
        sa.Column("fuente", sa.String(length=120), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_hist_clin_ant_version_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historias_clinicas_antecedentes_empresa_id", "historias_clinicas_antecedentes", ["empresa_id"])
    op.create_index("ix_hist_clin_ant_historia", "historias_clinicas_antecedentes", ["historia_clinica_id"])
    op.create_index("ix_hist_clin_ant_paciente_tipo", "historias_clinicas_antecedentes", ["paciente_id", "tipo"])
    op.create_index("ix_historias_clinicas_antecedentes_paciente_id", "historias_clinicas_antecedentes", ["paciente_id"])

    op.create_table(
        "historias_clinicas_alergias",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("sustancia", sa.String(length=200), nullable=False),
        sa.Column("reaccion", sa.String(length=300), nullable=True),
        sa.Column("severidad", sa.String(length=40), server_default="desconocida", nullable=False),
        sa.Column("estado", sa.String(length=40), server_default="no confirmada", nullable=False),
        sa.Column("alerta_critica", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_hist_clin_alergias_version_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historias_clinicas_alergias_empresa_id", "historias_clinicas_alergias", ["empresa_id"])
    op.create_index("ix_hist_clin_alergias_historia", "historias_clinicas_alergias", ["historia_clinica_id"])
    op.create_index("ix_hist_clin_alergias_paciente_critica", "historias_clinicas_alergias", ["paciente_id", "alerta_critica"])
    op.create_index("ix_historias_clinicas_alergias_paciente_id", "historias_clinicas_alergias", ["paciente_id"])

    op.create_table(
        "historias_clinicas_medicamentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("dosis", sa.String(length=120), nullable=True),
        sa.Column("frecuencia", sa.String(length=120), nullable=True),
        sa.Column("via", sa.String(length=80), nullable=True),
        sa.Column("desde", sa.String(length=120), nullable=True),
        sa.Column("motivo", sa.String(length=300), nullable=True),
        sa.Column("prescriptor", sa.String(length=200), nullable=True),
        sa.Column("estado", sa.String(length=40), server_default="activo", nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_hist_clin_medicamentos_version_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historias_clinicas_medicamentos_empresa_id", "historias_clinicas_medicamentos", ["empresa_id"])
    op.create_index("ix_hist_clin_meds_historia", "historias_clinicas_medicamentos", ["historia_clinica_id"])
    op.create_index("ix_hist_clin_meds_paciente_estado", "historias_clinicas_medicamentos", ["paciente_id", "estado"])
    op.create_index("ix_historias_clinicas_medicamentos_paciente_id", "historias_clinicas_medicamentos", ["paciente_id"])

    _upsert_permissions()
    _assign_permissions()


def downgrade() -> None:
    op.drop_index("ix_historias_clinicas_medicamentos_paciente_id", table_name="historias_clinicas_medicamentos")
    op.drop_index("ix_hist_clin_meds_paciente_estado", table_name="historias_clinicas_medicamentos")
    op.drop_index("ix_hist_clin_meds_historia", table_name="historias_clinicas_medicamentos")
    op.drop_index("ix_historias_clinicas_medicamentos_empresa_id", table_name="historias_clinicas_medicamentos")
    op.drop_table("historias_clinicas_medicamentos")
    op.drop_index("ix_historias_clinicas_alergias_paciente_id", table_name="historias_clinicas_alergias")
    op.drop_index("ix_hist_clin_alergias_paciente_critica", table_name="historias_clinicas_alergias")
    op.drop_index("ix_hist_clin_alergias_historia", table_name="historias_clinicas_alergias")
    op.drop_index("ix_historias_clinicas_alergias_empresa_id", table_name="historias_clinicas_alergias")
    op.drop_table("historias_clinicas_alergias")
    op.drop_index("ix_historias_clinicas_antecedentes_paciente_id", table_name="historias_clinicas_antecedentes")
    op.drop_index("ix_hist_clin_ant_paciente_tipo", table_name="historias_clinicas_antecedentes")
    op.drop_index("ix_hist_clin_ant_historia", table_name="historias_clinicas_antecedentes")
    op.drop_index("ix_historias_clinicas_antecedentes_empresa_id", table_name="historias_clinicas_antecedentes")
    op.drop_table("historias_clinicas_antecedentes")
    op.drop_index("ix_historias_clinicas_odontologo_apertura_id", table_name="historias_clinicas")
    op.drop_index("ix_historias_clinicas_sede_apertura_id", table_name="historias_clinicas")
    op.drop_index("ix_historias_clinicas_paciente_id", table_name="historias_clinicas")
    op.drop_index("ix_historias_clinicas_paciente", table_name="historias_clinicas")
    op.drop_index("ix_historias_clinicas_empresa_estado", table_name="historias_clinicas")
    op.drop_index("ix_historias_clinicas_empresa_id", table_name="historias_clinicas")
    op.drop_table("historias_clinicas")

    op.execute(
        """
        DELETE FROM rol_permisos
        WHERE permiso_id IN (
            SELECT id FROM permisos
            WHERE code IN (
                'clinical_records.view',
                'clinical_records.create',
                'clinical_records.update_draft',
                'clinical_records.view_sensitive',
                'clinical_records.audit'
            )
        )
        """
    )
    op.execute(
        """
        DELETE FROM permisos
        WHERE code IN (
            'clinical_records.view',
            'clinical_records.create',
            'clinical_records.update_draft',
            'clinical_records.view_sensitive',
            'clinical_records.audit'
        )
        """
    )
