"""add consent instances and pre-signature clinical flow

Revision ID: 20260801_0024
Revises: 20260801_0023
Create Date: 2026-08-01 02:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260801_0024"
down_revision = "20260801_0023"
branch_labels = None
depends_on = None


PERMISSIONS = [
    ("consent.instance.read", "Ver consentimientos del paciente", "consent_instances", "Consultar instancias de consentimiento autorizadas."),
    ("consent.instance.create", "Preparar consentimientos", "consent_instances", "Crear instancias en borrador con contexto clínico."),
    ("consent.instance.edit_draft", "Editar borradores de consentimiento", "consent_instances", "Modificar el contexto de instancias en borrador."),
    ("consent.instance.review", "Revisar consentimientos clínicamente", "consent_instances", "Confirmar profesionalmente el contenido antes de firma."),
    ("consent.instance.mark_pending_signature", "Habilitar firma futura de consentimientos", "consent_instances", "Permiso reservado para la emisión de sesión en C019A.3."),
    ("consent.instance.void", "Anular instancias de consentimiento", "consent_instances", "Anular administrativamente instancias conservando historial."),
    ("consent.instance.view_audit", "Auditar instancias de consentimiento", "consent_instances", "Consultar trazabilidad autorizada de instancias."),
]

ROLE_PERMISSIONS = {
    "ADMINISTRATOR": ["consent.instance.read", "consent.instance.create", "consent.instance.edit_draft", "consent.instance.void", "consent.instance.view_audit"],
    "DENTIST_ADMIN": [item[0] for item in PERMISSIONS],
    "DENTIST": ["consent.instance.read", "consent.instance.create", "consent.instance.edit_draft", "consent.instance.review", "consent.instance.mark_pending_signature"],
    "SECRETARY": ["consent.instance.read", "consent.instance.create", "consent.instance.edit_draft"],
}


def _permissions() -> None:
    for code, name, module, description in PERMISSIONS:
        op.execute(sa.text("""
            INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), :code, :name, :module, :description, true, now(), now())
            ON CONFLICT (code) DO UPDATE SET nombre=EXCLUDED.nombre, modulo=EXCLUDED.modulo,
                descripcion=EXCLUDED.descripcion, is_active=true, updated_at=now()
        """).bindparams(code=code, name=name, module=module, description=description))
    for role, codes in ROLE_PERMISSIONS.items():
        op.execute(sa.text("""
            INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
            SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
            FROM roles r JOIN permisos p ON p.code = ANY(:codes)
            WHERE r.code=:role AND NOT EXISTS (
                SELECT 1 FROM rol_permisos rp WHERE rp.rol_id=r.id AND rp.permiso_id=p.id
            )
        """).bindparams(sa.bindparam("role", value=role), sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String()))))


def upgrade() -> None:
    _permissions()
    op.create_table(
        "consentimiento_instancia_consecutivos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("next_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", name="uq_consent_instance_sequence_company"),
    )
    op.create_table(
        "consentimiento_instancias",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("professional_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dentist_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("visible_number", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False),
        sa.Column("document_kind", sa.String(60), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("clinical_date", sa.Date(), nullable=False),
        sa.Column("zona_horaria", sa.String(100), nullable=False),
        sa.Column("display_title", sa.String(250), nullable=False),
        sa.Column("rendered_content_snapshot", sa.Text(), nullable=True),
        sa.Column("template_content_snapshot", sa.Text(), nullable=False),
        sa.Column("variable_values_snapshot", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("missing_variables", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("context_snapshot", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("template_version_number", sa.Integer(), nullable=False),
        sa.Column("template_content_sha256", sa.String(64), nullable=False),
        sa.Column("instance_content_sha256", sa.String(64), nullable=True),
        sa.Column("context_sha256", sa.String(64), nullable=True),
        sa.Column("integrity_hash", sa.String(64), nullable=True),
        sa.Column("professional_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("professional_confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ready_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("sequence_number >= 1", name="ck_consent_instance_sequence_positive"),
        sa.CheckConstraint("row_version >= 1", name="ck_consent_instance_row_version_positive"),
        sa.CheckConstraint("status IN ('DRAFT','READY_FOR_REVIEW','VOIDED')", name="ck_consent_instance_status"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["consentimiento_plantillas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["professional_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dentist_profile_id"], ["odontologos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["professional_confirmed_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ready_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["voided_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "sequence_number", name="uq_consent_instance_company_sequence"),
        sa.UniqueConstraint("empresa_id", "visible_number", name="uq_consent_instance_company_visible"),
    )
    op.create_index("ix_consent_instance_company_patient_date", "consentimiento_instancias", ["empresa_id", "paciente_id", "clinical_date"])
    op.create_index("ix_consent_instance_company_status", "consentimiento_instancias", ["empresa_id", "status"])
    op.create_index("ix_consent_instance_company_site", "consentimiento_instancias", ["empresa_id", "sede_id"])
    op.create_table(
        "consentimiento_instancia_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procedure_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("treatment_procedure_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code_snapshot", sa.String(100), nullable=True),
        sa.Column("name_snapshot", sa.String(200), nullable=False),
        sa.Column("description_snapshot", sa.Text(), nullable=True),
        sa.Column("order_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["instance_id"], ["consentimiento_instancias.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["procedure_catalog_id"], ["catalogo_procedimientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["treatment_procedure_id"], ["tratamiento_procedimientos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "order_number", name="uq_consent_instance_procedure_order"),
    )
    op.create_index("ix_consent_instance_procedure_company", "consentimiento_instancia_procedimientos", ["empresa_id", "instance_id"])


def downgrade() -> None:
    op.drop_index("ix_consent_instance_procedure_company", table_name="consentimiento_instancia_procedimientos")
    op.drop_table("consentimiento_instancia_procedimientos")
    op.drop_index("ix_consent_instance_company_site", table_name="consentimiento_instancias")
    op.drop_index("ix_consent_instance_company_status", table_name="consentimiento_instancias")
    op.drop_index("ix_consent_instance_company_patient_date", table_name="consentimiento_instancias")
    op.drop_table("consentimiento_instancias")
    op.drop_table("consentimiento_instancia_consecutivos")
    # Permission rows are retained because bootstrap may have created them.
