"""add clinical narrative documents

Revision ID: 20260724_0021
Revises: 20260724_0020
Create Date: 2026-07-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260724_0021"
down_revision = "20260724_0020"
branch_labels = None
depends_on = None


CLINICAL_DOCUMENT_PERMISSIONS = [
    ("clinical_documents.view", "Ver informes clínicos", "clinical_documents", "Consultar informes, remisiones, certificados y cartas clínicas."),
    ("clinical_documents.create", "Crear informes clínicos", "clinical_documents", "Crear borradores de informes, remisiones, certificados y cartas clínicas."),
    ("clinical_documents.edit_draft", "Editar borradores de informes", "clinical_documents", "Editar documentos clínicos narrativos en borrador."),
    ("clinical_documents.finalize", "Finalizar informes clínicos", "clinical_documents", "Finalizar documentos clínicos y generar PDF institucional."),
    ("clinical_documents.download", "Descargar informes clínicos", "clinical_documents", "Descargar PDFs clínicos almacenados."),
    ("clinical_documents.void", "Anular informes clínicos", "clinical_documents", "Anular documentos clínicos finalizados conservando histórico."),
]


ROLE_PERMISSIONS = {
    "DENTIST": [
        "clinical_documents.view",
        "clinical_documents.create",
        "clinical_documents.edit_draft",
        "clinical_documents.finalize",
        "clinical_documents.download",
    ],
    "DENTIST_ADMIN": [
        "clinical_documents.view",
        "clinical_documents.create",
        "clinical_documents.edit_draft",
        "clinical_documents.finalize",
        "clinical_documents.download",
        "clinical_documents.void",
    ],
}


def _seed_permissions() -> None:
    for code, name, module, description in CLINICAL_DOCUMENT_PERMISSIONS:
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
                sa.bindparam(
                    "permission_codes",
                    value=permission_codes,
                    type_=postgresql.ARRAY(sa.String()),
                ),
            )
        )


def upgrade() -> None:
    _seed_permissions()
    _assign_permissions()
    op.create_table(
        "documentos_clinicos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("professional_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dentist_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tipo_documento", sa.String(length=40), nullable=False),
        sa.Column("estado", sa.String(length=30), server_default="DRAFT", nullable=False),
        sa.Column("numero_documento", sa.String(length=40), nullable=True),
        sa.Column("consecutivo", sa.Integer(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=True),
        sa.Column("destinatario_nombre", sa.String(length=200), nullable=True),
        sa.Column("destinatario_entidad", sa.String(length=200), nullable=True),
        sa.Column("destinatario_especialidad", sa.String(length=160), nullable=True),
        sa.Column("asunto", sa.String(length=250), nullable=True),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("fecha_clinica", sa.Date(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("institution_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("patient_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("professional_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pdf_storage_path", sa.String(length=600), nullable=True),
        sa.Column("pdf_sha256", sa.String(length=128), nullable=True),
        sa.Column("integrity_hash", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("tipo_documento IN ('REFERRAL', 'CLINICAL_REPORT', 'CERTIFICATE', 'GENERAL_LETTER')", name="ck_documentos_clinicos_tipo"),
        sa.CheckConstraint("estado IN ('DRAFT', 'FINALIZED', 'VOIDED')", name="ck_documentos_clinicos_estado"),
        sa.CheckConstraint("version >= 1", name="ck_documentos_clinicos_version_positive"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["professional_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dentist_profile_id"], ["odontologos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evolucion_id"], ["evoluciones_clinicas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["previous_document_id"], ["documentos_clinicos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finalized_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["voided_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "numero_documento", name="uq_documentos_clinicos_empresa_numero"),
    )
    op.create_index("ix_documentos_clinicos_empresa_paciente", "documentos_clinicos", ["empresa_id", "paciente_id"])
    op.create_index("ix_documentos_clinicos_empresa_estado", "documentos_clinicos", ["empresa_id", "estado"])
    op.create_index("ix_documentos_clinicos_empresa_tipo", "documentos_clinicos", ["empresa_id", "tipo_documento"])
    op.create_index("ix_documentos_clinicos_empresa_fecha", "documentos_clinicos", ["empresa_id", "fecha_clinica"])
    op.create_index("ix_documentos_clinicos_profesional", "documentos_clinicos", ["empresa_id", "dentist_profile_id"])


def downgrade() -> None:
    permission_codes = [code for code, *_ in CLINICAL_DOCUMENT_PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING permisos p
            WHERE rp.permiso_id = p.id
              AND p.code = ANY(:permission_codes)
            """
        ).bindparams(
            sa.bindparam(
                "permission_codes",
                value=permission_codes,
                type_=postgresql.ARRAY(sa.String()),
            )
        )
    )
    op.drop_index("ix_documentos_clinicos_profesional", table_name="documentos_clinicos")
    op.drop_index("ix_documentos_clinicos_empresa_fecha", table_name="documentos_clinicos")
    op.drop_index("ix_documentos_clinicos_empresa_tipo", table_name="documentos_clinicos")
    op.drop_index("ix_documentos_clinicos_empresa_estado", table_name="documentos_clinicos")
    op.drop_index("ix_documentos_clinicos_empresa_paciente", table_name="documentos_clinicos")
    op.drop_table("documentos_clinicos")
