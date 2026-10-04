from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agenda import Dentist, DentistSite
from app.models.company import Company
from app.schemas.periodontogram_schema import PeriodontogramAccessResponse
from app.services.auth_service import AuthContext
from app.services.site_access_service import is_authorized_site


PERIODONTOGRAM_CLINICAL_ROLES = frozenset({"DENTIST", "DENTIST_ADMIN"})


class PeriodontogramAccessError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 403):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def resolve_periodontogram_access(
    session: Session,
    context: AuthContext,
    *,
    site_id: UUID | None = None,
) -> PeriodontogramAccessResponse:
    company_id = context.user.company_id
    denied = {"company_id": company_id, "dentist_id": None}
    if not context.user.is_active or context.user.status != "Activo":
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTOGRAM_USER_INACTIVE",
            message="El usuario no está activo.",
            **denied,
        )
    company = session.get(Company, company_id)
    if company is None or not company.is_active or company.status != "Activa":
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTOGRAM_COMPANY_INACTIVE",
            message="La empresa no está activa.",
            **denied,
        )
    if PERIODONTOGRAM_CLINICAL_ROLES.isdisjoint(context.roles):
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTAL_CLINICAL_ROLE_REQUIRED",
            message="Se requiere un rol odontológico para acceder al Periodontograma.",
            **denied,
        )
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )
    if dentist is None:
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTAL_DENTIST_IDENTITY_REQUIRED",
            message="Se requiere un perfil odontológico activo para acceder al Periodontograma.",
            **denied,
        )
    active_site_id = site_id or context.auth_session.active_site_id
    if active_site_id is None or not is_authorized_site(
        session,
        company_id=company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=active_site_id,
    ):
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTAL_SITE_DENIED",
            message="No tienes acceso a la sede seleccionada.",
            company_id=company_id,
            dentist_id=dentist.id,
        )
    dentist_site = session.scalar(
        select(DentistSite.id).where(
            DentistSite.company_id == company_id,
            DentistSite.dentist_id == dentist.id,
            DentistSite.site_id == active_site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if dentist_site is None:
        return PeriodontogramAccessResponse(
            allowed=False,
            code="PERIODONTAL_DENTIST_SITE_DENIED",
            message="El odontólogo no está activo en la sede seleccionada.",
            company_id=company_id,
            dentist_id=dentist.id,
        )
    return PeriodontogramAccessResponse(
        allowed=True,
        code="PERIODONTOGRAM_ACCESS_GRANTED",
        message="Acceso al Periodontograma habilitado.",
        company_id=company_id,
        dentist_id=dentist.id,
    )


def require_periodontogram_access(
    session: Session,
    context: AuthContext,
    *,
    site_id: UUID | None = None,
) -> PeriodontogramAccessResponse:
    access = resolve_periodontogram_access(session, context, site_id=site_id)
    if not access.allowed:
        raise PeriodontogramAccessError(access.code, access.message)
    return access
