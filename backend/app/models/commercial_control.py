from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CommercialAccount(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "platform_commercial_accounts"
    __table_args__ = (UniqueConstraint("company_id", name="uq_commercial_account_company"),)

    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False, default="STANDARD")
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    service_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    coverage_through: Mapped[date | None] = mapped_column(Date, nullable=True)
    credit_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    agreement: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    next_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class CommercialTransfer(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "platform_commercial_transfers"
    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_key", name="uq_commercial_transfer_idempotency"),
        CheckConstraint("received_amount > 0", name="commercial_transfer_received_positive"),
        CheckConstraint("agreed_amount >= 0", name="commercial_transfer_agreed_nonnegative"),
        CheckConstraint("discount_amount >= 0", name="commercial_transfer_discount_nonnegative"),
        CheckConstraint("months_covered BETWEEN 0 AND 120", name="commercial_transfer_months_range"),
        CheckConstraint("credit_applied >= 0 AND credit_generated >= 0", name="commercial_transfer_credit_nonnegative"),
        CheckConstraint("status IN ('PENDING', 'VERIFIED', 'REVERSED')", name="commercial_transfer_status"),
    )

    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_accounts.id", ondelete="RESTRICT"), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    agreed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    list_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency_snapshot: Mapped[str] = mapped_column(String(3), nullable=False)
    monthly_fee_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    credit_applied: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    credit_generated: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    months_covered: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    receipt_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    coverage_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    coverage_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class CommercialObligation(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "platform_commercial_obligations"
    __table_args__ = (
        UniqueConstraint("transfer_id", "period_index", name="uq_commercial_obligation_transfer_period"),
        CheckConstraint("period_index > 0", name="commercial_obligation_period_positive"),
        CheckConstraint("list_amount >= 0 AND discount_amount >= 0 AND amount_due >= 0", name="commercial_obligation_amounts_nonnegative"),
    )
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_accounts.id", ondelete="RESTRICT"), nullable=False)
    transfer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_transfers.id", ondelete="RESTRICT"), nullable=False)
    period_index: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    list_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PAID")
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class CommercialReconciliation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_commercial_reconciliations"
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_accounts.id", ondelete="RESTRICT"), nullable=False)
    trigger_transfer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_transfers.id", ondelete="RESTRICT"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    coverage_through: Mapped[date | None] = mapped_column(Date, nullable=True)
    credit_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    pending_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
