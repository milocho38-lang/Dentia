from datetime import date
import ipaddress
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.demo_request_schema import (
    DemoRequestAssignmentUpdate,
    DemoRequestDetail,
    DemoRequestListResponse,
    DemoRequestNoteCreate,
    DemoRequestOwnersResponse,
    DemoRequestScheduleUpdate,
    DemoRequestStatusUpdate,
    PublicDemoRequestCreate,
    PublicDemoRequestResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.demo_request_service import (
    DemoRequestError,
    add_demo_request_note,
    assign_demo_request,
    create_public_demo_request,
    get_demo_request,
    list_demo_request_owners,
    list_demo_requests,
    schedule_demo_request,
    update_demo_request_status,
)


public = APIRouter(prefix="/api/public/demo-requests", tags=["Public demo requests"])
platform = APIRouter(prefix="/api/platform/demo-requests", tags=["Platform demo requests"])


def _handle(exc: DemoRequestError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"


def _public_metadata(request: Request) -> RequestMetadata:
    direct = request.client.host if request.client else None
    selected = direct
    try:
        direct_ip = ipaddress.ip_address(direct) if direct else None
    except ValueError:
        direct_ip = None
    # Forwarded IP is trusted only when the immediate peer is an internal proxy.
    # Choosing the right-most public address prevents a visitor-provided prefix
    # from becoming the rate-limit identity.
    if direct_ip and (direct_ip.is_private or direct_ip.is_loopback):
        candidates = [
            item.strip()
            for item in request.headers.get("x-forwarded-for", "").split(",")
            if item.strip()
        ]
        parsed: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for candidate in candidates:
            try:
                parsed.append(ipaddress.ip_address(candidate))
            except ValueError:
                continue
        public_candidates = [item for item in parsed if item.is_global]
        if public_candidates:
            selected = str(public_candidates[-1])
        elif parsed:
            selected = str(parsed[-1])
    return RequestMetadata(
        ip_address=selected,
        user_agent=(request.headers.get("user-agent") or "")[:500] or None,
    )


@public.post("", response_model=PublicDemoRequestResponse, status_code=201)
def create_public_demo_request_endpoint(
    payload: PublicDemoRequestCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> PublicDemoRequestResponse:
    _no_store(response)
    try:
        return create_public_demo_request(session, payload, _public_metadata(request))
    except DemoRequestError as exc:
        raise _handle(exc)


@platform.get("", response_model=DemoRequestListResponse)
def list_demo_requests_endpoint(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.view"))
    ],
    search: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default=None, max_length=30),
    country: str | None = Query(default=None, max_length=80),
    assigned_to_user_id: UUID | None = Query(default=None),
    created_from: date | None = Query(default=None),
    created_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> DemoRequestListResponse:
    _no_store(response)
    return list_demo_requests(
        session,
        search=search,
        status=status,
        country=country,
        assigned_to_user_id=assigned_to_user_id,
        created_from=created_from,
        created_to=created_to,
        page=page,
        page_size=page_size,
    )


@platform.get("/owners", response_model=DemoRequestOwnersResponse)
def list_demo_request_owners_endpoint(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.view"))
    ],
) -> DemoRequestOwnersResponse:
    _no_store(response)
    return list_demo_request_owners(session)


@platform.get("/{demo_request_id}", response_model=DemoRequestDetail)
def demo_request_detail_endpoint(
    demo_request_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.view"))
    ],
) -> DemoRequestDetail:
    _no_store(response)
    try:
        return get_demo_request(session, demo_request_id)
    except DemoRequestError as exc:
        raise _handle(exc)


@platform.patch("/{demo_request_id}/assignment", response_model=DemoRequestDetail)
def assign_demo_request_endpoint(
    demo_request_id: UUID,
    payload: DemoRequestAssignmentUpdate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.manage"))
    ],
) -> DemoRequestDetail:
    _no_store(response)
    try:
        return assign_demo_request(
            session, context, get_request_metadata(request), demo_request_id, payload
        )
    except DemoRequestError as exc:
        raise _handle(exc)


@platform.patch("/{demo_request_id}/status", response_model=DemoRequestDetail)
def update_demo_request_status_endpoint(
    demo_request_id: UUID,
    payload: DemoRequestStatusUpdate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.manage"))
    ],
) -> DemoRequestDetail:
    _no_store(response)
    try:
        return update_demo_request_status(
            session, context, get_request_metadata(request), demo_request_id, payload
        )
    except DemoRequestError as exc:
        raise _handle(exc)


@platform.patch("/{demo_request_id}/schedule", response_model=DemoRequestDetail)
def schedule_demo_request_endpoint(
    demo_request_id: UUID,
    payload: DemoRequestScheduleUpdate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.manage"))
    ],
) -> DemoRequestDetail:
    _no_store(response)
    try:
        return schedule_demo_request(
            session, context, get_request_metadata(request), demo_request_id, payload
        )
    except DemoRequestError as exc:
        raise _handle(exc)


@platform.post("/{demo_request_id}/notes", response_model=DemoRequestDetail)
def add_demo_request_note_endpoint(
    demo_request_id: UUID,
    payload: DemoRequestNoteCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("platform.demo_requests.manage"))
    ],
) -> DemoRequestDetail:
    _no_store(response)
    try:
        return add_demo_request_note(
            session, context, get_request_metadata(request), demo_request_id, payload
        )
    except DemoRequestError as exc:
        raise _handle(exc)
