from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.orthodontics_schema import (
    OrthodonticsAccessResponse,
    OrthodonticsAssignmentActionResponse,
    OrthodonticsAssignmentCreateRequest,
    OrthodonticsAssignmentListResponse,
    OrthodonticsAssignmentRevokeRequest,
    OrthodonticsEntitlementResponse,
)
from app.services.auth_service import AuthContext
from app.services.orthodontics_entitlement_service import (
    OrthodonticsError,
    assign_dentist,
    get_tenant_entitlement,
    list_tenant_assignments,
    resolve_orthodontics_access,
    revoke_assignment,
)


router = APIRouter(prefix="/api/orthodontics", tags=["Orthodontics"])


def _handle(exc: OrthodonticsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get("/entitlement", response_model=OrthodonticsEntitlementResponse)
def entitlement_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.entitlement.view"))
    ],
) -> OrthodonticsEntitlementResponse:
    return get_tenant_entitlement(session, context)


@router.get("/assignments", response_model=OrthodonticsAssignmentListResponse)
def assignments_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.assignment.view"))
    ],
) -> OrthodonticsAssignmentListResponse:
    return list_tenant_assignments(session, context)


@router.post(
    "/assignments",
    response_model=OrthodonticsAssignmentActionResponse,
)
def assign_endpoint(
    payload: OrthodonticsAssignmentCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.assignment.manage"))
    ],
) -> OrthodonticsAssignmentActionResponse:
    try:
        return assign_dentist(
            session,
            context,
            payload.dentist_id,
            get_request_metadata(request),
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.post(
    "/assignments/{assignment_id}/revoke",
    response_model=OrthodonticsAssignmentActionResponse,
)
def revoke_endpoint(
    assignment_id: UUID,
    payload: OrthodonticsAssignmentRevokeRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.assignment.manage"))
    ],
) -> OrthodonticsAssignmentActionResponse:
    try:
        return revoke_assignment(
            session,
            context,
            assignment_id,
            get_request_metadata(request),
            reason=payload.reason,
        )
    except OrthodonticsError as exc:
        raise _handle(exc)


@router.get("/access", response_model=OrthodonticsAccessResponse)
def access_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("clinical.view"))],
) -> OrthodonticsAccessResponse:
    return resolve_orthodontics_access(session, context)
