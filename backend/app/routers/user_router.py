from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import (
    get_request_metadata,
    require_permission,
)
from app.database.session import get_db
from app.schemas.user_schema import (
    AccessOptionsResponse,
    ActionResponse,
    TemporaryPasswordResponse,
    UserAuditResponse,
    UserCreateRequest,
    UserListResponse,
    UserRolesRequest,
    UserSessionsResponse,
    UserSitesRequest,
    UserSummaryResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.user_service import (
    UserManagementError,
    assign_roles,
    assign_sites,
    change_status,
    create_user,
    get_access_options,
    get_audit,
    get_sessions,
    get_user_detail,
    list_users,
    reset_password,
    revoke_all_sessions,
    revoke_session,
    unlock_user,
    update_user,
)


router = APIRouter(prefix="/api/users", tags=["Users"])


def handle_user_error(exc: UserManagementError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("", response_model=UserListResponse)
def list_users_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.view"))],
    search: str | None = Query(default=None, max_length=320),
    status: str | None = Query(default=None, max_length=20),
    locked: bool | None = None,
    role_id: UUID | None = None,
    site_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> UserListResponse:
    return list_users(
        session,
        context,
        search=search,
        status=status,
        locked=locked,
        role_id=role_id,
        site_id=site_id,
        page=page,
        page_size=page_size,
    )


@router.get("/access-options", response_model=AccessOptionsResponse)
def access_options_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.view"))],
) -> AccessOptionsResponse:
    return get_access_options(session, context)


@router.post("", response_model=TemporaryPasswordResponse, status_code=201)
def create_user_endpoint(
    payload: UserCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.create"))],
) -> TemporaryPasswordResponse:
    try:
        return create_user(
            session,
            context,
            payload,
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.get("/{user_id}", response_model=UserSummaryResponse)
def get_user_endpoint(
    user_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.view"))],
) -> UserSummaryResponse:
    try:
        return get_user_detail(session, context, user_id)
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.patch("/{user_id}", response_model=UserSummaryResponse)
def update_user_endpoint(
    user_id: UUID,
    payload: UserUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.update"))],
) -> UserSummaryResponse:
    try:
        return update_user(
            session,
            context,
            user_id,
            payload,
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/activate", response_model=ActionResponse)
def activate_user_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.update"))],
) -> ActionResponse:
    try:
        return change_status(
            session, context, user_id, "Activo", get_request_metadata(request)
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/suspend", response_model=ActionResponse)
def suspend_user_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.update"))],
) -> ActionResponse:
    try:
        return change_status(
            session,
            context,
            user_id,
            "Suspendido",
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/deactivate", response_model=ActionResponse)
def deactivate_user_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("users.deactivate"))
    ],
) -> ActionResponse:
    try:
        return change_status(
            session,
            context,
            user_id,
            "Inactivo",
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/unlock", response_model=ActionResponse)
def unlock_user_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("users.unlock"))],
) -> ActionResponse:
    try:
        return unlock_user(
            session, context, user_id, get_request_metadata(request)
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/reset-password", response_model=TemporaryPasswordResponse)
def reset_password_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("users.reset_password"))
    ],
) -> TemporaryPasswordResponse:
    try:
        return reset_password(
            session, context, user_id, get_request_metadata(request)
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.put("/{user_id}/roles", response_model=UserSummaryResponse)
def assign_roles_endpoint(
    user_id: UUID,
    payload: UserRolesRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("users.assign_roles"))
    ],
) -> UserSummaryResponse:
    try:
        return assign_roles(
            session,
            context,
            user_id,
            payload,
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.put("/{user_id}/sites", response_model=UserSummaryResponse)
def assign_sites_endpoint(
    user_id: UUID,
    payload: UserSitesRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("users.assign_sites"))
    ],
) -> UserSummaryResponse:
    try:
        return assign_sites(
            session,
            context,
            user_id,
            payload,
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.get("/{user_id}/sessions", response_model=UserSessionsResponse)
def get_sessions_endpoint(
    user_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("sessions.view_all"))
    ],
) -> UserSessionsResponse:
    try:
        return get_sessions(session, context, user_id)
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post(
    "/{user_id}/sessions/{session_id}/revoke",
    response_model=ActionResponse,
)
def revoke_session_endpoint(
    user_id: UUID,
    session_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("sessions.revoke_all"))
    ],
) -> ActionResponse:
    try:
        return revoke_session(
            session,
            context,
            user_id,
            session_id,
            get_request_metadata(request),
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.post("/{user_id}/sessions/revoke-all", response_model=ActionResponse)
def revoke_all_sessions_endpoint(
    user_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("sessions.revoke_all"))
    ],
) -> ActionResponse:
    try:
        return revoke_all_sessions(
            session, context, user_id, get_request_metadata(request)
        )
    except UserManagementError as exc:
        raise handle_user_error(exc)


@router.get("/{user_id}/audit", response_model=UserAuditResponse)
def get_audit_endpoint(
    user_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("audit.view"))],
) -> UserAuditResponse:
    try:
        return get_audit(session, context, user_id)
    except UserManagementError as exc:
        raise handle_user_error(exc)
