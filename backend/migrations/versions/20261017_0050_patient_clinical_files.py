"""add private patient clinical files

Revision ID: 20261017_0050
Revises: 20261012_0049
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261017_0050"
down_revision = "20261012_0049"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("clinical_files.view", "Ver archivos clínicos", "Consultar y descargar archivos clínicos privados."),
    ("clinical_files.create", "Cargar archivos clínicos", "Cargar radiografías, exámenes y documentos de pacientes."),
    ("clinical_files.manage", "Gestionar archivos clínicos", "Desactivar archivos clínicos conservando trazabilidad."),
)


def upgrade():
    op.create_table(
        "archivos_clinicos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tipo_archivo", sa.String(30), nullable=False),
        sa.Column("categoria", sa.String(30), nullable=False),
        sa.Column("nombre_archivo", sa.String(300), nullable=False),
        sa.Column("ruta_archivo", sa.String(600), nullable=False, unique=True),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_carga", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cargado_por_usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cargado_por_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deactivated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.CheckConstraint("tipo_archivo IN ('RADIOGRAPH','EXAM','PHOTOGRAPH','DOCUMENT','OTHER')", name="ck_archivos_clinicos_tipo"),
        sa.CheckConstraint("categoria IN ('INITIAL','EVOLUTION','FINAL','LEGAL','LABORATORY','GENERAL')", name="ck_archivos_clinicos_categoria"),
        sa.CheckConstraint("tamano_bytes > 0", name="ck_archivos_clinicos_size"),
        sa.UniqueConstraint("empresa_id", "idempotency_key", name="uq_archivos_clinicos_empresa_idempotency"),
    )
    op.create_index("ix_archivos_clinicos_empresa_paciente", "archivos_clinicos", ["empresa_id", "paciente_id"])
    op.create_index("ix_archivos_clinicos_empresa_tipo", "archivos_clinicos", ["empresa_id", "tipo_archivo"])
    op.execute("""
      CREATE FUNCTION validate_archivo_clinico_scope() RETURNS trigger AS $$
      BEGIN
        IF NOT EXISTS (SELECT 1 FROM pacientes p WHERE p.id=NEW.paciente_id AND p.empresa_id=NEW.empresa_id) THEN RAISE EXCEPTION 'clinical file patient scope mismatch'; END IF;
        IF NEW.tratamiento_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM tratamientos t WHERE t.id=NEW.tratamiento_id AND t.empresa_id=NEW.empresa_id AND t.paciente_id=NEW.paciente_id) THEN RAISE EXCEPTION 'clinical file treatment scope mismatch'; END IF;
        IF NEW.cita_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM citas c WHERE c.id=NEW.cita_id AND c.empresa_id=NEW.empresa_id AND c.paciente_id=NEW.paciente_id) THEN RAISE EXCEPTION 'clinical file appointment scope mismatch'; END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql;
      CREATE TRIGGER trg_archivos_clinicos_scope BEFORE INSERT OR UPDATE ON archivos_clinicos FOR EACH ROW EXECUTE FUNCTION validate_archivo_clinico_scope();
    """)
    for code, name, description in PERMISSIONS:
        op.execute(sa.text("INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at) VALUES (gen_random_uuid(), :code, :name, 'clinical_files', :description, true, now(), now()) ON CONFLICT (code) DO NOTHING").bindparams(code=code, name=name, description=description))
        role_codes = ("ADMINISTRATOR", "DENTIST_ADMIN", "DENTIST") if code != "clinical_files.manage" else ("ADMINISTRATOR", "DENTIST_ADMIN")
        op.execute(sa.text("INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at) SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now() FROM roles r JOIN permisos p ON p.code=:code WHERE r.code = ANY(:roles) AND NOT EXISTS (SELECT 1 FROM rol_permisos rp WHERE rp.rol_id=r.id AND rp.permiso_id=p.id)").bindparams(code=code, roles=list(role_codes)))


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_archivos_clinicos_scope ON archivos_clinicos")
    op.execute("DROP FUNCTION IF EXISTS validate_archivo_clinico_scope()")
    op.drop_index("ix_archivos_clinicos_empresa_tipo", table_name="archivos_clinicos")
    op.drop_index("ix_archivos_clinicos_empresa_paciente", table_name="archivos_clinicos")
    op.drop_table("archivos_clinicos")
    codes = tuple(code for code, _, _ in PERMISSIONS)
    op.execute(sa.text("DELETE FROM rol_permisos WHERE permiso_id IN (SELECT id FROM permisos WHERE code = ANY(:codes))").bindparams(codes=list(codes)))
    op.execute(sa.text("DELETE FROM permisos WHERE code = ANY(:codes)").bindparams(codes=list(codes)))
