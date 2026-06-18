from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import (
    get_current_auth_context,
    get_request_metadata,
)
from app.core.config import settings
from app.database.session import get_db
from app.schemas.auth_schema import (
    LoginRequest,
    LogoutResponse,
    MeResponse,
    TokenResponse,
)
from app.schemas.user_schema import ChangePasswordRequest
from app.services.auth_service import (
    AuthContext,
    AuthenticationError,
    change_password,
    login,
    logout,
    register_access_denied,
    refresh,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def set_refresh_cookie(
    response: Response,
    token: str,
    max_age: int,
) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


@router.post("/login", response_model=TokenResponse)
def login_endpoint(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    try:
        token_response, refresh_token, max_age = login(
            session,
            email=str(payload.email),
            password=payload.password,
            metadata=get_request_metadata(request),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        )
    set_refresh_cookie(response, refresh_token, max_age)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
def refresh_endpoint(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=settings.refresh_cookie_name),
    ] = None,
) -> TokenResponse:
    if not refresh_token:
        register_access_denied(
            session,
            metadata=get_request_metadata(request),
            reason="MISSING_REFRESH_TOKEN",
        )
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="No autenticado.")
    try:
        token_response, new_refresh_token, max_age = refresh(
            session,
            refresh_token=refresh_token,
            metadata=get_request_metadata(request),
        )
    except AuthenticationError as exc:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        )
    set_refresh_cookie(response, new_refresh_token, max_age)
    return token_response


@router.post("/logout", response_model=LogoutResponse)
def logout_endpoint(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> LogoutResponse:
    logout(
        session,
        context=context,
        metadata=get_request_metadata(request),
    )
    clear_refresh_cookie(response)
    return LogoutResponse()


@router.get("/me", response_model=MeResponse)
def me_endpoint(
    context: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> MeResponse:
    return MeResponse(
        id=context.user.id,
        name=context.user.name,
        email=context.user.email,
        company_id=context.user.company_id,
        active_site_id=context.auth_session.active_site_id,
        roles=context.roles,
        permissions=context.permissions,
        must_change_password=context.user.must_change_password,
        session_id=context.auth_session.id,
    )


@router.post("/change-password", response_model=TokenResponse)
def change_password_endpoint(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> TokenResponse:
    try:
        token_response, refresh_token, max_age = change_password(
            session,
            context=context,
            current_password=payload.current_password,
            new_password=payload.new_password,
            metadata=get_request_metadata(request),
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    set_refresh_cookie(response, refresh_token, max_age)
    return token_response
