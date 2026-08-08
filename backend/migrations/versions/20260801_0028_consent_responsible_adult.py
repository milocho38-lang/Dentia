"""responsible adult signer snapshots for electronic consent

Revision ID: 20260801_0028
Revises: 20260801_0027
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260801_0028"
down_revision = "20260801_0027"
branch_labels = None
depends_on = None

RESPONSIBLE_PERMISSIONS = [
    ("consent.responsible.read", "Ver adulto responsable de consentimiento", "consent_instances", "Consultar el adulto responsable congelado en consentimientos."),
    ("consent.responsible.create", "Registrar adulto responsable de consentimiento", "consent_instances", "Registrar o seleccionar adulto responsable antes de sellar un consentimiento."),
    ("consent.responsible.update", "Actualizar adulto responsable de consentimiento", "consent_instances", "Actualizar adulto responsable mientras el consentimiento esté en borrador."),
]
ROLE_PERMISSIONS = {
    "ADMINISTRATOR": [code for code, *_ in RESPONSIBLE_PERMISSIONS],
    "DENTIST_ADMIN": [code for code, *_ in RESPONSIBLE_PERMISSIONS],
    "DENTIST": [code for code, *_ in RESPONSIBLE_PERMISSIONS],
    "SECRETARY": [code for code, *_ in RESPONSIBLE_PERMISSIONS],
}


def _seed_permissions() -> None:
    for code, name, module, description in RESPONSIBLE_PERMISSIONS:
        op.execute(sa.text("""
            INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), :code, :name, :module, :description, true, now(), now())
            ON CONFLICT (code) DO UPDATE
            SET nombre = EXCLUDED.nombre,
                modulo = EXCLUDED.modulo,
                descripcion = EXCLUDED.descripcion,
                is_active = true,
                updated_at = now()
        """).bindparams(code=code, name=name, module=module, description=description))
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        op.execute(sa.text("""
            INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
            SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
            FROM roles r
            JOIN permisos p ON p.code = ANY(:permission_codes)
            WHERE r.code = :role_code
              AND NOT EXISTS (
                SELECT 1 FROM rol_permisos rp
                WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
              )
        """).bindparams(
            sa.bindparam("role_code", value=role_code),
            sa.bindparam("permission_codes", value=permission_codes, type_=postgresql.ARRAY(sa.String())),
        ))


def upgrade() -> None:
    _seed_permissions()
    op.drop_constraint("ck_consent_library_signer_scope", "consentimiento_biblioteca_documentos", type_="check")
    op.create_check_constraint(
        "ck_consent_library_signer_scope",
        "consentimiento_biblioteca_documentos",
        "signer_scope IN ('ADULT_SELF','ADULT_OR_REPRESENTATIVE','REPRESENTATIVE_REQUIRED','NO_SIGNATURE_REQUIRED','ADMINISTRATIVE_RECORD','PATIENT_SELF','PATIENT_OR_RESPONSIBLE_ADULT','RESPONSIBLE_ADULT_REQUIRED','NO_PATIENT_SIGNATURE','SPECIAL_WORKFLOW')",
    )
    op.add_column("consentimiento_instancias", sa.Column("signer_policy", sa.String(length=40), nullable=False, server_default="PATIENT_SELF"))
    op.add_column("consentimiento_instancias", sa.Column("signer_actor_type", sa.String(length=40), nullable=False, server_default="PATIENT_SELF"))
    op.add_column("consentimiento_instancias", sa.Column("signer_full_name_snapshot", sa.String(length=250), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_document_type_snapshot", sa.String(length=30), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_document_number_snapshot", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_email_snapshot", sa.String(length=220), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_phone_snapshot", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_relationship_type_snapshot", sa.String(length=40), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_relationship_other_snapshot", sa.String(length=160), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("minor_participation_status", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("minor_participation_observation", sa.Text(), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_selected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("consentimiento_instancias", sa.Column("signer_selected_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_consent_instance_signer_selected_by", "consentimiento_instancias", "usuarios", ["signer_selected_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_consent_instance_signer_actor", "consentimiento_instancias", ["empresa_id", "signer_actor_type"])
    op.create_check_constraint("ck_consent_instance_signer_policy", "consentimiento_instancias", "signer_policy IN ('PATIENT_SELF','PATIENT_OR_RESPONSIBLE_ADULT','RESPONSIBLE_ADULT_REQUIRED','NO_PATIENT_SIGNATURE','SPECIAL_WORKFLOW')")
    op.create_check_constraint("ck_consent_instance_signer_actor", "consentimiento_instancias", "signer_actor_type IN ('PATIENT_SELF','RESPONSIBLE_ADULT')")
    op.create_check_constraint("ck_consent_instance_minor_participation", "consentimiento_instancias", "minor_participation_status IS NULL OR minor_participation_status IN ('INFORMED_AND_AGREED','INFORMED_NO_OBJECTION','COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION','NOT_APPLICABLE','OTHER')")

    op.create_table(
        "consentimiento_adultos_responsables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("consent_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consentimiento_instancias.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_responsible_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("responsables_paciente.id", ondelete="SET NULL"), nullable=True),
        sa.Column("full_name", sa.String(length=250), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("document_number", sa.String(length=80), nullable=False),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("relationship_other", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=220), nullable=False),
        sa.Column("phone", sa.String(length=80), nullable=False),
        sa.Column("identity_verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("identity_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verification_statement", sa.Text(), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("relationship_type IN ('MOTHER','FATHER','SIBLING','GRANDPARENT','AUNT_UNCLE','COUSIN','CAREGIVER','NEIGHBOR','LEGAL_REPRESENTATIVE','OTHER')", name="ck_consent_responsible_relationship"),
        sa.CheckConstraint("row_version >= 1", name="ck_consent_responsible_row_version_positive"),
        sa.UniqueConstraint("consent_instance_id", name="uq_consent_responsible_adult_instance"),
    )
    op.create_index("ix_consent_responsible_company_patient", "consentimiento_adultos_responsables", ["empresa_id", "paciente_id"])

    op.add_column("consentimiento_aceptaciones", sa.Column("responsible_adult_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_full_name_snapshot", sa.String(length=250), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_document_type_snapshot", sa.String(length=30), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_document_number_snapshot", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_relationship_type_snapshot", sa.String(length=40), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_relationship_other_snapshot", sa.String(length=160), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("signer_email_masked_snapshot", sa.String(length=220), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("minor_participation_status_snapshot", sa.String(length=80), nullable=True))
    op.add_column("consentimiento_aceptaciones", sa.Column("minor_participation_observation_snapshot", sa.Text(), nullable=True))
    op.create_foreign_key("fk_consent_acceptance_responsible_snapshot", "consentimiento_aceptaciones", "consentimiento_adultos_responsables", ["responsible_adult_snapshot_id"], ["id"], ondelete="RESTRICT")


def downgrade() -> None:
    op.drop_constraint("fk_consent_acceptance_responsible_snapshot", "consentimiento_aceptaciones", type_="foreignkey")
    for column in ["minor_participation_observation_snapshot", "minor_participation_status_snapshot", "signer_email_masked_snapshot", "signer_relationship_other_snapshot", "signer_relationship_type_snapshot", "signer_document_number_snapshot", "signer_document_type_snapshot", "signer_full_name_snapshot", "responsible_adult_snapshot_id"]:
        op.drop_column("consentimiento_aceptaciones", column)
    op.drop_index("ix_consent_responsible_company_patient", table_name="consentimiento_adultos_responsables")
    op.drop_table("consentimiento_adultos_responsables")
    op.drop_constraint("ck_consent_instance_minor_participation", "consentimiento_instancias", type_="check")
    op.drop_constraint("ck_consent_instance_signer_actor", "consentimiento_instancias", type_="check")
    op.drop_constraint("ck_consent_instance_signer_policy", "consentimiento_instancias", type_="check")
    op.drop_index("ix_consent_instance_signer_actor", table_name="consentimiento_instancias")
    op.drop_constraint("fk_consent_instance_signer_selected_by", "consentimiento_instancias", type_="foreignkey")
    for column in ["signer_selected_by", "signer_selected_at", "minor_participation_observation", "minor_participation_status", "signer_relationship_other_snapshot", "signer_relationship_type_snapshot", "signer_phone_snapshot", "signer_email_snapshot", "signer_document_number_snapshot", "signer_document_type_snapshot", "signer_full_name_snapshot", "signer_actor_type", "signer_policy"]:
        op.drop_column("consentimiento_instancias", column)
    op.drop_constraint("ck_consent_library_signer_scope", "consentimiento_biblioteca_documentos", type_="check")
    op.execute(sa.text("""
        UPDATE consentimiento_biblioteca_documentos
        SET signer_scope = CASE signer_scope
            WHEN 'PATIENT_SELF' THEN 'ADULT_SELF'
            WHEN 'PATIENT_OR_RESPONSIBLE_ADULT' THEN 'ADULT_OR_REPRESENTATIVE'
            WHEN 'RESPONSIBLE_ADULT_REQUIRED' THEN 'REPRESENTATIVE_REQUIRED'
            WHEN 'NO_PATIENT_SIGNATURE' THEN 'NO_SIGNATURE_REQUIRED'
            WHEN 'SPECIAL_WORKFLOW' THEN 'ADMINISTRATIVE_RECORD'
            ELSE signer_scope
        END
    """))
    op.create_check_constraint("ck_consent_library_signer_scope", "consentimiento_biblioteca_documentos", "signer_scope IN ('ADULT_SELF','ADULT_OR_REPRESENTATIVE','REPRESENTATIVE_REQUIRED','NO_SIGNATURE_REQUIRED','ADMINISTRATIVE_RECORD')")
