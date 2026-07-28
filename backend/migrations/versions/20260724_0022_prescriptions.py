"""add odontological prescriptions

Revision ID: 20260724_0022
Revises: 20260724_0021
Create Date: 2026-07-24 00:22:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260724_0022"
down_revision = "20260724_0021"
branch_labels = None
depends_on = None


PRESCRIPTION_PERMISSIONS = [
    ("prescriptions.view", "Ver recetas", "prescriptions", "Consultar recetas odontológicas autorizadas."),
    ("prescriptions.create", "Crear recetas", "prescriptions", "Crear borradores de recetas odontológicas."),
    ("prescriptions.edit_draft", "Editar borradores de recetas", "prescriptions", "Editar recetas odontológicas en borrador."),
    ("prescriptions.finalize", "Finalizar recetas", "prescriptions", "Finalizar recetas y generar PDF institucional."),
    ("prescriptions.download", "Descargar recetas", "prescriptions", "Descargar PDFs históricos de recetas."),
    ("prescriptions.void", "Anular recetas", "prescriptions", "Anular recetas finalizadas conservando histórico."),
]


ROLE_PERMISSIONS = {
    "DENTIST": [
        "prescriptions.view",
        "prescriptions.create",
        "prescriptions.edit_draft",
        "prescriptions.finalize",
        "prescriptions.download",
    ],
    "DENTIST_ADMIN": [
        "prescriptions.view",
        "prescriptions.create",
        "prescriptions.edit_draft",
        "prescriptions.finalize",
        "prescriptions.download",
        "prescriptions.void",
    ],
}


def _seed_permissions() -> None:
    for code, name, module, description in PRESCRIPTION_PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), :code, :name, :module, :description, true, now(), now())
                ON CONFLICT (code) DO UPDATE
                SET nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true,
                    updated_at = now()
                """
            ).bindparams(code=code, name=name, module=module, description=description)
        )


def _assign_permissions() -> None:
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        op.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (
                    id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at
                )
                SELECT
                    gen_random_uuid(),
                    r.empresa_id,
                    r.id,
                    p.id,
                    true,
                    r.created_by,
                    now(),
                    now()
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
                sa.bindparam("permission_codes", value=permission_codes, type_=postgresql.ARRAY(sa.String())),
            )
        )


def upgrade() -> None:
    _seed_permissions()
    _assign_permissions()
    op.create_table(
        "recetas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dentist_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_prescription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estado", sa.String(length=30), server_default="DRAFT", nullable=False),
        sa.Column("numero_receta", sa.String(length=40), nullable=True),
        sa.Column("consecutivo", sa.Integer(), nullable=True),
        sa.Column("fecha_clinica", sa.Date(), nullable=False),
        sa.Column("indicaciones_generales", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("alergias_revisadas", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("institution_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("patient_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("professional_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prescription_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("clinical_alerts_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pdf_storage_path", sa.String(length=600), nullable=True),
        sa.Column("pdf_sha256", sa.String(length=128), nullable=True),
        sa.Column("integrity_hash", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('DRAFT', 'FINALIZED', 'VOIDED')", name="ck_recetas_estado"),
        sa.CheckConstraint("version >= 1", name="ck_recetas_version_positive"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["professional_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dentist_profile_id"], ["odontologos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evolucion_id"], ["evoluciones_clinicas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["previous_prescription_id"], ["recetas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finalized_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["voided_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "numero_receta", name="uq_recetas_empresa_numero"),
    )
    op.create_index("ix_recetas_empresa_paciente", "recetas", ["empresa_id", "paciente_id"])
    op.create_index("ix_recetas_empresa_estado", "recetas", ["empresa_id", "estado"])
    op.create_index("ix_recetas_empresa_fecha", "recetas", ["empresa_id", "fecha_clinica"])
    op.create_index("ix_recetas_profesional", "recetas", ["empresa_id", "dentist_profile_id"])
    op.create_table(
        "receta_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("nombre_generico", sa.String(length=240), nullable=False),
        sa.Column("marca", sa.String(length=200), nullable=True),
        sa.Column("forma_farmaceutica", sa.String(length=160), nullable=False),
        sa.Column("concentracion", sa.String(length=160), nullable=False),
        sa.Column("dosis", sa.String(length=180), nullable=False),
        sa.Column("via", sa.String(length=120), nullable=False),
        sa.Column("frecuencia", sa.String(length=180), nullable=False),
        sa.Column("duracion", sa.String(length=160), nullable=False),
        sa.Column("cantidad_total", sa.String(length=120), nullable=False),
        sa.Column("unidad_cantidad", sa.String(length=120), nullable=True),
        sa.Column("indicaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("position >= 1", name="ck_receta_items_position_positive"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receta_id"], ["recetas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_receta_items_receta", "receta_items", ["receta_id"])


def downgrade() -> None:
    permission_codes = [code for code, *_ in PRESCRIPTION_PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING permisos p
            WHERE rp.permiso_id = p.id
              AND p.code = ANY(:permission_codes)
            """
        ).bindparams(sa.bindparam("permission_codes", value=permission_codes, type_=postgresql.ARRAY(sa.String())))
    )
    op.drop_index("ix_receta_items_receta", table_name="receta_items")
    op.drop_table("receta_items")
    op.drop_index("ix_recetas_profesional", table_name="recetas")
    op.drop_index("ix_recetas_empresa_fecha", table_name="recetas")
    op.drop_index("ix_recetas_empresa_estado", table_name="recetas")
    op.drop_index("ix_recetas_empresa_paciente", table_name="recetas")
    op.drop_table("recetas")
