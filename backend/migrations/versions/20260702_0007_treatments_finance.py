"""add treatments budgets and finance MVP

Revision ID: 20260702_0007
Revises: 20260625_0006
Create Date: 2026-07-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260702_0007"
down_revision: str | Sequence[str] | None = "20260625_0006"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("treatments.view", "Ver tratamientos", "treatments", "Consultar tratamientos."),
    ("treatments.create", "Crear tratamientos", "treatments", "Crear tratamientos."),
    ("treatments.update", "Actualizar tratamientos", "treatments", "Gestionar etapas y procedimientos."),
    ("treatments.close", "Cerrar tratamientos", "treatments", "Finalizar tratamientos y registrar cierre."),
    ("treatments.cancel", "Cancelar tratamientos", "treatments", "Cancelar tratamientos con trazabilidad."),
    ("budgets.view", "Ver presupuestos", "budgets", "Consultar presupuestos."),
    ("budgets.create", "Crear presupuestos", "budgets", "Generar presupuestos."),
    ("budgets.update", "Actualizar presupuestos", "budgets", "Modificar y gestionar presupuestos."),
    ("payments.view", "Ver pagos", "finance", "Consultar pagos y cartera."),
    ("payments.create", "Registrar pagos", "finance", "Registrar pagos de pacientes."),
    ("payments.reverse", "Reversar pagos", "finance", "Reversar pagos con auditoría."),
    ("finance.dashboard.view", "Ver dashboard financiero", "finance", "Consultar indicadores económicos básicos."),
    ("reports.view", "Ver reportes", "reports", "Consultar reportes autorizados."),
)


ROLE_PERMISSIONS = {
    "ADMINISTRATOR": [code for code, *_ in PERMISSIONS],
    "DENTIST_ADMIN": [code for code, *_ in PERMISSIONS],
    "DENTIST": [
        "treatments.view",
        "treatments.create",
        "treatments.update",
        "treatments.close",
        "budgets.view",
        "budgets.create",
        "budgets.update",
    ],
    "SECRETARY": [
        "treatments.view",
        "budgets.view",
        "budgets.update",
        "payments.view",
        "payments.create",
        "finance.dashboard.view",
        "reports.view",
    ],
}


def _seed_permissions() -> None:
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
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        op.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (
                    id, empresa_id, rol_id, permiso_id, is_active, created_by
                )
                SELECT
                    gen_random_uuid(),
                    r.empresa_id,
                    r.id,
                    p.id,
                    true,
                    r.created_by
                FROM roles r
                JOIN permisos p ON p.code = ANY(:permission_codes)
                WHERE r.code = :role_code
                  AND NOT EXISTS (
                    SELECT 1
                    FROM rol_permisos rp
                    WHERE rp.rol_id = r.id
                      AND rp.permiso_id = p.id
                  )
                """
            ).bindparams(
                sa.bindparam("role_code", value=role_code),
                sa.bindparam(
                    "permission_codes",
                    value=permission_codes,
                    type_=postgresql.ARRAY(sa.String()),
                ),
            )
        )


def upgrade() -> None:
    op.create_table(
        "tratamientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("especialidad", sa.String(120), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("odontologo_responsable_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("odontologos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sede_principal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sedes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tratamientos_empresa_paciente", "tratamientos", ["empresa_id", "paciente_id"])
    op.create_index("ix_tratamientos_empresa_estado", "tratamientos", ["empresa_id", "estado"])
    op.create_index("ix_tratamientos_empresa_odontologo", "tratamientos", ["empresa_id", "odontologo_responsable_id"])
    op.create_index("ix_tratamientos_empresa_sede", "tratamientos", ["empresa_id", "sede_principal_id"])
    op.create_index("ix_tratamientos_empresa_id", "tratamientos", ["empresa_id"])
    op.create_index("ix_tratamientos_paciente_id", "tratamientos", ["paciente_id"])
    op.create_index("ix_tratamientos_odontologo_responsable_id", "tratamientos", ["odontologo_responsable_id"])
    op.create_index("ix_tratamientos_sede_principal_id", "tratamientos", ["sede_principal_id"])

    op.create_table(
        "tratamiento_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tratamientos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(120), nullable=True),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("odontologos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sedes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("citas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("valor_unitario", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("cantidad", sa.Numeric(10, 2), server_default="1", nullable=False),
        sa.Column("valor_total", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("fecha_estimada", sa.Date(), nullable=True),
        sa.Column("fecha_realizacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("requiere_pieza_dental", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("pieza_dental", sa.String(30), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valor_unitario >= 0", name="ck_proc_valor_unitario_no_negativo"),
        sa.CheckConstraint("cantidad > 0", name="ck_proc_cantidad_positiva"),
        sa.CheckConstraint("valor_total >= 0", name="ck_proc_valor_total_no_negativo"),
    )
    op.create_index("ix_proc_empresa_tratamiento", "tratamiento_procedimientos", ["empresa_id", "tratamiento_id"])
    op.create_index("ix_proc_empresa_estado", "tratamiento_procedimientos", ["empresa_id", "estado"])
    op.create_index("ix_proc_empresa_odontologo", "tratamiento_procedimientos", ["empresa_id", "odontologo_id"])
    op.create_index("ix_proc_empresa_sede", "tratamiento_procedimientos", ["empresa_id", "sede_id"])
    op.create_index("ix_proc_cita", "tratamiento_procedimientos", ["cita_id"])
    op.create_index("ix_tratamiento_procedimientos_empresa_id", "tratamiento_procedimientos", ["empresa_id"])
    op.create_index("ix_tratamiento_procedimientos_tratamiento_id", "tratamiento_procedimientos", ["tratamiento_id"])
    op.create_index("ix_tratamiento_procedimientos_paciente_id", "tratamiento_procedimientos", ["paciente_id"])
    op.create_index("ix_tratamiento_procedimientos_odontologo_id", "tratamiento_procedimientos", ["odontologo_id"])
    op.create_index("ix_tratamiento_procedimientos_sede_id", "tratamiento_procedimientos", ["sede_id"])
    op.create_index("ix_tratamiento_procedimientos_cita_id", "tratamiento_procedimientos", ["cita_id"])

    op.create_table(
        "presupuestos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tratamientos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero", sa.String(50), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("estado", sa.String(40), nullable=False),
        sa.Column("valor_bruto", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("descuento_tipo", sa.String(20), nullable=True),
        sa.Column("descuento_valor", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("valor_descuento_calculado", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("valor_final", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("fecha_emision", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aprobado_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rechazado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rechazado_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "tratamiento_id", "version", name="uq_presupuestos_empresa_tratamiento_version"),
        sa.CheckConstraint("valor_final >= 0", name="ck_presupuestos_valor_final_no_negativo"),
        sa.CheckConstraint("descuento_valor >= 0", name="ck_presupuestos_descuento_no_negativo"),
        sa.CheckConstraint("valor_descuento_calculado >= 0", name="ck_presupuestos_descuento_calc_no_negativo"),
    )
    op.create_index("ix_presupuestos_empresa_estado", "presupuestos", ["empresa_id", "estado"])
    op.create_index("ix_presupuestos_empresa_paciente", "presupuestos", ["empresa_id", "paciente_id"])
    op.create_index("ix_presupuestos_empresa_id", "presupuestos", ["empresa_id"])
    op.create_index("ix_presupuestos_paciente_id", "presupuestos", ["paciente_id"])
    op.create_index("ix_presupuestos_tratamiento_id", "presupuestos", ["tratamiento_id"])

    op.create_table(
        "presupuesto_detalle",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("presupuesto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("procedimiento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tratamiento_procedimientos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(120), nullable=True),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_unitario", sa.Numeric(14, 2), nullable=False),
        sa.Column("valor_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
    )
    op.create_index("ix_presupuesto_detalle_presupuesto", "presupuesto_detalle", ["presupuesto_id"])
    op.create_index("ix_presupuesto_detalle_empresa_id", "presupuesto_detalle", ["empresa_id"])
    op.create_index("ix_presupuesto_detalle_presupuesto_id", "presupuesto_detalle", ["presupuesto_id"])

    op.create_table(
        "pagos_tratamiento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tratamientos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("presupuesto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("presupuestos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("odontologos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valor", sa.Numeric(14, 2), nullable=False),
        sa.Column("medio_pago", sa.String(30), nullable=False),
        sa.Column("referencia", sa.String(120), nullable=True),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("registrado_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reversado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversado_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("motivo_reversion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_pagos_tratamiento_valor_positivo"),
    )
    op.create_index("ix_pagos_empresa_fecha", "pagos_tratamiento", ["empresa_id", "fecha_pago"])
    op.create_index("ix_pagos_empresa_tratamiento", "pagos_tratamiento", ["empresa_id", "tratamiento_id"])
    op.create_index("ix_pagos_empresa_paciente", "pagos_tratamiento", ["empresa_id", "paciente_id"])
    op.create_index("ix_pagos_empresa_sede", "pagos_tratamiento", ["empresa_id", "sede_id"])
    op.create_index("ix_pagos_empresa_odontologo", "pagos_tratamiento", ["empresa_id", "odontologo_id"])
    op.create_index("ix_pagos_empresa_estado", "pagos_tratamiento", ["empresa_id", "estado"])
    op.create_index("ix_pagos_tratamiento_empresa_id", "pagos_tratamiento", ["empresa_id"])
    op.create_index("ix_pagos_tratamiento_tratamiento_id", "pagos_tratamiento", ["tratamiento_id"])
    op.create_index("ix_pagos_tratamiento_paciente_id", "pagos_tratamiento", ["paciente_id"])
    op.create_index("ix_pagos_tratamiento_sede_id", "pagos_tratamiento", ["sede_id"])
    op.create_index("ix_pagos_tratamiento_odontologo_id", "pagos_tratamiento", ["odontologo_id"])

    op.create_table(
        "tratamiento_eventos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tratamientos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo_evento", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tratamiento_eventos_tratamiento_fecha", "tratamiento_eventos", ["tratamiento_id", "created_at"])
    op.create_index("ix_tratamiento_eventos_empresa_id", "tratamiento_eventos", ["empresa_id"])
    op.create_index("ix_tratamiento_eventos_tratamiento_id", "tratamiento_eventos", ["tratamiento_id"])

    op.add_column("citas", sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("citas", sa.Column("procedimiento_tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_citas_tratamiento_id", "citas", "tratamientos", ["tratamiento_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_citas_procedimiento_tratamiento_id", "citas", "tratamiento_procedimientos", ["procedimiento_tratamiento_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_citas_tratamiento_id", "citas", ["tratamiento_id"])
    op.create_index("ix_citas_procedimiento_tratamiento_id", "citas", ["procedimiento_tratamiento_id"])

    _seed_permissions()


def downgrade() -> None:
    op.drop_index("ix_citas_procedimiento_tratamiento_id", table_name="citas")
    op.drop_index("ix_citas_tratamiento_id", table_name="citas")
    op.drop_constraint("fk_citas_procedimiento_tratamiento_id", "citas", type_="foreignkey")
    op.drop_constraint("fk_citas_tratamiento_id", "citas", type_="foreignkey")
    op.drop_column("citas", "procedimiento_tratamiento_id")
    op.drop_column("citas", "tratamiento_id")

    op.drop_index("ix_tratamiento_eventos_tratamiento_id", table_name="tratamiento_eventos")
    op.drop_index("ix_tratamiento_eventos_empresa_id", table_name="tratamiento_eventos")
    op.drop_index("ix_tratamiento_eventos_tratamiento_fecha", table_name="tratamiento_eventos")
    op.drop_table("tratamiento_eventos")

    for index in (
        "ix_pagos_tratamiento_odontologo_id",
        "ix_pagos_tratamiento_sede_id",
        "ix_pagos_tratamiento_paciente_id",
        "ix_pagos_tratamiento_tratamiento_id",
        "ix_pagos_tratamiento_empresa_id",
        "ix_pagos_empresa_estado",
        "ix_pagos_empresa_odontologo",
        "ix_pagos_empresa_sede",
        "ix_pagos_empresa_paciente",
        "ix_pagos_empresa_tratamiento",
        "ix_pagos_empresa_fecha",
    ):
        op.drop_index(index, table_name="pagos_tratamiento")
    op.drop_table("pagos_tratamiento")

    op.drop_index("ix_presupuesto_detalle_presupuesto_id", table_name="presupuesto_detalle")
    op.drop_index("ix_presupuesto_detalle_empresa_id", table_name="presupuesto_detalle")
    op.drop_index("ix_presupuesto_detalle_presupuesto", table_name="presupuesto_detalle")
    op.drop_table("presupuesto_detalle")

    op.drop_index("ix_presupuestos_tratamiento_id", table_name="presupuestos")
    op.drop_index("ix_presupuestos_paciente_id", table_name="presupuestos")
    op.drop_index("ix_presupuestos_empresa_id", table_name="presupuestos")
    op.drop_index("ix_presupuestos_empresa_paciente", table_name="presupuestos")
    op.drop_index("ix_presupuestos_empresa_estado", table_name="presupuestos")
    op.drop_table("presupuestos")

    for index in (
        "ix_tratamiento_procedimientos_cita_id",
        "ix_tratamiento_procedimientos_sede_id",
        "ix_tratamiento_procedimientos_odontologo_id",
        "ix_tratamiento_procedimientos_paciente_id",
        "ix_tratamiento_procedimientos_tratamiento_id",
        "ix_tratamiento_procedimientos_empresa_id",
        "ix_proc_cita",
        "ix_proc_empresa_sede",
        "ix_proc_empresa_odontologo",
        "ix_proc_empresa_estado",
        "ix_proc_empresa_tratamiento",
    ):
        op.drop_index(index, table_name="tratamiento_procedimientos")
    op.drop_table("tratamiento_procedimientos")

    for index in (
        "ix_tratamientos_sede_principal_id",
        "ix_tratamientos_odontologo_responsable_id",
        "ix_tratamientos_paciente_id",
        "ix_tratamientos_empresa_id",
        "ix_tratamientos_empresa_sede",
        "ix_tratamientos_empresa_odontologo",
        "ix_tratamientos_empresa_estado",
        "ix_tratamientos_empresa_paciente",
    ):
        op.drop_index(index, table_name="tratamientos")
    op.drop_table("tratamientos")

    op.execute(
        """
        DELETE FROM rol_permisos rp
        USING permisos p
        WHERE rp.permiso_id = p.id
          AND p.code IN (
            'treatments.create',
            'treatments.cancel',
            'finance.dashboard.view'
          )
        """
    )
    op.execute(
        """
        DELETE FROM permisos
        WHERE code IN (
            'treatments.create',
            'treatments.cancel',
            'finance.dashboard.view'
        )
        """
    )
