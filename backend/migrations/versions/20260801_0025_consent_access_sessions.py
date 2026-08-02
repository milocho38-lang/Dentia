"""add secure consent access sessions, otp and clarifications

Revision ID: 20260801_0025
Revises: 20260801_0024
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260801_0025"
down_revision = "20260801_0024"
branch_labels = None
depends_on = None

PERMISSIONS = [
    ("consent.access.issue", "Emitir acceso de consentimiento", "consent_access", "Emitir un enlace seguro para una instancia revisada."),
    ("consent.access.read", "Consultar acceso de consentimiento", "consent_access", "Consultar estado del canal de acceso del paciente."),
    ("consent.access.revoke", "Revocar acceso de consentimiento", "consent_access", "Revocar enlaces y sesiones públicas activas."),
    ("consent.access.reissue", "Reemitir acceso de consentimiento", "consent_access", "Reemplazar de forma segura un enlace anterior."),
    ("consent.access.view_audit", "Auditar acceso de consentimiento", "consent_access", "Consultar trazabilidad técnica del canal."),
    ("consent.clarification.read", "Consultar aclaraciones", "consent_access", "Consultar solicitudes de aclaración del paciente."),
    ("consent.clarification.manage", "Gestionar aclaraciones", "consent_access", "Marcar solicitudes de aclaración como atendidas."),
]
ROLE_PERMISSIONS = {
    "ADMINISTRATOR": [p[0] for p in PERMISSIONS[:5]],
    "DENTIST_ADMIN": [p[0] for p in PERMISSIONS],
    "DENTIST": [p[0] for p in PERMISSIONS],
    "SECRETARY": ["consent.access.issue", "consent.access.read", "consent.access.revoke", "consent.access.reissue"],
}

def _seed_permissions():
    for code, name, module, description in PERMISSIONS:
        op.execute(sa.text("""INSERT INTO permisos (id,code,nombre,modulo,descripcion,is_active,created_at,updated_at)
        VALUES (gen_random_uuid(),:code,:name,:module,:description,true,now(),now())
        ON CONFLICT (code) DO UPDATE SET nombre=EXCLUDED.nombre,modulo=EXCLUDED.modulo,descripcion=EXCLUDED.descripcion,is_active=true,updated_at=now()""").bindparams(code=code,name=name,module=module,description=description))
    for role, codes in ROLE_PERMISSIONS.items():
        op.execute(sa.text("""INSERT INTO rol_permisos (id,empresa_id,rol_id,permiso_id,is_active,created_by,created_at,updated_at)
        SELECT gen_random_uuid(),r.empresa_id,r.id,p.id,true,r.created_by,now(),now() FROM roles r JOIN permisos p ON p.code=ANY(:codes)
        WHERE r.code=:role AND NOT EXISTS (SELECT 1 FROM rol_permisos rp WHERE rp.rol_id=r.id AND rp.permiso_id=p.id)""").bindparams(sa.bindparam("role",value=role),sa.bindparam("codes",value=codes,type_=postgresql.ARRAY(sa.String()))))

def upgrade():
    _seed_permissions()
    op.drop_constraint("ck_consent_instance_status", "consentimiento_instancias", type_="check")
    op.create_check_constraint("ck_consent_instance_status", "consentimiento_instancias", "status IN ('DRAFT','READY_FOR_REVIEW','PENDING_SIGNATURE','VOIDED')")
    op.create_table("consentimiento_sesiones_acceso",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True), sa.Column("empresa_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("sede_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("consent_instance_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("status",sa.String(30),server_default="ISSUED",nullable=False), sa.Column("public_token_hash",sa.String(64),nullable=False), sa.Column("public_token_prefix",sa.String(12),nullable=False),
        sa.Column("issued_at",sa.DateTime(timezone=True),nullable=False), sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False), sa.Column("revoked_at",sa.DateTime(timezone=True)), sa.Column("revoked_by",postgresql.UUID(as_uuid=True)), sa.Column("revoke_reason",sa.Text()),
        sa.Column("verified_at",sa.DateTime(timezone=True)), sa.Column("viewed_at",sa.DateTime(timezone=True)), sa.Column("clarification_requested_at",sa.DateTime(timezone=True)), sa.Column("last_activity_at",sa.DateTime(timezone=True),nullable=False), sa.Column("open_window_started_at",sa.DateTime(timezone=True)), sa.Column("open_count",sa.Integer(),server_default="0",nullable=False),
        sa.Column("channel",sa.String(20),server_default="EMAIL",nullable=False), sa.Column("recipient_masked",sa.String(220),nullable=False), sa.Column("created_by",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("row_version",sa.Integer(),server_default="1",nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.CheckConstraint("status IN ('ISSUED','OTP_PENDING','VERIFIED','VIEWED','CLARIFICATION_REQUESTED','REVOKED','EXPIRED')",name="ck_consent_access_status"), sa.CheckConstraint("row_version >= 1",name="ck_consent_access_row_version"), sa.CheckConstraint("open_count >= 0",name="ck_consent_access_open_count"),
        sa.ForeignKeyConstraint(["empresa_id"],["empresas.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["sede_id"],["sedes.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["consent_instance_id"],["consentimiento_instancias.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["revoked_by"],["usuarios.id"],ondelete="SET NULL"), sa.ForeignKeyConstraint(["created_by"],["usuarios.id"],ondelete="RESTRICT"))
    op.create_index("ix_consent_access_company_instance","consentimiento_sesiones_acceso",["empresa_id","consent_instance_id"])
    op.create_index("ix_consent_access_token_hash","consentimiento_sesiones_acceso",["public_token_hash"],unique=True)
    op.create_table("consentimiento_otp_desafios",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True), sa.Column("empresa_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("access_session_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("otp_hash",sa.String(64),nullable=False), sa.Column("status",sa.String(30),server_default="PENDING",nullable=False), sa.Column("channel",sa.String(20),server_default="EMAIL",nullable=False), sa.Column("recipient_masked",sa.String(220),nullable=False), sa.Column("recipient_hash",sa.String(64),nullable=False), sa.Column("request_ip_hash",sa.String(64)), sa.Column("issued_at",sa.DateTime(timezone=True),nullable=False), sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False), sa.Column("verified_at",sa.DateTime(timezone=True)), sa.Column("failed_attempts",sa.Integer(),server_default="0",nullable=False), sa.Column("max_attempts",sa.Integer(),server_default="5",nullable=False), sa.Column("resend_count",sa.Integer(),server_default="0",nullable=False), sa.Column("last_sent_at",sa.DateTime(timezone=True)), sa.Column("blocked_until",sa.DateTime(timezone=True)), sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.CheckConstraint("status IN ('PENDING','VERIFIED','INVALIDATED','BLOCKED','DELIVERY_FAILED','EXPIRED')",name="ck_consent_otp_status"),sa.CheckConstraint("failed_attempts >= 0 AND resend_count >= 0",name="ck_consent_otp_counts"),sa.ForeignKeyConstraint(["empresa_id"],["empresas.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["access_session_id"],["consentimiento_sesiones_acceso.id"],ondelete="RESTRICT"))
    op.create_index("ix_consent_otp_access_status","consentimiento_otp_desafios",["access_session_id","status"])
    op.create_index("ix_consent_otp_rate_ip","consentimiento_otp_desafios",["request_ip_hash","issued_at"])
    op.create_index("ix_consent_otp_rate_recipient","consentimiento_otp_desafios",["recipient_hash","issued_at"])
    op.create_table("consentimiento_sesiones_publicas",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("empresa_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("access_session_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("session_token_hash",sa.String(64),nullable=False),sa.Column("status",sa.String(20),server_default="ACTIVE",nullable=False),sa.Column("issued_at",sa.DateTime(timezone=True),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("last_activity_at",sa.DateTime(timezone=True),nullable=False),sa.Column("revoked_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')",name="ck_consent_public_session_status"),sa.ForeignKeyConstraint(["empresa_id"],["empresas.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["access_session_id"],["consentimiento_sesiones_acceso.id"],ondelete="RESTRICT"))
    op.create_index("ix_consent_public_session_hash","consentimiento_sesiones_publicas",["session_token_hash"],unique=True)
    op.create_table("consentimiento_solicitudes_aclaracion",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("empresa_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("consent_instance_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("access_session_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("professional_user_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("status",sa.String(20),server_default="OPEN",nullable=False),sa.Column("message",sa.String(500)),sa.Column("requested_at",sa.DateTime(timezone=True),nullable=False),sa.Column("resolved_at",sa.DateTime(timezone=True)),sa.Column("resolved_by",postgresql.UUID(as_uuid=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.CheckConstraint("status IN ('OPEN','RESOLVED')",name="ck_consent_clarification_status"),sa.ForeignKeyConstraint(["empresa_id"],["empresas.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["consent_instance_id"],["consentimiento_instancias.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["access_session_id"],["consentimiento_sesiones_acceso.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["professional_user_id"],["usuarios.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["resolved_by"],["usuarios.id"],ondelete="SET NULL"))
    op.create_index("ix_consent_clarification_company_instance","consentimiento_solicitudes_aclaracion",["empresa_id","consent_instance_id"])

def downgrade():
    op.drop_index("ix_consent_clarification_company_instance",table_name="consentimiento_solicitudes_aclaracion"); op.drop_table("consentimiento_solicitudes_aclaracion")
    op.drop_index("ix_consent_public_session_hash",table_name="consentimiento_sesiones_publicas"); op.drop_table("consentimiento_sesiones_publicas")
    op.drop_index("ix_consent_otp_rate_recipient",table_name="consentimiento_otp_desafios"); op.drop_index("ix_consent_otp_rate_ip",table_name="consentimiento_otp_desafios"); op.drop_index("ix_consent_otp_access_status",table_name="consentimiento_otp_desafios"); op.drop_table("consentimiento_otp_desafios")
    op.drop_index("ix_consent_access_token_hash",table_name="consentimiento_sesiones_acceso"); op.drop_index("ix_consent_access_company_instance",table_name="consentimiento_sesiones_acceso"); op.drop_table("consentimiento_sesiones_acceso")
    op.drop_constraint("ck_consent_instance_status","consentimiento_instancias",type_="check"); op.create_check_constraint("ck_consent_instance_status","consentimiento_instancias","status IN ('DRAFT','READY_FOR_REVIEW','VOIDED')")
