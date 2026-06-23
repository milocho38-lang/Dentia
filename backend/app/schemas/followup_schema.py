from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

BOGOTA_TZ = ZoneInfo("America/Bogota")


class CompleteAppointmentRequest(BaseModel):
    attention_description: str = Field(min_length=2, max_length=10000)
    prescribed_medications: str | None = Field(default=None, max_length=5000)
    requires_followup: bool = False
    recommended_followup_date: date | None = None
    followup_reason: str | None = Field(default=None, max_length=500)

    @field_validator("attention_description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("prescribed_medications", "followup_reason")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @model_validator(mode="after")
    def validate_followup(self):
        if self.requires_followup:
            if not self.recommended_followup_date or not self.followup_reason:
                raise ValueError("La fecha y el motivo del próximo control son obligatorios.")
            if self.recommended_followup_date < datetime.now(BOGOTA_TZ).date():
                raise ValueError("La fecha recomendada no puede ser anterior a hoy.")
        return self


class FollowupContactRequest(BaseModel):
    management_type: str
    result: str
    observation: str | None = Field(default=None, max_length=2000)
    next_contact_at: datetime | None = None

    @field_validator("management_type")
    @classmethod
    def validate_management_type(cls, value: str) -> str:
        if value not in {"WhatsApp", "Llamada", "Presencial"}:
            raise ValueError("Medio de contacto no válido.")
        return value

    @field_validator("result")
    @classmethod
    def validate_result(cls, value: str) -> str:
        allowed = {
            "Contactado",
            "No respondió",
            "Número inválido",
            "Contactar después",
            "No desea continuar",
        }
        if value not in allowed:
            raise ValueError("Resultado de contacto no válido.")
        return value


class FollowupCloseRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)
    status: str = "Cerrado sin cita"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"Cerrado sin cita", "No desea continuar"}:
            raise ValueError("Estado de cierre no válido.")
        return value


class FollowupAppointmentRequest(BaseModel):
    dentist_id: UUID
    site_id: UUID
    appointment_type_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=1, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    is_overbook: bool = False
    overbook_reason: str | None = Field(default=None, max_length=300)


class ManagementResponse(BaseModel):
    id: UUID
    management_type: str
    result: str
    observation: str | None
    next_contact_at: datetime | None
    message_content: str | None
    user_id: UUID | None
    occurred_at: datetime


class FollowupResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    contact_mobile: str
    origin_appointment_id: UUID
    care_id: UUID
    dentist_id: UUID
    dentist_name: str
    site_id: UUID
    site_name: str
    followup_date: date
    contact_from: date
    reason: str
    status: str
    classification: str
    scheduled_appointment_id: UUID | None
    scheduled_appointment_at: datetime | None
    last_contact_at: datetime | None
    next_contact_at: datetime | None
    close_reason: str | None
    attention_description: str | None = None
    prescribed_medications: str | None = None
    managements: list[ManagementResponse] = Field(default_factory=list)


class FollowupListResponse(BaseModel):
    items: list[FollowupResponse]
    page: int
    page_size: int
    total: int
    pages: int


class FollowupDashboardResponse(BaseModel):
    pending: int
    upcoming: int
    overdue: int
    scheduled: int
    priority_items: list[FollowupResponse]


class CompleteAppointmentResponse(BaseModel):
    appointment_id: UUID
    appointment_status: str
    care_id: UUID
    followup: FollowupResponse | None


class WhatsAppLinkResponse(BaseModel):
    url: str
    phone: str
    message: str


class FollowupActionResponse(BaseModel):
    success: bool = True
    message: str
    followup: FollowupResponse
