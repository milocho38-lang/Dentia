from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.commercial_control_schema import CommercialAccountList, CommercialAccountSummary, CommercialAccountUpdate, ReversalRequest, TransferCreate
from app.services.auth_service import AuthContext
from app.services.commercial_control_service import CommercialControlError, create_transfer, get_account, list_accounts, reverse_transfer, update_account, verify_transfer

router = APIRouter(prefix="/api/platform/commercial", tags=["Platform commercial"])


def _http(exc: CommercialControlError) -> HTTPException:
    return HTTPException(exc.status_code, detail=str(exc))


@router.get("/accounts", response_model=CommercialAccountList)
def accounts(session: Annotated[Session, Depends(get_db)], _context: Annotated[AuthContext, Depends(require_permission("platform.commercial.view"))]):
    return CommercialAccountList(items=list_accounts(session))


@router.get("/accounts/{company_id}", response_model=CommercialAccountSummary)
def account(company_id: UUID, session: Annotated[Session, Depends(get_db)], _context: Annotated[AuthContext, Depends(require_permission("platform.commercial.view"))]):
    try:
        return get_account(session, company_id)
    except CommercialControlError as exc:
        raise _http(exc)


@router.put("/accounts/{company_id}", response_model=CommercialAccountSummary)
def save_account(company_id: UUID, payload: CommercialAccountUpdate, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("platform.commercial.manage"))]):
    try:
        return update_account(session, context, company_id, payload, get_request_metadata(request))
    except CommercialControlError as exc:
        raise _http(exc)


@router.post("/accounts/{company_id}/transfers", response_model=CommercialAccountSummary, status_code=201)
def record_transfer(company_id: UUID, payload: TransferCreate, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("platform.commercial.manage"))]):
    try:
        return create_transfer(session, context, company_id, payload, get_request_metadata(request))
    except CommercialControlError as exc:
        raise _http(exc)


@router.post("/accounts/{company_id}/transfers/{transfer_id}/verify", response_model=CommercialAccountSummary)
def verify(company_id: UUID, transfer_id: UUID, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("platform.commercial.manage"))]):
    try:
        return verify_transfer(session, context, company_id, transfer_id, get_request_metadata(request))
    except CommercialControlError as exc:
        raise _http(exc)


@router.post("/accounts/{company_id}/transfers/{transfer_id}/reverse", response_model=CommercialAccountSummary)
def reverse(company_id: UUID, transfer_id: UUID, payload: ReversalRequest, request: Request, session: Annotated[Session, Depends(get_db)], context: Annotated[AuthContext, Depends(require_permission("platform.commercial.manage"))]):
    try:
        return reverse_transfer(session, context, company_id, transfer_id, payload.reason, get_request_metadata(request))
    except CommercialControlError as exc:
        raise _http(exc)
