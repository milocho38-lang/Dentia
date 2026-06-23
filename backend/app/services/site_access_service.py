from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.associations import UserSite
from app.models.site import Site


def authorized_sites(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    roles: list[str] | set[str],
    active_only: bool = True,
) -> list[Site]:
    filters = [Site.company_id == company_id, Site.is_active.is_(True)]
    if active_only:
        filters.append(Site.status == "Activa")
    statement = select(Site).where(*filters)
    if "ADMINISTRATOR" not in roles:
        statement = statement.join(
            UserSite, UserSite.site_id == Site.id
        ).where(
            UserSite.company_id == company_id,
            UserSite.user_id == user_id,
            UserSite.is_active.is_(True),
        )
    return list(session.scalars(statement.order_by(Site.name)))


def authorized_site_ids(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    roles: list[str] | set[str],
    active_only: bool = True,
) -> set[UUID]:
    return {
        site.id
        for site in authorized_sites(
            session,
            company_id=company_id,
            user_id=user_id,
            roles=roles,
            active_only=active_only,
        )
    }


def first_authorized_site_id(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    roles: list[str] | set[str],
) -> UUID | None:
    sites = authorized_sites(
        session,
        company_id=company_id,
        user_id=user_id,
        roles=roles,
    )
    return sites[0].id if sites else None


def is_authorized_site(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    roles: list[str] | set[str],
    site_id: UUID,
) -> bool:
    return site_id in authorized_site_ids(
        session,
        company_id=company_id,
        user_id=user_id,
        roles=roles,
    )
