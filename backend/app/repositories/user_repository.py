from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.associations import UserRole, UserSite
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.role import Role
from app.models.site import Site
from app.models.user import User


def get_company_user(
    session: Session,
    company_id: UUID,
    user_id: UUID,
    *,
    lock: bool = False,
) -> User | None:
    statement = select(User).where(
        User.id == user_id,
        User.company_id == company_id,
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_user_by_email(session: Session, normalized_email: str) -> User | None:
    return session.scalar(
        select(User).where(User.normalized_email == normalized_email)
    )


def list_company_users(
    session: Session,
    company_id: UUID,
    *,
    search: str | None,
    status: str | None,
    locked: bool | None,
    role_id: UUID | None,
    site_id: UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    filters = [User.company_id == company_id]
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                User.normalized_email.ilike(pattern.casefold()),
            )
        )
    if status:
        filters.append(User.status == status)
    now = datetime.now().astimezone()
    if locked is True:
        filters.append(User.locked_until > now)
    elif locked is False:
        filters.append(
            or_(User.locked_until.is_(None), User.locked_until <= now)
        )
    if role_id:
        filters.append(
            User.id.in_(
                select(UserRole.user_id).where(
                    UserRole.role_id == role_id,
                    UserRole.is_active.is_(True),
                )
            )
        )
    if site_id:
        filters.append(
            or_(
                User.id.in_(
                    select(UserSite.user_id).where(
                        UserSite.site_id == site_id,
                        UserSite.is_active.is_(True),
                    )
                ),
                User.id.in_(
                    select(UserRole.user_id)
                    .join(Role, Role.id == UserRole.role_id)
                    .where(
                        UserRole.is_active.is_(True),
                        Role.is_active.is_(True),
                        Role.code == "ADMINISTRATOR",
                    )
                )
            )
        )
    total = int(
        session.scalar(select(func.count()).select_from(User).where(*filters))
        or 0
    )
    items = list(
        session.scalars(
            select(User)
            .where(*filters)
            .order_by(User.name, User.email)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


def get_active_roles(
    session: Session,
    company_id: UUID,
    role_ids: list[UUID] | None = None,
) -> list[Role]:
    statement = select(Role).where(
        Role.company_id == company_id,
        Role.is_active.is_(True),
    )
    if role_ids is not None:
        statement = statement.where(Role.id.in_(role_ids))
    return list(session.scalars(statement.order_by(Role.name)))


def get_active_sites(
    session: Session,
    company_id: UUID,
    site_ids: list[UUID] | None = None,
) -> list[Site]:
    statement = select(Site).where(
        Site.company_id == company_id,
        Site.is_active.is_(True),
        Site.status == "Activa",
    )
    if site_ids is not None:
        statement = statement.where(Site.id.in_(site_ids))
    return list(session.scalars(statement.order_by(Site.name)))


def get_user_roles(session: Session, user_id: UUID) -> list[tuple[UserRole, Role]]:
    rows = session.execute(
        select(UserRole, Role)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, UserRole.is_active.is_(True))
        .order_by(Role.name)
    )
    return list(rows.tuples())


def get_user_sites(session: Session, user_id: UUID) -> list[tuple[UserSite, Site]]:
    rows = session.execute(
        select(UserSite, Site)
        .join(Site, Site.id == UserSite.site_id)
        .where(UserSite.user_id == user_id, UserSite.is_active.is_(True))
        .order_by(UserSite.is_default.desc(), Site.name)
    )
    return list(rows.tuples())


def count_active_sessions(session: Session, user_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    return int(
        session.scalar(
            select(func.count()).select_from(AuthSession).where(
                AuthSession.user_id == user_id,
                AuthSession.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )
        or 0
    )


def list_user_sessions(
    session: Session,
    company_id: UUID,
    user_id: UUID,
) -> list[tuple[AuthSession, str | None]]:
    rows = session.execute(
        select(AuthSession, Site.name)
        .outerjoin(Site, Site.id == AuthSession.active_site_id)
        .where(
            AuthSession.company_id == company_id,
            AuthSession.user_id == user_id,
        )
        .order_by(AuthSession.created_at.desc())
    )
    return list(rows.tuples())


def list_user_audit(
    session: Session,
    company_id: UUID,
    user_id: UUID,
) -> list[AuditEvent]:
    return list(
        session.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.company_id == company_id,
                AuditEvent.entity == "user",
                AuditEvent.entity_id == user_id,
            )
            .order_by(AuditEvent.occurred_at.desc())
            .limit(200)
        )
    )


def count_active_administrators(session: Session, company_id: UUID) -> int:
    return int(
        session.scalar(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.company_id == company_id,
                User.status == "Activo",
                User.is_active.is_(True),
                UserRole.is_active.is_(True),
                Role.code == "ADMINISTRATOR",
                Role.is_active.is_(True),
            )
        )
        or 0
    )
