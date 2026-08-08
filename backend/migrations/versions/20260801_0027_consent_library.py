"""official consent library

Revision ID: 20260801_0027
Revises: 20260801_0026
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260801_0027"
down_revision = "20260801_0026"
branch_labels = None
depends_on = None

CONSENT_LIBRARY_PERMISSIONS = [
    ("consent.library.read", "Ver biblioteca Dentia", "consent_library", "Consultar la biblioteca oficial de documentos odontológicos Dentia."),
    ("consent.library.install", "Instalar plantillas oficiales", "consent_library", "Instalar versiones oficiales publicadas sin modificar su contenido."),
    ("consent.library.clone", "Copiar plantillas Dentia", "consent_library", "Crear copias editables bajo responsabilidad de la clínica."),
    ("consent.library.manage", "Administrar biblioteca Dentia", "consent_library", "Importar y mantener la biblioteca oficial de plataforma."),
]

CONSENT_LIBRARY_ROLE_PERMISSIONS = {
    "ADMINISTRATOR": ["consent.library.read", "consent.library.install", "consent.library.clone"],
    "DENTIST_ADMIN": ["consent.library.read", "consent.library.install", "consent.library.clone"],
    "PLATFORM_ADMIN": ["consent.library.read", "consent.library.manage"],
}


def _seed_permissions() -> None:
    for code, name, module, description in CONSENT_LIBRARY_PERMISSIONS:
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
    for role_code, permission_codes in CONSENT_LIBRARY_ROLE_PERMISSIONS.items():
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

    op.create_table(
        "consentimiento_biblioteca_documentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("codigo", sa.String(length=80), nullable=False),
        sa.Column("titulo", sa.String(length=250), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column("tipo_documento", sa.String(length=60), nullable=False),
        sa.Column("categoria", sa.String(length=100), nullable=False),
        sa.Column("especialidad_codigo", sa.String(length=80), nullable=True),
        sa.Column("especialidad_nombre", sa.String(length=160), nullable=True),
        sa.Column("signer_scope", sa.String(length=40), nullable=False),
        sa.Column("requires_patient_signature", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supports_electronic_signature", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_package_version", sa.String(length=80), nullable=False),
        sa.Column("source_document_hash", sa.String(length=64), nullable=False),
        sa.Column("source_page_start", sa.Integer(), nullable=False),
        sa.Column("source_page_end", sa.Integer(), nullable=False),
        sa.Column("source_title_exact", sa.String(length=300), nullable=True),
        sa.Column("source_origin_note", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(length=250), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_page_start >= 1 AND source_page_end >= source_page_start", name="ck_consent_library_pages"),
        sa.CheckConstraint("tipo_documento IN ('INFORMED_CONSENT','TREATMENT_REFUSAL','CERTIFICATE','POST_CARE_INSTRUCTIONS','PRE_CARE_INSTRUCTIONS','NO_WARRANTY_ACKNOWLEDGEMENT','AESTHETIC_APPROVAL','TREATMENT_TERMINATION_ACKNOWLEDGEMENT')", name="ck_consent_library_document_type"),
        sa.CheckConstraint("signer_scope IN ('ADULT_SELF','ADULT_OR_REPRESENTATIVE','REPRESENTATIVE_REQUIRED','NO_SIGNATURE_REQUIRED','ADMINISTRATIVE_RECORD')", name="ck_consent_library_signer_scope"),
        sa.UniqueConstraint("codigo", name="uq_consent_library_document_code"),
    )
    op.create_index("ix_consent_library_document_type", "consentimiento_biblioteca_documentos", ["tipo_documento"])
    op.create_index("ix_consent_library_document_specialty", "consentimiento_biblioteca_documentos", ["especialidad_codigo"])

    op.create_table(
        "consentimiento_biblioteca_versiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("library_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_biblioteca_documentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("publication_status", sa.String(length=30), nullable=False, server_default="READY_FOR_REVIEW"),
        sa.Column("legal_review_status", sa.String(length=80), nullable=False),
        sa.Column("clinical_review_status", sa.String(length=80), nullable=False),
        sa.Column("reviewed_countries", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_reference", sa.String(length=250), nullable=True),
        sa.Column("content_format", sa.String(length=40), nullable=False, server_default="RESTRICTED_MARKDOWN_V1"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("source_text_sha256", sa.String(length=64), nullable=False),
        sa.Column("normalized_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("variable_schema_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_pages", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("transformation_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("equivalence_reviewer_name", sa.String(length=200), nullable=True),
        sa.Column("equivalence_review_reason", sa.Text(), nullable=True),
        sa.Column("equivalence_checklist_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version_number >= 1", name="ck_consent_library_version_number"),
        sa.CheckConstraint("country_code IN ('CO','CL')", name="ck_consent_library_country"),
        sa.CheckConstraint("language_code IN ('es-CO','es-CL')", name="ck_consent_library_language"),
        sa.CheckConstraint("publication_status IN ('READY_FOR_REVIEW','PUBLISHED','RETIRED')", name="ck_consent_library_publication_status"),
        sa.UniqueConstraint("library_document_id", "country_code", "language_code", "version_number", name="uq_consent_library_version_locale_number"),
    )
    op.create_index("ix_consent_library_version_status", "consentimiento_biblioteca_versiones", ["publication_status"])
    op.create_index("ix_consent_library_version_country", "consentimiento_biblioteca_versiones", ["country_code", "language_code"])

    op.create_table(
        "consentimiento_biblioteca_instalaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("library_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_biblioteca_documentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("library_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_biblioteca_versiones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("installed_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_plantillas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("installed_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("installation_mode", sa.String(length=20), nullable=False),
        sa.Column("content_responsibility", sa.String(length=20), nullable=False),
        sa.Column("installed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("installation_mode IN ('EXACT','CLONE')", name="ck_consent_library_install_mode"),
        sa.CheckConstraint("content_responsibility IN ('DENTIA','CLINIC')", name="ck_consent_library_install_responsibility"),
        sa.UniqueConstraint("empresa_id", "library_version_id", "installation_mode", name="uq_consent_library_install_company_version_mode"),
    )
    op.create_index("ix_consent_library_install_company", "consentimiento_biblioteca_instalaciones", ["empresa_id"])

    op.add_column("consentimiento_plantillas", sa.Column("template_origin", sa.String(length=40), nullable=False, server_default="CLINIC_CUSTOM"))
    op.add_column("consentimiento_plantillas", sa.Column("source_library_document_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("consentimiento_plantillas", sa.Column("content_responsibility", sa.String(length=20), nullable=False, server_default="CLINIC"))
    op.create_foreign_key("fk_consent_template_source_library_document", "consentimiento_plantillas", "consentimiento_biblioteca_documentos", ["source_library_document_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_consent_template_origin", "consentimiento_plantillas", ["empresa_id", "template_origin"])

    op.add_column("consentimiento_plantilla_versiones", sa.Column("source_library_version_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("consentimiento_plantilla_versiones", sa.Column("source_document_hash", sa.String(length=64), nullable=True))
    op.add_column("consentimiento_plantilla_versiones", sa.Column("legal_review_status", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_plantilla_versiones", sa.Column("clinical_review_status", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_plantilla_versiones", sa.Column("reviewed_countries", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("consentimiento_plantilla_versiones", sa.Column("installed_from_library_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_consent_version_source_library_version", "consentimiento_plantilla_versiones", "consentimiento_biblioteca_versiones", ["source_library_version_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_consent_template_version_source_library", "consentimiento_plantilla_versiones", ["source_library_version_id"])


def downgrade() -> None:
    op.drop_index("ix_consent_template_version_source_library", table_name="consentimiento_plantilla_versiones")
    op.drop_constraint("fk_consent_version_source_library_version", "consentimiento_plantilla_versiones", type_="foreignkey")
    op.drop_column("consentimiento_plantilla_versiones", "installed_from_library_at")
    op.drop_column("consentimiento_plantilla_versiones", "reviewed_countries")
    op.drop_column("consentimiento_plantilla_versiones", "clinical_review_status")
    op.drop_column("consentimiento_plantilla_versiones", "legal_review_status")
    op.drop_column("consentimiento_plantilla_versiones", "source_document_hash")
    op.drop_column("consentimiento_plantilla_versiones", "source_library_version_id")
    op.drop_index("ix_consent_template_origin", table_name="consentimiento_plantillas")
    op.drop_constraint("fk_consent_template_source_library_document", "consentimiento_plantillas", type_="foreignkey")
    op.drop_column("consentimiento_plantillas", "content_responsibility")
    op.drop_column("consentimiento_plantillas", "source_library_document_id")
    op.drop_column("consentimiento_plantillas", "template_origin")
    op.drop_index("ix_consent_library_install_company", table_name="consentimiento_biblioteca_instalaciones")
    op.drop_table("consentimiento_biblioteca_instalaciones")
    op.drop_index("ix_consent_library_version_country", table_name="consentimiento_biblioteca_versiones")
    op.drop_index("ix_consent_library_version_status", table_name="consentimiento_biblioteca_versiones")
    op.drop_table("consentimiento_biblioteca_versiones")
    op.drop_index("ix_consent_library_document_specialty", table_name="consentimiento_biblioteca_documentos")
    op.drop_index("ix_consent_library_document_type", table_name="consentimiento_biblioteca_documentos")
    op.drop_table("consentimiento_biblioteca_documentos")
