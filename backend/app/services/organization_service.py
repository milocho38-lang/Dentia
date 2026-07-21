import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Appointment, Dentist, DentistSite
from app.models.associations import UserRole, UserSite
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.company import Company
from app.models.followup import PatientFollowup
from app.models.role import Role
from app.models.site import Site
from app.models.user import User
from app.schemas.organization_schema import (
    BrandingResponse,
    BrandingUpdateRequest,
    CompanyResponse,
    CompanyUpdateRequest,
    DentistSiteListResponse,
    DentistSiteManagementResponse,
    DentistSiteOptionResponse,
    DentistSiteUpdateRequest,
    SiteActionResponse,
    SiteCreateRequest,
    SiteImpactResponse,
    SiteListResponse,
    SiteResponse,
    SiteUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_sites


class OrganizationError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


MAX_BRANDING_FILE_SIZE = 5 * 1024 * 1024
LOGO_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
}
SIGNATURE_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", normalized)


def normalize_tax_id(value: str | None) -> str | None:
    if not value:
        return None
    normalized = "".join(
        character for character in value.upper() if character.isalnum()
    )
    return normalized or None


def _branding_root() -> Path:
    root = Path(settings.branding_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _asset_path(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    root = _branding_root().resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        raise OrganizationError("Ruta de archivo inválida.", 500)
    return candidate


def _delete_asset(relative_path: str | None) -> None:
    path = _asset_path(relative_path)
    if path and path.exists() and path.is_file():
        path.unlink()


def _branding_response(company: Company) -> BrandingResponse:
    return BrandingResponse(
        id=company.id,
        name=company.name,
        legal_name=company.legal_name,
        company_type=company.company_type,
        tax_id=company.tax_id,
        address=company.address,
        city=company.city,
        department=company.department,
        country=company.country,
        phone=company.phone,
        mobile=company.mobile,
        email=company.email,
        website=company.website,
        social_media=company.social_media,
        logo_filename=company.logo_filename,
        logo_url="/api/company/branding/logo" if company.logo_path else None,
        signature_filename=company.signature_filename,
        signature_url="/api/company/branding/signature" if company.signature_path else None,
        primary_dentist_name=company.primary_dentist_name,
        professional_specialty=company.professional_specialty,
        professional_license=company.professional_license,
        university=company.university,
        experience_years=company.experience_years,
        header_text=company.header_text,
        footer_text=company.footer_text,
        legal_observations=company.legal_observations,
        cancellation_policy=company.cancellation_policy,
        thank_you_message=company.thank_you_message,
        payment_receipt_title=company.payment_receipt_title or "COMPROBANTE DE PAGO",
        primary_color=company.primary_color or "#16a34a",
        secondary_color=company.secondary_color or "#0f766e",
        button_color=company.button_color or "#16a34a",
        heading_color=company.heading_color or "#0f172a",
        updated_at=company.updated_at,
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    entity: str,
    entity_id: UUID,
    action: str,
    detail: dict | None = None,
    result: str = "SUCCESS",
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result=result,
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _company_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        company_type=company.company_type,
        tax_id=company.tax_id,
        phone=company.phone,
        email=company.email,
        address=company.address,
        city=company.city,
        country=company.country,
        timezone=company.timezone,
        status=company.status,
        profile_complete=all(
            [
                company.name,
                company.company_type,
                company.phone,
                company.email,
                company.address,
                company.city,
                company.country,
                company.timezone,
            ]
        ),
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def get_company(session: Session, context: AuthContext) -> CompanyResponse:
    company = session.get(Company, context.user.company_id)
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    return _company_response(company)


def update_company(
    session: Session,
    context: AuthContext,
    payload: CompanyUpdateRequest,
    metadata: RequestMetadata,
) -> CompanyResponse:
    company = session.scalar(
        select(Company)
        .where(Company.id == context.user.company_id)
        .with_for_update()
    )
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    before = {
        "name": company.name,
        "company_type": company.company_type,
        "tax_id": company.tax_id,
        "phone": company.phone,
        "email": company.email,
        "address": company.address,
        "city": company.city,
        "country": company.country,
        "timezone": company.timezone,
    }
    company.name = payload.name
    company.company_type = payload.company_type
    company.tax_id = payload.tax_id
    company.normalized_tax_id = normalize_tax_id(payload.tax_id)
    company.phone = payload.phone
    company.email = payload.email
    company.address = payload.address
    company.city = payload.city
    company.country = payload.country
    company.timezone = payload.timezone
    after = {
        "name": company.name,
        "company_type": company.company_type,
        "tax_id": company.tax_id,
        "phone": company.phone,
        "email": company.email,
        "address": company.address,
        "city": company.city,
        "country": company.country,
        "timezone": company.timezone,
    }
    changes = {
        key: {"before": before[key], "after": value}
        for key, value in after.items()
        if before[key] != value
    }
    if changes:
        _audit(
            session,
            context,
            metadata,
            entity="company",
            entity_id=company.id,
            action="COMPANY_UPDATED",
            detail={"changes": changes},
        )
    session.commit()
    return _company_response(company)


def get_branding(session: Session, context: AuthContext) -> BrandingResponse:
    company = session.get(Company, context.user.company_id)
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    return _branding_response(company)


def update_branding(
    session: Session,
    context: AuthContext,
    payload: BrandingUpdateRequest,
    metadata: RequestMetadata,
) -> BrandingResponse:
    company = session.scalar(
        select(Company)
        .where(Company.id == context.user.company_id)
        .with_for_update()
    )
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    fields = {
        "name": "name",
        "legal_name": "legal_name",
        "company_type": "company_type",
        "tax_id": "tax_id",
        "address": "address",
        "city": "city",
        "department": "department",
        "country": "country",
        "phone": "phone",
        "mobile": "mobile",
        "email": "email",
        "website": "website",
        "social_media": "social_media",
        "primary_dentist_name": "primary_dentist_name",
        "professional_specialty": "professional_specialty",
        "professional_license": "professional_license",
        "university": "university",
        "experience_years": "experience_years",
        "header_text": "header_text",
        "footer_text": "footer_text",
        "legal_observations": "legal_observations",
        "cancellation_policy": "cancellation_policy",
        "thank_you_message": "thank_you_message",
        "payment_receipt_title": "payment_receipt_title",
        "primary_color": "primary_color",
        "secondary_color": "secondary_color",
        "button_color": "button_color",
        "heading_color": "heading_color",
    }
    data = payload.model_dump()
    before = {key: getattr(company, attr) for key, attr in fields.items()}
    for key, attr in fields.items():
        setattr(company, attr, data[key])
    company.normalized_tax_id = normalize_tax_id(payload.tax_id)
    after = {key: getattr(company, attr) for key, attr in fields.items()}
    changes = {
        key: {"before": before[key], "after": value}
        for key, value in after.items()
        if before[key] != value
    }
    if changes:
        _audit(
            session,
            context,
            metadata,
            entity="company",
            entity_id=company.id,
            action="BRANDING_UPDATED",
            detail={"changes": changes},
        )
    session.commit()
    return _branding_response(company)


def get_branding_asset_path(
    session: Session,
    context: AuthContext,
    kind: str,
) -> tuple[Path, str]:
    company = session.get(Company, context.user.company_id)
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    if kind == "logo":
        relative_path = company.logo_path
        filename = company.logo_filename or "logo"
    elif kind == "signature":
        relative_path = company.signature_path
        filename = company.signature_filename or "firma"
    else:
        raise OrganizationError("Tipo de archivo no válido.", 404)
    path = _asset_path(relative_path)
    if path is None or not path.exists():
        raise OrganizationError("Archivo no encontrado.", 404)
    return path, filename


def save_branding_asset(
    session: Session,
    context: AuthContext,
    *,
    kind: str,
    filename: str | None,
    content_type: str | None,
    content: bytes,
    metadata: RequestMetadata,
) -> BrandingResponse:
    company = session.scalar(
        select(Company)
        .where(Company.id == context.user.company_id)
        .with_for_update()
    )
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    allowed = LOGO_CONTENT_TYPES if kind == "logo" else SIGNATURE_CONTENT_TYPES
    if content_type not in allowed:
        raise OrganizationError(
            "Formato de archivo no permitido."
            if kind == "logo"
            else "Formato de firma no permitido."
        )
    if len(content) > MAX_BRANDING_FILE_SIZE:
        raise OrganizationError("El archivo no puede superar 5 MB.")
    if not content:
        raise OrganizationError("El archivo está vacío.")

    old_path = company.logo_path if kind == "logo" else company.signature_path
    extension = allowed[content_type]
    company_dir_name = str(company.id)
    company_dir = _branding_root() / company_dir_name
    company_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{kind}_{uuid4().hex}{extension}"
    relative_path = f"{company_dir_name}/{safe_name}"
    path = _asset_path(relative_path)
    if path is None:
        raise OrganizationError("No fue posible preparar el archivo.", 500)
    path.write_bytes(content)

    if kind == "logo":
        company.logo_path = relative_path
        company.logo_filename = filename or safe_name
        action = "BRANDING_LOGO_UPLOADED"
        entity = "company_logo"
    else:
        company.signature_path = relative_path
        company.signature_filename = filename or safe_name
        action = "BRANDING_SIGNATURE_UPLOADED"
        entity = "company_signature"

    _delete_asset(old_path)
    _audit(
        session,
        context,
        metadata,
        entity=entity,
        entity_id=company.id,
        action=action,
        detail={"filename": filename, "content_type": content_type},
    )
    session.commit()
    return _branding_response(company)


def delete_branding_asset(
    session: Session,
    context: AuthContext,
    *,
    kind: str,
    metadata: RequestMetadata,
) -> BrandingResponse:
    company = session.scalar(
        select(Company)
        .where(Company.id == context.user.company_id)
        .with_for_update()
    )
    if company is None:
        raise OrganizationError("Empresa no encontrada.", 404)
    if kind == "logo":
        old_path = company.logo_path
        company.logo_path = None
        company.logo_filename = None
        action = "BRANDING_LOGO_DELETED"
        entity = "company_logo"
    elif kind == "signature":
        old_path = company.signature_path
        company.signature_path = None
        company.signature_filename = None
        action = "BRANDING_SIGNATURE_DELETED"
        entity = "company_signature"
    else:
        raise OrganizationError("Tipo de archivo no válido.", 404)
    _delete_asset(old_path)
    _audit(
        session,
        context,
        metadata,
        entity=entity,
        entity_id=company.id,
        action=action,
    )
    session.commit()
    return _branding_response(company)


def _site_counts(session: Session, site_id: UUID) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    return {
        "assigned_users": int(
            session.scalar(
                select(func.count())
                .select_from(UserSite)
                .where(
                    UserSite.site_id == site_id,
                    UserSite.is_active.is_(True),
                )
            )
            or 0
        ),
        "dentists": int(
            session.scalar(
                select(func.count())
                .select_from(DentistSite)
                .where(
                    DentistSite.site_id == site_id,
                    DentistSite.is_active.is_(True),
                )
            )
            or 0
        ),
        "future_appointments": int(
            session.scalar(
                select(func.count())
                .select_from(Appointment)
                .where(
                    Appointment.site_id == site_id,
                    Appointment.is_active.is_(True),
                    Appointment.status.in_({"Programada", "Confirmada"}),
                    Appointment.starts_at > now,
                )
            )
            or 0
        ),
        "open_followups": int(
            session.scalar(
                select(func.count())
                .select_from(PatientFollowup)
                .where(
                    PatientFollowup.site_id == site_id,
                    PatientFollowup.is_active.is_(True),
                    PatientFollowup.status.in_(
                        {"Pendiente", "Contactado", "Cita programada"}
                    ),
                )
            )
            or 0
        ),
    }


def _site_response(
    session: Session,
    company: Company,
    site: Site,
) -> SiteResponse:
    counts = _site_counts(session, site.id)
    return SiteResponse(
        id=site.id,
        name=site.name,
        address=site.address,
        city=site.city,
        phone=site.phone,
        timezone=site.timezone,
        effective_timezone=site.timezone or company.timezone,
        status=site.status,
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
        **counts,
    )


def _dentist_site_response(
    session: Session,
    context: AuthContext,
    dentist: Dentist,
) -> DentistSiteManagementResponse:
    active_sites = list(
        session.scalars(
            select(Site)
            .where(
                Site.company_id == context.user.company_id,
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
            .order_by(Site.name)
        )
    )
    assigned_ids = set(
        session.scalars(
            select(DentistSite.site_id).where(
                DentistSite.company_id == context.user.company_id,
                DentistSite.dentist_id == dentist.id,
                DentistSite.is_active.is_(True),
            )
        )
    )
    company = session.get(Company, context.user.company_id)
    return DentistSiteManagementResponse(
        id=dentist.id,
        name=dentist.name,
        status=dentist.status,
        user_id=dentist.user_id,
        site_ids=sorted(assigned_ids, key=str),
        sites=[
            DentistSiteOptionResponse(
                id=site.id,
                name=site.name,
                address=site.address,
                timezone=site.timezone or company.timezone,
                assigned=site.id in assigned_ids,
            )
            for site in active_sites
        ],
    )


def _get_site(
    session: Session,
    context: AuthContext,
    site_id: UUID,
    *,
    lock: bool = False,
) -> Site:
    statement = select(Site).where(
        Site.id == site_id,
        Site.company_id == context.user.company_id,
        Site.is_active.is_(True),
    )
    if lock:
        statement = statement.with_for_update()
    site = session.scalar(statement)
    if site is None:
        raise OrganizationError("Sede no encontrada.", 404)
    return site


def list_sites(
    session: Session,
    context: AuthContext,
    *,
    search: str | None,
    status: str | None,
) -> SiteListResponse:
    statement = select(Site).where(
        Site.company_id == context.user.company_id,
        Site.is_active.is_(True),
    )
    if search:
        statement = statement.where(
            Site.normalized_name.ilike(f"%{normalize_name(search)}%")
        )
    if status:
        if status not in {"Activa", "Inactiva"}:
            raise OrganizationError("Estado de sede no válido.")
        statement = statement.where(Site.status == status)
    company = session.get(Company, context.user.company_id)
    sites = list(session.scalars(statement.order_by(Site.name)))
    return SiteListResponse(
        items=[_site_response(session, company, site) for site in sites]
    )


def get_site(
    session: Session, context: AuthContext, site_id: UUID
) -> SiteResponse:
    company = session.get(Company, context.user.company_id)
    return _site_response(session, company, _get_site(session, context, site_id))


def _apply_site_payload(
    site: Site, payload: SiteCreateRequest | SiteUpdateRequest
) -> None:
    site.name = payload.name
    site.normalized_name = normalize_name(payload.name)
    site.address = payload.address
    site.city = payload.city
    site.phone = payload.phone
    site.timezone = payload.timezone


def create_site(
    session: Session,
    context: AuthContext,
    payload: SiteCreateRequest,
    metadata: RequestMetadata,
) -> SiteResponse:
    site = Site(
        company_id=context.user.company_id,
        name=payload.name,
        normalized_name=normalize_name(payload.name),
        address=payload.address,
        city=payload.city,
        phone=payload.phone,
        timezone=payload.timezone,
        status="Activa",
        created_by=context.user.id,
    )
    session.add(site)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise OrganizationError(
            "Ya existe una sede con ese nombre.", 409
        ) from exc
    _audit(
        session,
        context,
        metadata,
        entity="site",
        entity_id=site.id,
        action="SITE_CREATED",
        detail={"name": site.name},
    )
    session.commit()
    return _site_response(
        session, session.get(Company, context.user.company_id), site
    )


def update_site(
    session: Session,
    context: AuthContext,
    site_id: UUID,
    payload: SiteUpdateRequest,
    metadata: RequestMetadata,
) -> SiteResponse:
    site = _get_site(session, context, site_id, lock=True)
    before = {
        "name": site.name,
        "address": site.address,
        "city": site.city,
        "phone": site.phone,
        "timezone": site.timezone,
    }
    _apply_site_payload(site, payload)
    after = {
        "name": site.name,
        "address": site.address,
        "city": site.city,
        "phone": site.phone,
        "timezone": site.timezone,
    }
    changes = {
        key: {"before": before[key], "after": value}
        for key, value in after.items()
        if before[key] != value
    }
    if changes:
        _audit(
            session,
            context,
            metadata,
            entity="site",
            entity_id=site.id,
            action="SITE_UPDATED",
            detail={"changes": changes},
        )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise OrganizationError(
            "Ya existe una sede con ese nombre.", 409
        ) from exc
    return _site_response(
        session, session.get(Company, context.user.company_id), site
    )


def _has_admin_role(session: Session, user_id: UUID) -> bool:
    return bool(
        session.scalar(
            select(UserRole.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
                Role.code == "ADMINISTRATOR",
            )
            .limit(1)
        )
    )


def site_impact(
    session: Session,
    context: AuthContext,
    site_id: UUID,
) -> SiteImpactResponse:
    site = _get_site(session, context, site_id)
    counts = _site_counts(session, site.id)
    active_sites_after = int(
        session.scalar(
            select(func.count())
            .select_from(Site)
            .where(
                Site.company_id == context.user.company_id,
                Site.id != site.id,
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
        )
        or 0
    )
    default_users = list(
        session.scalars(
            select(User).where(
                User.company_id == context.user.company_id,
                User.default_site_id == site.id,
                User.status == "Activo",
                User.is_active.is_(True),
            )
        )
    )
    assigned_users = list(
        session.scalars(
            select(User)
            .join(UserSite, UserSite.user_id == User.id)
            .where(
                User.company_id == context.user.company_id,
                User.status == "Activo",
                User.is_active.is_(True),
                UserSite.site_id == site.id,
                UserSite.is_active.is_(True),
            )
            .distinct()
        )
    )
    users_without_alternative = 0
    affected_users = {user.id: user for user in default_users + assigned_users}
    for user in affected_users.values():
        roles = [
            role
            for role in session.scalars(
                select(Role.code)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(
                    UserRole.user_id == user.id,
                    UserRole.is_active.is_(True),
                    Role.is_active.is_(True),
                )
            )
        ]
        alternatives = authorized_sites(
            session,
            company_id=user.company_id,
            user_id=user.id,
            roles=roles,
        )
        if not any(candidate.id != site.id for candidate in alternatives):
            users_without_alternative += 1
    active_sessions = int(
        session.scalar(
            select(func.count())
            .select_from(AuthSession)
            .where(
                AuthSession.company_id == context.user.company_id,
                AuthSession.active_site_id == site.id,
                AuthSession.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
            )
        )
        or 0
    )
    blocking_reasons: list[str] = []
    if counts["future_appointments"]:
        blocking_reasons.append(
            "La sede tiene citas futuras programadas o confirmadas."
        )
    if users_without_alternative:
        blocking_reasons.append(
            "Hay usuarios activos que quedarían sin una sede disponible."
        )
    if active_sites_after == 0:
        blocking_reasons.append(
            "La empresa debe conservar al menos una sede activa."
        )
    return SiteImpactResponse(
        future_appointments=counts["future_appointments"],
        assigned_users=counts["assigned_users"],
        default_for_users=len(default_users),
        users_without_alternative=users_without_alternative,
        active_sessions=active_sessions,
        dentists=counts["dentists"],
        open_followups=counts["open_followups"],
        active_sites_after=active_sites_after,
        can_deactivate=not blocking_reasons,
        blocking_reasons=blocking_reasons,
    )


def deactivate_site(
    session: Session,
    context: AuthContext,
    site_id: UUID,
    reason: str,
    metadata: RequestMetadata,
) -> SiteActionResponse:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
        {"key": f"site-deactivate:{context.user.company_id}"},
    )
    site = _get_site(session, context, site_id, lock=True)
    if site.status == "Inactiva":
        raise OrganizationError("La sede ya está inactiva.", 409)
    impact = site_impact(session, context, site.id)
    if not impact.can_deactivate:
        _audit(
            session,
            context,
            metadata,
            entity="site",
            entity_id=site.id,
            action="SITE_DEACTIVATION_BLOCKED",
            result="FAILURE",
            detail={
                "reason": reason,
                "blocking_reasons": impact.blocking_reasons,
            },
        )
        session.commit()
        raise OrganizationError(" ".join(impact.blocking_reasons), 409)

    alternatives = list(
        session.scalars(
            select(Site)
            .where(
                Site.company_id == context.user.company_id,
                Site.id != site.id,
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
            .order_by(Site.name)
        )
    )
    defaults_reassigned = 0
    users = list(
        session.scalars(
            select(User).where(
                User.company_id == context.user.company_id,
                User.default_site_id == site.id,
                User.is_active.is_(True),
            )
        )
    )
    for user in users:
        if _has_admin_role(session, user.id):
            replacement = alternatives[0]
        else:
            replacement = session.scalar(
                select(Site)
                .join(UserSite, UserSite.site_id == Site.id)
                .where(
                    UserSite.user_id == user.id,
                    UserSite.is_active.is_(True),
                    Site.id != site.id,
                    Site.is_active.is_(True),
                    Site.status == "Activa",
                )
                .order_by(Site.name)
                .limit(1)
            )
        user.default_site_id = replacement.id
        for assignment in session.scalars(
            select(UserSite).where(UserSite.user_id == user.id)
        ):
            assignment.is_default = assignment.site_id == replacement.id
        defaults_reassigned += 1

    now = datetime.now(timezone.utc)
    sessions = list(
        session.scalars(
            select(AuthSession).where(
                AuthSession.company_id == context.user.company_id,
                AuthSession.active_site_id == site.id,
                AuthSession.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
            )
        )
    )
    for auth_session in sessions:
        auth_session.is_active = False
        auth_session.revoked_at = now
        auth_session.revoked_by = context.user.id
        auth_session.revoke_reason = "SITE_DEACTIVATED"

    site.status = "Inactiva"
    _audit(
        session,
        context,
        metadata,
        entity="site",
        entity_id=site.id,
        action="SITE_DEACTIVATED",
        detail={
            "reason": reason,
            "sessions_revoked": len(sessions),
            "defaults_reassigned": defaults_reassigned,
        },
    )
    session.commit()
    return SiteActionResponse(
        message="Sede inactivada.",
        site=_site_response(
            session, session.get(Company, context.user.company_id), site
        ),
        sessions_revoked=len(sessions),
        defaults_reassigned=defaults_reassigned,
    )


def reactivate_site(
    session: Session,
    context: AuthContext,
    site_id: UUID,
    reason: str,
    metadata: RequestMetadata,
) -> SiteActionResponse:
    site = _get_site(session, context, site_id, lock=True)
    if site.status == "Activa":
        raise OrganizationError("La sede ya está activa.", 409)
    site.status = "Activa"
    _audit(
        session,
        context,
        metadata,
        entity="site",
        entity_id=site.id,
        action="SITE_REACTIVATED",
        detail={"reason": reason},
    )
    session.commit()
    return SiteActionResponse(
        message="Sede reactivada.",
        site=_site_response(
            session, session.get(Company, context.user.company_id), site
        ),
    )


def list_dentists_for_site_management(
    session: Session,
    context: AuthContext,
) -> DentistSiteListResponse:
    dentists = list(
        session.scalars(
            select(Dentist)
            .where(
                Dentist.company_id == context.user.company_id,
                Dentist.is_active.is_(True),
                Dentist.status == "Activo",
            )
            .order_by(Dentist.name)
        )
    )
    return DentistSiteListResponse(
        items=[
            _dentist_site_response(session, context, dentist)
            for dentist in dentists
        ]
    )


def update_dentist_sites(
    session: Session,
    context: AuthContext,
    dentist_id: UUID,
    payload: DentistSiteUpdateRequest,
    metadata: RequestMetadata,
) -> DentistSiteManagementResponse:
    dentist = session.scalar(
        select(Dentist)
        .where(
            Dentist.id == dentist_id,
            Dentist.company_id == context.user.company_id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
        .with_for_update()
    )
    if dentist is None:
        raise OrganizationError("Odontólogo no encontrado.", 404)
    requested_ids = set(payload.site_ids)
    valid_ids = set(
        session.scalars(
            select(Site.id).where(
                Site.company_id == context.user.company_id,
                Site.id.in_(requested_ids) if requested_ids else True,
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
        )
    )
    if valid_ids != requested_ids:
        raise OrganizationError("Una o más sedes no están activas.", 400)
    existing = {
        assignment.site_id: assignment
        for assignment in session.scalars(
            select(DentistSite)
            .where(
                DentistSite.company_id == context.user.company_id,
                DentistSite.dentist_id == dentist.id,
            )
            .with_for_update()
        )
    }
    before = sorted(
        str(site_id)
        for site_id, assignment in existing.items()
        if assignment.is_active
    )
    for site_id, assignment in existing.items():
        assignment.is_active = site_id in requested_ids
    for site_id in requested_ids - existing.keys():
        session.add(
            DentistSite(
                company_id=context.user.company_id,
                dentist_id=dentist.id,
                site_id=site_id,
                created_by=context.user.id,
            )
        )
    after = sorted(str(site_id) for site_id in requested_ids)
    _audit(
        session,
        context,
        metadata,
        entity="dentist",
        entity_id=dentist.id,
        action="DENTIST_SITES_UPDATED",
        detail={"before": before, "after": after},
    )
    session.commit()
    return _dentist_site_response(session, context, dentist)
