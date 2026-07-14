import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, Dentist, DentistSite, Patient, PatientResponsible
from app.models.audit_event import AuditEvent
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
from app.models.company import Company
from app.models.site import Site
from app.models.treatment import Treatment, TreatmentProcedure
from app.schemas.clinical_record_schema import (
    AllergyInput,
    AllergyListResponse,
    AllergyResponse,
    AllergyUpdateRequest,
    ClinicalEvolutionAddendumCreateRequest,
    ClinicalEvolutionAddendumResponse,
    ClinicalEvolutionCreateRequest,
    ClinicalEvolutionDraftUpdateRequest,
    ClinicalEvolutionListResponse,
    ClinicalEvolutionProcedureInput,
    ClinicalEvolutionProcedureResponse,
    ClinicalEvolutionResponse,
    ClinicalEvolutionSignRequest,
    ClinicalRecordCreateRequest,
    ClinicalRecordDraftUpdateRequest,
    ClinicalRecordEnvelope,
    ClinicalRecordResponse,
    ClinicalSummaryResponse,
    ClinicalTimelineItemResponse,
    ClinicalTimelineResponse,
    DentalHistoryInput,
    HabitsInput,
    MedicalHistoryItemResponse,
    MedicalHistoryUpsertRequest,
    MedicalHistoryResponse,
    MedicationInput,
    MedicationListResponse,
    MedicationResponse,
    MedicationUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.patient_service import calculate_age, is_minor
from app.services.site_access_service import is_authorized_site


class ClinicalRecordError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def terminology_for_country(country: str | None) -> dict[str, str]:
    normalized = (country or "").strip().casefold()
    if normalized in {"chile", "cl", "ch"}:
        return {
            "record": "Ficha Clínica",
            "open_record": "Abrir ficha clínica",
            "summary": "Resumen clínico",
        }
    return {
        "record": "Historia Clínica",
        "open_record": "Abrir historia clínica",
        "summary": "Resumen clínico",
    }


def _terminology(session: Session, company_id: UUID) -> dict[str, str]:
    company = session.get(Company, company_id)
    return terminology_for_country(company.country if company else None)


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    action: str,
    entity: str,
    entity_id: UUID | None,
    patient_id: UUID,
    result: str = "SUCCESS",
    detail: dict | None = None,
) -> None:
    safe_detail = {"patient_id": str(patient_id), **(detail or {})}
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result=result,
            detail=safe_detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _require_permission(context: AuthContext, permission: str) -> None:
    if permission not in context.permissions:
        raise ClinicalRecordError("No tienes permisos clínicos para esta acción.", 403)


def _require_patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
        )
    )
    if patient is None:
        raise ClinicalRecordError("Paciente no encontrado.", 404)
    return patient


def _ensure_site_allowed(
    session: Session,
    context: AuthContext,
    site_id: UUID | None,
) -> None:
    if site_id is None:
        return
    site = session.get(Site, site_id)
    if site is None or site.company_id != context.user.company_id or not site.is_active:
        raise ClinicalRecordError("Sede no disponible.", 422)
    if not is_authorized_site(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=site_id,
    ):
        raise ClinicalRecordError("No tienes acceso a la sede seleccionada.", 403)


def _ensure_dentist_allowed(
    session: Session,
    context: AuthContext,
    dentist_id: UUID | None,
) -> None:
    if dentist_id is None:
        return
    dentist = session.get(Dentist, dentist_id)
    if dentist is None or dentist.company_id != context.user.company_id:
        raise ClinicalRecordError("Odontólogo no disponible.", 422)


def _effective_timezone(company: Company | None, site: Site | None) -> str:
    candidate = (site.timezone if site else None) or (
        company.timezone if company else None
    ) or "America/Bogota"
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return "America/Bogota"
    return candidate


def _normalize_datetime(value: datetime | None, timezone_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
    return value.astimezone(timezone.utc)


def _current_dentist(session: Session, context: AuthContext) -> Dentist | None:
    return session.scalar(
        select(Dentist).where(
            Dentist.company_id == context.user.company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )


def _require_dentist_for_action(
    session: Session,
    context: AuthContext,
    dentist_id: UUID | None,
) -> Dentist:
    if dentist_id is not None:
        dentist = session.get(Dentist, dentist_id)
        if dentist is None or dentist.company_id != context.user.company_id:
            raise ClinicalRecordError("Odontólogo no disponible.", 422)
        if "DENTIST_ADMIN" not in context.roles and dentist.user_id != context.user.id:
            raise ClinicalRecordError("Solo puedes registrar evoluciones propias.", 403)
        return dentist
    dentist = _current_dentist(session, context)
    if dentist is None:
        raise ClinicalRecordError("Tu usuario no tiene perfil odontólogo activo.", 403)
    return dentist


def _require_site_for_action(
    session: Session,
    context: AuthContext,
    site_id: UUID | None,
) -> Site:
    selected_site_id = site_id or context.auth_session.active_site_id
    if selected_site_id is None:
        raise ClinicalRecordError("Selecciona una sede para la evolución.", 422)
    site = session.get(Site, selected_site_id)
    if site is None or site.company_id != context.user.company_id or not site.is_active:
        raise ClinicalRecordError("Sede no disponible.", 422)
    _ensure_site_allowed(session, context, selected_site_id)
    return site


def _ensure_dentist_site(session: Session, dentist: Dentist, site_id: UUID) -> None:
    exists = session.scalar(
        select(DentistSite.id).where(
            DentistSite.company_id == dentist.company_id,
            DentistSite.dentist_id == dentist.id,
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if exists is None:
        raise ClinicalRecordError("Odontólogo no registrado en la sede.", 422)


def _require_record(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    lock: bool = False,
) -> ClinicalRecord:
    _require_patient(session, context, patient_id)
    statement = select(ClinicalRecord).where(
        ClinicalRecord.company_id == context.user.company_id,
        ClinicalRecord.patient_id == patient_id,
    )
    if lock:
        statement = statement.with_for_update()
    record = session.scalar(statement)
    if record is None:
        raise ClinicalRecordError("El paciente no tiene historia clínica abierta.", 404)
    return record


def _primary_responsible(
    session: Session,
    patient_id: UUID,
) -> PatientResponsible | None:
    return session.scalar(
        select(PatientResponsible).where(
            PatientResponsible.patient_id == patient_id,
            PatientResponsible.is_active.is_(True),
            PatientResponsible.is_primary.is_(True),
        )
    )


def _active_responsible(
    session: Session,
    patient_id: UUID,
    responsible_id: UUID,
) -> PatientResponsible | None:
    return session.scalar(
        select(PatientResponsible).where(
            PatientResponsible.id == responsible_id,
            PatientResponsible.patient_id == patient_id,
            PatientResponsible.is_active.is_(True),
        )
    )


def _patient_document(patient: Patient) -> str | None:
    return patient.document if patient.document_type != "Sin documento" else None


def _patient_full_name(patient: Patient) -> str:
    return " ".join(
        part.strip()
        for part in (patient.first_names, patient.last_names)
        if part and part.strip()
    )


def _normalize_informant(
    session: Session,
    patient: Patient,
    payload: ClinicalRecordCreateRequest | ClinicalRecordDraftUpdateRequest,
) -> None:
    informant_type = (payload.informant_type or "").strip().upper()
    patient_is_minor = is_minor(patient.birth_date)

    if not patient_is_minor:
        if not informant_type or informant_type == "PATIENT":
            payload.informant_type = "PATIENT"
            payload.informant_name = _patient_full_name(patient)
            payload.informant_relationship = None
            payload.informant_document = _patient_document(patient)
            return
        payload.informant_type = informant_type
        if not payload.informant_name:
            raise ClinicalRecordError("Ingrese el nombre del informante.", 422)
        if not payload.informant_relationship:
            raise ClinicalRecordError("Seleccione la relación con el paciente.", 422)
        return

    if informant_type == "PATIENT":
        raise ClinicalRecordError(
            "El paciente menor debe tener un responsable o informante adulto.",
            422,
        )

    if payload.informant_responsible_id:
        responsible = _active_responsible(
            session,
            patient.id,
            payload.informant_responsible_id,
        )
        if responsible is None:
            raise ClinicalRecordError(
                "El responsable seleccionado no pertenece al paciente o está inactivo.",
                422,
            )
        payload.informant_type = _informant_type_from_relationship(
            responsible.relationship
        )
        payload.informant_name = responsible.name
        payload.informant_relationship = responsible.relationship
        payload.informant_document = responsible.document
        return

    responsible = _primary_responsible(session, patient.id)
    if not informant_type and responsible is not None:
        payload.informant_type = _informant_type_from_relationship(
            responsible.relationship
        )
        payload.informant_name = responsible.name
        payload.informant_relationship = responsible.relationship
        payload.informant_document = responsible.document
        return

    if not informant_type and responsible is None:
        raise ClinicalRecordError(
            "El paciente menor debe tener un responsable o informante adulto.",
            422,
        )

    if not payload.informant_name:
        raise ClinicalRecordError("Ingrese el nombre del informante.", 422)
    if not payload.informant_relationship:
        raise ClinicalRecordError(
            "Seleccione quién suministra la información.",
            422,
        )
    payload.informant_type = informant_type or _informant_type_from_relationship(
        payload.informant_relationship
    )


def _informant_type_from_relationship(relationship: str | None) -> str:
    normalized = (relationship or "").strip().casefold()
    if "madre" in normalized:
        return "MOTHER"
    if "padre" in normalized:
        return "FATHER"
    if "pareja" in normalized or "espos" in normalized:
        return "PARTNER"
    if "hijo" in normalized or "hija" in normalized:
        return "CHILD"
    if "cuidador" in normalized or "cuidadora" in normalized:
        return "CAREGIVER"
    if "legal" in normalized:
        return "LEGAL_REPRESENTATIVE"
    if "acudiente" in normalized or "tutor" in normalized:
        return "GUARDIAN"
    return "OTHER"


def _record_response(
    session: Session,
    record: ClinicalRecord,
) -> ClinicalRecordResponse:
    return ClinicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        status=record.status,
        opened_at=record.opened_at,
        opening_site_id=record.opening_site_id,
        opening_dentist_id=record.opening_dentist_id,
        chief_complaint=record.chief_complaint,
        current_situation=record.current_situation,
        situation_start=record.situation_start,
        situation_evolution=record.situation_evolution,
        symptoms=record.symptoms,
        previous_treatments=record.previous_treatments,
        informant_type=record.informant_type,
        informant_name=record.informant_name,
        informant_relationship=record.informant_relationship,
        informant_document=record.informant_document,
        observations=record.observations,
        habits=HabitsInput(**(record.habits or {})),
        dental_history=DentalHistoryInput(**(record.dental_history or {})),
        allergies_state=record.allergies_state,
        medical_history_state=record.medical_history_state,
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
        terminology=_terminology(session, record.company_id),
    )


def _apply_record_payload(
    record: ClinicalRecord,
    payload: ClinicalRecordCreateRequest | ClinicalRecordDraftUpdateRequest,
) -> None:
    record.opening_site_id = payload.opening_site_id
    record.opening_dentist_id = payload.opening_dentist_id
    record.chief_complaint = payload.chief_complaint
    record.current_situation = payload.current_situation
    record.situation_start = payload.situation_start
    record.situation_evolution = payload.situation_evolution
    record.symptoms = payload.symptoms
    record.previous_treatments = payload.previous_treatments
    record.informant_type = payload.informant_type
    record.informant_name = payload.informant_name
    record.informant_relationship = payload.informant_relationship
    record.informant_document = payload.informant_document
    record.observations = payload.observations
    record.habits = payload.habits.model_dump()
    record.dental_history = payload.dental_history.model_dump()
    record.allergies_state = payload.allergies_state
    record.medical_history_state = payload.medical_history_state


def get_clinical_record(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    metadata: RequestMetadata,
) -> ClinicalRecordEnvelope:
    _require_permission(context, "clinical_records.view_sensitive")
    _require_patient(session, context, patient_id)
    record = session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == context.user.company_id,
            ClinicalRecord.patient_id == patient_id,
        )
    )
    terminology = _terminology(session, context.user.company_id)
    if record is None:
        return ClinicalRecordEnvelope(exists=False, terminology=terminology)
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_RECORD_VIEWED",
        entity="clinical_record",
        entity_id=record.id,
        patient_id=patient_id,
        detail={"version": record.version},
    )
    session.commit()
    return ClinicalRecordEnvelope(
        exists=True,
        record=_record_response(session, record),
        terminology=terminology,
    )


def create_clinical_record(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: ClinicalRecordCreateRequest,
    metadata: RequestMetadata,
) -> ClinicalRecordResponse:
    _require_permission(context, "clinical_records.create")
    _require_permission(context, "clinical_records.view_sensitive")
    patient = _require_patient(session, context, patient_id)
    existing = session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == context.user.company_id,
            ClinicalRecord.patient_id == patient_id,
        )
    )
    if existing is not None:
        return _record_response(session, existing)
    _ensure_site_allowed(session, context, payload.opening_site_id)
    _ensure_dentist_allowed(session, context, payload.opening_dentist_id)
    _normalize_informant(session, patient, payload)
    record = ClinicalRecord(
        company_id=context.user.company_id,
        patient_id=patient_id,
        opened_at=datetime.now(timezone.utc),
        created_by=context.user.id,
    )
    _apply_record_payload(record, payload)
    session.add(record)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(
            select(ClinicalRecord).where(
                ClinicalRecord.company_id == context.user.company_id,
                ClinicalRecord.patient_id == patient_id,
            )
        )
        if existing is not None:
            return _record_response(session, existing)
        raise ClinicalRecordError("Este paciente ya tiene una historia clínica.", 409) from exc
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_RECORD_CREATED",
        entity="clinical_record",
        entity_id=record.id,
        patient_id=patient_id,
        detail={"version": record.version},
    )
    session.commit()
    session.refresh(record)
    return _record_response(session, record)


def update_clinical_record_draft(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: ClinicalRecordDraftUpdateRequest,
    metadata: RequestMetadata,
) -> ClinicalRecordResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    if record.version != payload.version:
        raise ClinicalRecordError(
            "Esta historia fue modificada por otro usuario. Recarga la información antes de continuar.",
            409,
        )
    _ensure_site_allowed(session, context, payload.opening_site_id)
    _ensure_dentist_allowed(session, context, payload.opening_dentist_id)
    patient = _require_patient(session, context, patient_id)
    _normalize_informant(session, patient, payload)
    _apply_record_payload(record, payload)
    record.version += 1
    record.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_RECORD_UPDATED",
        entity="clinical_record",
        entity_id=record.id,
        patient_id=patient_id,
        detail={"version": record.version},
    )
    session.commit()
    session.refresh(record)
    return _record_response(session, record)


def _get_evolution(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    *,
    lock: bool = False,
) -> ClinicalEvolution:
    statement = select(ClinicalEvolution).where(
        ClinicalEvolution.id == evolution_id,
        ClinicalEvolution.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    evolution = session.scalar(statement)
    if evolution is None:
        raise ClinicalRecordError("Evolución clínica no encontrada.", 404)
    return evolution


def _ensure_evolution_access(context: AuthContext, evolution: ClinicalEvolution) -> None:
    if "DENTIST_ADMIN" in context.roles:
        return
    dentist_user_id = None
    # La consulta del usuario del odontólogo se hace en las rutas críticas mediante
    # _current_dentist; aquí solo bloqueamos si el autor clínico no coincide.
    if evolution.created_by != context.user.id:
        raise ClinicalRecordError("No tienes acceso a esta evolución clínica.", 403)


def _treatment_name(session: Session, treatment_id: UUID | None) -> str | None:
    if treatment_id is None:
        return None
    treatment = session.get(Treatment, treatment_id)
    return treatment.name if treatment else None


def _site_name(session: Session, site_id: UUID | None) -> str | None:
    if site_id is None:
        return None
    site = session.get(Site, site_id)
    return site.name if site else None


def _dentist_name(session: Session, dentist_id: UUID | None) -> str | None:
    if dentist_id is None:
        return None
    dentist = session.get(Dentist, dentist_id)
    return dentist.name if dentist else None


def _procedure_name(session: Session, procedure_id: UUID | None) -> str | None:
    if procedure_id is None:
        return None
    procedure = session.get(TreatmentProcedure, procedure_id)
    return procedure.name if procedure else None


def _procedure_response(
    session: Session,
    item: ClinicalEvolutionProcedure,
) -> ClinicalEvolutionProcedureResponse:
    return ClinicalEvolutionProcedureResponse(
        id=item.id,
        treatment_id=item.treatment_id,
        procedure_id=item.procedure_id,
        procedure_name=_procedure_name(session, item.procedure_id),
        action=item.action,
        observations=item.observations,
        created_at=item.created_at,
    )


def _addendum_response(
    session: Session,
    item: ClinicalEvolutionAddendum,
) -> ClinicalEvolutionAddendumResponse:
    return ClinicalEvolutionAddendumResponse(
        id=item.id,
        evolution_id=item.evolution_id,
        reason=item.reason,
        content=item.content,
        dentist_id=item.dentist_id,
        dentist_name=_dentist_name(session, item.dentist_id),
        site_id=item.site_id,
        site_name=_site_name(session, item.site_id),
        content_hash=item.content_hash,
        created_by=item.created_by,
        created_at=item.created_at,
    )


def _evolution_procedures(
    session: Session,
    evolution_id: UUID,
) -> list[ClinicalEvolutionProcedure]:
    return list(
        session.scalars(
            select(ClinicalEvolutionProcedure)
            .where(ClinicalEvolutionProcedure.evolution_id == evolution_id)
            .order_by(ClinicalEvolutionProcedure.created_at)
        )
    )


def _evolution_addenda(
    session: Session,
    evolution_id: UUID,
) -> list[ClinicalEvolutionAddendum]:
    return list(
        session.scalars(
            select(ClinicalEvolutionAddendum)
            .where(ClinicalEvolutionAddendum.evolution_id == evolution_id)
            .order_by(ClinicalEvolutionAddendum.created_at)
        )
    )


def _evolution_response(
    session: Session,
    evolution: ClinicalEvolution,
) -> ClinicalEvolutionResponse:
    return ClinicalEvolutionResponse(
        id=evolution.id,
        patient_id=evolution.patient_id,
        clinical_record_id=evolution.clinical_record_id,
        appointment_id=evolution.appointment_id,
        treatment_id=evolution.treatment_id,
        treatment_name=_treatment_name(session, evolution.treatment_id),
        site_id=evolution.site_id,
        site_name=_site_name(session, evolution.site_id),
        dentist_id=evolution.dentist_id,
        dentist_name=_dentist_name(session, evolution.dentist_id),
        attended_at=evolution.attended_at,
        timezone_name=evolution.timezone_name,
        reason=evolution.reason,
        subjective=evolution.subjective,
        objective=evolution.objective,
        assessment=evolution.assessment,
        performed_procedure=evolution.performed_procedure,
        anesthesia=evolution.anesthesia,
        materials=evolution.materials,
        administered_medications=evolution.administered_medications,
        findings=evolution.findings,
        complications=evolution.complications,
        indications=evolution.indications,
        recommendations=evolution.recommendations,
        next_control_at=evolution.next_control_at,
        next_control_reason=evolution.next_control_reason,
        followup_id=evolution.followup_id,
        observations=evolution.observations,
        status=evolution.status,
        version=evolution.version,
        content_hash=evolution.content_hash,
        signed_at=evolution.signed_at,
        signed_by=evolution.signed_by,
        created_by=evolution.created_by,
        updated_by=evolution.updated_by,
        created_at=evolution.created_at,
        updated_at=evolution.updated_at,
        procedures=[
            _procedure_response(session, item)
            for item in _evolution_procedures(session, evolution.id)
        ],
        addenda=[
            _addendum_response(session, item)
            for item in _evolution_addenda(session, evolution.id)
        ],
        terminology=_terminology(session, evolution.company_id),
    )


def _ensure_appointment(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    appointment_id: UUID | None,
) -> None:
    if appointment_id is None:
        return
    appointment = session.get(Appointment, appointment_id)
    if (
        appointment is None
        or appointment.company_id != context.user.company_id
        or appointment.patient_id != patient_id
    ):
        raise ClinicalRecordError("Cita no disponible para este paciente.", 422)


def _ensure_treatment(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    treatment_id: UUID | None,
) -> None:
    if treatment_id is None:
        return
    treatment = session.get(Treatment, treatment_id)
    if (
        treatment is None
        or treatment.company_id != context.user.company_id
        or treatment.patient_id != patient_id
    ):
        raise ClinicalRecordError("Tratamiento no disponible para este paciente.", 422)


def _validate_procedure_input(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    item: ClinicalEvolutionProcedureInput,
) -> TreatmentProcedure:
    procedure = session.get(TreatmentProcedure, item.procedure_id)
    if (
        procedure is None
        or procedure.company_id != context.user.company_id
        or procedure.patient_id != patient_id
    ):
        raise ClinicalRecordError("Procedimiento no disponible para este paciente.", 422)
    if item.treatment_id and item.treatment_id != procedure.treatment_id:
        raise ClinicalRecordError("El procedimiento no pertenece al tratamiento indicado.", 422)
    if item.treatment_id is None:
        item.treatment_id = procedure.treatment_id
    return procedure


def _replace_evolution_procedures(
    session: Session,
    context: AuthContext,
    evolution: ClinicalEvolution,
    procedures: list[ClinicalEvolutionProcedureInput],
) -> None:
    session.query(ClinicalEvolutionProcedure).filter(
        ClinicalEvolutionProcedure.evolution_id == evolution.id
    ).delete(synchronize_session=False)
    for item in procedures:
        procedure = _validate_procedure_input(
            session,
            context,
            evolution.patient_id,
            item,
        )
        session.add(
            ClinicalEvolutionProcedure(
                company_id=context.user.company_id,
                evolution_id=evolution.id,
                treatment_id=item.treatment_id or procedure.treatment_id,
                procedure_id=procedure.id,
                action=item.action,
                observations=item.observations,
            )
        )


def _apply_evolution_payload(
    session: Session,
    context: AuthContext,
    evolution: ClinicalEvolution,
    payload: ClinicalEvolutionCreateRequest | ClinicalEvolutionDraftUpdateRequest,
) -> None:
    site = _require_site_for_action(session, context, payload.site_id or evolution.site_id)
    dentist = _require_dentist_for_action(session, context, payload.dentist_id or evolution.dentist_id)
    _ensure_dentist_site(session, dentist, site.id)
    company = session.get(Company, context.user.company_id)
    timezone_name = _effective_timezone(company, site)
    attended_at = _normalize_datetime(payload.attended_at or evolution.attended_at, timezone_name)
    next_control_at = (
        _normalize_datetime(payload.next_control_at, timezone_name)
        if payload.next_control_at
        else None
    )
    _ensure_appointment(session, context, evolution.patient_id, payload.appointment_id)
    _ensure_treatment(session, context, evolution.patient_id, payload.treatment_id)

    evolution.appointment_id = payload.appointment_id
    evolution.treatment_id = payload.treatment_id
    evolution.site_id = site.id
    evolution.dentist_id = dentist.id
    evolution.attended_at = attended_at
    evolution.timezone_name = timezone_name
    evolution.reason = payload.reason
    evolution.subjective = payload.subjective
    evolution.objective = payload.objective
    evolution.assessment = payload.assessment
    evolution.performed_procedure = payload.performed_procedure
    evolution.anesthesia = payload.anesthesia
    evolution.materials = payload.materials
    evolution.administered_medications = payload.administered_medications
    evolution.findings = payload.findings
    evolution.complications = payload.complications
    evolution.indications = payload.indications
    evolution.recommendations = payload.recommendations
    evolution.next_control_at = next_control_at
    evolution.next_control_reason = payload.next_control_reason
    evolution.followup_id = payload.followup_id
    evolution.observations = payload.observations


def _canonical_evolution_payload(
    session: Session,
    evolution: ClinicalEvolution,
) -> dict:
    procedures = [
        {
            "procedure_id": str(item.procedure_id),
            "treatment_id": str(item.treatment_id) if item.treatment_id else None,
            "action": item.action,
            "observations": item.observations,
        }
        for item in _evolution_procedures(session, evolution.id)
    ]
    return {
        "id": str(evolution.id),
        "company_id": str(evolution.company_id),
        "patient_id": str(evolution.patient_id),
        "clinical_record_id": str(evolution.clinical_record_id),
        "appointment_id": str(evolution.appointment_id) if evolution.appointment_id else None,
        "treatment_id": str(evolution.treatment_id) if evolution.treatment_id else None,
        "site_id": str(evolution.site_id),
        "dentist_id": str(evolution.dentist_id),
        "attended_at": evolution.attended_at.isoformat(),
        "timezone_name": evolution.timezone_name,
        "reason": evolution.reason,
        "subjective": evolution.subjective,
        "objective": evolution.objective,
        "assessment": evolution.assessment,
        "performed_procedure": evolution.performed_procedure,
        "anesthesia": evolution.anesthesia,
        "materials": evolution.materials,
        "administered_medications": evolution.administered_medications,
        "findings": evolution.findings,
        "complications": evolution.complications,
        "indications": evolution.indications,
        "recommendations": evolution.recommendations,
        "next_control_at": evolution.next_control_at.isoformat()
        if evolution.next_control_at
        else None,
        "next_control_reason": evolution.next_control_reason,
        "observations": evolution.observations,
        "status": evolution.status,
        "version": evolution.version,
        "procedures": sorted(procedures, key=lambda item: item["procedure_id"]),
    }


def _content_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _add_timeline_event(
    session: Session,
    context: AuthContext,
    *,
    record: ClinicalRecord,
    event_type: str,
    entity_type: str,
    entity_id: UUID | None,
    title: str,
    summary: str | None,
    clinical_date: datetime,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
    metadata: dict | None = None,
) -> None:
    session.add(
        ClinicalTimelineEvent(
            company_id=context.user.company_id,
            patient_id=record.patient_id,
            clinical_record_id=record.id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            summary=summary,
            clinical_date=clinical_date,
            site_id=site_id,
            dentist_id=dentist_id,
            created_by=context.user.id,
            event_metadata=metadata or {},
        )
    )


def list_clinical_evolutions(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    status: str | None = None,
    treatment_id: UUID | None = None,
    dentist_id: UUID | None = None,
    site_id: UUID | None = None,
) -> ClinicalEvolutionListResponse:
    _require_permission(context, "clinical_evolutions.view")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    statement = select(ClinicalEvolution).where(
        ClinicalEvolution.company_id == context.user.company_id,
        ClinicalEvolution.patient_id == patient_id,
        ClinicalEvolution.clinical_record_id == record.id,
    )
    if status:
        statement = statement.where(ClinicalEvolution.status == status)
    if treatment_id:
        statement = statement.where(ClinicalEvolution.treatment_id == treatment_id)
    if dentist_id:
        statement = statement.where(ClinicalEvolution.dentist_id == dentist_id)
    if site_id:
        statement = statement.where(ClinicalEvolution.site_id == site_id)
    evolutions = list(
        session.scalars(statement.order_by(ClinicalEvolution.attended_at.desc()))
    )
    return ClinicalEvolutionListResponse(
        items=[_evolution_response(session, evolution) for evolution in evolutions]
    )


def create_clinical_evolution(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: ClinicalEvolutionCreateRequest,
    metadata: RequestMetadata,
) -> ClinicalEvolutionResponse:
    _require_permission(context, "clinical_evolutions.create")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    site = _require_site_for_action(session, context, payload.site_id)
    dentist = _require_dentist_for_action(session, context, payload.dentist_id)
    _ensure_dentist_site(session, dentist, site.id)
    company = session.get(Company, context.user.company_id)
    timezone_name = _effective_timezone(company, site)
    attended_at = _normalize_datetime(payload.attended_at, timezone_name)
    if payload.appointment_id:
        existing = session.scalar(
            select(ClinicalEvolution).where(
                ClinicalEvolution.company_id == context.user.company_id,
                ClinicalEvolution.appointment_id == payload.appointment_id,
            )
        )
        if existing is not None:
            return _evolution_response(session, existing)
    _ensure_appointment(session, context, patient_id, payload.appointment_id)
    _ensure_treatment(session, context, patient_id, payload.treatment_id)
    evolution = ClinicalEvolution(
        company_id=context.user.company_id,
        patient_id=patient_id,
        clinical_record_id=record.id,
        appointment_id=payload.appointment_id,
        treatment_id=payload.treatment_id,
        site_id=site.id,
        dentist_id=dentist.id,
        attended_at=attended_at,
        timezone_name=timezone_name,
        created_by=context.user.id,
    )
    _apply_evolution_payload(session, context, evolution, payload)
    session.add(evolution)
    session.flush()
    _replace_evolution_procedures(session, context, evolution, payload.procedures)
    _add_timeline_event(
        session,
        context,
        record=record,
        event_type="CLINICAL_EVOLUTION_CREATED",
        entity_type="clinical_evolution",
        entity_id=evolution.id,
        title="Evolución clínica creada",
        summary="Borrador de evolución clínica.",
        clinical_date=evolution.attended_at,
        site_id=evolution.site_id,
        dentist_id=evolution.dentist_id,
        metadata={"status": evolution.status},
    )
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_EVOLUTION_CREATED",
        entity="clinical_evolution",
        entity_id=evolution.id,
        patient_id=patient_id,
        detail={"version": evolution.version, "status": evolution.status},
    )
    session.commit()
    session.refresh(evolution)
    return _evolution_response(session, evolution)


def get_clinical_evolution(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    metadata: RequestMetadata,
) -> ClinicalEvolutionResponse:
    _require_permission(context, "clinical_evolutions.view")
    _require_permission(context, "clinical_records.view_sensitive")
    evolution = _get_evolution(session, context, evolution_id)
    _ensure_evolution_access(context, evolution)
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_EVOLUTION_VIEWED",
        entity="clinical_evolution",
        entity_id=evolution.id,
        patient_id=evolution.patient_id,
        detail={"version": evolution.version, "status": evolution.status},
    )
    session.commit()
    return _evolution_response(session, evolution)


def update_clinical_evolution_draft(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    payload: ClinicalEvolutionDraftUpdateRequest,
    metadata: RequestMetadata,
) -> ClinicalEvolutionResponse:
    _require_permission(context, "clinical_evolutions.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    evolution = _get_evolution(session, context, evolution_id, lock=True)
    _ensure_evolution_access(context, evolution)
    if evolution.status != "DRAFT":
        raise ClinicalRecordError("Una evolución firmada no puede editarse.", 409)
    if evolution.version != payload.version:
        raise ClinicalRecordError(
            "Esta evolución fue modificada o firmada por otro usuario. Recarga la versión más reciente.",
            409,
        )
    _apply_evolution_payload(session, context, evolution, payload)
    _replace_evolution_procedures(session, context, evolution, payload.procedures)
    evolution.version += 1
    evolution.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_EVOLUTION_DRAFT_UPDATED",
        entity="clinical_evolution",
        entity_id=evolution.id,
        patient_id=evolution.patient_id,
        detail={"version": evolution.version, "status": evolution.status},
    )
    session.commit()
    session.refresh(evolution)
    return _evolution_response(session, evolution)


def _validate_evolution_ready_to_sign(evolution: ClinicalEvolution) -> None:
    if not any(
        [
            evolution.objective,
            evolution.assessment,
            evolution.performed_procedure,
            evolution.indications,
        ]
    ):
        raise ClinicalRecordError(
            "Para firmar registra al menos objetivo, evaluación, procedimiento realizado o indicaciones.",
            422,
        )


def sign_clinical_evolution(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    payload: ClinicalEvolutionSignRequest,
    metadata: RequestMetadata,
) -> ClinicalEvolutionResponse:
    _require_permission(context, "clinical_evolutions.sign")
    _require_permission(context, "clinical_records.view_sensitive")
    evolution = _get_evolution(session, context, evolution_id, lock=True)
    _ensure_evolution_access(context, evolution)
    if evolution.status != "DRAFT":
        raise ClinicalRecordError("La evolución ya está firmada o cerrada.", 409)
    if evolution.version != payload.version:
        raise ClinicalRecordError(
            "Esta evolución fue modificada o firmada por otro usuario. Recarga la versión más reciente.",
            409,
        )
    if not payload.confirm_complete:
        raise ClinicalRecordError("Debes confirmar que el registro está completo.", 422)
    _validate_evolution_ready_to_sign(evolution)
    evolution.status = "SIGNED"
    evolution.signed_at = datetime.now(timezone.utc)
    evolution.signed_by = context.user.id
    evolution.version += 1
    session.flush()
    evolution.content_hash = _content_hash(_canonical_evolution_payload(session, evolution))
    record = session.get(ClinicalRecord, evolution.clinical_record_id)
    if record is not None:
        _add_timeline_event(
            session,
            context,
            record=record,
            event_type="CLINICAL_EVOLUTION_SIGNED",
            entity_type="clinical_evolution",
            entity_id=evolution.id,
            title="Evolución clínica firmada",
            summary="Registro clínico firmado y cerrado.",
            clinical_date=evolution.attended_at,
            site_id=evolution.site_id,
            dentist_id=evolution.dentist_id,
            metadata={"hash": evolution.content_hash},
        )
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_EVOLUTION_SIGNED",
        entity="clinical_evolution",
        entity_id=evolution.id,
        patient_id=evolution.patient_id,
        detail={
            "version": evolution.version,
            "status": evolution.status,
            "hash": evolution.content_hash,
        },
    )
    session.commit()
    session.refresh(evolution)
    return _evolution_response(session, evolution)


def list_evolution_addenda(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
) -> list[ClinicalEvolutionAddendumResponse]:
    _require_permission(context, "clinical_evolutions.view")
    _require_permission(context, "clinical_records.view_sensitive")
    evolution = _get_evolution(session, context, evolution_id)
    _ensure_evolution_access(context, evolution)
    return [_addendum_response(session, item) for item in _evolution_addenda(session, evolution.id)]


def create_evolution_addendum(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    payload: ClinicalEvolutionAddendumCreateRequest,
    metadata: RequestMetadata,
) -> ClinicalEvolutionAddendumResponse:
    _require_permission(context, "clinical_evolutions.add_addendum")
    _require_permission(context, "clinical_records.view_sensitive")
    evolution = _get_evolution(session, context, evolution_id)
    _ensure_evolution_access(context, evolution)
    if evolution.status != "SIGNED":
        raise ClinicalRecordError("Solo se pueden agregar adendas a evoluciones firmadas.", 409)
    site = _require_site_for_action(session, context, payload.site_id or evolution.site_id)
    dentist = _require_dentist_for_action(session, context, payload.dentist_id or evolution.dentist_id)
    _ensure_dentist_site(session, dentist, site.id)
    addendum_payload = {
        "evolution_id": str(evolution.id),
        "reason": payload.reason,
        "content": payload.content,
        "dentist_id": str(dentist.id),
        "site_id": str(site.id),
        "created_by": str(context.user.id),
    }
    addendum = ClinicalEvolutionAddendum(
        company_id=context.user.company_id,
        patient_id=evolution.patient_id,
        evolution_id=evolution.id,
        reason=payload.reason,
        content=payload.content,
        dentist_id=dentist.id,
        site_id=site.id,
        content_hash=_content_hash(addendum_payload),
        created_by=context.user.id,
    )
    session.add(addendum)
    session.flush()
    record = session.get(ClinicalRecord, evolution.clinical_record_id)
    if record is not None:
        _add_timeline_event(
            session,
            context,
            record=record,
            event_type="CLINICAL_EVOLUTION_ADDENDUM_CREATED",
            entity_type="clinical_evolution_addendum",
            entity_id=addendum.id,
            title="Adenda clínica agregada",
            summary=payload.reason[:240],
            clinical_date=addendum.created_at,
            site_id=site.id,
            dentist_id=dentist.id,
            metadata={"evolution_id": str(evolution.id), "hash": addendum.content_hash},
        )
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_EVOLUTION_ADDENDUM_CREATED",
        entity="clinical_evolution_addendum",
        entity_id=addendum.id,
        patient_id=evolution.patient_id,
        detail={"evolution_id": str(evolution.id), "hash": addendum.content_hash},
    )
    session.commit()
    return _addendum_response(session, addendum)


def list_clinical_timeline(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> ClinicalTimelineResponse:
    _require_permission(context, "clinical_timeline.view")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    items: list[ClinicalTimelineItemResponse] = [
        ClinicalTimelineItemResponse(
            id=record.id,
            event_type="CLINICAL_RECORD_CREATED",
            entity_type="clinical_record",
            entity_id=record.id,
            title=f"{_terminology(session, context.user.company_id)['record']} abierta",
            summary="Apertura del expediente clínico longitudinal.",
            clinical_date=record.opened_at,
            site_id=record.opening_site_id,
            site_name=_site_name(session, record.opening_site_id),
            dentist_id=record.opening_dentist_id,
            dentist_name=_dentist_name(session, record.opening_dentist_id),
            metadata={"version": record.version},
        )
    ]
    events = list(
        session.scalars(
            select(ClinicalTimelineEvent)
            .where(
                ClinicalTimelineEvent.company_id == context.user.company_id,
                ClinicalTimelineEvent.patient_id == patient_id,
                ClinicalTimelineEvent.clinical_record_id == record.id,
            )
            .order_by(ClinicalTimelineEvent.clinical_date.desc())
        )
    )
    items.extend(
        ClinicalTimelineItemResponse(
            id=event.id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            title=event.title,
            summary=event.summary,
            clinical_date=event.clinical_date,
            site_id=event.site_id,
            site_name=_site_name(session, event.site_id),
            dentist_id=event.dentist_id,
            dentist_name=_dentist_name(session, event.dentist_id),
            metadata=event.event_metadata,
        )
        for event in events
    )
    items.sort(key=lambda item: item.clinical_date, reverse=True)
    return ClinicalTimelineResponse(
        items=items,
        terminology=_terminology(session, context.user.company_id),
    )


def _medical_response(item: ClinicalMedicalHistoryItem) -> MedicalHistoryItemResponse:
    return MedicalHistoryItemResponse(
        id=item.id,
        type=item.type,
        present=item.present,
        detail=item.detail,
        severity=item.severity,
        status=item.status,
        source=item.source,
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def list_medical_history(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> MedicalHistoryResponse:
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    items = list(
        session.scalars(
            select(ClinicalMedicalHistoryItem)
            .where(
                ClinicalMedicalHistoryItem.company_id == context.user.company_id,
                ClinicalMedicalHistoryItem.clinical_record_id == record.id,
            )
            .order_by(ClinicalMedicalHistoryItem.type)
        )
    )
    return MedicalHistoryResponse(
        items=[_medical_response(item) for item in items],
        record_version=record.version,
        medical_history_state=record.medical_history_state,
    )


def replace_medical_history(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: MedicalHistoryUpsertRequest,
    metadata: RequestMetadata,
) -> MedicalHistoryResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    if record.version != payload.record_version:
        raise ClinicalRecordError(
            "Esta historia fue modificada por otro usuario. Recarga la información antes de continuar.",
            409,
        )
    existing = {
        item.type: item
        for item in session.scalars(
            select(ClinicalMedicalHistoryItem).where(
                ClinicalMedicalHistoryItem.clinical_record_id == record.id,
            )
        )
    }
    seen: set[str] = set()
    for input_item in payload.items:
        seen.add(input_item.type)
        item = existing.get(input_item.type)
        if item is None:
            item = ClinicalMedicalHistoryItem(
                company_id=context.user.company_id,
                clinical_record_id=record.id,
                patient_id=patient_id,
                type=input_item.type,
                created_by=context.user.id,
                version=1,
            )
            session.add(item)
        elif input_item.version is not None and item.version != input_item.version:
            raise ClinicalRecordError(
                "Un antecedente fue modificado por otro usuario. Recarga la información.",
                409,
            )
        elif item is not None:
            item.version += 1
        item.present = input_item.present
        item.detail = input_item.detail
        item.severity = input_item.severity
        item.status = input_item.status
        item.source = input_item.source
        item.updated_by = context.user.id
    record.medical_history_state = payload.medical_history_state
    record.version += 1
    record.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_RECORD_UPDATED",
        entity="clinical_record",
        entity_id=record.id,
        patient_id=patient_id,
        detail={"section": "medical_history", "version": record.version},
    )
    session.commit()
    return list_medical_history(session, context, patient_id)


def _allergy_response(item: ClinicalAllergy) -> AllergyResponse:
    return AllergyResponse(
        id=item.id,
        type=item.type,
        substance=item.substance,
        reaction=item.reaction,
        severity=item.severity,
        status=item.status,
        critical_alert=item.critical_alert,
        observations=item.observations,
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def list_allergies(session: Session, context: AuthContext, patient_id: UUID) -> AllergyListResponse:
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    items = list(
        session.scalars(
            select(ClinicalAllergy)
            .where(
                ClinicalAllergy.company_id == context.user.company_id,
                ClinicalAllergy.clinical_record_id == record.id,
            )
            .order_by(ClinicalAllergy.critical_alert.desc(), ClinicalAllergy.substance)
        )
    )
    return AllergyListResponse(
        items=[_allergy_response(item) for item in items],
        record_version=record.version,
        allergies_state=record.allergies_state,
    )


def create_allergy(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: AllergyInput,
    metadata: RequestMetadata,
) -> AllergyResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    item = ClinicalAllergy(
        company_id=context.user.company_id,
        clinical_record_id=record.id,
        patient_id=patient_id,
        type=payload.type,
        substance=payload.substance,
        reaction=payload.reaction,
        severity=payload.severity,
        status=payload.status,
        critical_alert=payload.critical_alert,
        observations=payload.observations,
        created_by=context.user.id,
    )
    record.allergies_state = "CON_ALERGIAS"
    record.version += 1
    record.updated_by = context.user.id
    session.add(item)
    session.flush()
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_ALLERGY_CREATED",
        entity="clinical_allergy",
        entity_id=item.id,
        patient_id=patient_id,
        detail={"critical_alert": item.critical_alert, "record_version": record.version},
    )
    session.commit()
    session.refresh(item)
    return _allergy_response(item)


def update_allergy(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    allergy_id: UUID,
    payload: AllergyUpdateRequest,
    metadata: RequestMetadata,
) -> AllergyResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    item = session.scalar(
        select(ClinicalAllergy).where(
            ClinicalAllergy.id == allergy_id,
            ClinicalAllergy.company_id == context.user.company_id,
            ClinicalAllergy.patient_id == patient_id,
        ).with_for_update()
    )
    if item is None:
        raise ClinicalRecordError("Alergia no encontrada.", 404)
    if item.version != payload.version:
        raise ClinicalRecordError("Esta alergia fue modificada por otro usuario.", 409)
    item.type = payload.type
    item.substance = payload.substance
    item.reaction = payload.reaction
    item.severity = payload.severity
    item.status = payload.status
    item.critical_alert = payload.critical_alert
    item.observations = payload.observations
    item.version += 1
    item.updated_by = context.user.id
    record.version += 1
    record.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_ALLERGY_UPDATED",
        entity="clinical_allergy",
        entity_id=item.id,
        patient_id=patient_id,
        detail={"critical_alert": item.critical_alert, "record_version": record.version},
    )
    session.commit()
    session.refresh(item)
    return _allergy_response(item)


def _medication_response(item: ClinicalMedication) -> MedicationResponse:
    return MedicationResponse(
        id=item.id,
        name=item.name,
        dose=item.dose,
        frequency=item.frequency,
        route=item.route,
        since=item.since,
        reason=item.reason,
        prescriber=item.prescriber,
        status=item.status,
        observations=item.observations,
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def list_medications(session: Session, context: AuthContext, patient_id: UUID) -> MedicationListResponse:
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id)
    items = list(
        session.scalars(
            select(ClinicalMedication)
            .where(
                ClinicalMedication.company_id == context.user.company_id,
                ClinicalMedication.clinical_record_id == record.id,
            )
            .order_by(ClinicalMedication.status, ClinicalMedication.name)
        )
    )
    return MedicationListResponse(
        items=[_medication_response(item) for item in items],
        record_version=record.version,
    )


def create_medication(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: MedicationInput,
    metadata: RequestMetadata,
) -> MedicationResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    item = ClinicalMedication(
        company_id=context.user.company_id,
        clinical_record_id=record.id,
        patient_id=patient_id,
        name=payload.name,
        dose=payload.dose,
        frequency=payload.frequency,
        route=payload.route,
        since=payload.since,
        reason=payload.reason,
        prescriber=payload.prescriber,
        status=payload.status,
        observations=payload.observations,
        created_by=context.user.id,
    )
    record.version += 1
    record.updated_by = context.user.id
    session.add(item)
    session.flush()
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_MEDICATION_CREATED",
        entity="clinical_medication",
        entity_id=item.id,
        patient_id=patient_id,
        detail={"status": item.status, "record_version": record.version},
    )
    session.commit()
    session.refresh(item)
    return _medication_response(item)


def update_medication(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    medication_id: UUID,
    payload: MedicationUpdateRequest,
    metadata: RequestMetadata,
) -> MedicationResponse:
    _require_permission(context, "clinical_records.update_draft")
    _require_permission(context, "clinical_records.view_sensitive")
    record = _require_record(session, context, patient_id, lock=True)
    item = session.scalar(
        select(ClinicalMedication).where(
            ClinicalMedication.id == medication_id,
            ClinicalMedication.company_id == context.user.company_id,
            ClinicalMedication.patient_id == patient_id,
        ).with_for_update()
    )
    if item is None:
        raise ClinicalRecordError("Medicamento no encontrado.", 404)
    if item.version != payload.version:
        raise ClinicalRecordError("Este medicamento fue modificado por otro usuario.", 409)
    item.name = payload.name
    item.dose = payload.dose
    item.frequency = payload.frequency
    item.route = payload.route
    item.since = payload.since
    item.reason = payload.reason
    item.prescriber = payload.prescriber
    item.status = payload.status
    item.observations = payload.observations
    item.version += 1
    item.updated_by = context.user.id
    record.version += 1
    record.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="CLINICAL_MEDICATION_UPDATED",
        entity="clinical_medication",
        entity_id=item.id,
        patient_id=patient_id,
        detail={"status": item.status, "record_version": record.version},
    )
    session.commit()
    session.refresh(item)
    return _medication_response(item)


def get_clinical_summary(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> ClinicalSummaryResponse:
    if (
        "patients.view" not in context.permissions
        and "clinical_records.view" not in context.permissions
    ):
        raise ClinicalRecordError("No tienes permisos para consultar el resumen clínico.", 403)
    _require_patient(session, context, patient_id)
    record = session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == context.user.company_id,
            ClinicalRecord.patient_id == patient_id,
        )
    )
    terminology = _terminology(session, context.user.company_id)
    if record is None:
        return ClinicalSummaryResponse(
            patient_id=patient_id,
            exists=False,
            terminology=terminology,
            limited="clinical_records.view_sensitive" not in context.permissions,
            has_critical_alerts=False,
            requires_clinical_precaution=False,
        )
    critical = list(
        session.scalars(
            select(ClinicalAllergy).where(
                ClinicalAllergy.clinical_record_id == record.id,
                ClinicalAllergy.critical_alert.is_(True),
                ClinicalAllergy.status != "descartada",
            )
        )
    )
    relevant_history = list(
        session.scalars(
            select(ClinicalMedicalHistoryItem)
            .where(
                ClinicalMedicalHistoryItem.clinical_record_id == record.id,
                ClinicalMedicalHistoryItem.present == "SI",
                ClinicalMedicalHistoryItem.status == "activo",
            )
            .limit(8)
        )
    )
    active_meds = list(
        session.scalars(
            select(ClinicalMedication)
            .where(
                ClinicalMedication.clinical_record_id == record.id,
                ClinicalMedication.status == "activo",
            )
            .order_by(ClinicalMedication.name)
            .limit(8)
        )
    )
    has_alerts = bool(critical or relevant_history or active_meds)
    limited = "clinical_records.view_sensitive" not in context.permissions
    return ClinicalSummaryResponse(
        patient_id=patient_id,
        exists=True,
        terminology=terminology,
        limited=limited,
        has_critical_alerts=bool(critical),
        requires_clinical_precaution=has_alerts,
        message=(
            "El paciente presenta alertas clínicas. Consultar al odontólogo antes de la atención."
            if limited and has_alerts
            else None
        ),
        opened_at=record.opened_at,
        updated_at=record.updated_at,
        allergies_state=record.allergies_state,
        medical_history_state=record.medical_history_state,
        critical_allergies=[_allergy_response(item) for item in critical],
        active_medications=[_medication_response(item) for item in active_meds],
        relevant_medical_history=[_medical_response(item) for item in relevant_history],
        active_diagnoses=[],
        last_evolution=None,
    )
