from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.models.agenda import Dentist, DentistSite
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.orthodontics import (
    OrthodonticsDentistAssignment,
    OrthodonticsEntitlement,
)
from app.models.user import User
from app.schemas.orthodontics_schema import (
    OrthodonticsAccessResponse,
    OrthodonticsAssignmentActionResponse,
    OrthodonticsAssignmentListResponse,
    OrthodonticsDentistAssignmentResponse,
    OrthodonticsEntitlementResponse,
    OrthodonticsEntitlementUpdateRequest,
    OrthodonticsSeatSummary,
)
from app.services.auth_service import AuthContext, RequestMetadata


class OrthodonticsError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    session: Session,
    *,
    company_id: UUID,
    actor_user_id: UUID | None,
    auth_session_id: UUID | None,
    entity: str,
    entity_id: UUID | None,
    action: str,
    metadata: RequestMetadata | None,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=company_id,
            user_id=actor_user_id,
            session_id=auth_session_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address if metadata else None,
            user_agent=metadata.user_agent if metadata else None,
        )
    )


def _is_effectively_enabled(
    entitlement: OrthodonticsEntitlement | None,
    *,
    at: datetime | None = None,
) -> bool:
    if entitlement is None or entitlement.status != "ACTIVE":
        return False
    current = at or _now()
    if entitlement.effective_from and entitlement.effective_from > current:
        return False
    if entitlement.effective_until and entitlement.effective_until < current:
        return False
    return True


def _active_assignment_statement(company_id: UUID):
    linked_user = aliased(User)
    return (
        select(OrthodonticsDentistAssignment)
        .join(Dentist, Dentist.id == OrthodonticsDentistAssignment.dentist_id)
        .join(linked_user, linked_user.id == Dentist.user_id)
        .where(
            OrthodonticsDentistAssignment.company_id == company_id,
            OrthodonticsDentistAssignment.is_active.is_(True),
            Dentist.company_id == company_id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
            linked_user.company_id == company_id,
            linked_user.is_active.is_(True),
            linked_user.status == "Activo",
        )
    )


def active_orthodontics_assignment_count(
    session: Session,
    company_id: UUID,
) -> int:
    statement = _active_assignment_statement(company_id).with_only_columns(
        func.count(OrthodonticsDentistAssignment.id)
    )
    return int(session.scalar(statement) or 0)


def _seat_summary(
    session: Session,
    company_id: UUID,
    entitlement: OrthodonticsEntitlement | None,
) -> OrthodonticsSeatSummary:
    assigned = active_orthodontics_assignment_count(session, company_id)
    limit = entitlement.seat_limit if entitlement else 0
    available = max(limit - assigned, 0) if _is_effectively_enabled(entitlement) else 0
    return OrthodonticsSeatSummary(
        seat_limit=limit,
        assigned_active=assigned,
        available=available,
    )


def _entitlement_response(
    session: Session,
    company_id: UUID,
    entitlement: OrthodonticsEntitlement | None,
) -> OrthodonticsEntitlementResponse:
    return OrthodonticsEntitlementResponse(
        id=entitlement.id if entitlement else None,
        company_id=company_id,
        enabled=_is_effectively_enabled(entitlement),
        status=entitlement.status if entitlement else "DISABLED",
        effective_from=entitlement.effective_from if entitlement else None,
        effective_until=entitlement.effective_until if entitlement else None,
        seats=_seat_summary(session, company_id, entitlement),
        created_at=entitlement.created_at if entitlement else None,
        updated_at=entitlement.updated_at if entitlement else None,
    )


def _company(session: Session, company_id: UUID, *, lock: bool = False) -> Company:
    statement = select(Company).where(Company.id == company_id)
    if lock:
        statement = statement.with_for_update()
    company = session.scalar(statement)
    if company is None:
        raise OrthodonticsError(
            "ORTHODONTICS_COMPANY_NOT_FOUND",
            "Empresa no encontrada.",
            404,
        )
    return company


def _entitlement(
    session: Session,
    company_id: UUID,
    *,
    lock: bool = False,
) -> OrthodonticsEntitlement | None:
    statement = select(OrthodonticsEntitlement).where(
        OrthodonticsEntitlement.company_id == company_id
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_platform_entitlement(
    session: Session,
    company_id: UUID,
) -> OrthodonticsEntitlementResponse:
    _company(session, company_id)
    return _entitlement_response(
        session,
        company_id,
        _entitlement(session, company_id),
    )


def update_platform_entitlement(
    session: Session,
    context: AuthContext,
    company_id: UUID,
    payload: OrthodonticsEntitlementUpdateRequest,
    metadata: RequestMetadata,
) -> OrthodonticsEntitlementResponse:
    company = _company(session, company_id, lock=True)
    entitlement = _entitlement(session, company_id, lock=True)
    previous_status = entitlement.status if entitlement else "DISABLED"
    previous_limit = entitlement.seat_limit if entitlement else 0
    seats_in_use = active_orthodontics_assignment_count(session, company_id)
    if payload.seat_limit < seats_in_use:
        raise OrthodonticsError(
            "ORTHODONTICS_SEAT_LIMIT_BELOW_ASSIGNMENTS",
            "El límite no puede ser menor que los cupos asignados a odontólogos activos.",
            409,
        )
    if entitlement is None:
        entitlement = OrthodonticsEntitlement(
            company_id=company.id,
            status="ACTIVE" if payload.enabled else "DISABLED",
            seat_limit=payload.seat_limit,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by=context.user.id,
            updated_by=context.user.id,
        )
        session.add(entitlement)
        session.flush()
    else:
        entitlement.status = "ACTIVE" if payload.enabled else "DISABLED"
        entitlement.seat_limit = payload.seat_limit
        entitlement.effective_from = payload.effective_from
        entitlement.effective_until = payload.effective_until
        entitlement.updated_by = context.user.id

    if previous_status != entitlement.status:
        _audit(
            session,
            company_id=company.id,
            actor_user_id=context.user.id,
            auth_session_id=context.auth_session.id,
            entity="orthodontics_entitlement",
            entity_id=entitlement.id,
            action=(
                "ORTHODONTICS_ENTITLEMENT_ENABLED"
                if entitlement.status == "ACTIVE"
                else "ORTHODONTICS_ENTITLEMENT_DISABLED"
            ),
            metadata=metadata,
            detail={
                "previous_status": previous_status,
                "new_status": entitlement.status,
            },
        )
    if previous_limit != entitlement.seat_limit:
        _audit(
            session,
            company_id=company.id,
            actor_user_id=context.user.id,
            auth_session_id=context.auth_session.id,
            entity="orthodontics_entitlement",
            entity_id=entitlement.id,
            action="ORTHODONTICS_SEAT_LIMIT_CHANGED",
            metadata=metadata,
            detail={
                "previous_seat_limit": previous_limit,
                "new_seat_limit": entitlement.seat_limit,
                "assigned_active": seats_in_use,
            },
        )
    session.commit()
    return _entitlement_response(session, company.id, entitlement)


def get_tenant_entitlement(
    session: Session,
    context: AuthContext,
) -> OrthodonticsEntitlementResponse:
    return _entitlement_response(
        session,
        context.user.company_id,
        _entitlement(session, context.user.company_id),
    )


def _active_assignment_for_dentist(
    session: Session,
    company_id: UUID,
    dentist_id: UUID,
    *,
    lock: bool = False,
) -> OrthodonticsDentistAssignment | None:
    statement = select(OrthodonticsDentistAssignment).where(
        OrthodonticsDentistAssignment.company_id == company_id,
        OrthodonticsDentistAssignment.dentist_id == dentist_id,
        OrthodonticsDentistAssignment.is_active.is_(True),
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
        raise OrthodonticsError(
            "ORTHODONTICS_DENTIST_NOT_IN_COMPANY",
            "El odontólogo no pertenece a la empresa.",
            404,
        )
    user = session.get(User, dentist.user_id) if dentist.user_id else None
    return dentist, user


def _dentist_is_operational(dentist: Dentist, user: User | None) -> bool:
    return bool(
        dentist.is_active
        and dentist.status == "Activo"
        and user is not None
        and user.company_id == dentist.company_id
        and user.is_active
        and user.status == "Activo"
    )


def _assignment_response(
    dentist: Dentist,
    user: User | None,
    assignment: OrthodonticsDentistAssignment | None,
) -> OrthodonticsDentistAssignmentResponse:
    return OrthodonticsDentistAssignmentResponse(
        id=assignment.id if assignment else None,
        dentist_id=dentist.id,
        dentist_name=dentist.name,
        dentist_status=dentist.status,
        dentist_is_active=dentist.is_active,
        user_id=dentist.user_id,
        user_is_active=bool(
            user
            and user.company_id == dentist.company_id
            and user.is_active
            and user.status == "Activo"
        ),
        assigned=bool(assignment and assignment.is_active),
        assigned_at=assignment.assigned_at if assignment else None,
        assigned_by_user_id=(assignment.assigned_by_user_id if assignment else None),
        revoked_at=assignment.revoked_at if assignment else None,
        revoked_by_user_id=(assignment.revoked_by_user_id if assignment else None),
    )


def list_tenant_assignments(
    session: Session,
    context: AuthContext,
) -> OrthodonticsAssignmentListResponse:
    company_id = context.user.company_id
    entitlement = _entitlement(session, company_id)
    dentists = list(
        session.scalars(
            select(Dentist)
            .where(Dentist.company_id == company_id)
            .order_by(Dentist.name)
        )
    )
    active_assignments = {
        assignment.dentist_id: assignment
        for assignment in session.scalars(
            select(OrthodonticsDentistAssignment).where(
                OrthodonticsDentistAssignment.company_id == company_id,
                OrthodonticsDentistAssignment.is_active.is_(True),
            )
        )
    }
    items = []
    for dentist in dentists:
        user = session.get(User, dentist.user_id) if dentist.user_id else None
        items.append(
            _assignment_response(dentist, user, active_assignments.get(dentist.id))
        )
    return OrthodonticsAssignmentListResponse(
        entitlement=_entitlement_response(session, company_id, entitlement),
        items=items,
    )


def assign_dentist(
    session: Session,
    context: AuthContext,
    dentist_id: UUID,
    metadata: RequestMetadata,
) -> OrthodonticsAssignmentActionResponse:
    company_id = context.user.company_id
    entitlement = _entitlement(session, company_id, lock=True)
    if not _is_effectively_enabled(entitlement):
        raise OrthodonticsError(
            "ORTHODONTICS_NOT_ENABLED",
            "El módulo de Ortodoncia no está habilitado para la empresa.",
            409,
        )
    dentist, user = _dentist_and_user(
        session,
        company_id,
        dentist_id,
        lock=True,
    )
    if not _dentist_is_operational(dentist, user):
        raise OrthodonticsError(
            "ORTHODONTICS_DENTIST_INACTIVE",
            "El odontólogo y su usuario vinculado deben estar activos.",
            409,
        )
    existing = _active_assignment_for_dentist(
        session,
        company_id,
        dentist.id,
        lock=True,
    )
    if existing is not None:
        return OrthodonticsAssignmentActionResponse(
            created=False,
            message="El odontólogo ya tiene Ortodoncia asignada.",
            assignment=_assignment_response(dentist, user, existing),
            seats=_seat_summary(session, company_id, entitlement),
        )
    if active_orthodontics_assignment_count(session, company_id) >= entitlement.seat_limit:
        raise OrthodonticsError(
            "ORTHODONTICS_NO_AVAILABLE_SEATS",
            "No hay cupos de Ortodoncia disponibles.",
            409,
        )
    assignment = OrthodonticsDentistAssignment(
        company_id=company_id,
        entitlement_id=entitlement.id,
        dentist_id=dentist.id,
        assigned_at=_now(),
        assigned_by_user_id=context.user.id,
    )
    session.add(assignment)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise OrthodonticsError(
            "ORTHODONTICS_ALREADY_ASSIGNED",
            "El odontólogo ya tiene Ortodoncia asignada.",
            409,
        ) from exc
    _audit(
        session,
        company_id=company_id,
        actor_user_id=context.user.id,
        auth_session_id=context.auth_session.id,
        entity="orthodontics_dentist_assignment",
        entity_id=assignment.id,
        action="ORTHODONTICS_DENTIST_ASSIGNED",
        metadata=metadata,
        detail={"dentist_id": str(dentist.id)},
    )
    session.commit()
    return OrthodonticsAssignmentActionResponse(
        created=True,
        message="Módulo de Ortodoncia asignado.",
        assignment=_assignment_response(dentist, user, assignment),
        seats=_seat_summary(session, company_id, entitlement),
    )


def revoke_assignment(
    session: Session,
    context: AuthContext,
    assignment_id: UUID,
    metadata: RequestMetadata,
    *,
    reason: str | None = None,
) -> OrthodonticsAssignmentActionResponse:
    company_id = context.user.company_id
    assignment = session.scalar(
        select(OrthodonticsDentistAssignment)
        .where(
            OrthodonticsDentistAssignment.id == assignment_id,
            OrthodonticsDentistAssignment.company_id == company_id,
            OrthodonticsDentistAssignment.is_active.is_(True),
        )
        .with_for_update()
    )
    if assignment is None:
        raise OrthodonticsError(
            "ORTHODONTICS_ASSIGNMENT_NOT_FOUND",
            "Asignación de Ortodoncia no encontrada.",
            404,
        )
    dentist, user = _dentist_and_user(
        session,
        company_id,
        assignment.dentist_id,
    )
    assignment.is_active = False
    assignment.revoked_at = _now()
    assignment.revoked_by_user_id = context.user.id
    assignment.revocation_reason = reason.strip() if reason and reason.strip() else None
    _audit(
        session,
        company_id=company_id,
        actor_user_id=context.user.id,
        auth_session_id=context.auth_session.id,
        entity="orthodontics_dentist_assignment",
        entity_id=assignment.id,
        action="ORTHODONTICS_DENTIST_REVOKED",
        metadata=metadata,
        detail={
            "dentist_id": str(dentist.id),
            "reason_provided": bool(assignment.revocation_reason),
        },
    )
    session.commit()
    entitlement = _entitlement(session, company_id)
    return OrthodonticsAssignmentActionResponse(
        created=False,
        message="Módulo de Ortodoncia retirado.",
        assignment=_assignment_response(dentist, user, assignment),
        seats=_seat_summary(session, company_id, entitlement),
    )


def revoke_assignment_for_inactive_dentist(
    session: Session,
    *,
    company_id: UUID,
    dentist_id: UUID,
    actor_user_id: UUID | None,
    auth_session_id: UUID | None,
    metadata: RequestMetadata | None,
    reason: str,
) -> OrthodonticsDentistAssignment | None:
    assignment = _active_assignment_for_dentist(
        session,
        company_id,
        dentist_id,
        lock=True,
    )
    if assignment is None:
        return None
    assignment.is_active = False
    assignment.revoked_at = _now()
    assignment.revoked_by_user_id = actor_user_id
    assignment.revocation_reason = reason[:300]
    _audit(
        session,
        company_id=company_id,
        actor_user_id=actor_user_id,
        auth_session_id=auth_session_id,
        entity="orthodontics_dentist_assignment",
        entity_id=assignment.id,
        action="ORTHODONTICS_DENTIST_REVOKED",
        metadata=metadata,
        detail={
            "dentist_id": str(dentist_id),
            "reason": reason,
            "automatic": True,
        },
    )
    return assignment


def resolve_orthodontics_access(
    session: Session,
    context: AuthContext,
) -> OrthodonticsAccessResponse:
    company_id = context.user.company_id
    entitlement = _entitlement(session, company_id)
    enabled = _is_effectively_enabled(entitlement)
    if not enabled:
        return OrthodonticsAccessResponse(
            allowed=False,
            code="ORTHODONTICS_NOT_ENABLED",
            message="El módulo de Ortodoncia no está habilitado para la empresa.",
            company_id=company_id,
            dentist_id=None,
            entitlement_enabled=False,
            assignment_active=False,
        )
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )
    if dentist is None or not context.user.is_active or context.user.status != "Activo":
        return OrthodonticsAccessResponse(
            allowed=False,
            code="ORTHODONTICS_DENTIST_INACTIVE",
            message="No existe un perfil odontológico activo para este usuario.",
            company_id=company_id,
            dentist_id=dentist.id if dentist else None,
            entitlement_enabled=True,
            assignment_active=False,
        )
    assignment = _active_assignment_for_dentist(
        session,
        company_id,
        dentist.id,
    )
    if assignment is None:
        return OrthodonticsAccessResponse(
            allowed=False,
            code="ORTHODONTICS_ASSIGNMENT_INACTIVE",
            message="El odontólogo no tiene un cupo activo de Ortodoncia.",
            company_id=company_id,
            dentist_id=dentist.id,
            entitlement_enabled=True,
            assignment_active=False,
        )
    if "clinical.view" not in context.permissions:
        return OrthodonticsAccessResponse(
            allowed=False,
            code="ORTHODONTICS_ACCESS_DENIED",
            message="El usuario no tiene permiso clínico para acceder a Ortodoncia.",
            company_id=company_id,
            dentist_id=dentist.id,
            entitlement_enabled=True,
            assignment_active=True,
        )
    active_site_id = context.auth_session.active_site_id
    if active_site_id is not None:
        has_site_scope = bool(
            session.scalar(
                select(DentistSite.id).where(
                    DentistSite.company_id == company_id,
                    DentistSite.dentist_id == dentist.id,
                    DentistSite.site_id == active_site_id,
                    DentistSite.is_active.is_(True),
                )
            )
        )
        if not has_site_scope:
            return OrthodonticsAccessResponse(
                allowed=False,
                code="ORTHODONTICS_ACCESS_DENIED",
                message="El odontólogo no está habilitado en la sede activa.",
                company_id=company_id,
                dentist_id=dentist.id,
                entitlement_enabled=True,
                assignment_active=True,
            )
    return OrthodonticsAccessResponse(
        allowed=True,
        code="ORTHODONTICS_ACCESS_GRANTED",
        message="Acceso a Ortodoncia habilitado.",
        company_id=company_id,
        dentist_id=dentist.id,
        entitlement_enabled=True,
        assignment_active=True,
    )
