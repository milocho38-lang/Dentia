"""add paper consent execution and digitized copy

Revision ID: 20260801_0030
Revises: 20260801_0029
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260801_0030"
down_revision = "20260801_0029"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("consent.paper.read", "Consultar consentimiento en papel", "consent_paper", "Consultar packet y copia digitalizada de consentimientos en papel."),
    ("consent.paper.prepare", "Preparar consentimiento en papel", "consent_paper", "Generar el packet inmutable para firma manuscrita."),
    ("consent.paper.record_signed", "Registrar firma manuscrita", "consent_paper", "Declarar que existe el original físico firmado."),
    ("consent.paper.upload", "Digitalizar consentimiento en papel", "consent_paper", "Cargar, ordenar y corregir páginas antes del sellado."),
    ("consent.paper.finalize", "Finalizar consentimiento en papel", "consent_paper", "Verificar y sellar la copia digitalizada final."),
)
ROLE_PERMISSIONS = {
    "ADMINISTRATOR": [code for code, *_ in PERMISSIONS],
    "DENTIST_ADMIN": [code for code, *_ in PERMISSIONS],
}


def _seed_permissions() -> None:
    for code, name, module, description in PERMISSIONS:
        op.execute(sa.text("""
            INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), :code, :name, :module, :description, true, now(), now())
            ON CONFLICT (code) DO UPDATE SET nombre=EXCLUDED.nombre, modulo=EXCLUDED.modulo,
              descripcion=EXCLUDED.descripcion, is_active=true, updated_at=now()
        """).bindparams(code=code, name=name, module=module, description=description))
    for role_code, codes in ROLE_PERMISSIONS.items():
        op.execute(sa.text("""
            INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
            SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
            FROM roles r JOIN permisos p ON p.code = ANY(:codes)
            WHERE r.code=:role_code AND NOT EXISTS (
              SELECT 1 FROM rol_permisos rp WHERE rp.rol_id=r.id AND rp.permiso_id=p.id)
        """).bindparams(
            sa.bindparam("role_code", value=role_code),
            sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String())),
        ))


def upgrade() -> None:
    _seed_permissions()
    op.add_column("consentimiento_instancias", sa.Column("completion_channel", sa.String(20), nullable=True))
    op.create_check_constraint("ck_consent_instance_completion_channel", "consentimiento_instancias", "completion_channel IS NULL OR completion_channel IN ('ELECTRONIC','PAPER')")
    op.create_table(
        "consentimiento_paquetes_papel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consent_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(40), server_default="PRINTED", nullable=False),
        sa.Column("print_storage_key", sa.String(700), nullable=False),
        sa.Column("print_sha256", sa.String(64), nullable=False),
        sa.Column("print_byte_size", sa.BigInteger(), nullable=False),
        sa.Column("expected_page_count", sa.Integer(), nullable=False),
        sa.Column("uploaded_page_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("printed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("printed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paper_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paper_signed_recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("digitalization_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("digitization_finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_physical_retention_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_statements", postgresql.JSONB(), nullable=True),
        sa.Column("verification_version", sa.String(30), nullable=True),
        sa.Column("final_pdf_storage_key", sa.String(700), nullable=True),
        sa.Column("final_pdf_sha256", sa.String(64), nullable=True),
        sa.Column("final_pdf_size", sa.BigInteger(), nullable=True),
        sa.Column("final_page_count", sa.Integer(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consent_instance_id"], ["consentimiento_instancias.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["printed_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paper_signed_recorded_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["finalized_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("consent_instance_id", name="uq_consent_paper_packet_instance"),
        sa.CheckConstraint("status IN ('PRINTED','SIGNED_PENDING_DIGITIZATION','DIGITIZING','FINALIZED')", name="ck_consent_paper_packet_status"),
        sa.CheckConstraint("expected_page_count >= 1", name="ck_consent_paper_expected_pages"),
        sa.CheckConstraint("uploaded_page_count >= 0", name="ck_consent_paper_uploaded_pages"),
    )
    op.create_index("ix_consent_paper_company_instance", "consentimiento_paquetes_papel", ["empresa_id", "consent_instance_id"])
    op.create_index("ix_consent_paper_company_status", "consentimiento_paquetes_papel", ["empresa_id", "status"])
    op.create_table(
        "consentimiento_paginas_papel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paper_packet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(700), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("source_mime_type", sa.String(80), nullable=False),
        sa.Column("upload_group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_page_number", sa.Integer(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paper_packet_id"], ["consentimiento_paquetes_papel.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("paper_packet_id", "position", name="uq_consent_paper_page_position"),
    )
    op.create_index("ix_consent_paper_page_company_packet", "consentimiento_paginas_papel", ["empresa_id", "paper_packet_id"])


def downgrade() -> None:
    op.drop_index("ix_consent_paper_page_company_packet", table_name="consentimiento_paginas_papel")
    op.drop_table("consentimiento_paginas_papel")
    op.drop_index("ix_consent_paper_company_status", table_name="consentimiento_paquetes_papel")
    op.drop_index("ix_consent_paper_company_instance", table_name="consentimiento_paquetes_papel")
    op.drop_table("consentimiento_paquetes_papel")
    op.drop_constraint("ck_consent_instance_completion_channel", "consentimiento_instancias", type_="check")
    op.drop_column("consentimiento_instancias", "completion_channel")
    codes = [code for code, *_ in PERMISSIONS]
    op.execute(sa.text("DELETE FROM rol_permisos rp USING permisos p WHERE rp.permiso_id=p.id AND p.code=ANY(:codes)").bindparams(sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String()))))
