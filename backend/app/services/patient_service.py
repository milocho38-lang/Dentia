import math
import re
import unicodedata
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import (
    Appointment,
    AppointmentType,
    Dentist,
    Patient,
    PatientResponsible,
)
from app.models.audit_event import AuditEvent
from app.models.site import Site
from app.schemas.patient_schema import (
    DuplicateCandidateResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    PatientActionResponse,
    PatientAppointmentResponse,
    PatientAppointmentsResponse,
    PatientCreateRequest,
    PatientListItemResponse,
    PatientListResponse,
    PatientResponse,
    PatientSummaryResponse,
    PatientUpdateRequest,
    ResponsibleCreateRequest,
    ResponsibleListResponse,
    ResponsibleResponse,
    ResponsibleUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata


ACTIVE_FUTURE_APPOINTMENT_STATES = {"Programada", "Confirmada"}


class PatientManagementError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        *,
        duplicates: DuplicateCheckResponse | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.duplicates = duplicates


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(without_marks.split())


def normalize_document(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"[^0-9A-Za-z]", "", value).upper()
    return normalized or None


def normalize_phone(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().casefold()


def calculate_age(birth_date: date | None, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    current = today or date.today()
    return (
        current.year
        - birth_date.year
        - ((current.month, current.day) < (birth_date.month, birth_date.day))
    )


def is_minor(birth_date: date | None) -> bool:
    age = calculate_age(birth_date)
    return age is not None and age < 18


def _is_profile_complete(patient: Patient) -> bool:
    return bool(
        patient.first_names
        and patient.last_names
        and patient.mobile
        and patient.birth_date
        and patient.document_type != "Sin documento"
        and patient.document
    )


def _refresh_normalized_fields(patient: Patient) -> None:
    patient.normalized_document = (
        None
        if patient.document_type == "Sin documento"
        else normalize_document(patient.document)
    )
    patient.normalized_mobile = normalize_phone(patient.mobile)
    patient.normalized_email = normalize_email(patient.email)
    patient.search_text = " ".join(
        filter(
            None,
            (
                normalize_text(patient.first_names),
                normalize_text(patient.last_names),
                patient.normalized_document or "",
                patient.normalized_mobile,
                patient.normalized_email or "",
            ),
        )
    )
    patient.profile_complete = _is_profile_complete(patient)


def _get_patient(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    lock: bool = False,
) -> Patient:
    statement = select(Patient).where(
        Patient.id == patient_id,
        Patient.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    patient = session.scalar(statement)
    if patient is None:
        raise PatientManagementError("Paciente no encontrado.", 404)
    return patient


def _responsible_response(item: PatientResponsible) -> ResponsibleResponse:
    return ResponsibleResponse(
        id=item.id,
        name=item.name,
        document_type=item.document_type,
        document=item.document,
        relationship=item.relationship,
        mobile=item.mobile,
        email=item.email,
        is_primary=item.is_primary,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _active_responsibles(
    session: Session,
    patient_id: UUID,
) -> list[PatientResponsible]:
    return list(
        session.scalars(
            select(PatientResponsible)
            .where(
                PatientResponsible.patient_id == patient_id,
                PatientResponsible.is_active.is_(True),
            )
            .order_by(
                PatientResponsible.is_primary.desc(),
                PatientResponsible.name,
            )
        )
    )


def _patient_response(session: Session, patient: Patient) -> PatientResponse:
    return PatientResponse(
        id=patient.id,
        first_names=patient.first_names,
        last_names=patient.last_names,
        full_name=f"{patient.first_names} {patient.last_names}".strip(),
        document_type=patient.document_type,
        document=patient.document,
        mobile=patient.mobile,
        birth_date=patient.birth_date,
        age=calculate_age(patient.birth_date),
        is_minor=is_minor(patient.birth_date),
        sex=patient.sex,
        email=patient.email,
        alternate_phone=patient.alternate_phone,
        address=patient.address,
        city=patient.city,
        department=patient.department,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_mobile=patient.emergency_contact_mobile,
        administrative_notes=patient.administrative_notes,
        status=patient.status,
        profile_complete=patient.profile_complete,
        is_active=patient.is_active,
        responsibles=[
            _responsible_response(item)
            for item in _active_responsibles(session, patient.id)
        ],
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    patient_id: UUID,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="patient",
            entity_id=patient_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _duplicate_candidate(
    patient: Patient,
    reasons: list[str],
) -> DuplicateCandidateResponse:
    return DuplicateCandidateResponse(
        id=patient.id,
        full_name=f"{patient.first_names} {patient.last_names}".strip(),
        document_type=patient.document_type,
        document=patient.document,
        mobile=patient.mobile,
        birth_date=patient.birth_date,
        reasons=reasons,
    )


def check_duplicates(
    session: Session,
    context: AuthContext,
    payload: DuplicateCheckRequest,
) -> DuplicateCheckResponse:
    normalized_doc = (
        None
        if payload.document_type == "Sin documento"
        else normalize_document(payload.document)
    )
    normalized_mobile = normalize_phone(payload.mobile)
    normalized_name = normalize_text(
        f"{payload.first_names} {payload.last_names}"
    )
    statement = select(Patient).where(
        Patient.company_id == context.user.company_id,
        Patient.is_active.is_(True),
    )
    if payload.exclude_patient_id:
        statement = statement.where(Patient.id != payload.exclude_patient_id)
    candidates = list(
        session.scalars(
            statement.where(
                or_(
                    Patient.normalized_document == normalized_doc
                    if normalized_doc
                    else False,
                    Patient.normalized_mobile == normalized_mobile,
                    Patient.search_text.ilike(
                        f"%{normalize_text(payload.first_names)}%"
                    ),
                    Patient.search_text.ilike(
                        f"%{normalize_text(payload.last_names)}%"
                    ),
                )
            ).limit(50)
        )
    )
    exact: list[DuplicateCandidateResponse] = []
    approximate: list[DuplicateCandidateResponse] = []
    for candidate in candidates:
        if (
            normalized_doc
            and candidate.document_type == payload.document_type
            and candidate.normalized_document == normalized_doc
        ):
            exact.append(_duplicate_candidate(candidate, ["Documento exacto"]))
            continue
        reasons: list[str] = []
        candidate_name = normalize_text(
            f"{candidate.first_names} {candidate.last_names}"
        )
        if candidate_name == normalized_name:
            reasons.append("Nombre completo coincidente")
        if (
            payload.birth_date
            and candidate.birth_date
            and candidate.birth_date == payload.birth_date
        ):
            reasons.append("Fecha de nacimiento coincidente")
        if normalized_mobile and candidate.normalized_mobile == normalized_mobile:
            reasons.append("Celular compartido")
        if reasons:
            approximate.append(_duplicate_candidate(candidate, reasons))
    return DuplicateCheckResponse(exact=exact, approximate=approximate)


def _validate_duplicate_result(
    result: DuplicateCheckResponse,
    *,
    acknowledged: bool,
) -> None:
    if result.exact:
        raise PatientManagementError(
            "Ya existe un paciente con ese tipo y número de documento.",
            409,
            duplicates=result,
        )
    if result.approximate and not acknowledged:
        raise PatientManagementError(
            "Se encontraron posibles pacientes duplicados.",
            409,
            duplicates=result,
        )


def _validate_responsibles_for_minor(
    birth_date: date,
    responsibles: list,
) -> None:
    if not is_minor(birth_date):
        return
    primary_count = sum(1 for item in responsibles if item.is_primary)
    if primary_count != 1:
        raise PatientManagementError(
            "Un paciente menor de edad requiere un responsable principal.",
            422,
        )


def _apply_patient_data(patient: Patient, payload) -> None:
    patient.first_names = payload.first_names
    patient.last_names = payload.last_names
    patient.document_type = payload.document_type
    patient.document = payload.document
    patient.mobile = payload.mobile
    patient.birth_date = payload.birth_date
    patient.sex = payload.sex
    patient.email = payload.email
    patient.alternate_phone = payload.alternate_phone
    patient.address = payload.address
    patient.city = payload.city
    patient.department = payload.department
    patient.emergency_contact_name = payload.emergency_contact_name
    patient.emergency_contact_mobile = payload.emergency_contact_mobile
    patient.administrative_notes = payload.administrative_notes
    _refresh_normalized_fields(patient)


def _new_responsible(
    *,
    company_id: UUID,
    patient_id: UUID,
    payload,
    actor_id: UUID,
) -> PatientResponsible:
    return PatientResponsible(
        company_id=company_id,
        patient_id=patient_id,
        name=payload.name,
        document_type=payload.document_type,
        document=payload.document,
        normalized_document=normalize_document(payload.document),
        relationship=payload.relationship,
        mobile=payload.mobile,
        email=normalize_email(payload.email),
        is_primary=payload.is_primary,
        created_by=actor_id,
        updated_by=actor_id,
    )


def create_patient(
    session: Session,
    context: AuthContext,
    payload: PatientCreateRequest,
    metadata: RequestMetadata,
) -> PatientResponse:
    _validate_responsibles_for_minor(payload.birth_date, payload.responsibles)
    if sum(1 for item in payload.responsibles if item.is_primary) > 1:
        raise PatientManagementError(
            "Solo puede existir un responsable principal.",
            422,
        )
    duplicates = check_duplicates(
        session,
        context,
        DuplicateCheckRequest(
            first_names=payload.first_names,
            last_names=payload.last_names,
            document_type=payload.document_type,
            document=payload.document,
            mobile=payload.mobile,
            birth_date=payload.birth_date,
        ),
    )
    _validate_duplicate_result(
        duplicates,
        acknowledged=payload.acknowledge_duplicate_warning,
    )
    patient = Patient(
        company_id=context.user.company_id,
        first_names=payload.first_names,
        last_names=payload.last_names,
        document_type=payload.document_type,
        document=payload.document,
        mobile=payload.mobile,
        status="Activo",
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    _apply_patient_data(patient, payload)
    session.add(patient)
    session.flush()
    for responsible in payload.responsibles:
        session.add(
            _new_responsible(
                company_id=context.user.company_id,
                patient_id=patient.id,
                payload=responsible,
                actor_id=context.user.id,
            )
        )
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_CREATED",
        detail={"profile_complete": patient.profile_complete},
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise PatientManagementError(
            "Ya existe un paciente con ese tipo y número de documento.",
            409,
        )
    return _patient_response(session, patient)


def create_quick_patient(
    session: Session,
    context: AuthContext,
    payload,
    metadata: RequestMetadata,
) -> PatientResponse:
    duplicates = check_duplicates(
        session,
        context,
        DuplicateCheckRequest(
            first_names=payload.first_names,
            last_names=payload.last_names,
            document_type=payload.document_type,
            document=payload.document,
            mobile=payload.mobile,
        ),
    )
    _validate_duplicate_result(
        duplicates,
        acknowledged=payload.acknowledge_duplicate_warning,
    )
    patient = Patient(
        company_id=context.user.company_id,
        first_names=payload.first_names,
        last_names=payload.last_names,
        document_type=payload.document_type,
        document=payload.document,
        mobile=payload.mobile,
        birth_date=None,
        status="Activo",
        profile_complete=False,
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    _refresh_normalized_fields(patient)
    session.add(patient)
    session.flush()
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_QUICK_CREATED",
        detail={"profile_complete": False},
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise PatientManagementError(
            "Ya existe un paciente con ese tipo y número de documento.",
            409,
        )
    return _patient_response(session, patient)


def update_patient(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: PatientUpdateRequest,
    metadata: RequestMetadata,
) -> PatientResponse:
    patient = _get_patient(session, context, patient_id, lock=True)
    duplicates = check_duplicates(
        session,
        context,
        DuplicateCheckRequest(
            first_names=payload.first_names,
            last_names=payload.last_names,
            document_type=payload.document_type,
            document=payload.document,
            mobile=payload.mobile,
            birth_date=payload.birth_date,
            exclude_patient_id=patient.id,
        ),
    )
    _validate_duplicate_result(
        duplicates,
        acknowledged=payload.acknowledge_duplicate_warning,
    )
    if is_minor(payload.birth_date):
        responsibles = _active_responsibles(session, patient.id)
        if sum(1 for item in responsibles if item.is_primary) != 1:
            raise PatientManagementError(
                "Un paciente menor de edad requiere un responsable principal.",
                422,
            )
    previous_document = {
        "type": patient.document_type,
        "value": patient.document,
    }
    _apply_patient_data(patient, payload)
    patient.updated_by = context.user.id
    detail: dict = {"profile_complete": patient.profile_complete}
    if (
        previous_document["type"] != patient.document_type
        or previous_document["value"] != patient.document
    ):
        detail["document_changed"] = True
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_UPDATED",
        detail=detail,
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise PatientManagementError(
            "Ya existe un paciente con ese tipo y número de documento.",
            409,
        )
    return _patient_response(session, patient)


def get_patient_detail(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> PatientResponse:
    return _patient_response(session, _get_patient(session, context, patient_id))


def _appointment_response(row) -> PatientAppointmentResponse:
    appointment, dentist, site, appointment_type = row
    return PatientAppointmentResponse(
        id=appointment.id,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        status=appointment.status,
        reason=appointment.reason,
        is_overbook=appointment.is_overbook,
        confirmation_method=appointment.confirmation_method,
        dentist_name=dentist.name,
        site_name=site.name,
        appointment_type_name=appointment_type.name,
        origin_appointment_id=appointment.origin_appointment_id,
    )


def _appointment_statement(context: AuthContext, patient_id: UUID):
    return (
        select(Appointment, Dentist, Site, AppointmentType)
        .join(Dentist, Dentist.id == Appointment.dentist_id)
        .join(Site, Site.id == Appointment.site_id)
        .join(
            AppointmentType,
            AppointmentType.id == Appointment.appointment_type_id,
        )
        .where(
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == patient_id,
            Appointment.is_active.is_(True),
        )
    )


def get_patient_appointments(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    page: int,
    page_size: int,
) -> PatientAppointmentsResponse:
    _get_patient(session, context, patient_id)
    total = int(
        session.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.company_id == context.user.company_id,
                Appointment.patient_id == patient_id,
                Appointment.is_active.is_(True),
            )
        )
        or 0
    )
    rows = session.execute(
        _appointment_statement(context, patient_id)
        .order_by(Appointment.starts_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return PatientAppointmentsResponse(
        items=[_appointment_response(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
        pages=max(1, math.ceil(total / page_size)),
    )


def _one_appointment(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    future: bool,
) -> PatientAppointmentResponse | None:
    now = datetime.now(timezone.utc)
    statement = _appointment_statement(context, patient_id)
    if future:
        statement = statement.where(
            Appointment.starts_at >= now,
            Appointment.status.in_(ACTIVE_FUTURE_APPOINTMENT_STATES),
        ).order_by(Appointment.starts_at.asc())
    else:
        statement = statement.where(Appointment.starts_at < now).order_by(
            Appointment.starts_at.desc()
        )
    row = session.execute(statement.limit(1)).one_or_none()
    return _appointment_response(row) if row else None


def get_patient_summary(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> PatientSummaryResponse:
    patient = _get_patient(session, context, patient_id)
    now = datetime.now(timezone.utc)
    appointment_count = int(
        session.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.company_id == context.user.company_id,
                Appointment.patient_id == patient_id,
                Appointment.is_active.is_(True),
            )
        )
        or 0
    )
    future_count = int(
        session.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.company_id == context.user.company_id,
                Appointment.patient_id == patient_id,
                Appointment.is_active.is_(True),
                Appointment.starts_at >= now,
                Appointment.status.in_(ACTIVE_FUTURE_APPOINTMENT_STATES),
            )
        )
        or 0
    )
    return PatientSummaryResponse(
        patient=_patient_response(session, patient),
        next_appointment=_one_appointment(
            session, context, patient_id, future=True
        ),
        last_appointment=_one_appointment(
            session, context, patient_id, future=False
        ),
        appointment_count=appointment_count,
        active_future_appointment_count=future_count,
    )


def list_patients(
    session: Session,
    context: AuthContext,
    *,
    search: str | None,
    status: str | None,
    incomplete: bool | None,
    minor: bool | None,
    page: int,
    page_size: int,
) -> PatientListResponse:
    filters = [Patient.company_id == context.user.company_id]
    if search:
        normalized = normalize_text(search)
        digits = normalize_phone(search)
        filters.append(
            or_(
                Patient.search_text.ilike(f"%{normalized}%"),
                Patient.normalized_mobile.ilike(f"%{digits}%")
                if digits
                else False,
            )
        )
    if status:
        filters.append(Patient.status == status)
    if incomplete is not None:
        filters.append(Patient.profile_complete.is_(not incomplete))
    if minor is not None:
        today = date.today()
        try:
            majority_cutoff = today.replace(year=today.year - 18)
        except ValueError:
            majority_cutoff = today.replace(
                year=today.year - 18,
                day=28,
            )
        if minor:
            filters.extend(
                [
                    Patient.birth_date.is_not(None),
                    Patient.birth_date > majority_cutoff,
                ]
            )
        else:
            filters.extend(
                [
                    Patient.birth_date.is_not(None),
                    Patient.birth_date <= majority_cutoff,
                ]
            )
    total = int(
        session.scalar(
            select(func.count()).select_from(Patient).where(*filters)
        )
        or 0
    )
    patients = list(
        session.scalars(
            select(Patient)
            .where(*filters)
            .order_by(Patient.first_names, Patient.last_names)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    items: list[PatientListItemResponse] = []
    for patient in patients:
        next_appointment = _one_appointment(
            session, context, patient.id, future=True
        )
        last_appointment = _one_appointment(
            session, context, patient.id, future=False
        )
        items.append(
            PatientListItemResponse(
                id=patient.id,
                full_name=f"{patient.first_names} {patient.last_names}".strip(),
                document_type=patient.document_type,
                document=patient.document,
                mobile=patient.mobile,
                age=calculate_age(patient.birth_date),
                is_minor=is_minor(patient.birth_date),
                status=patient.status,
                profile_complete=patient.profile_complete,
                next_appointment_at=(
                    next_appointment.starts_at if next_appointment else None
                ),
                last_appointment_at=(
                    last_appointment.starts_at if last_appointment else None
                ),
            )
        )
    return PatientListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=max(1, math.ceil(total / page_size)),
    )


def change_patient_status(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    active: bool,
    metadata: RequestMetadata,
) -> PatientActionResponse:
    patient = _get_patient(session, context, patient_id, lock=True)
    if not active:
        now = datetime.now(timezone.utc)
        future_count = int(
            session.scalar(
                select(func.count())
                .select_from(Appointment)
                .where(
                    Appointment.company_id == context.user.company_id,
                    Appointment.patient_id == patient.id,
                    Appointment.is_active.is_(True),
                    Appointment.starts_at >= now,
                    Appointment.status.in_(ACTIVE_FUTURE_APPOINTMENT_STATES),
                )
            )
            or 0
        )
        if future_count:
            raise PatientManagementError(
                "No puedes desactivar un paciente con citas futuras activas.",
                409,
            )
    patient.status = "Activo" if active else "Inactivo"
    patient.is_active = active
    patient.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_REACTIVATED" if active else "PATIENT_DEACTIVATED",
    )
    session.commit()
    return PatientActionResponse(
        message="Paciente reactivado." if active else "Paciente desactivado.",
        patient=_patient_response(session, patient),
    )


def list_responsibles(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> ResponsibleListResponse:
    _get_patient(session, context, patient_id)
    return ResponsibleListResponse(
        items=[
            _responsible_response(item)
            for item in _active_responsibles(session, patient_id)
        ]
    )


def create_responsible(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: ResponsibleCreateRequest,
    metadata: RequestMetadata,
) -> ResponsibleResponse:
    patient = _get_patient(session, context, patient_id, lock=True)
    if payload.is_primary:
        for current in _active_responsibles(session, patient.id):
            current.is_primary = False
            current.updated_by = context.user.id
        session.flush()
    responsible = _new_responsible(
        company_id=context.user.company_id,
        patient_id=patient.id,
        payload=payload,
        actor_id=context.user.id,
    )
    session.add(responsible)
    session.flush()
    if is_minor(patient.birth_date) and not any(
        item.is_primary
        for item in _active_responsibles(session, patient.id)
    ):
        raise PatientManagementError(
            "Un paciente menor de edad requiere un responsable principal.",
            422,
        )
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_RESPONSIBLE_CREATED",
        detail={"responsible_id": str(responsible.id)},
    )
    session.commit()
    return _responsible_response(responsible)


def _get_responsible(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    responsible_id: UUID,
    *,
    lock: bool = False,
) -> PatientResponsible:
    _get_patient(session, context, patient_id)
    statement = select(PatientResponsible).where(
        PatientResponsible.id == responsible_id,
        PatientResponsible.patient_id == patient_id,
        PatientResponsible.company_id == context.user.company_id,
        PatientResponsible.is_active.is_(True),
    )
    if lock:
        statement = statement.with_for_update()
    responsible = session.scalar(statement)
    if responsible is None:
        raise PatientManagementError("Responsable no encontrado.", 404)
    return responsible


def update_responsible(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    responsible_id: UUID,
    payload: ResponsibleUpdateRequest,
    metadata: RequestMetadata,
) -> ResponsibleResponse:
    patient = _get_patient(session, context, patient_id, lock=True)
    responsible = _get_responsible(
        session, context, patient_id, responsible_id, lock=True
    )
    if payload.is_primary:
        for current in _active_responsibles(session, patient.id):
            if current.id != responsible.id:
                current.is_primary = False
                current.updated_by = context.user.id
        session.flush()
    elif responsible.is_primary and is_minor(patient.birth_date):
        raise PatientManagementError(
            "El menor debe conservar un responsable principal.",
            409,
        )
    responsible.name = payload.name
    responsible.document_type = payload.document_type
    responsible.document = payload.document
    responsible.normalized_document = normalize_document(payload.document)
    responsible.relationship = payload.relationship
    responsible.mobile = payload.mobile
    responsible.email = normalize_email(payload.email)
    responsible.is_primary = payload.is_primary
    responsible.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_RESPONSIBLE_UPDATED",
        detail={"responsible_id": str(responsible.id)},
    )
    session.commit()
    return _responsible_response(responsible)


def delete_responsible(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    responsible_id: UUID,
    metadata: RequestMetadata,
) -> ResponsibleListResponse:
    patient = _get_patient(session, context, patient_id, lock=True)
    responsible = _get_responsible(
        session, context, patient_id, responsible_id, lock=True
    )
    if responsible.is_primary and is_minor(patient.birth_date):
        raise PatientManagementError(
            "No puedes eliminar el responsable principal de un menor.",
            409,
        )
    responsible.is_active = False
    responsible.is_primary = False
    responsible.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        patient_id=patient.id,
        action="PATIENT_RESPONSIBLE_DELETED",
        detail={"responsible_id": str(responsible.id)},
    )
    session.commit()
    return list_responsibles(session, context, patient.id)
