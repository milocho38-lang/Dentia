from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    email_fingerprint,
    get_refresh_session_id,
    hash_password,
    hash_refresh_token,
    normalize_email,
    refresh_token_matches,
    utc_now,
    verify_dummy_password,
    verify_password,
)
from app.models.audit_event import AuditEvent
from app.models.auth_attempt import AuthAttempt
from app.models.auth_session import AuthSession
from app.models.company import Company
from app.models.user import User
from app.repositories.auth_repository import (
    count_recent_failed_attempts_for_ip,
    get_active_permission_codes,
    get_active_role_codes,
    get_active_site,
    get_auth_session,
    get_first_active_user_site,
    get_user,
    get_user_for_login,
)
from app.schemas.auth_schema import AuthUserResponse, TokenResponse
from app.schemas.site_context_schema import AuthSiteResponse
from app.services.site_access_service import (
    authorized_sites,
    first_authorized_site_id,
    is_authorized_site,
)


GENERIC_LOGIN_ERROR = "Credenciales inválidas o acceso no disponible."


class AuthenticationError(RuntimeError):
    def __init__(self, message: str = GENERIC_LOGIN_ERROR, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class RequestMetadata:
    ip_address: str | None
    user_agent: str | None


@dataclass(frozen=True)
class AuthContext:
    user: User
    auth_session: AuthSession
    roles: list[str]
    permissions: list[str]


def _add_audit(
    session: Session,
    *,
    action: str,
    result: str,
    metadata: RequestMetadata,
    company_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    entity: str = "authentication",
    entity_id: UUID | None = None,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=company_id,
            user_id=user_id,
            session_id=session_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result=result,
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _add_attempt(
    session: Session,
    *,
    normalized_email: str,
    metadata: RequestMetadata,
    result: str,
    user: User | None = None,
    failure_reason: str | None = None,
) -> None:
    session.add(
        AuthAttempt(
            company_id=user.company_id if user else None,
            user_id=user.id if user else None,
            email_fingerprint=email_fingerprint(normalized_email),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
            result=result,
            failure_reason=failure_reason,
        )
    )


def _build_user_response(
    session: Session,
    user: User,
    auth_session: AuthSession,
    roles: list[str],
    permissions: list[str],
) -> AuthUserResponse:
    company = session.get(Company, user.company_id)
    sites = authorized_sites(
        session,
        company_id=user.company_id,
        user_id=user.id,
        roles=roles,
    )
    active_site = next(
        (site for site in sites if site.id == auth_session.active_site_id),
        None,
    )
    return AuthUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        company_id=user.company_id,
        active_site_id=auth_session.active_site_id,
        active_site_name=active_site.name if active_site else None,
        sites=[
            AuthSiteResponse(
                id=site.id,
                name=site.name,
                city=site.city,
                timezone=site.timezone or company.timezone,
            )
            for site in sites
        ],
        roles=roles,
        permissions=permissions,
        must_change_password=user.must_change_password,
    )


def _build_token_response(
    session: Session,
    user: User,
    auth_session: AuthSession,
) -> TokenResponse:
    roles = get_active_role_codes(session, user.id)
    permissions = get_active_permission_codes(session, user.id)
    access_token, _ = create_access_token(
        user_id=user.id,
        session_id=auth_session.id,
        company_id=user.company_id,
        site_id=auth_session.active_site_id,
        roles=roles,
        auth_version=user.auth_version,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=_build_user_response(
            session, user, auth_session, roles, permissions
        ),
    )


def login(
    session: Session,
    *,
    email: str,
    password: str,
    metadata: RequestMetadata,
) -> tuple[TokenResponse, str, int]:
    now = utc_now()
    normalized_email = normalize_email(email)
    ip_window_start = now - timedelta(minutes=settings.auth_ip_window_minutes)
    ip_failures = count_recent_failed_attempts_for_ip(
        session,
        metadata.ip_address,
        ip_window_start,
    )
    if ip_failures >= settings.auth_ip_max_failed_attempts:
        verify_dummy_password(password)
        _add_attempt(
            session,
            normalized_email=normalized_email,
            metadata=metadata,
            result="FAILURE",
            failure_reason="IP_RATE_LIMIT",
        )
        _add_audit(
            session,
            action="LOGIN_FAILED",
            result="FAILURE",
            metadata=metadata,
            detail={"reason": "IP_RATE_LIMIT"},
        )
        session.commit()
        raise AuthenticationError(status_code=429)

    user = get_user_for_login(session, normalized_email)
    if user is None:
        verify_dummy_password(password)
        _add_attempt(
            session,
            normalized_email=normalized_email,
            metadata=metadata,
            result="FAILURE",
            failure_reason="INVALID_CREDENTIALS",
        )
        _add_audit(
            session,
            action="LOGIN_FAILED",
            result="FAILURE",
            metadata=metadata,
            detail={"reason": "INVALID_CREDENTIALS"},
        )
        session.commit()
        raise AuthenticationError()

    if user.locked_until and user.locked_until > now:
        verify_dummy_password(password)
        _add_attempt(
            session,
            normalized_email=normalized_email,
            metadata=metadata,
            result="FAILURE",
            user=user,
            failure_reason="ACCOUNT_LOCKED",
        )
        _add_audit(
            session,
            action="LOGIN_FAILED",
            result="FAILURE",
            metadata=metadata,
            company_id=user.company_id,
            user_id=user.id,
            entity_id=user.id,
            detail={"reason": "ACCOUNT_LOCKED"},
        )
        session.commit()
        raise AuthenticationError()

    if user.locked_until and user.locked_until <= now:
        user.locked_until = None
        user.failed_login_attempts = 0

    password_valid = verify_password(password, user.password_hash)
    account_active = user.is_active and user.status == "Activo"
    company = session.get(Company, user.company_id)
    company_active = bool(
        company and company.is_active and company.status == "Activa"
    )

    if not password_valid or not account_active or not company_active:
        user.failed_login_attempts += 1
        locked = user.failed_login_attempts >= settings.auth_max_failed_attempts
        if locked:
            user.locked_until = now + timedelta(
                minutes=settings.auth_lockout_minutes
            )
        reason = "INVALID_CREDENTIALS"
        if not account_active:
            reason = "USER_UNAVAILABLE"
        elif not company_active:
            reason = "COMPANY_UNAVAILABLE"
        _add_attempt(
            session,
            normalized_email=normalized_email,
            metadata=metadata,
            result="FAILURE",
            user=user,
            failure_reason=reason,
        )
        _add_audit(
            session,
            action="LOGIN_FAILED",
            result="FAILURE",
            metadata=metadata,
            company_id=user.company_id,
            user_id=user.id,
            entity_id=user.id,
            detail={"reason": reason, "account_locked": locked},
        )
        session.commit()
        raise AuthenticationError()

    roles = get_active_role_codes(session, user.id)
    active_site_id = user.default_site_id
    if (
        active_site_id is None
        or not is_authorized_site(
            session,
            company_id=user.company_id,
            user_id=user.id,
            roles=roles,
            site_id=active_site_id,
        )
    ):
        active_site_id = first_authorized_site_id(
            session,
            company_id=user.company_id,
            user_id=user.id,
            roles=roles,
        )
    if active_site_id is None:
        _add_attempt(
            session,
            normalized_email=normalized_email,
            metadata=metadata,
            result="FAILURE",
            user=user,
            failure_reason="NO_ACTIVE_SITE",
        )
        _add_audit(
            session,
            action="LOGIN_FAILED",
            result="FAILURE",
            metadata=metadata,
            company_id=user.company_id,
            user_id=user.id,
            entity_id=user.id,
            detail={"reason": "NO_ACTIVE_SITE"},
        )
        session.commit()
        raise AuthenticationError()

    session_id = uuid4()
    refresh_token = create_refresh_token(session_id)
    auth_session = AuthSession(
        id=session_id,
        company_id=user.company_id,
        user_id=user.id,
        active_site_id=active_site_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        token_family_id=uuid4(),
        rotation_counter=0,
        ip_address=metadata.ip_address,
        user_agent=metadata.user_agent,
        last_seen_at=now,
        expires_at=now
        + timedelta(hours=settings.refresh_token_expire_hours),
    )
    session.add(auth_session)
    session.flush()

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    _add_attempt(
        session,
        normalized_email=normalized_email,
        metadata=metadata,
        result="SUCCESS",
        user=user,
    )
    _add_audit(
        session,
        action="LOGIN_SUCCESS",
        result="SUCCESS",
        metadata=metadata,
        company_id=user.company_id,
        user_id=user.id,
        session_id=auth_session.id,
        entity_id=user.id,
    )
    response = _build_token_response(session, user, auth_session)
    session.commit()
    return (
        response,
        refresh_token,
        settings.refresh_token_expire_hours * 3600,
    )


def refresh(
    session: Session,
    *,
    refresh_token: str,
    metadata: RequestMetadata,
) -> tuple[TokenResponse, str, int]:
    try:
        session_id = get_refresh_session_id(refresh_token)
    except (ValueError, TypeError):
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            detail={"reason": "INVALID_REFRESH_TOKEN"},
        )
        session.commit()
        raise AuthenticationError()

    auth_session = get_auth_session(session, session_id, lock=True)
    now = utc_now()
    if auth_session is None:
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            session_id=session_id,
            detail={"reason": "UNKNOWN_SESSION"},
        )
        session.commit()
        raise AuthenticationError()

    if not refresh_token_matches(
        refresh_token,
        auth_session.refresh_token_hash,
    ):
        auth_session.revoked_at = now
        auth_session.is_active = False
        auth_session.revoke_reason = "REFRESH_TOKEN_REUSE"
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            company_id=auth_session.company_id,
            user_id=auth_session.user_id,
            session_id=auth_session.id,
            detail={"reason": "REFRESH_TOKEN_REUSE"},
        )
        session.commit()
        raise AuthenticationError()

    idle_deadline = auth_session.last_seen_at + timedelta(
        minutes=settings.session_idle_timeout_minutes
    )
    if (
        not auth_session.is_active
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= now
        or idle_deadline <= now
    ):
        auth_session.revoked_at = auth_session.revoked_at or now
        auth_session.is_active = False
        auth_session.revoke_reason = (
            auth_session.revoke_reason or "SESSION_EXPIRED"
        )
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            company_id=auth_session.company_id,
            user_id=auth_session.user_id,
            session_id=auth_session.id,
            detail={"reason": "SESSION_EXPIRED"},
        )
        session.commit()
        raise AuthenticationError()

    user = get_user(session, auth_session.user_id)
    company = session.get(Company, auth_session.company_id)
    if (
        user is None
        or not user.is_active
        or user.status != "Activo"
        or company is None
        or not company.is_active
        or company.status != "Activa"
    ):
        auth_session.revoked_at = now
        auth_session.is_active = False
        auth_session.revoke_reason = "ACCOUNT_UNAVAILABLE"
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            company_id=auth_session.company_id,
            user_id=auth_session.user_id,
            session_id=auth_session.id,
            detail={"reason": "ACCOUNT_UNAVAILABLE"},
        )
        session.commit()
        raise AuthenticationError()
    roles = get_active_role_codes(session, user.id)
    if (
        auth_session.active_site_id is None
        or not is_authorized_site(
            session,
            company_id=user.company_id,
            user_id=user.id,
            roles=roles,
            site_id=auth_session.active_site_id,
        )
    ):
        auth_session.revoked_at = now
        auth_session.is_active = False
        auth_session.revoke_reason = "SITE_UNAVAILABLE"
        _add_audit(
            session,
            action="ACCESS_DENIED",
            result="FAILURE",
            metadata=metadata,
            company_id=auth_session.company_id,
            user_id=auth_session.user_id,
            session_id=auth_session.id,
            detail={"reason": "SITE_UNAVAILABLE"},
        )
        session.commit()
        raise AuthenticationError()

    new_refresh_token = create_refresh_token(auth_session.id)
    auth_session.refresh_token_hash = hash_refresh_token(new_refresh_token)
    auth_session.rotation_counter += 1
    auth_session.last_seen_at = now
    auth_session.ip_address = metadata.ip_address
    auth_session.user_agent = metadata.user_agent

    _add_audit(
        session,
        action="TOKEN_REFRESHED",
        result="SUCCESS",
        metadata=metadata,
        company_id=user.company_id,
        user_id=user.id,
        session_id=auth_session.id,
        entity_id=auth_session.id,
        detail={"rotation_counter": auth_session.rotation_counter},
    )
    response = _build_token_response(session, user, auth_session)
    remaining_seconds = max(
        0,
        int((auth_session.expires_at - now).total_seconds()),
    )
    session.commit()
    return response, new_refresh_token, remaining_seconds


def logout(
    session: Session,
    *,
    context: AuthContext,
    metadata: RequestMetadata,
) -> None:
    now = utc_now()
    context.auth_session.revoked_at = now
    context.auth_session.revoked_by = context.user.id
    context.auth_session.revoke_reason = "LOGOUT"
    context.auth_session.is_active = False
    _add_audit(
        session,
        action="LOGOUT",
        result="SUCCESS",
        metadata=metadata,
        company_id=context.user.company_id,
        user_id=context.user.id,
        session_id=context.auth_session.id,
        entity_id=context.auth_session.id,
    )
    session.commit()


def change_password(
    session: Session,
    *,
    context: AuthContext,
    current_password: str,
    new_password: str,
    metadata: RequestMetadata,
) -> tuple[TokenResponse, str, int]:
    if not verify_password(current_password, context.user.password_hash):
        raise AuthenticationError("La contraseña actual no es correcta.", 400)
    if len(new_password) < 12:
        raise AuthenticationError(
            "La nueva contraseña debe tener al menos 12 caracteres.",
            400,
        )
    if current_password == new_password:
        raise AuthenticationError(
            "La nueva contraseña debe ser diferente.",
            400,
        )

    now = utc_now()
    other_sessions = list(
        session.scalars(
            select(AuthSession).where(
                AuthSession.user_id == context.user.id,
                AuthSession.company_id == context.user.company_id,
                AuthSession.id != context.auth_session.id,
                AuthSession.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
            )
        )
    )
    for auth_session in other_sessions:
        auth_session.is_active = False
        auth_session.revoked_at = now
        auth_session.revoked_by = context.user.id
        auth_session.revoke_reason = "PASSWORD_CHANGED"

    context.user.password_hash = hash_password(new_password)
    context.user.password_changed_at = now
    context.user.must_change_password = False
    context.user.auth_version += 1

    new_refresh_token = create_refresh_token(context.auth_session.id)
    context.auth_session.refresh_token_hash = hash_refresh_token(
        new_refresh_token
    )
    context.auth_session.rotation_counter += 1
    context.auth_session.last_seen_at = now
    context.auth_session.ip_address = metadata.ip_address
    context.auth_session.user_agent = metadata.user_agent

    _add_audit(
        session,
        action="PASSWORD_CHANGED",
        result="SUCCESS",
        metadata=metadata,
        company_id=context.user.company_id,
        user_id=context.user.id,
        session_id=context.auth_session.id,
        entity="user",
        entity_id=context.user.id,
        detail={"sessions_revoked": len(other_sessions)},
    )
    response = _build_token_response(
        session,
        context.user,
        context.auth_session,
    )
    remaining_seconds = max(
        0,
        int((context.auth_session.expires_at - now).total_seconds()),
    )
    session.commit()
    return response, new_refresh_token, remaining_seconds


def register_access_denied(
    session: Session,
    *,
    metadata: RequestMetadata,
    reason: str,
    company_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
) -> None:
    _add_audit(
        session,
        action="ACCESS_DENIED",
        result="FAILURE",
        metadata=metadata,
        company_id=company_id,
        user_id=user_id,
        session_id=session_id,
        detail={"reason": reason},
    )
    session.commit()


def build_auth_context(
    session: Session,
    *,
    user_id: UUID,
    session_id: UUID,
    company_id: UUID,
    site_id: UUID | None,
    auth_version: int,
) -> AuthContext | None:
    user = get_user(session, user_id)
    auth_session = get_auth_session(session, session_id)
    company = session.get(Company, company_id)
    site = get_active_site(session, site_id)
    roles = get_active_role_codes(session, user.id) if user else []

    if (
        user is None
        or auth_session is None
        or company is None
        or user.company_id != company_id
        or auth_session.user_id != user_id
        or auth_session.company_id != company_id
        or auth_session.active_site_id != site_id
        or not user.is_active
        or user.status != "Activo"
        or user.auth_version != auth_version
        or not company.is_active
        or company.status != "Activa"
        or not auth_session.is_active
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= utc_now()
        or site is None
        or not is_authorized_site(
            session,
            company_id=company_id,
            user_id=user_id,
            roles=roles,
            site_id=site_id,
        )
    ):
        return None

    if auth_session.last_seen_at + timedelta(
        minutes=settings.session_idle_timeout_minutes
    ) <= utc_now():
        return None

    return AuthContext(
        user=user,
        auth_session=auth_session,
        roles=roles,
        permissions=get_active_permission_codes(session, user.id),
    )


def get_auth_sites(
    session: Session,
    context: AuthContext,
) -> list[AuthSiteResponse]:
    company = session.get(Company, context.user.company_id)
    return [
        AuthSiteResponse(
            id=site.id,
            name=site.name,
            city=site.city,
            timezone=site.timezone or company.timezone,
        )
        for site in authorized_sites(
            session,
            company_id=context.user.company_id,
            user_id=context.user.id,
            roles=context.roles,
        )
    ]


def switch_site(
    session: Session,
    *,
    context: AuthContext,
    site_id: UUID,
    metadata: RequestMetadata,
) -> TokenResponse:
    if not is_authorized_site(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=site_id,
    ):
        raise AuthenticationError(
            "La sede no está activa o no está autorizada.", 403
        )
    previous_site_id = context.auth_session.active_site_id
    context.auth_session.active_site_id = site_id
    context.auth_session.last_seen_at = utc_now()
    _add_audit(
        session,
        action="SITE_CHANGED",
        result="SUCCESS",
        metadata=metadata,
        company_id=context.user.company_id,
        user_id=context.user.id,
        session_id=context.auth_session.id,
        entity="site",
        entity_id=site_id,
        detail={
            "previous_site_id": (
                str(previous_site_id) if previous_site_id else None
            ),
            "new_site_id": str(site_id),
        },
    )
    response = _build_token_response(
        session, context.user, context.auth_session
    )
    session.commit()
    return response
