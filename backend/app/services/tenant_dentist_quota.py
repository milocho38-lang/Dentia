from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.security_catalog import DENTIST_IDENTITY_PERMISSION_CODES
from app.models.agenda import Dentist
from app.models.associations import RolePermission
from app.models.company import Company
from app.models.permission import Permission
from app.models.user import User


DENTIST_LIMIT_MESSAGE = "Has alcanzado el límite de odontólogos de tu plan."


class TenantDentistLimitError(RuntimeError):
    pass


def active_dentist_count(session: Session, company_id: UUID) -> int:
    """Count active professionals, never roles.

    Unlinked active dentist profiles consume a seat. A linked profile consumes
    one seat only while both the professional and its user are active.
    """
    linked_user = aliased(User)
    return int(
        session.scalar(
            select(func.count())
            .select_from(Dentist)
            .outerjoin(linked_user, linked_user.id == Dentist.user_id)
            .where(
                Dentist.company_id == company_id,
                Dentist.is_active.is_(True),
                Dentist.status == "Activo",
                or_(
                    Dentist.user_id.is_(None),
                    and_(
                        linked_user.company_id == company_id,
                        linked_user.is_active.is_(True),
                        linked_user.status == "Activo",
                    ),
                ),
            )
        )
        or 0
    )


def user_has_active_dentist_profile(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
) -> bool:
    return bool(
        session.scalar(
            select(Dentist.id).where(
                Dentist.company_id == company_id,
                Dentist.user_id == user_id,
                Dentist.is_active.is_(True),
                Dentist.status == "Activo",
            )
        )
    )


def get_user_dentist_profile(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    lock: bool = False,
) -> Dentist | None:
    statement = select(Dentist).where(
        Dentist.company_id == company_id,
        Dentist.user_id == user_id,
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def deactivate_user_dentist_profile(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
) -> Dentist | None:
    """Preserve a historical profile while removing its practicing status."""
    dentist = get_user_dentist_profile(
        session,
        company_id=company_id,
        user_id=user_id,
        lock=True,
    )
    if dentist is not None:
        dentist.status = "Inactivo"
        dentist.is_active = False
    return dentist


def roles_require_dentist_profile(
    session: Session,
    role_ids: list[UUID] | set[UUID],
) -> bool:
    """Classify clinical roles by capabilities, not by mutable role names."""
    if not role_ids:
        return False
    return bool(
        session.scalar(
            select(RolePermission.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                RolePermission.role_id.in_(role_ids),
                RolePermission.is_active.is_(True),
                Permission.is_active.is_(True),
                Permission.code.in_(DENTIST_IDENTITY_PERMISSION_CODES),
            )
            .limit(1)
        )
    )


def lock_company_and_require_dentist_slot(
    session: Session,
    company_id: UUID,
) -> Company:
    company = session.scalar(
        select(Company).where(Company.id == company_id).with_for_update()
    )
    if company is None:
        raise TenantDentistLimitError("Empresa no encontrada.")
    if active_dentist_count(session, company_id) >= company.max_active_dentists:
        raise TenantDentistLimitError(DENTIST_LIMIT_MESSAGE)
    return company
