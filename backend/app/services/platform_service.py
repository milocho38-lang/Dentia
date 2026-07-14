import re
import secrets
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.core.security_catalog import PERMISSIONS, ROLES
from app.models.agenda import Dentist
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
    PlatformCompanyListItem,
    PlatformCompanyListResponse,
    PlatformSiteSummary,
    PlatformUserSummary,
)
from app.services.agenda_service import ensure_agenda_seed_data
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.organization_service import normalize_tax_id


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
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def _user_summary(session: Session, user: User) -> PlatformUserSummary:
    roles = list(
        session.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
            .order_by(Role.code)
        )
    )
    return PlatformUserSummary(
        id=user.id,
        name=user.name,
        email=user.email,
        status=user.status,
        roles=roles,
    )


def _detail(session: Session, company: Company) -> PlatformCompanyDetail:
    base = _list_item(session, company)
    sites = list(
        session.scalars(
            select(Site).where(Site.company_id == company.id).order_by(Site.name)
        )
    )
    users = list(
        session.scalars(
            select(User).where(User.company_id == company.id).order_by(User.name).limit(10)
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
