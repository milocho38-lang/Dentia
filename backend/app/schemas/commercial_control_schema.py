from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class CommercialAccountUpdate(BaseModel):
    plan_type: str
    monthly_fee: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    service_start_date: date | None = None
    last_contact_at: datetime | None = None
    agreement: str | None = Field(default=None, max_length=4000)
    owner: str | None = Field(default=None, max_length=200)
    next_contact_date: date | None = None

    @field_validator("plan_type")
    @classmethod
    def valid_plan(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"STANDARD", "FOUNDER", "FREE"}:
            raise ValueError("Tipo de tarifa no válido.")
        return value

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.isalpha():
            raise ValueError("Moneda no válida.")
        return value

    @model_validator(mode="after")
    def free_has_zero_fee(self):
        if self.plan_type == "FREE" and self.monthly_fee != 0:
            raise ValueError("Una clínica gratuita debe tener tarifa cero.")
        if self.plan_type != "FREE" and self.monthly_fee <= 0:
            raise ValueError("La tarifa debe ser mayor que cero.")
        return self


class TransferCreate(BaseModel):
    transfer_date: date
    received_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    agreed_amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    months_covered: int = Field(ge=0, le=120)
    reference: str | None = Field(default=None, max_length=200)
    receipt_reference: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def has_reference_and_allocation(self):
        if not (self.reference and self.reference.strip()) and not (self.receipt_reference and self.receipt_reference.strip()):
            raise ValueError("Registra referencia o comprobante.")
        if self.transfer_date > date.today():
            raise ValueError("La fecha de transferencia no puede ser futura.")
        if self.months_covered == 0 and (self.agreed_amount != 0 or self.discount_amount != 0):
            raise ValueError("Un abono sin meses no puede declarar importe acordado ni descuento.")
        if self.months_covered > 0 and self.agreed_amount <= 0:
            raise ValueError("Los meses cubiertos requieren un importe acordado positivo.")
        return self


class ReversalRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class TransferSummary(BaseModel):
    id: UUID
    transfer_date: date
    received_amount: Decimal
    agreed_amount: Decimal
    list_amount: Decimal
    discount_amount: Decimal
    currency_snapshot: str
    monthly_fee_snapshot: Decimal
    credit_applied: Decimal
    credit_generated: Decimal
    months_covered: int
    reference: str | None
    receipt_reference: str | None
    status: str
    coverage_start: date | None
    coverage_end: date | None
    created_at: datetime
    verified_at: datetime | None
    reversed_at: datetime | None
    reversal_reason: str | None


class CommercialAccountSummary(BaseModel):
    company_id: UUID
    company_name: str
    plan_type: str
    monthly_fee: Decimal
    currency: str
    service_start_date: date | None
    last_verified_payment_date: date | None
    total_months_covered: int
    coverage_through: date | None
    next_due_date: date | None
    pending_balance: Decimal
    credit_balance: Decimal
    last_contact_at: datetime | None
    agreement: str | None
    owner: str | None
    next_contact_date: date | None
    transfers: list[TransferSummary] = Field(default_factory=list)


class CommercialAccountList(BaseModel):
    items: list[CommercialAccountSummary]
