"""add tenant consent template and version engine

Revision ID: 20260801_0023
Revises: 20260724_0022
Create Date: 2026-08-01 00:23:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260801_0023"
down_revision = "20260724_0022"
branch_labels = None
depends_on = None


CONSENT_PERMISSIONS = [
    ("consent.template.read", "Ver plantillas de consentimiento", "consent_templates", "Consultar plantillas y versiones de consentimiento de la empresa."),
    ("consent.template.create", "Crear plantillas de consentimiento", "consent_templates", "Crear plantillas y nuevas versiones en borrador."),
    ("consent.template.edit_draft", "Editar borradores de consentimiento", "consent_templates", "Editar contenido y aplicabilidad de versiones en borrador."),
    ("consent.template.publish", "Publicar plantillas de consentimiento", "consent_templates", "Publicar versiones inmutables y reemplazar prospectivamente la vigente."),
    ("consent.template.retire", "Retirar plantillas de consentimiento", "consent_templates", "Retirar una versión publicada sin eliminar historial."),
    ("consent.template.void_draft", "Anular borradores de consentimiento", "consent_templates", "Anular borradores con motivo y trazabilidad."),
    ("consent.template.view_audit", "Auditar plantillas de consentimiento", "consent_templates", "Consultar trazabilidad administrativa autorizada de plantillas."),
]

FULL = [item[0] for item in CONSENT_PERMISSIONS]
ROLE_PERMISSIONS = {
    "ADMINISTRATOR": FULL,
    "DENTIST_ADMIN": FULL,
    "DENTIST": ["consent.template.read", "consent.template.create", "consent.template.edit_draft"],
    "SECRETARY": ["consent.template.read"],
}


def _seed_permissions() -> None:
    for code, name, module, description in CONSENT_PERMISSIONS:
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
                INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
                SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
                FROM roles r
                JOIN permisos p ON p.code = ANY(:permission_codes)
                WHERE r.code = :role_code
                  AND NOT EXISTS (
                    SELECT 1 FROM rol_permisos rp
                    WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
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
        "consentimiento_plantillas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("document_kind", sa.String(length=60), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_consent_template_empresa_codigo"),
    )
    op.create_index("ix_consent_template_empresa_activa", "consentimiento_plantillas", ["empresa_id", "is_active"])
    op.create_index("ix_consent_template_empresa_pais_tipo", "consentimiento_plantillas", ["empresa_id", "country_code", "document_kind"])

    op.create_table(
        "consentimiento_plantilla_versiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="DRAFT", nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_format", sa.String(length=40), server_default="RESTRICTED_MARKDOWN_V1", nullable=False),
        sa.Column("variable_schema_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
        sa.Column("based_on_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("scope_type", sa.String(length=20), server_default="GENERAL", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retire_reason", sa.Text(), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version_number >= 1", name="ck_consent_template_version_number_positive"),
        sa.CheckConstraint("row_version >= 1", name="ck_consent_template_row_version_positive"),
        sa.CheckConstraint("priority BETWEEN 0 AND 1000", name="ck_consent_template_priority_range"),
        sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','SUPERSEDED','RETIRED','VOIDED')", name="ck_consent_template_version_status"),
        sa.CheckConstraint("scope_type IN ('GENERAL','SPECIFIC')", name="ck_consent_template_scope_type"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["consentimiento_plantillas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["based_on_version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retired_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["voided_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version_number", name="uq_consent_template_version_number"),
    )
    op.create_index("ix_consent_template_version_empresa_estado", "consentimiento_plantilla_versiones", ["empresa_id", "status"])
    op.create_index("ix_consent_template_version_template_estado", "consentimiento_plantilla_versiones", ["template_id", "status"])
    op.create_index("uq_consent_template_one_published", "consentimiento_plantilla_versiones", ["template_id"], unique=True, postgresql_where=sa.text("status = 'PUBLISHED'"))

    op.create_table(
        "consentimiento_plantilla_version_sedes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "site_id", name="uq_consent_version_site"),
    )
    op.create_index("ix_consent_version_site_empresa", "consentimiento_plantilla_version_sedes", ["empresa_id", "site_id"])

    op.create_table(
        "consentimiento_plantilla_version_procedimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procedure_catalog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["procedure_catalog_id"], ["catalogo_procedimientos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "procedure_catalog_id", name="uq_consent_version_procedure"),
    )
    op.create_index("ix_consent_version_procedure_empresa", "consentimiento_plantilla_version_procedimientos", ["empresa_id", "procedure_catalog_id"])

    op.create_table(
        "consentimiento_plantilla_version_especialidades",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specialty_code", sa.String(length=80), nullable=False),
        sa.Column("specialty_name", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "specialty_code", name="uq_consent_version_specialty"),
    )
    op.create_index("ix_consent_version_specialty_empresa", "consentimiento_plantilla_version_especialidades", ["empresa_id", "specialty_code"])


def downgrade() -> None:
    op.drop_index("ix_consent_version_specialty_empresa", table_name="consentimiento_plantilla_version_especialidades")
    op.drop_table("consentimiento_plantilla_version_especialidades")
    op.drop_index("ix_consent_version_procedure_empresa", table_name="consentimiento_plantilla_version_procedimientos")
    op.drop_table("consentimiento_plantilla_version_procedimientos")
    op.drop_index("ix_consent_version_site_empresa", table_name="consentimiento_plantilla_version_sedes")
    op.drop_table("consentimiento_plantilla_version_sedes")
    op.drop_index("uq_consent_template_one_published", table_name="consentimiento_plantilla_versiones")
    op.drop_index("ix_consent_template_version_template_estado", table_name="consentimiento_plantilla_versiones")
    op.drop_index("ix_consent_template_version_empresa_estado", table_name="consentimiento_plantilla_versiones")
    op.drop_table("consentimiento_plantilla_versiones")
    op.drop_index("ix_consent_template_empresa_pais_tipo", table_name="consentimiento_plantillas")
    op.drop_index("ix_consent_template_empresa_activa", table_name="consentimiento_plantillas")
    op.drop_table("consentimiento_plantillas")
    # Permissions are intentionally retained: they may have been created by the
    # idempotent bootstrap before this migration and deleting them is destructive.
