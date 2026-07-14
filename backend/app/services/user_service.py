import math
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email, utc_now
from app.core.config import settings
from app.models.associations import UserRole, UserSite
from app.models.agenda import Dentist, DentistSite
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import (
    count_active_administrators,
    count_active_sessions,
    get_active_roles,
    get_active_sites,
    get_company_user,
    get_user_by_email,
    get_user_roles,
    get_user_sites,
    list_company_users,
    list_user_audit,
    list_user_sessions,
)
from app.schemas.user_schema import (
    AccessOptionsResponse,
    ActionResponse,
    AuditEventResponse,
    RoleOptionResponse,
    SiteOptionResponse,
    TemporaryPasswordResponse,
    EnableClinicalRoleRequest,
    UserAuditResponse,
    UserCreateRequest,
    UserListResponse,
    UserRoleResponse,
    UserRolesRequest,
    UserSessionResponse,
    UserSessionsResponse,
    UserSiteResponse,
    UserSitesRequest,
    UserSummaryResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_sites


class UserManagementError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


LAST_ADMIN_LOCK_ID = 3_368_450_062


def _audit(
    session: Session,
    *,
    context: AuthContext,
    metadata: RequestMetadata,
    target_user_id: UUID,
    action: str,
    detail: dict | None = None,
    result: str = "SUCCESS",
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="user",
            entity_id=target_user_id,
            action=action,
            result=result,
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _validate_email(email: str) -> str:
    normalized = normalize_email(email)
    if (
        "@" not in normalized
        or normalized.startswith("@")
        or normalized.endswith("@")
        or "." not in normalized.rsplit("@", 1)[-1]
    ):
        raise UserManagementError("Ingresa un correo electrónico válido.")
    return normalized


def _generate_temporary_password() -> str:
    return f"Dnt!{secrets.token_urlsafe(15)}"


def _build_user_summary(session: Session, user: User) -> UserSummaryResponse:
    role_rows = get_user_roles(session, user.id)
    roles = [
        UserRoleResponse(id=role.id, code=role.code, name=role.name)
        for _, role in role_rows
    ]
    role_codes = [role.code for _, role in role_rows]
    sites = [
        UserSiteResponse(
            id=site.id,
            name=site.name,
            is_default=site.id == user.default_site_id,
        )
        for site in authorized_sites(
            session,
            company_id=user.company_id,
            user_id=user.id,
            roles=role_codes,
        )
    ]
    default_site_name = next(
        (site.name for site in sites if site.id == user.default_site_id),
        None,
    )
    now = utc_now()
    return UserSummaryResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        status=user.status,
        is_active=user.is_active,
        is_locked=bool(user.locked_until and user.locked_until > now),
        locked_until=user.locked_until,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        default_site_id=user.default_site_id,
        default_site_name=default_site_name,
        roles=roles,
        sites=sites,
        active_sessions=count_active_sessions(session, user.id),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _get_target(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    *,
    lock: bool = False,
) -> User:
    user = get_company_user(
        session,
        context.user.company_id,
        user_id,
        lock=lock,
    )
    if user is None:
        raise UserManagementError("Usuario no encontrado.", 404)
    return user


def _validate_roles(
    session: Session,
    context: AuthContext,
    role_ids: list[UUID],
) -> list[Role]:
    unique_ids = list(dict.fromkeys(role_ids))
    roles = get_active_roles(session, context.user.company_id, unique_ids)
    if len(roles) != len(unique_ids):
        raise UserManagementError("Uno o más roles no son válidos.")
    if any(role.code == "ADMINISTRATOR" for role in roles):
        if "ADMINISTRATOR" not in context.roles:
            raise UserManagementError(
                "Solo un Administrador puede asignar ese rol.",
                403,
            )
    return roles


def _validate_sites(
    session: Session,
    context: AuthContext,
    site_ids: list[UUID],
    default_site_id: UUID,
):
    unique_ids = list(dict.fromkeys(site_ids))
    sites = get_active_sites(session, context.user.company_id, unique_ids)
    if len(sites) != len(unique_ids):
        raise UserManagementError("Una o más sedes no son válidas.")
    if default_site_id not in unique_ids:
        raise UserManagementError(
            "La sede predeterminada debe estar asignada."
        )
    return sites


def _has_admin_role(session: Session, user_id: UUID) -> bool:
    return any(role.code == "ADMINISTRATOR" for _, role in get_user_roles(session, user_id))


def _protect_last_admin(
    session: Session,
    context: AuthContext,
    target: User,
) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": LAST_ADMIN_LOCK_ID},
    )
    if (
        target.status == "Activo"
        and target.is_active
        and _has_admin_role(session, target.id)
        and count_active_administrators(session, context.user.company_id) <= 1
    ):
        raise UserManagementError(
            "No puedes modificar al último Administrador activo.",
            409,
        )


def _revoke_sessions(
    session: Session,
    *,
    target: User,
    actor_id: UUID,
    reason: str,
    exclude_session_id: UUID | None = None,
) -> int:
    now = utc_now()
    sessions = list(
        session.scalars(
            select(AuthSession).where(
                AuthSession.company_id == target.company_id,
                AuthSession.user_id == target.id,
                AuthSession.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
            )
        )
    )
    revoked = 0
    for auth_session in sessions:
        if exclude_session_id and auth_session.id == exclude_session_id:
            continue
        auth_session.is_active = False
        auth_session.revoked_at = now
        auth_session.revoked_by = actor_id
        auth_session.revoke_reason = reason
        revoked += 1
    return revoked


def _invalidate_access(
    session: Session,
    *,
    target: User,
    actor_id: UUID,
    reason: str,
) -> int:
    target.auth_version += 1
    return _revoke_sessions(
        session,
        target=target,
        actor_id=actor_id,
        reason=reason,
    )


def _sync_roles(
    session: Session,
    *,
    target: User,
    role_ids: list[UUID],
    actor_id: UUID,
) -> None:
    requested = set(role_ids)
    existing = {
        assignment.role_id: assignment
        for assignment in session.scalars(
            select(UserRole).where(UserRole.user_id == target.id)
        )
    }
    for role_id, assignment in existing.items():
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


def _sync_sites(
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
            select(UserSite).where(UserSite.user_id == target.id)
        )
    }
    for site_id, assignment in existing.items():
        assignment.is_active = site_id in requested
        assignment.is_default = (
            site_id == default_site_id and site_id in requested
        )
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


def _active_company_sites(session: Session, company_id: UUID) -> list[UUID]:
    from app.models.site import Site

    return list(
        session.scalars(
            select(Site.id)
            .where(
                Site.company_id == company_id,
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
            .order_by(Site.name)
        )
    )


def _target_site_ids_for_clinical_profile(
    session: Session,
    target: User,
    role_codes: set[str],
) -> list[UUID]:
    if "ADMINISTRATOR" in role_codes:
        return _active_company_sites(session, target.company_id)
    assigned = [
        site.id
        for _, site in get_user_sites(session, target.id)
        if site.is_active and site.status == "Activa"
    ]
    if assigned:
        return assigned
    return [target.default_site_id] if target.default_site_id else []


def list_users(
    session: Session,
    context: AuthContext,
    *,
    search: str | None,
    status: str | None,
    locked: bool | None,
    role_id: UUID | None,
    site_id: UUID | None,
    page: int,
    page_size: int,
) -> UserListResponse:
    users, total = list_company_users(
        session,
        context.user.company_id,
        search=search,
        status=status,
        locked=locked,
        role_id=role_id,
        site_id=site_id,
        page=page,
        page_size=page_size,
    )
    return UserListResponse(
        items=[_build_user_summary(session, user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
        pages=max(1, math.ceil(total / page_size)),
    )


def get_user_detail(
    session: Session,
    context: AuthContext,
    user_id: UUID,
) -> UserSummaryResponse:
    return _build_user_summary(session, _get_target(session, context, user_id))


def get_access_options(
    session: Session,
    context: AuthContext,
) -> AccessOptionsResponse:
    roles = get_active_roles(session, context.user.company_id)
    if "ADMINISTRATOR" not in context.roles:
        roles = [role for role in roles if role.code != "ADMINISTRATOR"]
    sites = get_active_sites(session, context.user.company_id)
    return AccessOptionsResponse(
        roles=[
            RoleOptionResponse(
                id=role.id,
                code=role.code,
                name=role.name,
                description=role.description,
            )
            for role in roles
        ],
        sites=[SiteOptionResponse(id=site.id, name=site.name) for site in sites],
    )


def create_user(
    session: Session,
    context: AuthContext,
    data: UserCreateRequest,
    metadata: RequestMetadata,
) -> TemporaryPasswordResponse:
    if "users.assign_roles" not in context.permissions:
        raise UserManagementError(
            "No tienes permiso para asignar roles al crear usuarios.",
            403,
        )
    if "users.assign_sites" not in context.permissions:
        raise UserManagementError(
            "No tienes permiso para asignar sedes al crear usuarios.",
            403,
        )
    normalized_email = _validate_email(data.email)
    if get_user_by_email(session, normalized_email):
        raise UserManagementError("Ya existe un usuario con ese correo.", 409)
    roles = _validate_roles(session, context, data.role_ids)
    _validate_sites(
        session,
        context,
        data.site_ids,
        data.default_site_id,
    )
    temporary_password = _generate_temporary_password()
    user = User(
        company_id=context.user.company_id,
        default_site_id=data.default_site_id,
        name=data.name.strip(),
        email=data.email.strip(),
        normalized_email=normalized_email,
        phone=data.phone,
        password_hash=hash_password(temporary_password),
        password_changed_at=datetime.now(timezone.utc),
        must_change_password=True,
        status="Pendiente",
        created_by=context.user.id,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise UserManagementError(
            "Ya existe un usuario con ese correo.",
            409,
        ) from exc
    _sync_roles(
        session,
        target=user,
        role_ids=[role.id for role in roles],
        actor_id=context.user.id,
    )
    _sync_sites(
        session,
        target=user,
        site_ids=data.site_ids,
        default_site_id=data.default_site_id,
        actor_id=context.user.id,
    )
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=user.id,
        action="USER_CREATED",
        detail={
            "status": "Pendiente",
            "role_codes": sorted(role.code for role in roles),
            "site_ids": sorted(str(site_id) for site_id in data.site_ids),
        },
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise UserManagementError(
            "Ya existe un usuario con ese correo.",
            409,
        ) from exc
    return TemporaryPasswordResponse(
        user=_build_user_summary(session, user),
        temporary_password=temporary_password,
    )


def update_user(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    data: UserUpdateRequest,
    metadata: RequestMetadata,
) -> UserSummaryResponse:
    target = _get_target(session, context, user_id, lock=True)
    normalized_email = _validate_email(data.email)
    duplicate = get_user_by_email(session, normalized_email)
    if duplicate and duplicate.id != target.id:
        raise UserManagementError("Ya existe un usuario con ese correo.", 409)
    changes: dict[str, dict[str, str | None]] = {}
    for field, new_value in {
        "name": data.name.strip(),
        "email": data.email.strip(),
        "phone": data.phone,
    }.items():
        old_value = getattr(target, field)
        if old_value != new_value:
            changes[field] = {"before": old_value, "after": new_value}
            setattr(target, field, new_value)
    if target.normalized_email != normalized_email:
        target.normalized_email = normalized_email
        revoked = _invalidate_access(
            session,
            target=target,
            actor_id=context.user.id,
            reason="USER_EMAIL_CHANGED",
        )
        changes["sessions_revoked"] = {"before": None, "after": str(revoked)}
    if changes:
        _audit(
            session,
            context=context,
            metadata=metadata,
            target_user_id=target.id,
            action="USER_UPDATED",
            detail={"changes": changes},
        )
    session.commit()
    return _build_user_summary(session, target)


def change_status(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    new_status: str,
    metadata: RequestMetadata,
) -> ActionResponse:
    target = _get_target(session, context, user_id, lock=True)
    if new_status not in {"Activo", "Suspendido", "Inactivo"}:
        raise UserManagementError("Estado no válido.")
    if target.id == context.user.id and new_status != "Activo":
        raise UserManagementError("No puedes suspender o desactivar tu cuenta.", 409)
    if new_status != "Activo":
        _protect_last_admin(session, context, target)
    if new_status == "Activo":
        roles = get_user_roles(session, target.id)
        is_administrator = any(
            role.code == "ADMINISTRATOR" for _, role in roles
        )
        if not roles or (
            not is_administrator and not get_user_sites(session, target.id)
        ):
            raise UserManagementError(
                "El usuario necesita al menos un rol y una sede para activarse.",
                409,
            )
        if target.default_site_id is None:
            raise UserManagementError(
                "El usuario necesita una sede predeterminada.",
                409,
            )
    old_status = target.status
    target.status = new_status
    target.is_active = new_status != "Inactivo"
    revoked = 0
    if old_status != new_status:
        revoked = _invalidate_access(
            session,
            target=target,
            actor_id=context.user.id,
            reason=f"USER_{new_status.upper()}",
        )
    action = {
        "Activo": "USER_ACTIVATED",
        "Suspendido": "USER_SUSPENDED",
        "Inactivo": "USER_DEACTIVATED",
    }[new_status]
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action=action,
        detail={
            "previous_status": old_status,
            "new_status": new_status,
            "sessions_revoked": revoked,
        },
    )
    session.commit()
    return ActionResponse(
        message=f"Usuario actualizado a {new_status}.",
        user=_build_user_summary(session, target),
    )


def unlock_user(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    metadata: RequestMetadata,
) -> ActionResponse:
    target = _get_target(session, context, user_id, lock=True)
    target.locked_until = None
    target.failed_login_attempts = 0
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="ACCOUNT_UNLOCKED",
    )
    session.commit()
    return ActionResponse(
        message="Usuario desbloqueado.",
        user=_build_user_summary(session, target),
    )


def reset_password(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    metadata: RequestMetadata,
) -> TemporaryPasswordResponse:
    target = _get_target(session, context, user_id, lock=True)
    temporary_password = _generate_temporary_password()
    target.password_hash = hash_password(temporary_password)
    target.password_changed_at = datetime.now(timezone.utc)
    target.must_change_password = True
    revoked = _invalidate_access(
        session,
        target=target,
        actor_id=context.user.id,
        reason="ADMIN_PASSWORD_RESET",
    )
    target.failed_login_attempts = 0
    target.locked_until = None
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="ADMIN_PASSWORD_RESET",
        detail={"sessions_revoked": revoked},
    )
    session.commit()
    return TemporaryPasswordResponse(
        user=_build_user_summary(session, target),
        temporary_password=temporary_password,
    )


def assign_roles(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    data: UserRolesRequest,
    metadata: RequestMetadata,
) -> UserSummaryResponse:
    target = _get_target(session, context, user_id, lock=True)
    roles = _validate_roles(session, context, data.role_ids)
    old_codes = {role.code for _, role in get_user_roles(session, target.id)}
    new_codes = {role.code for role in roles}
    if old_codes == new_codes:
        return _build_user_summary(session, target)
    if target.id == context.user.id and "ADMINISTRATOR" in old_codes and "ADMINISTRATOR" not in new_codes:
        raise UserManagementError("No puedes retirar tu propio rol Administrador.", 409)
    if "ADMINISTRATOR" in old_codes and "ADMINISTRATOR" not in new_codes:
        _protect_last_admin(session, context, target)
    _sync_roles(
        session,
        target=target,
        role_ids=[role.id for role in roles],
        actor_id=context.user.id,
    )
    revoked = _invalidate_access(
        session,
        target=target,
        actor_id=context.user.id,
        reason="USER_ROLES_UPDATED",
    )
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="USER_ROLES_UPDATED",
        detail={
            "before": sorted(old_codes),
            "after": sorted(new_codes),
            "sessions_revoked": revoked,
        },
    )
    session.commit()
    return _build_user_summary(session, target)


def assign_sites(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    data: UserSitesRequest,
    metadata: RequestMetadata,
) -> UserSummaryResponse:
    target = _get_target(session, context, user_id, lock=True)
    _validate_sites(
        session,
        context,
        data.site_ids,
        data.default_site_id,
    )
    old_sites = [str(site.id) for _, site in get_user_sites(session, target.id)]
    old_default = target.default_site_id
    if set(old_sites) == {str(site_id) for site_id in data.site_ids} and (
        old_default == data.default_site_id
    ):
        return _build_user_summary(session, target)
    _sync_sites(
        session,
        target=target,
        site_ids=data.site_ids,
        default_site_id=data.default_site_id,
        actor_id=context.user.id,
    )
    revoked = _invalidate_access(
        session,
        target=target,
        actor_id=context.user.id,
        reason="USER_SITES_UPDATED",
    )
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="USER_SITES_UPDATED",
        detail={
            "before": sorted(old_sites),
            "after": sorted(str(site_id) for site_id in data.site_ids),
            "default_before": str(old_default) if old_default else None,
            "default_after": str(data.default_site_id),
            "sessions_revoked": revoked,
        },
    )
    session.commit()
    return _build_user_summary(session, target)


def enable_clinical_role(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    data: EnableClinicalRoleRequest,
    metadata: RequestMetadata,
) -> UserSummaryResponse:
    if "users.assign_roles" not in context.permissions:
        raise UserManagementError(
            "No tienes permiso para asignar función clínica.",
            403,
        )
    if "sites.manage" not in context.permissions:
        raise UserManagementError(
            "No tienes permiso para crear o asociar perfiles odontológicos.",
            403,
        )
    target = _get_target(session, context, user_id, lock=True)
    if target.status != "Activo" or not target.is_active:
        raise UserManagementError(
            "Solo se puede habilitar función clínica a usuarios activos.",
            409,
        )
    existing_role_rows = get_user_roles(session, target.id)
    existing_role_codes = {role.code for _, role in existing_role_rows}
    clinical_role = session.scalar(
        select(Role).where(
            Role.company_id == target.company_id,
            Role.code == data.role_code,
            Role.is_active.is_(True),
        )
    )
    if clinical_role is None:
        raise UserManagementError("Rol clínico no disponible para esta empresa.", 409)

    dentist = session.scalar(
        select(Dentist)
        .where(
            Dentist.company_id == target.company_id,
            Dentist.user_id == target.id,
        )
        .with_for_update()
    )
    dentist_created = False
    if dentist is None:
        dentist = Dentist(
            company_id=target.company_id,
            user_id=target.id,
            name=target.name,
            status="Activo",
            created_by=context.user.id,
        )
        session.add(dentist)
        session.flush()
        dentist_created = True
    else:
        dentist.is_active = True
        dentist.status = "Activo"
        dentist.name = target.name

    role_added = False
    if data.role_code not in existing_role_codes:
        existing_assignments = {
            assignment.role_id: assignment
            for assignment in session.scalars(
                select(UserRole)
                .where(UserRole.user_id == target.id)
                .with_for_update()
            )
        }
        assignment = existing_assignments.get(clinical_role.id)
        if assignment is None:
            session.add(
                UserRole(
                    company_id=target.company_id,
                    user_id=target.id,
                    role_id=clinical_role.id,
                    created_by=context.user.id,
                )
            )
        else:
            assignment.is_active = True
        role_added = True

    target_site_ids = set(
        _target_site_ids_for_clinical_profile(session, target, existing_role_codes)
    )
    existing_dentist_sites = {
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
    active_existing = {
        site_id
        for site_id, assignment in existing_dentist_sites.items()
        if assignment.is_active
    }
    if not active_existing and target_site_ids:
        for site_id in target_site_ids:
            assignment = existing_dentist_sites.get(site_id)
            if assignment is None:
                session.add(
                    DentistSite(
                        company_id=target.company_id,
                        dentist_id=dentist.id,
                        site_id=site_id,
                        created_by=context.user.id,
                    )
                )
            else:
                assignment.is_active = True

    revoked = _invalidate_access(
        session,
        target=target,
        actor_id=context.user.id,
        reason="USER_CLINICAL_ROLE_ENABLED",
    )
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="USER_CLINICAL_ROLE_ENABLED",
        detail={
            "role_code": data.role_code,
            "role_added": role_added,
            "dentist_id": str(dentist.id),
            "dentist_created": dentist_created,
            "site_ids": sorted(str(site_id) for site_id in target_site_ids),
            "sessions_revoked": revoked,
        },
    )
    session.commit()
    return _build_user_summary(session, target)


def get_sessions(
    session: Session,
    context: AuthContext,
    user_id: UUID,
) -> UserSessionsResponse:
    _get_target(session, context, user_id)
    items = [
        UserSessionResponse(
            id=auth_session.id,
            active_site_id=auth_session.active_site_id,
            active_site_name=site_name,
            ip_address=str(auth_session.ip_address) if auth_session.ip_address else None,
            user_agent=auth_session.user_agent,
            device_name=auth_session.device_name,
            created_at=auth_session.created_at,
            last_seen_at=auth_session.last_seen_at,
            expires_at=auth_session.expires_at,
            revoked_at=auth_session.revoked_at,
            revoke_reason=auth_session.revoke_reason,
            is_active=(
                auth_session.is_active
                and auth_session.revoked_at is None
                and auth_session.expires_at > utc_now()
                and auth_session.last_seen_at
                + timedelta(minutes=settings.session_idle_timeout_minutes)
                > utc_now()
            ),
        )
        for auth_session, site_name in list_user_sessions(
            session, context.user.company_id, user_id
        )
    ]
    return UserSessionsResponse(items=items)


def revoke_session(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    session_id: UUID,
    metadata: RequestMetadata,
) -> ActionResponse:
    target = _get_target(session, context, user_id)
    auth_session = session.scalar(
        select(AuthSession).where(
            AuthSession.id == session_id,
            AuthSession.company_id == context.user.company_id,
            AuthSession.user_id == target.id,
        ).with_for_update()
    )
    if auth_session is None:
        raise UserManagementError("Sesión no encontrada.", 404)
    if auth_session.is_active and auth_session.revoked_at is None:
        auth_session.is_active = False
        auth_session.revoked_at = utc_now()
        auth_session.revoked_by = context.user.id
        auth_session.revoke_reason = "ADMIN_SESSION_REVOKED"
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="SESSION_REVOKED",
        detail={"revoked_session_id": str(auth_session.id)},
    )
    session.commit()
    return ActionResponse(message="Sesión revocada.")


def revoke_all_sessions(
    session: Session,
    context: AuthContext,
    user_id: UUID,
    metadata: RequestMetadata,
) -> ActionResponse:
    target = _get_target(session, context, user_id, lock=True)
    revoked = _revoke_sessions(
        session,
        target=target,
        actor_id=context.user.id,
        reason="ADMIN_REVOKE_ALL",
    )
    target.auth_version += 1
    _audit(
        session,
        context=context,
        metadata=metadata,
        target_user_id=target.id,
        action="USER_SESSIONS_REVOKED",
        detail={"sessions_revoked": revoked},
    )
    session.commit()
    return ActionResponse(message=f"Se revocaron {revoked} sesiones.")


def get_audit(
    session: Session,
    context: AuthContext,
    user_id: UUID,
) -> UserAuditResponse:
    _get_target(session, context, user_id)
    return UserAuditResponse(
        items=[
            AuditEventResponse(
                id=event.id,
                action=event.action,
                result=event.result,
                detail=event.detail,
                ip_address=str(event.ip_address) if event.ip_address else None,
                user_agent=event.user_agent,
                occurred_at=event.occurred_at,
                actor_user_id=event.user_id,
            )
            for event in list_user_audit(
                session, context.user.company_id, user_id
            )
        ]
    )
