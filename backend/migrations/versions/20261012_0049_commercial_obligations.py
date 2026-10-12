"""commercial obligations, snapshots and rate periods

Revision ID: 20261012_0049
Revises: 20261012_0048
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261012_0049"
down_revision = "20261012_0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in (
        sa.Column("list_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("discount_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("currency_snapshot", sa.String(3), server_default="COP", nullable=False),
        sa.Column("monthly_fee_snapshot", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("credit_applied", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("credit_generated", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("payload_hash", sa.String(64), server_default="", nullable=False),
    ):
        op.add_column("platform_commercial_transfers", column)
    op.execute("""
      UPDATE platform_commercial_transfers t SET
        list_amount = a.monthly_fee * t.months_covered,
        discount_amount = GREATEST(a.monthly_fee * t.months_covered - t.agreed_amount, 0),
        currency_snapshot = a.currency,
        monthly_fee_snapshot = a.monthly_fee,
        credit_applied = 0,
        credit_generated = 0,
        payload_hash = md5(t.id::text) || md5(t.id::text || '-legacy')
      FROM platform_commercial_accounts a WHERE a.id = t.account_id
    """)
    # Rebuild the legacy credit ledger in verification order. 0048 did not store
    # credit attribution, so an underfunded VERIFIED row cannot safely be treated
    # as paid: return it to PENDING and preserve its received cash for review.
    op.execute("CREATE TEMP TABLE commercial_legacy_partial_review (transfer_id uuid PRIMARY KEY) ON COMMIT DROP")
    op.execute("""
      DO $$
      DECLARE
        row RECORD;
        current_account uuid := NULL;
        available numeric(14,2) := 0;
        applied numeric(14,2);
        generated numeric(14,2);
      BEGIN
        FOR row IN
          SELECT id, account_id, received_amount, agreed_amount
          FROM platform_commercial_transfers
          WHERE status = 'VERIFIED'
          ORDER BY account_id, verified_at NULLS LAST, created_at, id
        LOOP
          IF current_account IS DISTINCT FROM row.account_id THEN
            current_account := row.account_id;
            available := 0;
          END IF;
          IF row.received_amount + available >= row.agreed_amount THEN
            applied := LEAST(available, row.agreed_amount);
            generated := row.received_amount - (row.agreed_amount - applied);
            available := available - applied + generated;
            UPDATE platform_commercial_transfers
              SET credit_applied = applied, credit_generated = generated
              WHERE id = row.id;
          ELSE
            INSERT INTO commercial_legacy_partial_review (transfer_id) VALUES (row.id);
            UPDATE platform_commercial_transfers
              SET status = 'PENDING', verified_at = NULL, verified_by = NULL,
                  coverage_start = NULL, coverage_end = NULL,
                  credit_applied = 0, credit_generated = 0
              WHERE id = row.id;
          END IF;
        END LOOP;
      END $$
    """)
    op.create_check_constraint("commercial_transfer_received_positive", "platform_commercial_transfers", "received_amount > 0")
    op.create_check_constraint("commercial_transfer_agreed_nonnegative", "platform_commercial_transfers", "agreed_amount >= 0")
    op.create_check_constraint("commercial_transfer_discount_nonnegative", "platform_commercial_transfers", "discount_amount >= 0")
    op.create_check_constraint("commercial_transfer_months_range", "platform_commercial_transfers", "months_covered BETWEEN 0 AND 120")
    op.create_check_constraint("commercial_transfer_credit_nonnegative", "platform_commercial_transfers", "credit_applied >= 0 AND credit_generated >= 0")
    op.create_check_constraint("commercial_transfer_status", "platform_commercial_transfers", "status IN ('PENDING','VERIFIED','REVERSED')")
    op.create_table(
        "platform_commercial_obligations",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_index", sa.Integer(), nullable=False), sa.Column("period_start", sa.Date(), nullable=False), sa.Column("period_end", sa.Date(), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("list_amount", sa.Numeric(14,2), nullable=False), sa.Column("discount_amount", sa.Numeric(14,2), nullable=False), sa.Column("amount_due", sa.Numeric(14,2), nullable=False),
        sa.Column("status", sa.String(20), server_default="PAID", nullable=False), sa.Column("voided_at", sa.DateTime(timezone=True)), sa.Column("void_reason", sa.Text()), sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"],["empresas.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["account_id"],["platform_commercial_accounts.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["transfer_id"],["platform_commercial_transfers.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by"],["usuarios.id"],ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("transfer_id","period_index",name="uq_commercial_obligation_transfer_period"), sa.CheckConstraint("period_index > 0",name="commercial_obligation_period_positive"), sa.CheckConstraint("list_amount >= 0 AND discount_amount >= 0 AND amount_due >= 0",name="commercial_obligation_amounts_nonnegative"),
    )
    op.create_index("ix_platform_commercial_obligations_company_id","platform_commercial_obligations",["company_id"])
    op.create_table(
        "platform_commercial_reconciliations",
        sa.Column("company_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("account_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("trigger_transfer_id",postgresql.UUID(as_uuid=True)), sa.Column("action",sa.String(40),nullable=False), sa.Column("coverage_through",sa.Date()), sa.Column("credit_balance",sa.Numeric(14,2),nullable=False), sa.Column("pending_balance",sa.Numeric(14,2),nullable=False), sa.Column("detail",sa.Text()), sa.Column("created_by",postgresql.UUID(as_uuid=True)), sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["company_id"],["empresas.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["account_id"],["platform_commercial_accounts.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["trigger_transfer_id"],["platform_commercial_transfers.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by"],["usuarios.id"],ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_commercial_reconciliations_company_id","platform_commercial_reconciliations",["company_id"])
    op.execute("""
      INSERT INTO platform_commercial_reconciliations
        (id, company_id, account_id, trigger_transfer_id, action,
         coverage_through, credit_balance, pending_balance, detail,
         created_by, created_at, updated_at)
      SELECT gen_random_uuid(), t.company_id, t.account_id, t.id,
        'LEGACY_PARTIAL_REVIEW', a.coverage_through, 0,
        GREATEST(t.agreed_amount - t.received_amount, 0),
        'Pago heredado insuficiente: importe recibido preservado y cobertura pendiente de verificación.',
        NULL, now(), now()
      FROM commercial_legacy_partial_review p
      JOIN platform_commercial_transfers t ON t.id = p.transfer_id
      JOIN platform_commercial_accounts a ON a.id = t.account_id
    """)
    op.create_table(
        "platform_commercial_rates",
        sa.Column("company_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("account_id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("effective_period_index",sa.Integer(),nullable=False), sa.Column("monthly_fee",sa.Numeric(14,2),nullable=False), sa.Column("currency",sa.String(3),nullable=False), sa.Column("created_by",postgresql.UUID(as_uuid=True)), sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False), sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False), sa.Column("is_active",sa.Boolean(),server_default=sa.true(),nullable=False),
        sa.ForeignKeyConstraint(["company_id"],["empresas.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["account_id"],["platform_commercial_accounts.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by"],["usuarios.id"],ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("account_id","effective_period_index",name="uq_commercial_rate_effective_period"), sa.CheckConstraint("effective_period_index > 0 AND monthly_fee >= 0",name="commercial_rate_valid"),
    )
    op.create_index("ix_platform_commercial_rates_company_id","platform_commercial_rates",["company_id"])
    op.execute("INSERT INTO platform_commercial_rates (id,company_id,account_id,effective_period_index,monthly_fee,currency,created_by,is_active,created_at,updated_at) SELECT gen_random_uuid(),company_id,id,1,monthly_fee,currency,created_by,true,now(),now() FROM platform_commercial_accounts")
    op.execute("""
      WITH ordered AS (
        SELECT t.*, COALESCE(SUM(months_covered) OVER (PARTITION BY account_id ORDER BY verified_at,created_at ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0)::int prior
        FROM platform_commercial_transfers t WHERE status='VERIFIED' AND months_covered>0
      )
      INSERT INTO platform_commercial_obligations (id,company_id,account_id,transfer_id,period_index,period_start,period_end,currency,list_amount,discount_amount,amount_due,status,created_by,is_active,created_at,updated_at)
      SELECT gen_random_uuid(),o.company_id,o.account_id,o.id,o.prior+g,
        (a.service_start_date + make_interval(months => o.prior+g-1))::date,
        (a.service_start_date + make_interval(months => o.prior+g))::date - 1,
        o.currency_snapshot,o.monthly_fee_snapshot,o.discount_amount/o.months_covered,o.agreed_amount/o.months_covered,'PAID',o.verified_by,true,now(),now()
      FROM ordered o JOIN platform_commercial_accounts a ON a.id=o.account_id CROSS JOIN LATERAL generate_series(1,o.months_covered) g
      WHERE a.service_start_date IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_table("platform_commercial_rates"); op.drop_table("platform_commercial_reconciliations"); op.drop_table("platform_commercial_obligations")
    for name in ("commercial_transfer_status","commercial_transfer_credit_nonnegative","commercial_transfer_months_range","commercial_transfer_discount_nonnegative","commercial_transfer_agreed_nonnegative","commercial_transfer_received_positive"):
        op.drop_constraint(name,"platform_commercial_transfers",type_="check")
    for name in ("payload_hash","credit_generated","credit_applied","monthly_fee_snapshot","currency_snapshot","discount_amount","list_amount"):
        op.drop_column("platform_commercial_transfers",name)
