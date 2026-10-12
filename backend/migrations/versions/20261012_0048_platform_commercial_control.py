"""platform commercial control

Revision ID: 20261012_0048
Revises: 20261006_0047
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261012_0048"
down_revision: str | Sequence[str] | None = "20261006_0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_commercial_accounts",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_type", sa.String(20), server_default="STANDARD", nullable=False),
        sa.Column("monthly_fee", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(3), server_default="COP", nullable=False),
        sa.Column("service_start_date", sa.Date(), nullable=True),
        sa.Column("coverage_through", sa.Date(), nullable=True),
        sa.Column("credit_balance", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agreement", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(200), nullable=True),
        sa.Column("next_contact_date", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="uq_commercial_account_company"),
    )
    op.create_index("ix_platform_commercial_accounts_company_id", "platform_commercial_accounts", ["company_id"])
    op.create_table(
        "platform_commercial_transfers",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("received_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("agreed_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("months_covered", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(200), nullable=True),
        sa.Column("receipt_reference", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("coverage_start", sa.Date(), nullable=True),
        sa.Column("coverage_end", sa.Date(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reversal_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["account_id"], ["platform_commercial_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reversed_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "idempotency_key", name="uq_commercial_transfer_idempotency"),
    )
    op.create_index("ix_platform_commercial_transfers_company_id", "platform_commercial_transfers", ["company_id"])
    op.execute("""
      INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
      VALUES
      (gen_random_uuid(), 'platform.commercial.view', 'Ver control comercial', 'platform', 'Consultar cartera comercial de clínicas.', true, now(), now()),
      (gen_random_uuid(), 'platform.commercial.manage', 'Gestionar control comercial', 'platform', 'Registrar y verificar movimientos comerciales.', true, now(), now())
      ON CONFLICT (code) DO NOTHING
    """)
    op.execute("""
      INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
      SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
      FROM roles r CROSS JOIN permisos p
      WHERE r.code = 'PLATFORM_ADMIN'
        AND p.code IN ('platform.commercial.view', 'platform.commercial.manage')
        AND NOT EXISTS (
          SELECT 1 FROM rol_permisos rp WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
        )
    """)


def downgrade() -> None:
    op.drop_table("platform_commercial_transfers")
    op.drop_table("platform_commercial_accounts")
    op.execute("DELETE FROM rol_permisos WHERE permiso_id IN (SELECT id FROM permisos WHERE code IN ('platform.commercial.view', 'platform.commercial.manage'))")
    op.execute("DELETE FROM permisos WHERE code IN ('platform.commercial.view', 'platform.commercial.manage')")
