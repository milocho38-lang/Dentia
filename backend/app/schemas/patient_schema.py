from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


DOCUMENT_TYPES = {
    "CC",
    "TI",
    "RC",
    "CE",
    "Pasaporte",
    "Otro",
    "Sin documento",
}
SEX_VALUES = {"femenino", "masculino", "otro", "no informa"}
PATIENT_STATUSES = {"Activo", "Inactivo"}


class ResponsibleInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    document_type: str
    document: str | None = Field(default=None, max_length=50)
    relationship: str = Field(min_length=2, max_length=100)
    mobile: str = Field(min_length=7, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    is_primary: bool = False

    @field_validator("name", "relationship", "mobile")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("document", "email")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        if value not in DOCUMENT_TYPES:
            raise ValueError("Tipo de documento no válido.")
        return value

    @model_validator(mode="after")
    def validate_document(self):
        if self.document_type != "Sin documento" and not self.document:
            raise ValueError("El documento del responsable es obligatorio.")
        if self.document_type == "Sin documento":
            self.document = None
        return self


class PatientDataInput(BaseModel):
    first_names: str = Field(min_length=1, max_length=150)
    last_names: str = Field(min_length=1, max_length=150)
    document_type: str
    document: str | None = Field(default=None, max_length=50)
    mobile: str = Field(min_length=7, max_length=50)
    birth_date: date
    sex: str | None = None
    email: str | None = Field(default=None, max_length=200)
    alternate_phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    emergency_contact_name: str | None = Field(default=None, max_length=200)
    emergency_contact_mobile: str | None = Field(default=None, max_length=50)
    administrative_notes: str | None = Field(default=None, max_length=3000)

    @field_validator("first_names", "last_names", "mobile")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "document",
        "email",
        "alternate_phone",
        "address",
        "city",
        "department",
        "emergency_contact_name",
        "emergency_contact_mobile",
        "administrative_notes",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        if value not in DOCUMENT_TYPES:
            raise ValueError("Tipo de documento no válido.")
        return value

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: str | None) -> str | None:
        if value is not None and value not in SEX_VALUES:
            raise ValueError("Sexo no válido.")
        return value

    @model_validator(mode="after")
    def validate_document_and_birth_date(self):
        if self.birth_date > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        if self.document_type != "Sin documento" and not self.document:
            raise ValueError("El documento es obligatorio para el tipo seleccionado.")
        if self.document_type == "Sin documento":
            self.document = None
        return self


class PatientCreateRequest(PatientDataInput):
    responsibles: list[ResponsibleInput] = Field(default_factory=list)
    acknowledge_duplicate_warning: bool = False


class PatientUpdateRequest(PatientDataInput):
    acknowledge_duplicate_warning: bool = False


class PatientQuickCreateRequest(BaseModel):
    first_names: str = Field(min_length=1, max_length=150)
    last_names: str = Field(min_length=1, max_length=150)
    document_type: str = "Otro"
    document: str | None = Field(default=None, max_length=50)
    mobile: str = Field(min_length=7, max_length=50)
    acknowledge_duplicate_warning: bool = False

    @field_validator("first_names", "last_names", "mobile")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("document")
    @classmethod
    def strip_document(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        if value not in DOCUMENT_TYPES:
            raise ValueError("Tipo de documento no válido.")
        return value

    @model_validator(mode="after")
    def validate_document(self):
        if self.document_type != "Sin documento" and not self.document:
            raise ValueError("El documento es obligatorio para el tipo seleccionado.")
        if self.document_type == "Sin documento":
            self.document = None
        return self


class DuplicateCheckRequest(BaseModel):
    first_names: str = Field(min_length=1, max_length=150)
    last_names: str = Field(min_length=1, max_length=150)
    document_type: str
    document: str | None = Field(default=None, max_length=50)
    mobile: str = Field(min_length=7, max_length=50)
    birth_date: date | None = None
    exclude_patient_id: UUID | None = None


class ResponsibleResponse(BaseModel):
    id: UUID
    name: str
    document_type: str
    document: str | None
    relationship: str
    mobile: str
    email: str | None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatientResponse(BaseModel):
    id: UUID
    first_names: str
    last_names: str
    full_name: str
    document_type: str
    document: str | None
    mobile: str
    birth_date: date | None
    age: int | None
    is_minor: bool
    sex: str | None
    email: str | None
    alternate_phone: str | None
    address: str | None
    city: str | None
    department: str | None
    emergency_contact_name: str | None
    emergency_contact_mobile: str | None
    administrative_notes: str | None
    status: str
    profile_complete: bool
    is_active: bool
    responsibles: list[ResponsibleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PatientListItemResponse(BaseModel):
    id: UUID
    full_name: str
    document_type: str
    document: str | None
    mobile: str
    age: int | None
    is_minor: bool
    status: str
    profile_complete: bool
    next_appointment_at: datetime | None
    last_appointment_at: datetime | None


class PatientListResponse(BaseModel):
    items: list[PatientListItemResponse]
    page: int
    page_size: int
    total: int
    pages: int


class DuplicateCandidateResponse(BaseModel):
    id: UUID
    full_name: str
    document_type: str
    document: str | None
    mobile: str
    birth_date: date | None
    reasons: list[str]


class DuplicateCheckResponse(BaseModel):
    exact: list[DuplicateCandidateResponse]
    approximate: list[DuplicateCandidateResponse]


class PatientAppointmentResponse(BaseModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    reason: str
    is_overbook: bool
    confirmation_method: str | None
    dentist_name: str
    site_name: str
    appointment_type_name: str
    origin_appointment_id: UUID | None


class PatientAppointmentsResponse(BaseModel):
    items: list[PatientAppointmentResponse]
    page: int
    page_size: int
    total: int
    pages: int


class PatientSummaryResponse(BaseModel):
    patient: PatientResponse
    next_appointment: PatientAppointmentResponse | None
    last_appointment: PatientAppointmentResponse | None
    appointment_count: int
    active_future_appointment_count: int


class ResponsibleCreateRequest(ResponsibleInput):
    pass


class ResponsibleUpdateRequest(ResponsibleInput):
    pass


class ResponsibleListResponse(BaseModel):
    items: list[ResponsibleResponse]


class PatientActionResponse(BaseModel):
    success: bool = True
    message: str
    patient: PatientResponse
