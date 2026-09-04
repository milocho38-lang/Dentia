import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Patient
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_template import ConsentAccessSession, ConsentClarificationRequest, ConsentInstance, ConsentInstanceProcedure, ConsentOtpChallenge, ConsentPublicSession, ConsentTemplate, ConsentTemplateVersion
from app.schemas.consent_access_schema import AccessAuditResponse, AccessIssuedResponse, AccessSessionResponse, ClarificationResponse, PublicConsentDocumentResponse
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.consent_library_normalization import validate_patient_facing_content
from app.services.consent_production_readiness import ConsentProductionReadinessError, assert_template_ready
from app.services.consent_instance_service import ConsentInstanceError, _require_instance, _verify_seal
from app.services.consent_declaration_catalog import ConsentDeclarationSetError, DECLARATION_SETS, TEST_DOCUMENT_NOTICE, declaration_set_for
from app.services.consent_acceptance_context import inspect_acceptance_context
from app.services.email_service import EmailDeliveryError, build_consent_otp_email, get_email_provider, use_email_company
from app.services.consent_signer import RESPONSIBLE_ADULT, signer_snapshot_from_instance


class ConsentAccessError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message); self.status_code = status_code


def _now(): return datetime.now(timezone.utc)
def _hash(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()
def _otp_hash(value: str) -> str: return hmac.new(settings.jwt_secret.encode(), value.encode(), hashlib.sha256).hexdigest()
def _token() -> str: return secrets.token_urlsafe(32)
def _public_path(token: str) -> str: return f"/consentimiento/{token}"


def mask_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def _audit(session: Session, access: ConsentAccessSession, action: str, metadata: RequestMetadata, *, user_id: UUID | None = None, result="SUCCESS", detail: dict | None = None):
    session.add(AuditEvent(company_id=access.company_id, user_id=user_id, entity="consent_access", entity_id=access.id, action=action, result=result, detail={"consent_instance_id": str(access.consent_instance_id), "access_session_id": str(access.id), **(detail or {})}, ip_address=metadata.ip_address, user_agent=(metadata.user_agent or "")[:500] or None))


def _response(access: ConsentAccessSession) -> AccessSessionResponse:
    return AccessSessionResponse(id=access.id,status=access.status,recipient_masked=access.recipient_masked,issued_at=access.issued_at,expires_at=access.expires_at,verified_at=access.verified_at,viewed_at=access.viewed_at,clarification_requested_at=access.clarification_requested_at,last_activity_at=access.last_activity_at,row_version=access.row_version)


def _revoke_related(session: Session, access: ConsentAccessSession, now: datetime):
    for challenge in session.scalars(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id==access.id,ConsentOtpChallenge.status=="PENDING")):
        challenge.status="INVALIDATED"
    for public in session.scalars(select(ConsentPublicSession).where(ConsentPublicSession.access_session_id==access.id,ConsentPublicSession.status=="ACTIVE")):
        public.status="REVOKED"; public.revoked_at=now


def issue_access(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata, expires_in_hours: int | None = None, *, reissue=False) -> AccessIssuedResponse:
    instance = _require_instance(session, context, instance_id, lock=True)
    if instance.completion_channel == "PAPER":
        raise ConsentAccessError("Este consentimiento fue preparado para firma en papel.", 409)
    if instance.status not in ({"READY_FOR_REVIEW","PENDING_SIGNATURE"} if reissue else {"READY_FOR_REVIEW"}):
        raise ConsentAccessError("Solo una instancia revisada puede emitir acceso.",409)
    if instance.missing_variables: raise ConsentAccessError("La instancia todavía tiene variables pendientes.",409)
    template = session.get(ConsentTemplate, instance.template_id)
    version = session.get(ConsentTemplateVersion, instance.template_version_id)
    if template is None or version is None:
        raise ConsentAccessError("La plantilla sellada ya no está disponible.", 409)
    try:
        assert_template_ready(session, template=template, version=version, signer_policy=getattr(instance, "signer_policy", "PATIENT_SELF"), channel="ELECTRONIC")
        declaration_set_for(
            instance.country_code,
            instance.language_code,
            actor_type=getattr(instance, "signer_actor_type", "PATIENT_SELF"),
            app_env=settings.app_env,
            acceptance_enabled=settings.consent_acceptance_enabled,
            on_date=_now().date(),
            session=session,
        )
    except (ConsentProductionReadinessError, ConsentDeclarationSetError) as exc:
        raise ConsentAccessError(str(exc), 409) from exc
    patient_content=instance.rendered_content_snapshot or ""; content_validation=validate_patient_facing_content(patient_content,allowed_variables=None,document_type=instance.document_kind,signer_compatibility=getattr(instance, "signer_policy", "PATIENT_SELF"),normalized_hash=_hash(patient_content),enforce_electronic_readiness=True)
    if content_validation.status=="BLOCKED": raise ConsentAccessError("El documento no está disponible para firma electrónica. Contacta a la clínica.",409)
    _verify_seal(instance)
    signer = signer_snapshot_from_instance(instance)
    email = (signer.email or "").strip()
    if not email or "@" not in email: raise ConsentAccessError("El firmante no tiene un correo válido. Actualiza la información antes de emitir acceso.",422)
    now=_now()
    active=list(session.scalars(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id==instance.id,ConsentAccessSession.status.notin_(["REVOKED","EXPIRED"])).with_for_update()))
    if active and not reissue: raise ConsentAccessError("Ya existe un acceso activo. Revócalo o utiliza reemitir.",409)
    for old in active:
        old.status="REVOKED"; old.revoked_at=now; old.revoked_by=context.user.id; old.revoke_reason="REISSUED"; old.row_version+=1; _revoke_related(session,old,now); _audit(session,old,"CONSENT_ACCESS_SESSION_REISSUED",metadata,user_id=context.user.id)
    raw=_token(); hours=expires_in_hours or settings.consent_access_expire_hours
    access=ConsentAccessSession(company_id=instance.company_id,site_id=instance.site_id,consent_instance_id=instance.id,status="ISSUED",public_token_hash=_hash(raw),public_token_prefix=raw[:8],issued_at=now,expires_at=now+timedelta(hours=hours),last_activity_at=now,recipient_masked=mask_email(email),created_by=context.user.id)
    session.add(access); session.flush()
    previous=instance.status; instance.status="PENDING_SIGNATURE"; instance.completion_channel="ELECTRONIC"; instance.updated_by=context.user.id; instance.row_version+=1
    _audit(session,access,"CONSENT_ACCESS_SESSION_REISSUED" if reissue else "CONSENT_ACCESS_SESSION_ISSUED",metadata,user_id=context.user.id,detail={"previous_instance_status":previous,"new_instance_status":instance.status,"expires_at":access.expires_at.isoformat()})
    session.commit()
    public_path = _public_path(raw)
    return AccessIssuedResponse(**_response(access).model_dump(),public_url=f"{settings.public_frontend_url.rstrip('/')}{public_path}",public_path=public_path)


def list_access(session: Session, context: AuthContext, instance_id: UUID) -> list[AccessSessionResponse]:
    instance=_require_instance(session,context,instance_id)
    return [_response(x) for x in session.scalars(select(ConsentAccessSession).where(ConsentAccessSession.company_id==instance.company_id,ConsentAccessSession.consent_instance_id==instance.id).order_by(ConsentAccessSession.issued_at.desc()))]


def list_access_audit(session: Session, context: AuthContext, instance_id: UUID) -> list[AccessAuditResponse]:
    instance=_require_instance(session,context,instance_id)
    access_ids=list(session.scalars(select(ConsentAccessSession.id).where(ConsentAccessSession.company_id==instance.company_id,ConsentAccessSession.consent_instance_id==instance.id)))
    if not access_ids:return []
    rows=session.scalars(select(AuditEvent).where(AuditEvent.company_id==instance.company_id,AuditEvent.entity=="consent_access",AuditEvent.entity_id.in_(access_ids)).order_by(AuditEvent.occurred_at.desc()).limit(200))
    return [AccessAuditResponse(id=x.id,action=x.action,result=x.result,user_id=x.user_id,occurred_at=x.occurred_at,detail=x.detail) for x in rows]


def revoke_access(session: Session, context: AuthContext, instance_id: UUID, access_id: UUID, reason: str, metadata: RequestMetadata):
    _require_instance(session,context,instance_id)
    access=session.scalar(select(ConsentAccessSession).where(ConsentAccessSession.id==access_id,ConsentAccessSession.company_id==context.user.company_id,ConsentAccessSession.consent_instance_id==instance_id).with_for_update())
    if not access: raise ConsentAccessError("Acceso no encontrado.",404)
    if access.status=="REVOKED": raise ConsentAccessError("El acceso ya está revocado.",409)
    now=_now(); access.status="REVOKED"; access.revoked_at=now; access.revoked_by=context.user.id; access.revoke_reason=reason; access.row_version+=1; _revoke_related(session,access,now); _audit(session,access,"CONSENT_ACCESS_SESSION_REVOKED",metadata,user_id=context.user.id,detail={"reason":reason}); session.commit(); return _response(access)


def _public_access(session: Session, token: str, metadata: RequestMetadata, *, lock=False) -> ConsentAccessSession:
    if len(token)<32: raise ConsentAccessError("El enlace no está disponible.",404)
    stmt=select(ConsentAccessSession).where(ConsentAccessSession.public_token_hash==_hash(token))
    if lock: stmt=stmt.with_for_update()
    access=session.scalar(stmt); now=_now()
    if not access: raise ConsentAccessError("El enlace no está disponible.",404)
    if access.status=="REVOKED":
        _audit(session,access,"CONSENT_PUBLIC_ACCESS_DENIED",metadata,result="FAILURE",detail={"reason":"REVOKED"}); session.commit(); raise ConsentAccessError("El enlace no está disponible.",404)
    instance=session.get(ConsentInstance,access.consent_instance_id)
    if not instance or instance.status=="VOIDED":
        _audit(session,access,"CONSENT_PUBLIC_ACCESS_DENIED",metadata,result="FAILURE",detail={"reason":"INSTANCE_UNAVAILABLE"}); session.commit(); raise ConsentAccessError("El enlace no está disponible.",404)
    if access.expires_at<=now:
        access.status="EXPIRED"; _revoke_related(session,access,now); _audit(session,access,"CONSENT_ACCESS_EXPIRED",metadata,result="FAILURE"); session.commit(); raise ConsentAccessError("El enlace no está disponible.",404)
    return access


def public_link(session: Session, token: str, metadata: RequestMetadata):
    access=_public_access(session,token,metadata,lock=True); now=_now()
    window=timedelta(seconds=settings.consent_link_open_window_seconds)
    if not access.open_window_started_at or access.open_window_started_at+window<=now:
        access.open_window_started_at=now; access.open_count=0
    if access.open_count>=settings.consent_link_open_max_requests:
        session.rollback(); raise ConsentAccessError("No fue posible procesar la solicitud en este momento.",429)
    access.open_count+=1; access.last_activity_at=now; _audit(session,access,"CONSENT_ACCESS_LINK_OPENED",metadata); session.commit()
    return {"status":access.status,"recipient_masked":access.recipient_masked,"expires_at":access.expires_at,"message":"Tiene un consentimiento pendiente de revisión."}


def request_otp(session: Session, token: str, metadata: RequestMetadata):
    access=_public_access(session,token,metadata,lock=True); now=_now(); instance=session.get(ConsentInstance,access.consent_instance_id); signer=signer_snapshot_from_instance(instance); email=(signer.email or "").strip()
    recipient_hash=_otp_hash(email.casefold()); ip_hash=_hash(metadata.ip_address) if metadata.ip_address else None
    recent=now-timedelta(minutes=15); daily=now-timedelta(days=1)
    if ip_hash and session.scalar(select(func.count()).select_from(ConsentOtpChallenge).where(ConsentOtpChallenge.request_ip_hash==ip_hash,ConsentOtpChallenge.issued_at>=recent))>=settings.consent_otp_max_sends: raise ConsentAccessError("No fue posible enviar otro código en este momento.",429)
    if session.scalar(select(func.count()).select_from(ConsentOtpChallenge).where(ConsentOtpChallenge.recipient_hash==recipient_hash,ConsentOtpChallenge.issued_at>=daily))>=settings.consent_otp_max_daily_sends: raise ConsentAccessError("No fue posible enviar otro código en este momento.",429)
    previous=session.scalar(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id==access.id,ConsentOtpChallenge.status=="PENDING").order_by(ConsentOtpChallenge.issued_at.desc()).with_for_update())
    resend=0
    if previous:
        elapsed=(now-(previous.last_sent_at or previous.issued_at)).total_seconds()
        if elapsed<settings.consent_otp_resend_seconds: raise ConsentAccessError("Espera antes de solicitar un nuevo código.",429)
        resend=previous.resend_count+1
        if resend>=settings.consent_otp_max_sends: raise ConsentAccessError("No fue posible enviar otro código en este momento.",429)
        previous.status="INVALIDATED"
    otp=f"{secrets.randbelow(1_000_000):06d}"
    challenge=ConsentOtpChallenge(company_id=access.company_id,access_session_id=access.id,otp_hash=_otp_hash(otp),status="PENDING",recipient_masked=access.recipient_masked,recipient_hash=recipient_hash,request_ip_hash=ip_hash,issued_at=now,expires_at=now+timedelta(minutes=settings.consent_otp_expire_minutes),max_attempts=settings.consent_otp_max_attempts,resend_count=resend,last_sent_at=now)
    session.add(challenge); session.flush()
    try:
        with use_email_company(access.company_id):
            get_email_provider().send(build_consent_otp_email(email,otp,settings.consent_otp_expire_minutes))
    except EmailDeliveryError:
        challenge.status="DELIVERY_FAILED"; _audit(session,access,"CONSENT_OTP_DELIVERY_FAILED",metadata,result="FAILURE"); session.commit(); raise ConsentAccessError("No fue posible enviar el código. Intenta nuevamente más tarde.",503)
    access.status="OTP_PENDING"; access.last_activity_at=now; access.row_version+=1; _audit(session,access,"CONSENT_OTP_REQUESTED",metadata); _audit(session,access,"CONSENT_OTP_DELIVERY_SUCCEEDED",metadata); session.commit()
    return {"detail":"Si el canal está disponible, recibirás un código de seguridad.","recipient_masked":access.recipient_masked,"retry_after_seconds":settings.consent_otp_resend_seconds}


def verify_otp(session: Session, token: str, code: str, metadata: RequestMetadata):
    access=_public_access(session,token,metadata,lock=True); now=_now(); challenge=session.scalar(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id==access.id,ConsentOtpChallenge.status=="PENDING").order_by(ConsentOtpChallenge.issued_at.desc()).with_for_update())
    if not challenge or challenge.expires_at<=now: raise ConsentAccessError("El código no es válido o expiró.",400)
    if not hmac.compare_digest(challenge.otp_hash,_otp_hash(code)):
        challenge.failed_attempts+=1; blocked=challenge.failed_attempts>=challenge.max_attempts
        if blocked: challenge.status="BLOCKED"; challenge.blocked_until=now+timedelta(minutes=15)
        _audit(session,access,"CONSENT_OTP_VERIFICATION_FAILED",metadata,result="FAILURE"); session.commit(); raise ConsentAccessError("El código no es válido o expiró.",429 if blocked else 400)
    challenge.status="VERIFIED"; challenge.verified_at=now; access.status="VERIFIED"; access.verified_at=now; access.last_activity_at=now; access.row_version+=1
    for old in session.scalars(select(ConsentPublicSession).where(ConsentPublicSession.access_session_id==access.id,ConsentPublicSession.status=="ACTIVE")): old.status="REVOKED"; old.revoked_at=now
    raw=_token(); public=ConsentPublicSession(company_id=access.company_id,access_session_id=access.id,session_token_hash=_hash(raw),status="ACTIVE",issued_at=now,expires_at=now+timedelta(minutes=settings.consent_public_session_minutes),last_activity_at=now); session.add(public); instance=session.get(ConsentInstance,access.consent_instance_id); _audit(session,access,"CONSENT_OTP_VERIFIED",metadata);
    if getattr(instance, "signer_actor_type", "PATIENT_SELF") == RESPONSIBLE_ADULT:
        _audit(session,access,"RESPONSIBLE_ADULT_OTP_VERIFIED",metadata)
    _audit(session,access,"CONSENT_PUBLIC_SESSION_CREATED",metadata); session.commit()
    return raw, public.expires_at


def _verified(session: Session, token: str, cookie: str | None, metadata: RequestMetadata) -> tuple[ConsentAccessSession, ConsentInstance, ConsentPublicSession]:
    access=_public_access(session,token,metadata)
    if not cookie:
        _audit(session,access,"CONSENT_PUBLIC_ACCESS_DENIED",metadata,result="FAILURE",detail={"reason":"PUBLIC_SESSION_MISSING"}); session.commit(); raise ConsentAccessError("La sesión de revisión expiró.",401)
    public=session.scalar(select(ConsentPublicSession).where(ConsentPublicSession.access_session_id==access.id,ConsentPublicSession.session_token_hash==_hash(cookie),ConsentPublicSession.status=="ACTIVE").with_for_update())
    now=_now()
    if not public or public.expires_at<=now or public.last_activity_at+timedelta(minutes=settings.consent_public_session_minutes)<=now:
        if public: public.status="EXPIRED"
        _audit(session,access,"CONSENT_PUBLIC_ACCESS_DENIED",metadata,result="FAILURE",detail={"reason":"PUBLIC_SESSION_EXPIRED"}); session.commit(); raise ConsentAccessError("La sesión de revisión expiró.",401)
    instance=session.get(ConsentInstance,access.consent_instance_id)
    try:_verify_seal(instance)
    except ConsentInstanceError:
        public.status="REVOKED"; public.revoked_at=now; _audit(session,access,"CONSENT_INTEGRITY_FAILURE",metadata,result="FAILURE"); session.commit(); raise ConsentAccessError("El documento no está disponible.",409)
    public.last_activity_at=now; access.last_activity_at=now
    return access,instance,public


def public_document(session: Session, token: str, cookie: str | None, metadata: RequestMetadata):
    access,instance,_=_verified(session,token,cookie,metadata); company=session.get(Company,instance.company_id); procedures=list(session.scalars(select(ConsentInstanceProcedure).where(ConsentInstanceProcedure.instance_id==instance.id).order_by(ConsentInstanceProcedure.order_number)));context=instance.context_snapshot or {};patient_snapshot=context.get("patient") or {};professional_snapshot=context.get("professional") or {};compatibility=inspect_acceptance_context(instance)
    try:
        declaration_set=declaration_set_for(compatibility.country_code,compatibility.locale,actor_type=getattr(instance,"signer_actor_type","PATIENT_SELF"),app_env=settings.app_env,acceptance_enabled=settings.consent_acceptance_enabled,on_date=_now().date(),session=session) if compatibility.compatible else None
    except ConsentDeclarationSetError as exc:
        raise ConsentAccessError(str(exc), 409) from exc
    test_document=bool(declaration_set.is_test_document) if declaration_set else True
    patient_content=instance.rendered_content_snapshot or ""; content_validation=validate_patient_facing_content(patient_content,allowed_variables=None,document_type=instance.document_kind,signer_compatibility=getattr(instance, "signer_policy", "PATIENT_SELF"),normalized_hash=_hash(patient_content),enforce_electronic_readiness=True)
    if content_validation.status=="BLOCKED": raise ConsentAccessError("El documento no está disponible para firma electrónica. Contacta a la clínica.",409)
    now=_now(); first=access.viewed_at is None; access.viewed_at=access.viewed_at or now; access.status="VIEWED" if access.status!="CLARIFICATION_REQUESTED" else access.status; access.row_version+=1; _audit(session,access,"CONSENT_DOCUMENT_VIEWED",metadata,detail={"first_view":first}); session.commit()
    signer=signer_snapshot_from_instance(instance)
    return PublicConsentDocumentResponse(title=instance.display_title,clinic_name=company.name,patient_name=patient_snapshot.get("full_name") or "Paciente",signer_actor_type=signer.actor_type,signer_name=signer.full_name,signer_relationship=signer.relationship_label,professional_name=professional_snapshot.get("full_name") or "Profesional",clinical_date=instance.clinical_date.isoformat(),procedures=[p.name_snapshot for p in procedures],content=patient_content,template_version=instance.template_version_number,test_document=test_document,is_test_document=test_document,test_notice=TEST_DOCUMENT_NOTICE if test_document else None,legal_review_status=declaration_set.legal_status if declaration_set else None,declaration_set_code=declaration_set.code if declaration_set else None,declaration_set_version=declaration_set.version if declaration_set else None,acceptance_compatible=compatibility.compatible,acceptance_block_message=compatibility.public_message)


def create_clarification(session: Session, token: str, cookie: str | None, message: str | None, metadata: RequestMetadata):
    access,instance,_=_verified(session,token,cookie,metadata); existing=session.scalar(select(ConsentClarificationRequest).where(ConsentClarificationRequest.access_session_id==access.id,ConsentClarificationRequest.status=="OPEN").with_for_update())
    if existing: return ClarificationResponse(id=existing.id,status=existing.status,message=existing.message,requested_at=existing.requested_at,resolved_at=existing.resolved_at)
    now=_now(); item=ConsentClarificationRequest(company_id=instance.company_id,consent_instance_id=instance.id,access_session_id=access.id,professional_user_id=instance.professional_user_id,status="OPEN",message=message,requested_at=now); session.add(item); access.status="CLARIFICATION_REQUESTED"; access.clarification_requested_at=now; access.row_version+=1; _audit(session,access,"CONSENT_CLARIFICATION_REQUESTED",metadata,detail={"has_message":bool(message)}); session.commit(); return ClarificationResponse(id=item.id,status=item.status,message=item.message,requested_at=item.requested_at,resolved_at=None)


def list_clarifications(session: Session, context: AuthContext, instance_id: UUID):
    instance=_require_instance(session,context,instance_id)
    return [ClarificationResponse(id=x.id,status=x.status,message=x.message,requested_at=x.requested_at,resolved_at=x.resolved_at) for x in session.scalars(select(ConsentClarificationRequest).where(ConsentClarificationRequest.company_id==instance.company_id,ConsentClarificationRequest.consent_instance_id==instance.id).order_by(ConsentClarificationRequest.requested_at.desc()))]


def resolve_clarification(session: Session, context: AuthContext, instance_id: UUID, clarification_id: UUID, metadata: RequestMetadata):
    _require_instance(session,context,instance_id); item=session.scalar(select(ConsentClarificationRequest).where(ConsentClarificationRequest.id==clarification_id,ConsentClarificationRequest.company_id==context.user.company_id,ConsentClarificationRequest.consent_instance_id==instance_id).with_for_update())
    if not item: raise ConsentAccessError("Solicitud no encontrada.",404)
    if item.status!="RESOLVED": item.status="RESOLVED"; item.resolved_at=_now(); item.resolved_by=context.user.id
    access=session.get(ConsentAccessSession,item.access_session_id); _audit(session,access,"CONSENT_CLARIFICATION_RESOLVED",metadata,user_id=context.user.id); session.commit(); return ClarificationResponse(id=item.id,status=item.status,message=item.message,requested_at=item.requested_at,resolved_at=item.resolved_at)
