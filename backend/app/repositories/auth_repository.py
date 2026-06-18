from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.associations import RolePermission, UserRole, UserSite
from app.models.auth_attempt import AuthAttempt
from app.models.auth_session import AuthSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.site import Site
from app.models.user import User


def get_user_for_login(session: Session, normalized_email: str) -> User | None:
    statement = (
        select(User)
        .where(User.normalized_email == normalized_email)
        .with_for_update()
    )
    return session.scalar(statement)


def get_user(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def get_auth_session(
    session: Session,
    session_id: UUID,
    *,
    lock: bool = False,
) -> AuthSession | None:
    statement = select(AuthSession).where(AuthSession.id == session_id)
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_active_role_codes(session: Session, user_id: UUID) -> list[str]:
    statement = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            UserRole.is_active.is_(True),
            Role.is_active.is_(True),
        )
        .order_by(Role.code)
    )
    return list(session.scalars(statement))


def get_active_permission_codes(session: Session, user_id: UUID) -> list[str]:
    statement = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            UserRole.is_active.is_(True),
            Role.is_active.is_(True),
            RolePermission.is_active.is_(True),
            Permission.is_active.is_(True),
        )
        .distinct()
        .order_by(Permission.code)
    )
    return list(session.scalars(statement))


def get_active_site(session: Session, site_id: UUID | None) -> Site | None:
    if site_id is None:
        return None
    return session.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
    )


def get_first_active_user_site(session: Session, user_id: UUID) -> UUID | None:
    statement = (
        select(UserSite.site_id)
        .join(Site, Site.id == UserSite.site_id)
        .where(
            UserSite.user_id == user_id,
            UserSite.is_active.is_(True),
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
        .order_by(UserSite.is_default.desc(), UserSite.created_at)
        .limit(1)
    )
    return session.scalar(statement)


def count_recent_failed_attempts_for_ip(
    session: Session,
    ip_address: str | None,
    since: datetime,
) -> int:
    if ip_address is None:
        return 0
    statement = select(func.count()).select_from(AuthAttempt).where(
        AuthAttempt.ip_address == ip_address,
        AuthAttempt.result == "FAILURE",
        AuthAttempt.occurred_at >= since,
    )
    return int(session.scalar(statement) or 0)
