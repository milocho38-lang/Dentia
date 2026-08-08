from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_auth_context, get_request_metadata
from app.core.config import settings
from app.database.session import get_db
from app.schemas.consent_access_schema import AccessAuditResponse, AccessIssueRequest, AccessIssuedResponse, AccessRevokeRequest, AccessSessionResponse, AcceptanceEvidenceResponse, AcceptanceRequirementsResponse, AcceptanceSubmitRequest, AcceptanceSubmitResponse, AcceptanceSummaryResponse, ClarificationCreateRequest, ClarificationResponse, OtpRequestResponse, OtpVerifyRequest, OtpVerifyResponse, PublicConsentDocumentResponse, PublicLinkResponse
from app.services.auth_service import AuthContext
from app.services.consent_access_service import ConsentAccessError, create_clarification, issue_access, list_access, list_access_audit, list_clarifications, public_document, public_link, request_otp, resolve_clarification, revoke_access, verify_otp
from app.services.consent_instance_service import ConsentInstanceError
from app.services.consent_acceptance_service import ConsentAcceptanceError, acceptance_evidence, acceptance_requirements, acceptance_summary, audit_acceptance_rejection, private_final_document, public_final_document, resend_copy, submit_acceptance

private = APIRouter(prefix="/api/consent-instances", tags=["Acceso a consentimientos"])
public = APIRouter(prefix="/api/public/consents", tags=["Portal público de consentimientos"])

def _error(exc): return HTTPException(status_code=exc.status_code,detail=str(exc))
def _permission(code):
    def permission_dependency(context: Annotated[AuthContext,Depends(get_current_auth_context)]):
        if context.user.must_change_password or code not in context.permissions: raise HTTPException(403,"No tienes permisos para realizar esta acción.")
        return context
    return permission_dependency
def _no_store(response: Response):
    response.headers["Cache-Control"]="no-store, max-age=0"; response.headers["Pragma"]="no-cache"; response.headers["X-Frame-Options"]="DENY"; response.headers["Referrer-Policy"]="no-referrer"; response.headers["X-Robots-Tag"]="noindex, nofollow"; response.headers["Content-Security-Policy"]="default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

@private.post("/{instance_id}/access-sessions",response_model=AccessIssuedResponse,status_code=201)
def issue(instance_id:UUID,payload:AccessIssueRequest,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.access.issue"))]):
    try:return issue_access(session,context,instance_id,get_request_metadata(request),payload.expires_in_hours)
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@private.get("/{instance_id}/access-sessions",response_model=list[AccessSessionResponse])
def accesses(instance_id:UUID,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.access.read"))]):
    try:return list_access(session,context,instance_id)
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@private.get("/{instance_id}/access-sessions/audit",response_model=list[AccessAuditResponse])
def access_audit(instance_id:UUID,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.access.view_audit"))]):
    try:return list_access_audit(session,context,instance_id)
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@private.post("/{instance_id}/access-sessions/{access_id}/revoke",response_model=AccessSessionResponse)
def revoke(instance_id:UUID,access_id:UUID,payload:AccessRevokeRequest,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.access.revoke"))]):
    try:return revoke_access(session,context,instance_id,access_id,payload.reason,get_request_metadata(request))
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@private.post("/{instance_id}/access-sessions/reissue",response_model=AccessIssuedResponse,status_code=201)
def reissue(instance_id:UUID,payload:AccessIssueRequest,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.access.reissue"))]):
    try:return issue_access(session,context,instance_id,get_request_metadata(request),payload.expires_in_hours,reissue=True)
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@private.get("/{instance_id}/clarifications",response_model=list[ClarificationResponse])
def clarifications(instance_id:UUID,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.clarification.read"))]):return list_clarifications(session,context,instance_id)

@private.post("/{instance_id}/clarifications/{clarification_id}/resolve",response_model=ClarificationResponse)
def resolve(instance_id:UUID,clarification_id:UUID,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.clarification.manage"))]):
    try:return resolve_clarification(session,context,instance_id,clarification_id,get_request_metadata(request))
    except ConsentAccessError as exc:raise _error(exc)

@public.get("/{token}",response_model=PublicLinkResponse)
def link(token:str,response:Response,request:Request,session:Annotated[Session,Depends(get_db)]):
    _no_store(response)
    try:return public_link(session,token,get_request_metadata(request))
    except ConsentAccessError as exc:raise _error(exc)

@public.post("/{token}/otp",response_model=OtpRequestResponse)
def otp(token:str,response:Response,request:Request,session:Annotated[Session,Depends(get_db)]):
    _no_store(response)
    try:return request_otp(session,token,get_request_metadata(request))
    except ConsentAccessError as exc:raise _error(exc)

@public.post("/{token}/otp/verify",response_model=OtpVerifyResponse)
def verify(token:str,payload:OtpVerifyRequest,response:Response,request:Request,session:Annotated[Session,Depends(get_db)]):
    _no_store(response)
    try:
        raw,expires=verify_otp(session,token,payload.code,get_request_metadata(request)); response.set_cookie(settings.consent_public_cookie_name,raw,httponly=True,secure=(settings.consent_public_cookie_secure or settings.app_env == "production"),samesite="strict",path="/api/public/consents",max_age=settings.consent_public_session_minutes*60); return OtpVerifyResponse(detail="Canal verificado.",expires_at=expires)
    except ConsentAccessError as exc:raise _error(exc)

@public.get("/{token}/document",response_model=PublicConsentDocumentResponse)
def document(token:str,response:Response,request:Request,session:Annotated[Session,Depends(get_db)],public_cookie:Annotated[str|None,Cookie(alias=settings.consent_public_cookie_name)]=None):
    _no_store(response)
    try:return public_document(session,token,public_cookie,get_request_metadata(request))
    except (ConsentAccessError,ConsentInstanceError) as exc:raise _error(exc)

@public.post("/{token}/clarification",response_model=ClarificationResponse,status_code=201)
def clarification(token:str,payload:ClarificationCreateRequest,response:Response,request:Request,session:Annotated[Session,Depends(get_db)],public_cookie:Annotated[str|None,Cookie(alias=settings.consent_public_cookie_name)]=None):
    _no_store(response)
    try:return create_clarification(session,token,public_cookie,payload.message,get_request_metadata(request))
    except ConsentAccessError as exc:raise _error(exc)

@public.get("/{token}/acceptance-requirements",response_model=AcceptanceRequirementsResponse)
def requirements(token:str,response:Response,request:Request,session:Annotated[Session,Depends(get_db)],public_cookie:Annotated[str|None,Cookie(alias=settings.consent_public_cookie_name)]=None):
    _no_store(response)
    try:return acceptance_requirements(session,token,public_cookie,get_request_metadata(request))
    except (ConsentAccessError,ConsentAcceptanceError) as exc:raise _error(exc)

@public.post("/{token}/acceptance",response_model=AcceptanceSubmitResponse)
def accept(token:str,payload:AcceptanceSubmitRequest,response:Response,request:Request,session:Annotated[Session,Depends(get_db)],public_cookie:Annotated[str|None,Cookie(alias=settings.consent_public_cookie_name)]=None):
    _no_store(response); metadata=get_request_metadata(request)
    try:return submit_acceptance(session,token,public_cookie,payload,metadata)
    except ConsentAcceptanceError as exc:
        audit_acceptance_rejection(session,token,payload,metadata,exc)
        raise HTTPException(status_code=exc.status_code,detail={"code":exc.code,"message":str(exc)})
    except ConsentAccessError as exc:
        raise HTTPException(status_code=exc.status_code,detail={"code":"SESSION_INVALID","message":"La sesión no está disponible."})

@public.get("/final-documents/{download_token}")
def public_download(download_token:str,response:Response,request:Request,session:Annotated[Session,Depends(get_db)]):
    _no_store(response)
    try:
        final,path=public_final_document(session,download_token,get_request_metadata(request))
        return FileResponse(path,media_type="application/pdf",filename=final.filename,headers={"Cache-Control":"no-store, max-age=0"})
    except ConsentAcceptanceError as exc:raise _error(exc)

@private.get("/{instance_id}/acceptance",response_model=AcceptanceSummaryResponse)
def acceptance(instance_id:UUID,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.acceptance.read"))]):
    try:return acceptance_summary(session,context,instance_id)
    except (ConsentAcceptanceError,ConsentInstanceError) as exc:raise _error(exc)

@private.get("/{instance_id}/acceptance/evidence",response_model=AcceptanceEvidenceResponse)
def evidence(instance_id:UUID,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.acceptance.view_evidence"))]):
    try:return acceptance_evidence(session,context,instance_id)
    except (ConsentAcceptanceError,ConsentInstanceError) as exc:raise _error(exc)

@private.get("/{instance_id}/final-document")
def final_document(instance_id:UUID,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.final_document.download"))]):
    try:
        final,path=private_final_document(session,context,instance_id,get_request_metadata(request))
        return FileResponse(path,media_type="application/pdf",filename=final.filename,headers={"Cache-Control":"private, no-store"})
    except (ConsentAcceptanceError,ConsentInstanceError) as exc:raise _error(exc)

@private.post("/{instance_id}/copy-deliveries/resend")
def resend(instance_id:UUID,request:Request,session:Annotated[Session,Depends(get_db)],context:Annotated[AuthContext,Depends(_permission("consent.copy.resend"))]):
    try:return resend_copy(session,context,instance_id,get_request_metadata(request))
    except (ConsentAcceptanceError,ConsentInstanceError) as exc:raise _error(exc)
