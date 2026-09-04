from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consent_template import (
    ConsentProcedureApproval,
    ConsentTemplate,
    ConsentTemplateContentReview,
    ConsentTemplateVersion,
)
from app.services.consent_library_normalization import validate_patient_facing_content
from app.services.consent_signer import ELECTRONIC_CONSENT_SIGNER_POLICIES, canonical_signer_policy
from app.services.consent_template_integrity import consent_template_version_hash
from app.services.consent_template_service import validate_content


PROCEDURE_VERSION = "DENTIA_CONSENT_PROCEDURE_V1"


class ConsentProductionReadinessError(RuntimeError):
    pass


def active_content_review(session: Session, version: ConsentTemplateVersion) -> ConsentTemplateContentReview | None:
    return session.scalar(
        select(ConsentTemplateContentReview).where(
            ConsentTemplateContentReview.company_id == version.company_id,
            ConsentTemplateContentReview.template_version_id == version.id,
            ConsentTemplateContentReview.invalidated_at.is_(None),
        )
    )


def reviewed_content_hash(session: Session, template: ConsentTemplate, version: ConsentTemplateVersion) -> tuple[str, ConsentTemplateContentReview | None]:
    validation = validate_content(version.content, require_registered=True)
    if not validation.valid:
        raise ConsentProductionReadinessError("La plantilla no supera la validación técnica de contenido.")
    current_hash = consent_template_version_hash(session, template, version, validation.used_variables)
    return current_hash, active_content_review(session, version)


def production_configuration_errors(*, channel: str) -> list[str]:
    if settings.app_env.casefold() != "production":
        return []
    errors: list[str] = []
    if settings.app_debug:
        errors.append("APP_DEBUG debe estar desactivado")
    parsed = urlparse(settings.public_frontend_url)
    if parsed.scheme != "https" or parsed.netloc.casefold() != "app.dentiapro.com":
        errors.append("PUBLIC_FRONTEND_URL debe ser https://app.dentiapro.com")
    if not settings.consent_acceptance_enabled:
        errors.append("CONSENT_ACCEPTANCE_ENABLED debe estar habilitado")
    if not settings.consent_public_cookie_secure:
        errors.append("CONSENT_PUBLIC_COOKIE_SECURE debe estar habilitado")
    if not settings.consent_storage_persistent:
        errors.append("el storage de consentimientos debe declararse persistente")
    if not Path(settings.consent_final_storage_dir).is_absolute():
        errors.append("CONSENT_FINAL_STORAGE_DIR debe ser una ruta absoluta")
    if settings.consent_otp_expire_minutes <= 0 or settings.consent_otp_max_attempts <= 0 or settings.consent_public_session_minutes <= 0:
        errors.append("la configuración OTP/sesión pública no es válida")
    if channel == "ELECTRONIC" and (not settings.smtp_host or not settings.smtp_from_email):
        errors.append("SMTP debe estar configurado para el canal electrónico")
    return errors


def require_procedure_approval(session: Session, *, country_code: str, channel: str) -> ConsentProcedureApproval:
    approval = session.scalar(
        select(ConsentProcedureApproval).where(
            ConsentProcedureApproval.procedure_version == settings.consent_procedure_version,
            ConsentProcedureApproval.status == "APPROVED",
        )
    )
    channel_ok = bool(
        approval
        and country_code in (approval.countries or [])
        and approval.declaration_flow_reviewed
        and approval.responsible_adult_flow_reviewed
        and (
            approval.electronic_channel_reviewed
            if channel == "ELECTRONIC"
            else approval.paper_channel_reviewed
            if channel == "PAPER"
            else approval.electronic_channel_reviewed and approval.paper_channel_reviewed
        )
    )
    if not channel_ok:
        raise ConsentProductionReadinessError("El procedimiento Dentia no está aprobado para este país y canal.")
    return approval


def assert_template_ready(
    session: Session,
    *,
    template: ConsentTemplate,
    version: ConsentTemplateVersion,
    signer_policy: str,
    channel: str,
) -> None:
    if settings.app_env.casefold() != "production":
        return
    config_errors = production_configuration_errors(channel=channel)
    if config_errors:
        raise ConsentProductionReadinessError("Configuración productiva incompleta: " + "; ".join(config_errors) + ".")
    if version.status != "PUBLISHED":
        raise ConsentProductionReadinessError("La versión tenant no está publicada.")
    current_hash, review = reviewed_content_hash(session, template, version)
    if review is None or review.content_sha256 != current_hash or version.content_sha256 != current_hash:
        raise ConsentProductionReadinessError("La versión exacta no cuenta con revisión vigente de la clínica.")
    policy = canonical_signer_policy(signer_policy)
    if policy not in ELECTRONIC_CONSENT_SIGNER_POLICIES:
        raise ConsentProductionReadinessError("El documento requiere un flujo especial no habilitado en C019A.6.")
    validation = validate_patient_facing_content(
        version.content,
        allowed_variables=None,
        document_type=template.document_kind,
        signer_compatibility=policy,
        normalized_hash=current_hash,
        enforce_electronic_readiness=channel == "ELECTRONIC",
    )
    if validation.status == "BLOCKED":
        raise ConsentProductionReadinessError("La plantilla no supera las barreras técnicas del canal seleccionado.")
    require_procedure_approval(session, country_code=template.country_code, channel=channel)
