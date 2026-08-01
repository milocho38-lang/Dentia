from app.models.associations import RolePermission, UserRole, UserSite
from app.models.agenda import (
    Appointment,
    AppointmentHistory,
    AppointmentType,
    Dentist,
    DentistSite,
    Patient,
    PatientResponsible,
)
from app.models.audit_event import AuditEvent
from app.models.followup import AppointmentCare, FollowupManagement, PatientFollowup
from app.models.auth_attempt import AuthAttempt
from app.models.auth_session import AuthSession
from app.models.clinical_record import (
    ClinicalAllergy,
    ClinicalEvolution,
    ClinicalEvolutionAddendum,
    ClinicalEvolutionProcedure,
    ClinicalMedicalHistoryItem,
    ClinicalMedication,
    ClinicalRecord,
    ClinicalTimelineEvent,
)
from app.models.clinical_document import ClinicalDocument
from app.models.company import Company
from app.models.consent_template import (
    ConsentInstance,
    ConsentInstanceProcedure,
    ConsentInstanceSequence,
    ConsentTemplate,
    ConsentTemplateVersion,
    ConsentTemplateVersionProcedure,
    ConsentTemplateVersionSite,
    ConsentTemplateVersionSpecialty,
)
from app.models.prescription import Prescription, PrescriptionItem
from app.models.odontogram import (
    Odontogram,
    OdontogramCatalogItem,
    OdontogramEvent,
    OdontogramEventDetail,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.site import Site
from app.models.treatment import (
    Budget,
    BudgetDetail,
    ProcedureCatalogDiagnosis,
    ProcedureCatalogItem,
    Treatment,
    TreatmentEvent,
    TreatmentPayment,
    TreatmentPaymentProcedure,
    TreatmentProcedure,
)
from app.models.user import User

__all__ = [
    "AuditEvent",
    "Appointment",
    "AppointmentHistory",
    "AppointmentType",
    "AppointmentCare",
    "AuthAttempt",
    "AuthSession",
    "ClinicalAllergy",
    "ClinicalEvolution",
    "ClinicalEvolutionAddendum",
    "ClinicalEvolutionProcedure",
    "ClinicalMedicalHistoryItem",
    "ClinicalMedication",
    "ClinicalRecord",
    "ClinicalTimelineEvent",
    "ClinicalDocument",
    "Company",
    "ConsentInstance",
    "ConsentInstanceProcedure",
    "ConsentInstanceSequence",
    "ConsentTemplate",
    "ConsentTemplateVersion",
    "ConsentTemplateVersionProcedure",
    "ConsentTemplateVersionSite",
    "ConsentTemplateVersionSpecialty",
    "Dentist",
    "DentistSite",
    "Odontogram",
    "OdontogramCatalogItem",
    "OdontogramEvent",
    "OdontogramEventDetail",
    "Permission",
    "Prescription",
    "PrescriptionItem",
    "Patient",
    "PatientResponsible",
    "PatientFollowup",
    "FollowupManagement",
    "Role",
    "RolePermission",
    "Site",
    "Budget",
    "BudgetDetail",
    "ProcedureCatalogDiagnosis",
    "ProcedureCatalogItem",
    "Treatment",
    "TreatmentEvent",
    "TreatmentPayment",
    "TreatmentPaymentProcedure",
    "TreatmentProcedure",
    "User",
    "UserRole",
    "UserSite",
]
