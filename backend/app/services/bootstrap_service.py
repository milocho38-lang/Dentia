import re
from dataclasses import dataclass
from datetime import datetime, timezone

from pwdlib import PasswordHash
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.security_catalog import PERMISSIONS, ROLES, validate_security_catalog
from app.models.associations import RolePermission, UserRole, UserSite
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.permission import Permission
from app.models.role import Role
from app.models.site import Site
from app.models.user import User


PASSWORD_HASH = PasswordHash.recommended()
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BOOTSTRAP_ADVISORY_LOCK_ID = 3_368_450_051


class BootstrapError(RuntimeError):
    pass


@dataclass(frozen=True)
class BootstrapInput:
    company_name: str
    company_slug: str
    site_name: str
    admin_name: str
    admin_email: str
    admin_password: str


@dataclass(frozen=True)
class BootstrapResult:
    company_id: str
    site_id: str
    admin_user_id: str
    permission_count: int
    role_count: int


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def validate_bootstrap_input(data: BootstrapInput) -> BootstrapInput:
    company_name = data.company_name.strip()
    company_slug = data.company_slug.strip().casefold()
    site_name = data.site_name.strip()
    admin_name = data.admin_name.strip()
    admin_email = data.admin_email.strip()
    normalized_email = normalize_email(admin_email)

    if not company_name:
        raise BootstrapError("El nombre de la empresa es obligatorio.")
    if not SLUG_PATTERN.fullmatch(company_slug):
        raise BootstrapError(
            "El slug solo puede contener letras minúsculas, números y guiones."
        )
    if not site_name:
        raise BootstrapError("El nombre de la sede es obligatorio.")
    if not admin_name:
        raise BootstrapError("El nombre del administrador es obligatorio.")
    if "@" not in normalized_email or normalized_email.startswith("@"):
        raise BootstrapError("El correo del administrador no es válido.")
    if len(data.admin_password) < 12:
        raise BootstrapError("La contraseña debe tener al menos 12 caracteres.")
    if len(data.admin_password) > 256:
        raise BootstrapError("La contraseña excede la longitud permitida.")

    return BootstrapInput(
        company_name=company_name,
        company_slug=company_slug,
        site_name=site_name,
        admin_name=admin_name,
        admin_email=admin_email,
        admin_password=data.admin_password,
    )


def ensure_bootstrap_available(session: Session) -> None:
    company_count = session.scalar(select(func.count()).select_from(Company))
    user_count = session.scalar(select(func.count()).select_from(User))

    if company_count or user_count:
        raise BootstrapError(
            "La instalación ya contiene empresas o usuarios. "
            "El bootstrap solo puede ejecutarse una vez."
        )


def bootstrap_installation(
    session: Session,
    raw_data: BootstrapInput,
) -> BootstrapResult:
    validate_security_catalog()
    data = validate_bootstrap_input(raw_data)
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": BOOTSTRAP_ADVISORY_LOCK_ID},
    )
    ensure_bootstrap_available(session)

    company = Company(
        name=data.company_name,
        slug=data.company_slug,
        status="Activa",
    )
    session.add(company)
    session.flush()

    site = Site(
        company_id=company.id,
        name=data.site_name,
        status="Activa",
    )
    session.add(site)
    session.flush()

    permissions_by_code: dict[str, Permission] = {}
    for definition in PERMISSIONS:
        permission = Permission(
            code=definition.code,
            name=definition.name,
            module=definition.module,
            description=definition.description,
        )
        permissions_by_code[definition.code] = permission
        session.add(permission)
    session.flush()

    roles_by_code: dict[str, Role] = {}
    for definition in ROLES:
        role = Role(
            company_id=company.id,
            code=definition.code,
            name=definition.name,
            description=definition.description,
            is_system=True,
        )
        roles_by_code[definition.code] = role
        session.add(role)
    session.flush()

    admin = User(
        company_id=company.id,
        default_site_id=site.id,
        name=data.admin_name,
        email=data.admin_email,
        normalized_email=normalize_email(data.admin_email),
        password_hash=PASSWORD_HASH.hash(data.admin_password),
        status="Activo",
        failed_login_attempts=0,
        must_change_password=False,
        auth_version=1,
    )
    session.add(admin)
    session.flush()

    company.created_by = admin.id
    site.created_by = admin.id
    for role in roles_by_code.values():
        role.created_by = admin.id

    session.add(
        UserRole(
            company_id=company.id,
            user_id=admin.id,
            role_id=roles_by_code["ADMINISTRATOR"].id,
            created_by=admin.id,
        )
    )
    session.add(
        UserSite(
            company_id=company.id,
            user_id=admin.id,
            site_id=site.id,
            is_default=True,
            created_by=admin.id,
        )
    )

    for role_definition in ROLES:
        role = roles_by_code[role_definition.code]
        for permission_code in sorted(role_definition.permission_codes):
            session.add(
                RolePermission(
                    company_id=company.id,
                    role_id=role.id,
                    permission_id=permissions_by_code[permission_code].id,
                    created_by=admin.id,
                )
            )

    completed_at = datetime.now(timezone.utc)
    company.installation_completed_at = completed_at

    session.add(
        AuditEvent(
            company_id=company.id,
            user_id=admin.id,
            entity="installation",
            entity_id=company.id,
            action="INITIAL_INSTALLATION",
            result="SUCCESS",
            detail={
                "company_slug": company.slug,
                "site_id": str(site.id),
                "permission_count": len(PERMISSIONS),
                "role_count": len(ROLES),
                "completed_at": completed_at.isoformat(),
            },
        )
    )

    session.commit()

    return BootstrapResult(
        company_id=str(company.id),
        site_id=str(site.id),
        admin_user_id=str(admin.id),
        permission_count=len(PERMISSIONS),
        role_count=len(ROLES),
    )
