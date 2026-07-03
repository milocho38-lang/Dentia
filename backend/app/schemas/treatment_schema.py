from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


TREATMENT_STATUSES = {
    "Borrador",
    "Presupuestado",
    "Aprobado",
    "En ejecución",
    "Pausado",
    "Finalizado",
    "Cancelado",
}
PROCEDURE_STATUSES = {
    "Pendiente",
    "Agendado",
    "En proceso",
    "Realizado",
    "Cancelado",
}
BUDGET_STATUSES = {
    "Borrador",
    "Pendiente de aprobación",
    "Aprobado",
    "Rechazado",
    "En ejecución",
    "Finalizado",
}
PAYMENT_METHODS = {"Efectivo", "Transferencia", "Tarjeta", "Otro"}


class TreatmentCreateRequest(BaseModel):
    patient_id: UUID
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    specialty: str | None = Field(default=None, max_length=120)
    responsible_dentist_id: UUID | None = None
    main_site_id: UUID | None = None
    start_date: date | None = None
    observations: str | None = None

    @field_validator("name", "description", "specialty", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class TreatmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    specialty: str | None = Field(default=None, max_length=120)
    responsible_dentist_id: UUID | None = None
    main_site_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    observations: str | None = None

    @field_validator("name", "description", "specialty", "observations")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class StatusReasonRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class TreatmentSummaryResponse(BaseModel):
    gross_value: Decimal
    discount_value: Decimal
    final_value: Decimal
    paid_value: Decimal
    balance: Decimal
    procedures_total: int
    procedures_done: int


class TreatmentListItemResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    name: str
    status: str
    responsible_dentist_id: UUID | None
    responsible_dentist_name: str | None
    main_site_id: UUID | None
    main_site_name: str | None
    final_value: Decimal
    paid_value: Decimal
    balance: Decimal
    updated_at: datetime


class TreatmentListResponse(BaseModel):
    items: list[TreatmentListItemResponse]
    total: int


class TreatmentResponse(TreatmentListItemResponse):
    description: str | None
    specialty: str | None
    start_date: date | None
    end_date: date | None
    observations: str | None
    created_at: datetime
    summary: TreatmentSummaryResponse


class ProcedureCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    unit_value: Decimal = Field(default=Decimal("0"), ge=0)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    status: str = "Pendiente"
    estimated_date: date | None = None
    observations: str | None = None
    requires_tooth: bool = False
    tooth: str | None = Field(default=None, max_length=30)

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in PROCEDURE_STATUSES:
            raise ValueError("Estado de procedimiento no válido.")
        return value

    @field_validator("name", "category", "observations", "tooth")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ProcedureUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    unit_value: Decimal | None = Field(default=None, ge=0)
    quantity: Decimal | None = Field(default=None, gt=0)
    status: str | None = None
    estimated_date: date | None = None
    observations: str | None = None
    requires_tooth: bool | None = None
    tooth: str | None = Field(default=None, max_length=30)

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str | None) -> str | None:
        if value is not None and value not in PROCEDURE_STATUSES:
            raise ValueError("Estado de procedimiento no válido.")
        return value

    @field_validator("name", "category", "observations", "tooth")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class LinkProcedureAppointmentRequest(BaseModel):
    appointment_id: UUID


class ProcedureResponse(BaseModel):
    id: UUID
    treatment_id: UUID
    patient_id: UUID
    name: str
    category: str | None
    dentist_id: UUID | None
    dentist_name: str | None
    site_id: UUID | None
    site_name: str | None
    appointment_id: UUID | None
    unit_value: Decimal
    quantity: Decimal
    total_value: Decimal
    status: str
    estimated_date: date | None
    performed_at: datetime | None
    observations: str | None
    requires_tooth: bool
    tooth: str | None


class BudgetCreateRequest(BaseModel):
    discount_type: str | None = Field(default=None, pattern="^(porcentaje|valor)$")
    discount_value: Decimal = Field(default=Decimal("0"), ge=0)
    observations: str | None = None
    expires_on: date | None = None

    @field_validator("observations")
    @classmethod
    def strip_observations(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class BudgetUpdateRequest(BudgetCreateRequest):
    pass


class BudgetDetailResponse(BaseModel):
    id: UUID
    procedure_id: UUID | None
    name: str
    category: str | None
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal
    order: int
    observations: str | None


class BudgetResponse(BaseModel):
    id: UUID
    patient_id: UUID
    treatment_id: UUID
    number: str | None
    version: int
    status: str
    gross_value: Decimal
    discount_type: str | None
    discount_value: Decimal
    discount_calculated_value: Decimal
    final_value: Decimal
    observations: str | None
    issued_at: datetime
    expires_on: date | None
    approved_at: datetime | None
    rejected_at: datetime | None
    details: list[BudgetDetailResponse] = []


class BudgetListResponse(BaseModel):
    items: list[BudgetResponse]
    total: int


class PaymentCreateRequest(BaseModel):
    site_id: UUID
    dentist_id: UUID | None = None
    paid_at: datetime
    value: Decimal = Field(gt=0)
    payment_method: str
    reference: str | None = Field(default=None, max_length=120)
    observation: str | None = None

    @field_validator("payment_method")
    @classmethod
    def valid_method(cls, value: str) -> str:
        if value not in PAYMENT_METHODS:
            raise ValueError("Medio de pago no válido.")
        return value

    @field_validator("reference", "observation")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_timezone(self):
        if self.paid_at.tzinfo is None:
            raise ValueError("La fecha de pago debe incluir zona horaria.")
        return self


class PaymentReverseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class PaymentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    treatment_id: UUID
    treatment_name: str
    budget_id: UUID | None
    site_id: UUID
    site_name: str
    dentist_id: UUID | None
    dentist_name: str | None
    paid_at: datetime
    value: Decimal
    payment_method: str
    reference: str | None
    observation: str | None
    status: str
    reversed_at: datetime | None
    reversal_reason: str | None


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int


class FinanceDashboardResponse(BaseModel):
    income_today: Decimal
    income_month: Decimal
    income_year: Decimal
    receivables_total: Decimal
    active_treatments: int
    average_ticket: Decimal


class FinanceBreakdownItem(BaseModel):
    id: UUID | None = None
    name: str
    value: Decimal


class FinanceBreakdownResponse(BaseModel):
    items: list[FinanceBreakdownItem]


class PatientBalanceItem(BaseModel):
    patient_id: UUID
    patient_name: str
    balance: Decimal


class PatientBalancesResponse(BaseModel):
    items: list[PatientBalanceItem]
