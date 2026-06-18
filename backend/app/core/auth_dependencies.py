from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import AccessTokenError, decode_access_token, utc_now
from app.database.session import get_db
from app.services.auth_service import (
    AuthContext,
    RequestMetadata,
    build_auth_context,
    register_access_denied,
)


bearer_scheme = HTTPBearer(auto_error=False)


def get_request_metadata(request: Request) -> RequestMetadata:
    return RequestMetadata(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def get_current_auth_context(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_db)],
) -> AuthContext:
    metadata = get_request_metadata(request)
    if credentials is None or credentials.scheme.casefold() != "bearer":
        register_access_denied(
            session,
            metadata=metadata,
            reason="MISSING_ACCESS_TOKEN",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
        company_id = UUID(payload["empresa_id"])
        site_id = UUID(payload["sede_id"]) if payload.get("sede_id") else None
        auth_version = int(payload.get("ver", 0))
    except (AccessTokenError, ValueError, TypeError, KeyError):
        register_access_denied(
            session,
            metadata=metadata,
            reason="INVALID_ACCESS_TOKEN",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    context = build_auth_context(
        session,
        user_id=user_id,
        session_id=session_id,
        company_id=company_id,
        site_id=site_id,
        auth_version=auth_version,
    )
    if context is None:
        register_access_denied(
            session,
            metadata=metadata,
            reason="INVALID_SESSION_CONTEXT",
            company_id=company_id,
            user_id=user_id,
            session_id=session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    context.auth_session.last_seen_at = utc_now()
    session.commit()
    return context
