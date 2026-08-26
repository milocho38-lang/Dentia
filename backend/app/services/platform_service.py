import re
import secrets
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.core.config import settings
from app.core.security_catalog import PERMISSIONS, PLATFORM_PERMISSION_CODES, ROLES
from app.models.agenda import Dentist, DentistSite
from app.models.associations import RolePermission, UserRole, UserSite
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.company import Company
from app.models.permission import Permission
from app.models.role import Role
from app.models.site import Site
from app.models.user import User
from app.schemas.platform_schema import (
    PlatformCompanyActionResponse,
    PlatformCompanyCreateRequest,
    PlatformCompanyCreateResponse,
    PlatformCompanyDetail,
    PlatformCompanyUserRoleUpdateRequest,
    PlatformCompanyUserRoleUpdateResponse,
    PlatformCompanyDentistLimitUpdateRequest,
    PlatformCompanyDentistLimitUpdateResponse,
    PlatformDentistProfileSummary,
    PlatformCompanyListItem,
    PlatformCompanyListResponse,
    PlatformRoleOption,
    PlatformSiteSummary,
    PlatformUserSiteSummary,
    PlatformUserSummary,
)
from app.services.agenda_service import ensure_agenda_seed_data
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.organization_service import normalize_tax_id
from app.services.tenant_dentist_quota import (
    TenantDentistLimitError,
    active_dentist_count,
    deactivate_user_dentist_profile,
    get_user_dentist_profile,
    lock_company_and_require_dentist_slot,
    roles_require_dentist_profile,
)


PLATFORM_COMPANY_LOCK_ID = 8_011_001


class PlatformError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    ascii_text = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or f"empresa-{secrets.token_hex(4)}"


def _unique_slug(session: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    counter = 2
    while session.scalar(select(Company.id).where(Company.slug == slug)):
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _temporary_password(explicit: str | None = None) -> str:
    return explicit or f"Dnt!{secrets.token_urlsafe(15)}"


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    company_id: UUID,
    user_id: UUID | None = None,
    entity: str = "platform_company",
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


def _ensure_permissions(session: Session) -> dict[str, Permission]:
    permissions_by_code = {
        item.code: item for item in session.scalars(select(Permission))
    }
    for definition in PERMISSIONS:
        permission = permissions_by_code.get(definition.code)
        if permission is None:
            permission = Permission(
                code=definition.code,
                name=definition.name,
                module=definition.module,
                description=definition.description,
            )
            session.add(permission)
            permissions_by_code[definition.code] = permission
    session.flush()
    return permissions_by_code


def _seed_roles(
    session: Session,
    *,
    company_id: UUID,
    created_by: UUID | None,
    permissions_by_code: dict[str, Permission],
) -> dict[str, Role]:
    roles_by_code: dict[str, Role] = {}
    for definition in ROLES:
        role = session.scalar(
            select(Role).where(
                Role.company_id == company_id,
                Role.code == definition.code,
            )
        )
        if role is None:
            role = Role(
                company_id=company_id,
                code=definition.code,
                name=definition.name,
                description=definition.description,
                is_system=True,
                created_by=created_by,
            )
            session.add(role)
            session.flush()
        roles_by_code[definition.code] = role
        for permission_code in definition.permission_codes:
            permission = permissions_by_code[permission_code]
            exists = session.scalar(
                select(RolePermission.id).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            if exists is None:
                session.add(
                    RolePermission(
                        company_id=company_id,
                        role_id=role.id,
                        permission_id=permission.id,
                        created_by=created_by,
                    )
                )
    session.flush()
    return roles_by_code


def _company_counts(session: Session, company_id: UUID) -> tuple[int, int]:
    site_count = int(
        session.scalar(
            select(func.count()).select_from(Site).where(
                Site.company_id == company_id,
                Site.is_active.is_(True),
            )
        )
        or 0
    )
    user_count = int(
        session.scalar(
            select(func.count()).select_from(User).where(
                User.company_id == company_id,
                User.is_active.is_(True),
            )
        )
        or 0
    )
    return site_count, user_count


def _list_item(session: Session, company: Company) -> PlatformCompanyListItem:
    site_count, user_count = _company_counts(session, company.id)
    return PlatformCompanyListItem(
        id=company.id,
        name=company.name,
        company_type=company.company_type,
        tax_id=company.tax_id,
        phone=company.phone,
        email=company.email,
        address=company.address,
        city=company.city,
        country=company.country,
        timezone=company.timezone,
        status=company.status,
        is_active=company.is_active,
        site_count=site_count,
        user_count=user_count,
        active_dentist_count=active_dentist_count(session, company.id),
        max_active_dentists=company.max_active_dentists,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def _user_summary(session: Session, user: User) -> PlatformUserSummary:
    role_rows = list(
        session.execute(
            select(Role.id, Role.code, Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.company_id == user.company_id,
                UserRole.user_id == user.id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
            .order_by(Role.code)
        )
    )
    site_rows = list(
        session.execute(
            select(Site.id, Site.name, UserSite.is_default)
            .join(UserSite, UserSite.site_id == Site.id)
            .where(
                UserSite.company_id == user.company_id,
                UserSite.user_id == user.id,
                UserSite.is_active.is_(True),
                Site.is_active.is_(True),
            )
            .order_by(UserSite.is_default.desc(), Site.name)
        )
    )
    role_codes = [row.code for row in role_rows]
    dentist_profile = _dentist_profile_summary(session, user)
    return PlatformUserSummary(
        id=user.id,
        name=user.name,
        email=user.email,
        status=user.status,
        is_active=user.is_active,
        role_ids=[row.id for row in role_rows],
        roles=role_codes,
        role_names=[row.name for row in role_rows],
        sites=[
            PlatformUserSiteSummary(
                id=row.id,
                name=row.name,
                is_default=row.is_default,
            )
            for row in site_rows
        ],
        dentist_profile=dentist_profile,
        needs_dentist_profile=roles_require_dentist_profile(
            session, {row.id for row in role_rows}
        )
        and dentist_profile is None,
    )


def _dentist_profile_summary(
    session: Session,
    user: User,
) -> PlatformDentistProfileSummary | None:
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == user.company_id,
            Dentist.user_id == user.id,
        )
    )
    if dentist is None:
        return None
    sites = list(
        session.execute(
            select(Site.id, Site.name, DentistSite.is_active)
            .join(DentistSite, DentistSite.site_id == Site.id)
            .where(
                DentistSite.company_id == user.company_id,
                DentistSite.dentist_id == dentist.id,
                DentistSite.is_active.is_(True),
                Site.is_active.is_(True),
            )
            .order_by(Site.name)
        )
    )
    return PlatformDentistProfileSummary(
        id=dentist.id,
        name=dentist.name,
        status=dentist.status,
        is_active=dentist.is_active,
        sites=[
            PlatformUserSiteSummary(id=row.id, name=row.name, is_default=False)
            for row in sites
        ],
    )


def _role_has_platform_permissions(session: Session, role_id: UUID) -> bool:
    return bool(
        session.scalar(
            select(func.count())
            .select_from(RolePermission)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                RolePermission.role_id == role_id,
                RolePermission.is_active.is_(True),
                Permission.code.in_(PLATFORM_PERMISSION_CODES),
            )
        )
    )


def _business_role_options(session: Session, company_id: UUID) -> list[PlatformRoleOption]:
    roles = list(
        session.scalars(
            select(Role)
            .where(
                Role.company_id == company_id,
                Role.is_active.is_(True),
                Role.code != "PLATFORM_ADMIN",
            )
            .order_by(Role.name)
        )
    )
    return [
        PlatformRoleOption(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
        )
        for role in roles
        if not _role_has_platform_permissions(session, role.id)
    ]


def _detail(session: Session, company: Company) -> PlatformCompanyDetail:
    base = _list_item(session, company)
    sites = list(
        session.scalars(
            select(Site).where(Site.company_id == company.id).order_by(Site.name)
        )
    )
    users = list(
        session.scalars(
            select(User).where(User.company_id == company.id).order_by(User.name)
        )
    )
    return PlatformCompanyDetail(
        **base.model_dump(),
        sites=[
            PlatformSiteSummary(
                id=site.id,
                name=site.name,
                city=site.city,
                timezone=site.timezone,
                effective_timezone=site.timezone or company.timezone,
                status=site.status,
            )
            for site in sites
        ],
        users=[_user_summary(session, user) for user in users],
        role_options=_business_role_options(session, company.id),
    )


def list_platform_companies(
    session: Session,
    search: str | None = None,
) -> PlatformCompanyListResponse:
    statement = select(Company).order_by(Company.created_at.desc())
    if search:
        statement = statement.where(Company.name.ilike(f"%{search.strip()}%"))
    companies = list(session.scalars(statement))
    return PlatformCompanyListResponse(
        items=[_list_item(session, company) for company in companies]
    )


def get_platform_company(session: Session, company_id: UUID) -> PlatformCompanyDetail:
    company = session.get(Company, company_id)
    if company is None:
        raise PlatformError("Empresa no encontrada.", 404)
    return _detail(session, company)


def _get_company_and_user(
    session: Session,
    company_id: UUID,
    user_id: UUID,
    *,
    lock_user: bool = False,
) -> tuple[Company, User]:
    company = session.get(Company, company_id)
    if company is None:
        raise PlatformError("Empresa no encontrada.", 404)
    statement = select(User).where(
        User.id == user_id,
        User.company_id == company_id,
    )
    if lock_user:
        statement = statement.with_for_update()
    user = session.scalar(statement)
    if user is None:
        raise PlatformError("Usuario no pertenece a la empresa indicada.", 404)
    return company, user


def _validate_business_roles(
    session: Session,
    company_id: UUID,
    role_ids: list[UUID],
) -> list[Role]:
    unique_ids = list(dict.fromkeys(role_ids))
    roles = list(
        session.scalars(
            select(Role).where(
                Role.company_id == company_id,
                Role.id.in_(unique_ids),
                Role.is_active.is_(True),
            )
        )
    )
    if len(roles) != len(unique_ids):
        raise PlatformError("Uno o más roles no pertenecen a la empresa indicada.", 400)
    if any(
        role.code == "PLATFORM_ADMIN" or _role_has_platform_permissions(session, role.id)
        for role in roles
    ):
        raise PlatformError(
            "No se puede asignar Administrador de plataforma desde esta pantalla.",
            403,
        )
    return roles


def _validate_company_sites(
    session: Session,
    company_id: UUID,
    site_ids: list[UUID],
    default_site_id: UUID,
) -> None:
    unique_ids = set(site_ids)
    if default_site_id not in unique_ids:
        raise PlatformError("La sede predeterminada debe estar asignada.")
    count = int(
        session.scalar(
            select(func.count())
            .select_from(Site)
            .where(
                Site.company_id == company_id,
                Site.id.in_(unique_ids),
                Site.is_active.is_(True),
            )
        )
        or 0
    )
    if count != len(unique_ids):
        raise PlatformError("Una o más sedes no pertenecen a la empresa indicada.")


def _active_role_codes(session: Session, user: User) -> set[str]:
    return set(
        session.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.company_id == user.company_id,
                UserRole.user_id == user.id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
        )
    )


def _active_site_ids(session: Session, user: User) -> set[UUID]:
    return set(
        session.scalars(
            select(UserSite.site_id).where(
                UserSite.company_id == user.company_id,
                UserSite.user_id == user.id,
                UserSite.is_active.is_(True),
            )
        )
    )


def _sync_business_roles(
    session: Session,
    *,
    target: User,
    roles: list[Role],
    actor_id: UUID,
) -> None:
    requested = {role.id for role in roles}
    role_by_id = {
        role.id: role
        for role in session.scalars(
            select(Role).where(Role.company_id == target.company_id)
        )
    }
    existing = {
        assignment.role_id: assignment
        for assignment in session.scalars(
            select(UserRole)
            .where(
                UserRole.company_id == target.company_id,
                UserRole.user_id == target.id,
            )
            .with_for_update()
        )
    }
    for role_id, assignment in existing.items():
        role = role_by_id.get(role_id)
        if role and role.code == "PLATFORM_ADMIN":
            continue
        assignment.is_active = role_id in requested
    for role_id in requested - existing.keys():
        session.add(
            UserRole(
                company_id=target.company_id,
                user_id=target.id,
                role_id=role_id,
                created_by=actor_id,
            )
        )


def _sync_user_sites_for_platform(
    session: Session,
    *,
    target: User,
    site_ids: list[UUID],
    default_site_id: UUID,
    actor_id: UUID,
) -> None:
    requested = set(site_ids)
    existing = {
        assignment.site_id: assignment
        for assignment in session.scalars(
            select(UserSite)
            .where(
                UserSite.company_id == target.company_id,
                UserSite.user_id == target.id,
            )
            .with_for_update()
        )
    }
    for site_id, assignment in existing.items():
        assignment.is_active = site_id in requested
        assignment.is_default = site_id == default_site_id and site_id in requested
    for site_id in requested - existing.keys():
        session.add(
            UserSite(
                company_id=target.company_id,
                user_id=target.id,
                site_id=site_id,
                is_default=site_id == default_site_id,
                created_by=actor_id,
            )
        )
    target.default_site_id = default_site_id


def _ensure_dentist_profile(
    session: Session,
    *,
    target: User,
    site_ids: list[UUID],
    actor_id: UUID,
    active: bool = True,
) -> tuple[Dentist, bool]:
    dentist = get_user_dentist_profile(
        session,
        company_id=target.company_id,
        user_id=target.id,
        lock=True,
    )
    created = False
    if dentist is None:
        dentist = Dentist(
            company_id=target.company_id,
            user_id=target.id,
            name=target.name,
            status="Activo" if active else "Inactivo",
            is_active=active,
            created_by=actor_id,
        )
        session.add(dentist)
        session.flush()
        created = True
    else:
        dentist.name = target.name
        dentist.status = "Activo" if active else "Inactivo"
        dentist.is_active = active
    existing = {
        assignment.site_id: assignment
        for assignment in session.scalars(
            select(DentistSite)
            .where(
                DentistSite.company_id == target.company_id,
                DentistSite.dentist_id == dentist.id,
            )
            .with_for_update()
        )
    }
    requested = set(site_ids)
    for site_id, assignment in existing.items():
        assignment.is_active = site_id in requested
    for site_id in requested - existing.keys():
        session.add(
            DentistSite(
                company_id=target.company_id,
                dentist_id=dentist.id,
                site_id=site_id,
                created_by=actor_id,
            )
        )
    return dentist, created


def update_platform_company_user_roles(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    user_id: UUID,
    payload: PlatformCompanyUserRoleUpdateRequest,
    metadata: RequestMetadata,
) -> PlatformCompanyUserRoleUpdateResponse:
    company, target = _get_company_and_user(
        session,
        company_id,
        user_id,
        lock_user=True,
    )
    roles = _validate_business_roles(session, company.id, payload.role_ids)
    _validate_company_sites(
        session,
        company.id,
        payload.site_ids,
        payload.default_site_id,
    )
    before_roles = _active_role_codes(session, target)
    before_role_ids = set(
        session.scalars(
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.company_id == company.id,
                UserRole.user_id == target.id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
        )
    )
    before_sites = _active_site_ids(session, target)
    before_status = target.status
    had_dentist_capability = roles_require_dentist_profile(
        session, before_role_ids
    )
    has_dentist_capability = roles_require_dentist_profile(
        session, {role.id for role in roles}
    )
    dentist_before = get_user_dentist_profile(
        session,
        company_id=company.id,
        user_id=target.id,
        lock=True,
    )
    dentist_was_active = bool(
        dentist_before
        and dentist_before.is_active
        and dentist_before.status == "Activo"
    )
    if (
        payload.status == "Activo"
        and has_dentist_capability
        and dentist_before is None
        and not payload.ensure_dentist_profile
    ):
        raise PlatformError(
            "El usuario necesita crear o vincular su perfil de odontólogo para activar roles clínicos.",
            409,
        )
    currently_consumes_dentist_seat = (
        target.status == "Activo"
        and target.is_active
        and dentist_was_active
    )
    will_consume_dentist_seat = (
        payload.status == "Activo" and has_dentist_capability
    )
    if will_consume_dentist_seat and not currently_consumes_dentist_seat:
        try:
            lock_company_and_require_dentist_slot(session, company.id)
        except TenantDentistLimitError as exc:
            raise PlatformError(str(exc), 409) from exc
    new_role_codes = {role.code for role in roles}
    if (
        target.status == "Activo"
        and "ADMINISTRATOR" in before_roles
        and "ADMINISTRATOR" not in new_role_codes
    ):
        active_admin_count = int(
            session.scalar(
                select(func.count())
                .select_from(User)
                .join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(
                    User.company_id == company.id,
                    User.status == "Activo",
                    User.is_active.is_(True),
                    UserRole.is_active.is_(True),
                    Role.code == "ADMINISTRATOR",
                    Role.is_active.is_(True),
                )
            )
            or 0
        )
        if active_admin_count <= 1:
            raise PlatformError(
                "No puedes retirar el último Administrador activo de la empresa.",
                409,
            )
    _sync_business_roles(
        session,
        target=target,
        roles=roles,
        actor_id=context.user.id,
    )
    _sync_user_sites_for_platform(
        session,
        target=target,
        site_ids=payload.site_ids,
        default_site_id=payload.default_site_id,
        actor_id=context.user.id,
    )
    target.status = payload.status
    target.is_active = payload.status == "Activo"
    dentist_profile_created = False
    dentist = dentist_before
    if has_dentist_capability and (
        dentist_before is not None or payload.ensure_dentist_profile
    ):
        dentist, dentist_profile_created = _ensure_dentist_profile(
            session,
            target=target,
            site_ids=payload.site_ids,
            actor_id=context.user.id,
            active=target.status == "Activo" and target.is_active,
        )
    elif not has_dentist_capability:
        dentist = deactivate_user_dentist_profile(
            session,
            company_id=company.id,
            user_id=target.id,
        )
    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity="user",
        entity_id=target.id,
        action="PLATFORM_COMPANY_USER_ROLES_UPDATED",
        detail={
            "target_user_id": str(target.id),
            "company_id": str(company.id),
            "roles_before": sorted(before_roles),
            "roles_after": sorted(new_role_codes),
            "sites_before": sorted(str(site_id) for site_id in before_sites),
            "sites_after": sorted(str(site_id) for site_id in payload.site_ids),
            "default_site_after": str(payload.default_site_id),
            "status_before": before_status,
            "status_after": target.status,
            "had_dentist_capability": had_dentist_capability,
            "has_dentist_capability": has_dentist_capability,
            "dentist_profile_id": str(dentist.id) if dentist else None,
            "dentist_profile_created": dentist_profile_created,
            "dentist_profile_active_before": dentist_was_active,
            "dentist_profile_active_after": bool(
                dentist
                and dentist.is_active
                and dentist.status == "Activo"
            ),
        },
    )
    if before_status != target.status:
        _audit(
            session,
            context,
            metadata,
            company_id=company.id,
            entity="user",
            entity_id=target.id,
            action=(
                "USER_REACTIVATED"
                if target.status == "Activo"
                else "USER_DEACTIVATED"
            ),
            detail={
                "status_before": before_status,
                "status_after": target.status,
            },
        )
    session.commit()
    user = _user_summary(session, target)
    message = "Roles empresariales actualizados. El usuario debe cerrar sesión y volver a iniciar para actualizar sus permisos."
    if user.needs_dentist_profile:
        message += " El usuario tiene rol clínico, pero aún no tiene perfil de odontólogo vinculado."
    return PlatformCompanyUserRoleUpdateResponse(message=message, user=user)


def update_platform_company_dentist_limit(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    payload: PlatformCompanyDentistLimitUpdateRequest,
    metadata: RequestMetadata,
) -> PlatformCompanyDentistLimitUpdateResponse:
    company = session.scalar(
        select(Company).where(Company.id == company_id).with_for_update()
    )
    if company is None:
        raise PlatformError("Empresa no encontrada.", 404)
    seats_in_use = active_dentist_count(session, company.id)
    if payload.max_active_dentists < seats_in_use:
        raise PlatformError(
            f"El límite no puede ser menor que los {seats_in_use} odontólogos activos.",
            409,
        )
    previous = company.max_active_dentists
    company.max_active_dentists = payload.max_active_dentists
    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity="company",
        entity_id=company.id,
        action="COMPANY_DENTIST_LIMIT_CHANGED",
        detail={
            "previous_max_active_dentists": previous,
            "new_max_active_dentists": company.max_active_dentists,
            "active_dentists": seats_in_use,
        },
    )
    session.commit()
    return PlatformCompanyDentistLimitUpdateResponse(
        message="Límite de odontólogos actualizado.",
        company=_detail(session, company),
    )


def create_platform_company(
    session: Session,
    context: AuthContext,
    payload: PlatformCompanyCreateRequest,
    metadata: RequestMetadata,
) -> PlatformCompanyCreateResponse:
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": PLATFORM_COMPANY_LOCK_ID},
    )
    normalized_admin_email = normalize_email(payload.admin_email)
    if session.scalar(select(User.id).where(User.normalized_email == normalized_admin_email)):
        raise PlatformError("Ya existe un usuario con ese correo.", 409)
    normalized_tax_id = normalize_tax_id(payload.tax_id)
    if normalized_tax_id and session.scalar(
        select(Company.id).where(Company.normalized_tax_id == normalized_tax_id)
    ):
        raise PlatformError("Ya existe una empresa con esa identificación tributaria.", 409)
    password = _temporary_password(payload.admin_password)
    company = Company(
        name=payload.company_name,
        slug=_unique_slug(session, payload.company_name),
        company_type=payload.company_type,
        tax_id=payload.tax_id,
        normalized_tax_id=normalized_tax_id,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        city=payload.city,
        country=payload.country,
        timezone=payload.timezone,
        status="Activa",
        max_active_dentists=settings.default_tenant_max_active_dentists,
    )
    session.add(company)
    session.flush()

    site = Site(
        company_id=company.id,
        name="Sede Principal",
        normalized_name="sede principal",
        address=payload.address,
        city=payload.city,
        timezone=None,
        status="Activa",
        created_by=context.user.id,
    )
    session.add(site)
    session.flush()

    permissions = _ensure_permissions(session)
    roles = _seed_roles(
        session,
        company_id=company.id,
        created_by=context.user.id,
        permissions_by_code=permissions,
    )
    admin = User(
        company_id=company.id,
        default_site_id=site.id,
        name=payload.admin_name,
        email=payload.admin_email,
        normalized_email=normalized_admin_email,
        password_hash=hash_password(password),
        status="Activo",
        failed_login_attempts=0,
        must_change_password=True,
        auth_version=1,
        created_by=context.user.id,
    )
    session.add(admin)
    session.flush()
    company.created_by = admin.id
    session.add_all(
        [
            UserRole(
                company_id=company.id,
                user_id=admin.id,
                role_id=roles["ADMINISTRATOR"].id,
                created_by=context.user.id,
            ),
            UserRole(
                company_id=company.id,
                user_id=admin.id,
                role_id=roles["DENTIST_ADMIN"].id,
                created_by=context.user.id,
            ),
            UserSite(
                company_id=company.id,
                user_id=admin.id,
                site_id=site.id,
                is_default=True,
                created_by=context.user.id,
            ),
        ]
    )
    ensure_agenda_seed_data(
        session,
        company_id=company.id,
        admin_user=admin,
        site=site,
    )
    now = datetime.now(timezone.utc)
    company.installation_completed_at = now
    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity_id=company.id,
        action="COMPANY_CREATED",
        detail={"country": company.country, "timezone": company.timezone},
    )
    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity="user",
        entity_id=admin.id,
        action="COMPANY_ADMIN_CREATED",
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise PlatformError("No fue posible crear la empresa por datos duplicados.", 409) from exc
    return PlatformCompanyCreateResponse(
        company=_detail(session, company),
        admin_user=_user_summary(session, admin),
        temporary_password=password,
    )


def change_company_status(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    *,
    active: bool,
    metadata: RequestMetadata,
) -> PlatformCompanyActionResponse:
    company = session.get(Company, company_id)
    if company is None:
        raise PlatformError("Empresa no encontrada.", 404)
    if company.id == context.user.company_id and not active:
        raise PlatformError("No puedes inactivar la empresa de tu propia sesión.", 409)
    company.status = "Activa" if active else "Inactiva"
    company.is_active = active
    if not active:
        session.query(AuthSession).filter(
            AuthSession.company_id == company.id,
            AuthSession.revoked_at.is_(None),
        ).update(
            {
                AuthSession.revoked_at: datetime.now(timezone.utc),
                AuthSession.revoked_reason: "COMPANY_DEACTIVATED",
            },
            synchronize_session=False,
        )
    _audit(
        session,
        context,
        metadata,
        company_id=company.id,
        entity_id=company.id,
        action="COMPANY_REACTIVATED" if active else "COMPANY_DEACTIVATED",
    )
    session.commit()
    return PlatformCompanyActionResponse(
        message="Empresa reactivada." if active else "Empresa inactivada.",
        company=_detail(session, company),
    )
