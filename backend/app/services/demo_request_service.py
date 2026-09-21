from collections import defaultdict, deque
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import logging
import re
from threading import Lock
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import normalize_email, utc_now
from app.models.associations import UserRole
from app.models.audit_event import AuditEvent
from app.models.demo_request import DemoRequest, DemoRequestNote
from app.models.role import Role
from app.models.user import User
from app.schemas.demo_request_schema import (
    DemoRequestAssignmentUpdate,
    DemoRequestDetail,
    DemoRequestListItem,
    DemoRequestListResponse,
    DemoRequestNoteCreate,
    DemoRequestNoteResponse,
    DemoRequestOwner,
    DemoRequestOwnersResponse,
    DemoRequestScheduleUpdate,
    DemoRequestStatusUpdate,
    PublicDemoRequestCreate,
    PublicDemoRequestResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.email_service import EmailDelivery, get_email_provider


logger = logging.getLogger(__name__)
SUCCESS_MESSAGE = (
    "Gracias por tu interés en Dentia. Revisaremos tu solicitud y te "
    "contactaremos para coordinar una demostración."
)


class DemoRequestError(RuntimeError):
    def __init__(self, message: str, status_code: int, code: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class _RateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, now: datetime) -> None:
        cutoff = now - timedelta(seconds=settings.demo_request_rate_limit_window_seconds)
        with self._lock:
            events = self._events[key]
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= settings.demo_request_rate_limit_max:
                raise DemoRequestError(
                    "Has realizado varios intentos. Espera unos minutos e inténtalo nuevamente.",
                    429,
                    "DEMO_REQUEST_RATE_LIMITED",
                )
            events.append(now)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


_rate_limiter = _RateLimiter()
_control_characters = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_html_tags = re.compile(r"<[^>]*>")
_whitespace = re.compile(r"[ \t]+")


def reset_demo_request_throttle_for_tests() -> None:
    if settings.app_env != "test":
        raise RuntimeError("El rate limiter solo se puede reiniciar en pruebas.")
    _rate_limiter.reset()


def _plain_text(value: str | None, *, multiline: bool = False) -> str | None:
    if value is None:
        return None
    cleaned = _control_characters.sub("", value)
    cleaned = _html_tags.sub("", cleaned)
    if multiline:
        lines = [_whitespace.sub(" ", line).strip() for line in cleaned.splitlines()]
        cleaned = "\n".join(line for line in lines if line).strip()
    else:
        cleaned = _whitespace.sub(" ", cleaned).strip()
    return cleaned or None


def _client_key(metadata: RequestMetadata) -> str:
    value = metadata.ip_address or "unknown"
    return hashlib.sha256(
        f"{settings.jwt_secret}:demo-rate:{value}".encode("utf-8")
    ).hexdigest()


def _submission_fingerprint(payload: PublicDemoRequestCreate, client_key: str) -> str:
    parts = (
        payload.first_name.casefold(),
        payload.last_name.casefold(),
        normalize_email(payload.email),
        payload.phone,
        payload.country.casefold(),
        payload.city.casefold(),
        payload.practice_type,
        str(payload.dentist_count),
        (payload.message or "").casefold(),
        client_key,
    )
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _audit(
    session: Session,
    *,
    demo_request_id: UUID,
    action: str,
    detail: dict | None = None,
    context: AuthContext | None = None,
    metadata: RequestMetadata | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=None,
            user_id=context.user.id if context else None,
            session_id=context.auth_session.id if context else None,
            entity="demo_request",
            entity_id=demo_request_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            # The public creation audit intentionally does not retain visitor IP
            # or user-agent. Authenticated platform actions follow the existing
            # administrative audit policy.
            ip_address=metadata.ip_address if context and metadata else None,
            user_agent=metadata.user_agent if context and metadata else None,
        )
    )


def _notification_subject(item: DemoRequest) -> str:
    country = {"CO": "Colombia", "CL": "Chile", "OTHER": "Otro"}.get(
        item.country, item.country
    )
    practice = {
        "INDEPENDENT_DENTIST": "Odontólogo independiente",
        "DENTAL_OFFICE": "Consultorio",
        "DENTAL_CLINIC": "Clínica",
    }[item.practice_type]
    return (
        f"Nueva solicitud de demo — {country} — {practice} — "
        f"{item.dentist_count} odontólogo(s)"
    )


def _notification_body(item: DemoRequest) -> str:
    return "\n".join(
        (
            "Dentia recibió una nueva solicitud de demostración.",
            "",
            f"Nombre: {item.first_name} {item.last_name}",
            f"País / ciudad: {item.country} / {item.city}",
            f"Email: {item.email}",
            f"Teléfono: {item.phone}",
            f"Tipo de práctica: {item.practice_type}",
            f"Odontólogos: {item.dentist_count}",
            f"Mensaje: {item.message or 'Sin mensaje'}",
            f"Fecha UTC: {item.created_at.astimezone(timezone.utc).isoformat()}",
            "",
            "Gestiona esta solicitud desde Administración → Solicitudes de demo.",
        )
    )


def _notify_internal_recipients(session: Session, item: DemoRequest) -> None:
    recipients = settings.demo_request_notification_recipients
    item.notification_attempted_at = utc_now()
    if not recipients:
        item.notification_status = "NOT_CONFIGURED"
        item.notification_error_code = None
        session.commit()
        logger.info("demo_request_notification_not_configured")
        return
    try:
        provider = get_email_provider()
        for recipient in recipients:
            provider.send(
                EmailDelivery(
                    recipient=recipient,
                    sender=settings.demo_request_from_email,
                    subject=_notification_subject(item),
                    body=_notification_body(item),
                )
            )
        item.notification_status = "SENT"
        item.notification_error_code = None
        _audit(
            session,
            demo_request_id=item.id,
            action="DEMO_REQUEST_NOTIFICATION_SENT",
            detail={"recipient_count": len(recipients)},
        )
        session.commit()
        logger.info("demo_request_notification_sent")
    except Exception:
        item.notification_status = "FAILED"
        item.notification_error_code = "DELIVERY_FAILED"
        _audit(
            session,
            demo_request_id=item.id,
            action="DEMO_REQUEST_NOTIFICATION_FAILED",
            detail={"error_code": "DELIVERY_FAILED"},
        )
        session.commit()
        logger.warning("demo_request_notification_failed")


def create_public_demo_request(
    session: Session,
    payload: PublicDemoRequestCreate,
    metadata: RequestMetadata,
) -> PublicDemoRequestResponse:
    if payload.company_website:
        logger.info("demo_request_honeypot_rejected")
        return PublicDemoRequestResponse(message=SUCCESS_MESSAGE)

    now = utc_now()
    client_key = _client_key(metadata)
    fingerprint = _submission_fingerprint(payload, client_key)
    advisory_key = int(fingerprint[:16], 16)
    if advisory_key >= 2**63:
        advisory_key -= 2**64
    session.execute(select(func.pg_advisory_xact_lock(advisory_key)))
    duplicate_cutoff = now - timedelta(
        seconds=settings.demo_request_duplicate_window_seconds
    )
    duplicate = session.scalar(
        select(DemoRequest.id).where(
            DemoRequest.submission_fingerprint == fingerprint,
            DemoRequest.created_at >= duplicate_cutoff,
            DemoRequest.deleted_at.is_(None),
        )
    )
    if duplicate is not None:
        logger.info("demo_request_duplicate_suppressed")
        return PublicDemoRequestResponse(message=SUCCESS_MESSAGE)
    _rate_limiter.check(client_key, now)

    item = DemoRequest(
        first_name=_plain_text(payload.first_name) or "",
        last_name=_plain_text(payload.last_name) or "",
        email=normalize_email(payload.email),
        normalized_email=normalize_email(payload.email),
        phone=_plain_text(payload.phone) or "",
        country=_plain_text(payload.country) or "OTHER",
        city=_plain_text(payload.city) or "",
        practice_type=payload.practice_type,
        dentist_count=payload.dentist_count,
        message=_plain_text(payload.message, multiline=True),
        source="WEBSITE",
        status="NEW",
        consent_at=now,
        consent_version=(
            payload.consent_version or settings.demo_request_consent_version
        ),
        submission_fingerprint=fingerprint,
    )
    session.add(item)
    session.flush()
    _audit(
        session,
        demo_request_id=item.id,
        action="DEMO_REQUEST_CREATED",
        detail={
            "source": item.source,
            "status": item.status,
            "country": item.country,
            "practice_type": item.practice_type,
            "dentist_count": item.dentist_count,
            "consent_version": item.consent_version,
        },
    )
    session.commit()
    session.refresh(item)
    logger.info("demo_request_created")
    _notify_internal_recipients(session, item)
    return PublicDemoRequestResponse(message=SUCCESS_MESSAGE)


def _platform_users_query():
    return (
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            Role.code == "PLATFORM_ADMIN",
            Role.is_active.is_(True),
            UserRole.is_active.is_(True),
            User.is_active.is_(True),
            User.status == "Activo",
        )
        .distinct()
    )


def list_demo_request_owners(session: Session) -> DemoRequestOwnersResponse:
    users = session.scalars(_platform_users_query().order_by(User.name)).all()
    return DemoRequestOwnersResponse(
        items=[DemoRequestOwner(id=user.id, name=user.name, email=user.email) for user in users]
    )


def _owner(session: Session, user_id: UUID | None) -> DemoRequestOwner | None:
    if user_id is None:
        return None
    user = session.scalar(_platform_users_query().where(User.id == user_id))
    if user is None:
        return None
    return DemoRequestOwner(id=user.id, name=user.name, email=user.email)


def _list_item(session: Session, item: DemoRequest) -> DemoRequestListItem:
    return DemoRequestListItem(
        id=item.id,
        first_name=item.first_name,
        last_name=item.last_name,
        email=item.email,
        country=item.country,
        city=item.city,
        practice_type=item.practice_type,
        dentist_count=item.dentist_count,
        source=item.source,
        status=item.status,
        assigned_to=_owner(session, item.assigned_to_user_id),
        scheduled_at=item.scheduled_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        row_version=item.row_version,
    )


def list_demo_requests(
    session: Session,
    *,
    search: str | None,
    status: str | None,
    country: str | None,
    assigned_to_user_id: UUID | None,
    created_from: date | None,
    created_to: date | None,
    page: int,
    page_size: int,
) -> DemoRequestListResponse:
    filters = [DemoRequest.deleted_at.is_(None)]
    if status:
        filters.append(DemoRequest.status == status)
    if country:
        filters.append(DemoRequest.country == country)
    if assigned_to_user_id:
        filters.append(DemoRequest.assigned_to_user_id == assigned_to_user_id)
    if created_from:
        filters.append(
            DemoRequest.created_at >= datetime.combine(created_from, time.min, timezone.utc)
        )
    if created_to:
        filters.append(
            DemoRequest.created_at
            < datetime.combine(created_to + timedelta(days=1), time.min, timezone.utc)
        )
    normalized_search = _plain_text(search)
    if normalized_search:
        pattern = f"%{normalized_search.replace('%', '').replace('_', '')}%"
        filters.append(
            or_(
                DemoRequest.first_name.ilike(pattern),
                DemoRequest.last_name.ilike(pattern),
                DemoRequest.normalized_email.ilike(pattern.casefold()),
            )
        )
    total = int(
        session.scalar(select(func.count()).select_from(DemoRequest).where(*filters))
        or 0
    )
    items = session.scalars(
        select(DemoRequest)
        .where(*filters)
        .order_by(DemoRequest.created_at.desc(), DemoRequest.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return DemoRequestListResponse(
        items=[_list_item(session, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def _get_item(session: Session, demo_request_id: UUID, *, lock: bool = False) -> DemoRequest:
    query = select(DemoRequest).where(
        DemoRequest.id == demo_request_id,
        DemoRequest.deleted_at.is_(None),
    )
    if lock:
        query = query.with_for_update()
    item = session.scalar(query)
    if item is None:
        raise DemoRequestError("Solicitud de demo no encontrada.", 404, "DEMO_REQUEST_NOT_FOUND")
    return item


def _notes(session: Session, demo_request_id: UUID) -> list[DemoRequestNoteResponse]:
    rows = session.execute(
        select(DemoRequestNote, User)
        .join(User, User.id == DemoRequestNote.author_user_id)
        .where(DemoRequestNote.demo_request_id == demo_request_id)
        .order_by(DemoRequestNote.created_at.desc(), DemoRequestNote.id.desc())
    ).all()
    return [
        DemoRequestNoteResponse(
            id=note.id,
            text=note.text,
            author=DemoRequestOwner(id=author.id, name=author.name, email=author.email),
            created_at=note.created_at,
        )
        for note, author in rows
    ]


def get_demo_request(session: Session, demo_request_id: UUID) -> DemoRequestDetail:
    item = _get_item(session, demo_request_id)
    return DemoRequestDetail(
        **_list_item(session, item).model_dump(),
        phone=item.phone,
        message=item.message,
        timezone=item.timezone,
        meeting_url=item.meeting_url,
        contacted_at=item.contacted_at,
        converted_at=item.converted_at,
        consent_at=item.consent_at,
        consent_version=item.consent_version,
        notification_status=item.notification_status,
        notes=_notes(session, item.id),
    )


def _ensure_version(item: DemoRequest, row_version: int) -> None:
    if item.row_version != row_version:
        raise DemoRequestError(
            "La solicitud cambió mientras la editabas. Recarga e intenta nuevamente.",
            409,
            "DEMO_REQUEST_VERSION_CONFLICT",
        )


def _valid_owner(session: Session, user_id: UUID | None) -> User | None:
    if user_id is None:
        return None
    user = session.scalar(_platform_users_query().where(User.id == user_id))
    if user is None:
        raise DemoRequestError(
            "El responsable seleccionado no es un usuario válido de plataforma.",
            422,
            "DEMO_REQUEST_INVALID_OWNER",
        )
    return user


def _append_note(
    session: Session,
    item: DemoRequest,
    context: AuthContext,
    text: str,
) -> DemoRequestNote:
    note = DemoRequestNote(
        demo_request_id=item.id,
        author_user_id=context.user.id,
        text=_plain_text(text, multiline=True) or "",
    )
    session.add(note)
    return note


def assign_demo_request(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    demo_request_id: UUID,
    payload: DemoRequestAssignmentUpdate,
) -> DemoRequestDetail:
    item = _get_item(session, demo_request_id, lock=True)
    _ensure_version(item, payload.row_version)
    owner = _valid_owner(session, payload.assigned_to_user_id)
    previous = item.assigned_to_user_id
    item.assigned_to_user_id = owner.id if owner else None
    item.row_version += 1
    _audit(
        session,
        demo_request_id=item.id,
        action="DEMO_REQUEST_ASSIGNED",
        detail={
            "previous_assigned_to_user_id": str(previous) if previous else None,
            "assigned_to_user_id": str(item.assigned_to_user_id) if item.assigned_to_user_id else None,
        },
        context=context,
        metadata=metadata,
    )
    session.commit()
    return get_demo_request(session, item.id)


_ALLOWED_TRANSITIONS = {
    "NEW": {"CONTACTED", "DEMO_SCHEDULED", "NOT_CONTINUING"},
    "CONTACTED": {"DEMO_SCHEDULED", "NOT_CONTINUING"},
    "DEMO_SCHEDULED": {"DEMO_COMPLETED", "NOT_CONTINUING"},
    "DEMO_COMPLETED": {"CONVERTED", "NOT_CONTINUING", "DEMO_SCHEDULED"},
    "CONVERTED": set(),
    "NOT_CONTINUING": set(),
}


def update_demo_request_status(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    demo_request_id: UUID,
    payload: DemoRequestStatusUpdate,
) -> DemoRequestDetail:
    item = _get_item(session, demo_request_id, lock=True)
    _ensure_version(item, payload.row_version)
    if payload.status == item.status:
        return get_demo_request(session, item.id)
    if payload.status not in _ALLOWED_TRANSITIONS[item.status]:
        raise DemoRequestError(
            "La transición de estado solicitada no es válida.",
            409,
            "DEMO_REQUEST_INVALID_TRANSITION",
        )
    previous = item.status
    item.status = payload.status
    now = utc_now()
    if payload.status == "CONTACTED" and item.contacted_at is None:
        item.contacted_at = now
    if payload.status == "CONVERTED":
        item.converted_at = now
    if payload.reason:
        _append_note(session, item, context, payload.reason)
    item.row_version += 1
    _audit(
        session,
        demo_request_id=item.id,
        action=(
            "DEMO_REQUEST_CONVERTED"
            if payload.status == "CONVERTED"
            else "DEMO_REQUEST_CLOSED"
            if payload.status == "NOT_CONTINUING"
            else "DEMO_REQUEST_STATUS_CHANGED"
        ),
        detail={
            "previous_status": previous,
            "new_status": item.status,
            "reason_recorded": bool(payload.reason),
        },
        context=context,
        metadata=metadata,
    )
    session.commit()
    return get_demo_request(session, item.id)


def schedule_demo_request(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    demo_request_id: UUID,
    payload: DemoRequestScheduleUpdate,
) -> DemoRequestDetail:
    item = _get_item(session, demo_request_id, lock=True)
    _ensure_version(item, payload.row_version)
    if item.status not in {"NEW", "CONTACTED", "DEMO_SCHEDULED", "DEMO_COMPLETED"}:
        raise DemoRequestError(
            "No se puede agendar una demo para esta solicitud.",
            409,
            "DEMO_REQUEST_CANNOT_SCHEDULE",
        )
    owner_id = payload.assigned_to_user_id or item.assigned_to_user_id
    owner = _valid_owner(session, owner_id)
    if owner is None:
        raise DemoRequestError(
            "Selecciona un responsable para agendar la demo.",
            422,
            "DEMO_REQUEST_OWNER_REQUIRED",
        )
    previous_status = item.status
    item.assigned_to_user_id = owner.id
    item.scheduled_at = payload.scheduled_at
    item.timezone = payload.timezone
    item.meeting_url = _plain_text(payload.meeting_url)
    item.status = "DEMO_SCHEDULED"
    if payload.note:
        _append_note(session, item, context, payload.note)
    item.row_version += 1
    _audit(
        session,
        demo_request_id=item.id,
        action="DEMO_REQUEST_SCHEDULED",
        detail={
            "previous_status": previous_status,
            "new_status": item.status,
            "scheduled_at": item.scheduled_at.isoformat(),
            "timezone": item.timezone,
            "assigned_to_user_id": str(owner.id),
            "meeting_url_recorded": bool(item.meeting_url),
        },
        context=context,
        metadata=metadata,
    )
    session.commit()
    return get_demo_request(session, item.id)


def add_demo_request_note(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    demo_request_id: UUID,
    payload: DemoRequestNoteCreate,
) -> DemoRequestDetail:
    item = _get_item(session, demo_request_id, lock=True)
    _ensure_version(item, payload.row_version)
    note = _append_note(session, item, context, payload.text)
    item.row_version += 1
    session.flush()
    _audit(
        session,
        demo_request_id=item.id,
        action="DEMO_REQUEST_NOTE_ADDED",
        detail={"note_id": str(note.id)},
        context=context,
        metadata=metadata,
    )
    session.commit()
    return get_demo_request(session, item.id)
