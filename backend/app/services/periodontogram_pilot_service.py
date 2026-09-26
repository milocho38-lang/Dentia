from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import Dentist, DentistSite
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.periodontogram import (
    PeriodontogramPilotCompanyGate,
    PeriodontogramPilotDentistAuthorization,
)
from app.models.user import User
from app.schemas.periodontogram_schema import (
    PeriodontogramPilotAccessResponse,
    PeriodontogramPilotDentistResponse,
    PeriodontogramPilotResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import is_authorized_site


class PeriodontogramPilotError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _company(
    session: Session,
    company_id: UUID,
    *,
    lock: bool = False,
) -> Company:
    statement = select(Company).where(Company.id == company_id)
    if lock:
        statement = statement.with_for_update()
    company = session.scalar(statement)
    if company is None:
        raise PeriodontogramPilotError(
            "PERIODONTOGRAM_PILOT_COMPANY_NOT_FOUND",
            "Empresa no encontrada.",
            404,
        )
    return company


def _gate(
    session: Session,
    company_id: UUID,
    *,
    lock: bool = False,
) -> PeriodontogramPilotCompanyGate | None:
    statement = select(PeriodontogramPilotCompanyGate).where(
        PeriodontogramPilotCompanyGate.company_id == company_id
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _active_authorization(
    session: Session,
    company_id: UUID,
    dentist_id: UUID,
    *,
    lock: bool = False,
) -> PeriodontogramPilotDentistAuthorization | None:
    statement = select(PeriodontogramPilotDentistAuthorization).where(
        PeriodontogramPilotDentistAuthorization.company_id == company_id,
        PeriodontogramPilotDentistAuthorization.dentist_id == dentist_id,
        PeriodontogramPilotDentistAuthorization.is_active.is_(True),
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _dentist_and_user(
    session: Session,
    company_id: UUID,
    dentist_id: UUID,
    *,
    lock: bool = False,
) -> tuple[Dentist, User | None]:
    statement = select(Dentist).where(
        Dentist.id == dentist_id,
        Dentist.company_id == company_id,
    )
    if lock:
        statement = statement.with_for_update()
    dentist = session.scalar(statement)
    if dentist is None:
        raise PeriodontogramPilotError(
            "PERIODONTOGRAM_PILOT_DENTIST_NOT_FOUND",
            "El odontólogo no pertenece a la empresa.",
            404,
        )
    user = session.get(User, dentist.user_id) if dentist.user_id else None
    return dentist, user


def _operational(dentist: Dentist, user: User | None) -> bool:
    return bool(
        dentist.is_active
        and dentist.status == "Activo"
        and user is not None
        and user.company_id == dentist.company_id
        and user.is_active
        and user.status == "Activo"
    )


def _authorization_response(
    dentist: Dentist,
    user: User | None,
    authorization: PeriodontogramPilotDentistAuthorization | None,
) -> PeriodontogramPilotDentistResponse:
    return PeriodontogramPilotDentistResponse(
        authorization_id=authorization.id if authorization else None,
        dentist_id=dentist.id,
        user_id=dentist.user_id,
        dentist_name=dentist.name,
        dentist_status=dentist.status,
        dentist_is_active=dentist.is_active,
        user_is_active=bool(
            user
            and user.company_id == dentist.company_id
            and user.is_active
            and user.status == "Activo"
        ),
        authorized=bool(authorization and authorization.is_active),
        authorized_at=authorization.authorized_at if authorization else None,
        authorized_by_user_id=(
            authorization.authorized_by_user_id if authorization else None
        ),
        revoked_at=authorization.revoked_at if authorization else None,
        revoked_by_user_id=(
            authorization.revoked_by_user_id if authorization else None
        ),
    )


def _pilot_response(
    session: Session,
    company_id: UUID,
) -> PeriodontogramPilotResponse:
    gate = _gate(session, company_id)
    dentists = list(
        session.scalars(
            select(Dentist)
            .where(Dentist.company_id == company_id)
            .order_by(Dentist.name)
        )
    )
    active_authorizations = {
        authorization.dentist_id: authorization
        for authorization in session.scalars(
            select(PeriodontogramPilotDentistAuthorization).where(
                PeriodontogramPilotDentistAuthorization.company_id == company_id,
                PeriodontogramPilotDentistAuthorization.is_active.is_(True),
            )
        )
    }
    return PeriodontogramPilotResponse(
        company_id=company_id,
        enabled=bool(gate and gate.is_enabled),
        enabled_at=gate.enabled_at if gate else None,
        enabled_by_user_id=gate.enabled_by_user_id if gate else None,
        disabled_at=gate.disabled_at if gate else None,
        disabled_by_user_id=gate.disabled_by_user_id if gate else None,
        dentists=[
            _authorization_response(
                dentist,
                session.get(User, dentist.user_id) if dentist.user_id else None,
                active_authorizations.get(dentist.id),
            )
            for dentist in dentists
        ],
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    company_id: UUID,
    entity: str,
    entity_id: UUID,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def get_platform_periodontogram_pilot(
    session: Session,
    company_id: UUID,
) -> PeriodontogramPilotResponse:
    _company(session, company_id)
    return _pilot_response(session, company_id)


def update_platform_periodontogram_pilot(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    *,
    enabled: bool,
    metadata: RequestMetadata,
) -> PeriodontogramPilotResponse:
    company = _company(session, company_id, lock=True)
    gate = _gate(session, company.id, lock=True)
    if gate is None and not enabled:
        return _pilot_response(session, company.id)
    if gate is not None and gate.is_enabled == enabled:
        return _pilot_response(session, company.id)

    now = _now()
    if gate is None:
        gate = PeriodontogramPilotCompanyGate(
            company_id=company.id,
            is_enabled=True,
            enabled_at=now,
            enabled_by_user_id=context.user.id,
        )
        session.add(gate)
        session.flush()
    elif enabled:
        gate.is_enabled = True
        gate.enabled_at = now
        gate.enabled_by_user_id = context.user.id
        gate.disabled_at = None
        gate.disabled_by_user_id = None
    else:
        gate.is_enabled = False
        gate.disabled_at = now
        gate.disabled_by_user_id = context.user.id

    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity="periodontogram_pilot_company_gate",
        entity_id=gate.id,
        action=(
            "PERIODONTOGRAM_PILOT_ENABLED"
            if enabled
            else "PERIODONTOGRAM_PILOT_DISABLED"
        ),
        detail={"enabled": enabled},
    )
    session.commit()
    return _pilot_response(session, company.id)


def update_platform_periodontogram_dentist(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    dentist_id: UUID,
    *,
    enabled: bool,
    reason: str | None,
    metadata: RequestMetadata,
) -> PeriodontogramPilotResponse:
    company = _company(session, company_id, lock=True)
    gate = _gate(session, company.id, lock=True)
    if enabled and (gate is None or not gate.is_enabled):
        raise PeriodontogramPilotError(
            "PERIODONTOGRAM_PILOT_DISABLED",
            "Habilita primero el piloto de Periodontograma para la empresa.",
            409,
        )
    dentist, user = _dentist_and_user(
        session,
        company.id,
        dentist_id,
        lock=True,
    )
    authorization = _active_authorization(
        session,
        company.id,
        dentist.id,
        lock=True,
    )
    if enabled and authorization is not None:
        return _pilot_response(session, company.id)
    if not enabled and authorization is None:
        return _pilot_response(session, company.id)
    if enabled and not _operational(dentist, user):
        raise PeriodontogramPilotError(
            "PERIODONTOGRAM_PILOT_DENTIST_INACTIVE",
            "El odontólogo y su usuario vinculado deben estar activos.",
            409,
        )

    now = _now()
    if enabled:
        authorization = PeriodontogramPilotDentistAuthorization(
            company_id=company.id,
            dentist_id=dentist.id,
            authorized_at=now,
            authorized_by_user_id=context.user.id,
        )
        session.add(authorization)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            raise PeriodontogramPilotError(
                "PERIODONTOGRAM_PILOT_DENTIST_ALREADY_AUTHORIZED",
                "El odontólogo ya está autorizado para el piloto.",
                409,
            ) from exc
    else:
        authorization.is_active = False
        authorization.revoked_at = now
        authorization.revoked_by_user_id = context.user.id
        authorization.revocation_reason = (
            reason.strip() if reason and reason.strip() else None
        )

    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity="periodontogram_pilot_dentist_authorization",
        entity_id=authorization.id,
        action=(
            "PERIODONTOGRAM_PILOT_DENTIST_AUTHORIZED"
            if enabled
            else "PERIODONTOGRAM_PILOT_DENTIST_REVOKED"
        ),
        detail={"dentist_id": str(dentist.id)},
    )
    session.commit()
    return _pilot_response(session, company.id)


def resolve_periodontogram_pilot_access(
    session: Session,
    context: AuthContext,
    *,
    site_id: UUID | None = None,
) -> PeriodontogramPilotAccessResponse:
    company_id = context.user.company_id
    denied = {
        "company_id": company_id,
        "dentist_id": None,
        "company_enabled": False,
        "dentist_authorized": False,
    }
    if not context.user.is_active or context.user.status != "Activo":
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTOGRAM_USER_INACTIVE",
            message="El usuario no está activo.",
            **denied,
        )
    gate = _gate(session, company_id)
    if gate is None or not gate.is_enabled:
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTOGRAM_PILOT_DISABLED",
            message="El piloto de Periodontograma no está habilitado para la empresa.",
            **denied,
        )
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )
    if dentist is None:
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTAL_DENTIST_IDENTITY_REQUIRED",
            message="Se requiere un perfil odontológico activo para acceder al Periodontograma.",
            company_id=company_id,
            dentist_id=None,
            company_enabled=True,
            dentist_authorized=False,
        )
    active_site_id = site_id or context.auth_session.active_site_id
    if active_site_id is None or not is_authorized_site(
        session,
        company_id=company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=active_site_id,
    ):
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTAL_SITE_DENIED",
            message="No tienes acceso a la sede seleccionada.",
            company_id=company_id,
            dentist_id=dentist.id,
            company_enabled=True,
            dentist_authorized=False,
        )
    dentist_site = session.scalar(
        select(DentistSite.id).where(
            DentistSite.company_id == company_id,
            DentistSite.dentist_id == dentist.id,
            DentistSite.site_id == active_site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if dentist_site is None:
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTAL_DENTIST_SITE_DENIED",
            message="El odontólogo no está activo en la sede seleccionada.",
            company_id=company_id,
            dentist_id=dentist.id,
            company_enabled=True,
            dentist_authorized=False,
        )
    authorization = _active_authorization(session, company_id, dentist.id)
    if authorization is None:
        return PeriodontogramPilotAccessResponse(
            allowed=False,
            code="PERIODONTOGRAM_PILOT_DENTIST_NOT_AUTHORIZED",
            message="El odontólogo no está autorizado para el piloto de Periodontograma.",
            company_id=company_id,
            dentist_id=dentist.id,
            company_enabled=True,
            dentist_authorized=False,
        )
    return PeriodontogramPilotAccessResponse(
        allowed=True,
        code="PERIODONTOGRAM_PILOT_ACCESS_GRANTED",
        message="Acceso al piloto de Periodontograma habilitado.",
        company_id=company_id,
        dentist_id=dentist.id,
        company_enabled=True,
        dentist_authorized=True,
    )


def require_periodontogram_pilot_access(
    session: Session,
    context: AuthContext,
    *,
    site_id: UUID | None = None,
) -> PeriodontogramPilotAccessResponse:
    access = resolve_periodontogram_pilot_access(
        session,
        context,
        site_id=site_id,
    )
    if not access.allowed:
        raise PeriodontogramPilotError(access.code, access.message, 403)
    return access
