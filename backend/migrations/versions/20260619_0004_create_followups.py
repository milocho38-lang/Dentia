"""create patient followups

Revision ID: 20260619_0004
Revises: 20260619_0003
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260619_0004"
down_revision: str | Sequence[str] | None = "20260619_0003"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("appointments.complete", "Finalizar atención", "appointments", "Registrar cierre básico de atención y marcar citas atendidas."),
    ("followups.view", "Ver seguimientos", "followups", "Consultar controles y seguimientos operativos."),
    ("followups.manage", "Gestionar seguimientos", "followups", "Cerrar, reabrir y vincular citas de seguimiento."),
    ("followups.contact", "Contactar pacientes", "followups", "Registrar contactos y generar mensajes manuales."),
    ("followups.view_clinical_summary", "Ver resumen de atención", "followups", "Consultar descripción de atención y medicamentos informativos."),
)


def upgrade() -> None:
    op.create_table(
        "atenciones_cita",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("cita_id", sa.UUID(), nullable=False),
        sa.Column("paciente_id", sa.UUID(), nullable=False),
        sa.Column("odontologo_id", sa.UUID(), nullable=False),
        sa.Column("descripcion_atencion", sa.Text(), nullable=False),
        sa.Column("medicamentos_formulados", sa.Text(), nullable=True),
        sa.Column("requiere_control", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("fecha_control_recomendada", sa.Date(), nullable=True),
        sa.Column("motivo_control", sa.String(length=500), nullable=True),
        sa.Column("registrado_por", sa.UUID(), nullable=True),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["registrado_por"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_atenciones_cita_empresa_id", "atenciones_cita", ["empresa_id"])
    op.create_index("ix_atenciones_cita_cita_id", "atenciones_cita", ["cita_id"])
    op.create_index("ix_atenciones_cita_paciente_id", "atenciones_cita", ["paciente_id"])
    op.create_index("ix_atenciones_cita_odontologo_id", "atenciones_cita", ["odontologo_id"])
    op.create_index("uq_atenciones_cita_cita_id", "atenciones_cita", ["cita_id"], unique=True)

    op.create_table(
        "seguimientos_paciente",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("paciente_id", sa.UUID(), nullable=False),
        sa.Column("cita_origen_id", sa.UUID(), nullable=False),
        sa.Column("atencion_id", sa.UUID(), nullable=False),
        sa.Column("odontologo_id", sa.UUID(), nullable=False),
        sa.Column("sede_id", sa.UUID(), nullable=False),
        sa.Column("fecha_control", sa.Date(), nullable=False),
        sa.Column("fecha_contacto_desde", sa.Date(), nullable=False),
        sa.Column("motivo", sa.String(length=500), nullable=False),
        sa.Column("estado", sa.String(length=30), server_default="Pendiente", nullable=False),
        sa.Column("cita_programada_id", sa.UUID(), nullable=True),
        sa.Column("ultimo_contacto_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proximo_contacto_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cerrado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cerrado_por", sa.UUID(), nullable=True),
        sa.Column("motivo_cierre", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cita_origen_id"], ["citas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["atencion_id"], ["atenciones_cita.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cita_programada_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cerrado_por"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("empresa_id", "paciente_id", "cita_origen_id", "atencion_id", "odontologo_id", "sede_id", "fecha_control", "fecha_contacto_desde", "estado", "cita_programada_id"):
        op.create_index(f"ix_seguimientos_paciente_{column}", "seguimientos_paciente", [column])
    op.create_index("uq_seguimientos_atencion", "seguimientos_paciente", ["atencion_id"], unique=True)
    op.create_index("ix_seguimientos_empresa_fecha", "seguimientos_paciente", ["empresa_id", "fecha_control"])

    op.create_table(
        "seguimiento_gestiones",
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.Column("seguimiento_id", sa.UUID(), nullable=False),
        sa.Column("paciente_id", sa.UUID(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("resultado", sa.String(length=50), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("proximo_contacto_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contenido_mensaje", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.UUID(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seguimiento_id"], ["seguimientos_paciente.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seguimiento_gestiones_empresa_id", "seguimiento_gestiones", ["empresa_id"])
    op.create_index("ix_seguimiento_gestiones_seguimiento_id", "seguimiento_gestiones", ["seguimiento_id"])
    op.create_index("ix_seguimiento_gestiones_paciente_id", "seguimiento_gestiones", ["paciente_id"])

    for code, name, module, description in PERMISSIONS:
        op.execute(sa.text("""
            INSERT INTO permisos (id, code, nombre, descripcion, modulo, is_active)
            SELECT gen_random_uuid(), :code, :name, :description, :module, true
            WHERE EXISTS (SELECT 1 FROM empresas)
            ON CONFLICT (code) DO NOTHING
        """).bindparams(code=code, name=name, description=description, module=module))

    role_permissions = {
        "SECRETARY": ("followups.view", "followups.manage", "followups.contact"),
        "DENTIST": ("appointments.complete", "followups.view", "followups.manage", "followups.contact", "followups.view_clinical_summary"),
        "DENTIST_ADMIN": tuple(code for code, *_ in PERMISSIONS),
        "ADMINISTRATOR": tuple(code for code, *_ in PERMISSIONS),
    }
    for role_code, permission_codes in role_permissions.items():
        for permission_code in permission_codes:
            op.execute(sa.text("""
                INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, created_by, is_active)
                SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, r.created_by, true
                FROM roles r JOIN permisos p ON p.code = :permission_code
                WHERE r.code = :role_code
                ON CONFLICT (rol_id, permiso_id) DO UPDATE SET is_active = true
            """).bindparams(permission_code=permission_code, role_code=role_code))


def downgrade() -> None:
    codes = tuple(code for code, *_ in PERMISSIONS)
    op.execute(sa.text("DELETE FROM rol_permisos WHERE permiso_id IN (SELECT id FROM permisos WHERE code = ANY(:codes))").bindparams(codes=list(codes)))
    op.execute(sa.text("DELETE FROM permisos WHERE code = ANY(:codes)").bindparams(codes=list(codes)))
    op.drop_table("seguimiento_gestiones")
    op.drop_table("seguimientos_paciente")
    op.drop_table("atenciones_cita")
