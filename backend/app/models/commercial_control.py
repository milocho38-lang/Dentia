from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
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
    __table_args__ = (UniqueConstraint("company_id", "idempotency_key", name="uq_commercial_transfer_idempotency"),)

    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("platform_commercial_accounts.id", ondelete="RESTRICT"), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    agreed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    months_covered: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    receipt_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    coverage_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    coverage_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
