"""Safe, explicit and idempotent provisioning for the Aurora demo tenant.

This module is intentionally not imported by application startup.  It is only
used by ``python -m app.cli.demo_tenant`` and its isolated tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import base64
from io import BytesIO
import os
from pathlib import Path
import re
import shutil
from types import SimpleNamespace
from typing import Iterable
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import (
    Appointment,
    AppointmentHistory,
    AppointmentType,
    Dentist,
    DentistSite,
    Patient,
)
from app.models.associations import RolePermission, UserRole, UserSite
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_template import ConsentInstance, ConsentTemplate, ConsentTemplateVersion
from app.models.followup import AppointmentCare, PatientFollowup
from app.models.permission import Permission
from app.models.role import Role
from app.models.site import Site
from app.models.odontogram import OdontogramCatalogItem
from app.models.treatment import (
    ProcedureCatalogItem,
    Treatment,
    TreatmentPayment,
    TreatmentProcedure,
)
from app.models.user import User
from app.schemas.clinical_document_schema import ClinicalDocumentCreateRequest
from app.schemas.clinical_record_schema import (
    ClinicalEvolutionCreateRequest,
    ClinicalEvolutionSignRequest,
    ClinicalRecordCreateRequest,
)
from app.schemas.consent_access_schema import AcceptanceSubmitRequest
from app.schemas.consent_instance_schema import (
    ConsentContextInput,
    ConsentInstanceBatchCreateRequest,
    ConsentInstanceConfirmRequest,
    ConsentPaperVerificationRequest,
)
from app.schemas.consent_template_schema import (
    ConsentContentReviewRequest,
    ConsentTemplateCreateRequest,
)
from app.schemas.odontogram_schema import (
    OdontogramCreateRequest,
    OdontogramEventCreateRequest,
    OdontogramEventDetailInput,
)
from app.schemas.patient_schema import PatientCreateRequest
from app.schemas.platform_schema import PlatformCompanyCreateRequest
from app.schemas.treatment_schema import (
    BudgetCreateRequest,
    PaymentCreateRequest,
    ProcedureCatalogCreateRequest,
    ProcedureCreateRequest,
    TreatmentCreateRequest,
)
from app.schemas.user_schema import UserCreateRequest, UserRolesRequest, UserSitesRequest
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.clinical_document_service import create_document, finalize_document
from app.services.clinical_record_service import (
    create_clinical_evolution,
    create_clinical_record,
    sign_clinical_evolution,
)
from app.services.consent_acceptance_service import (
    acceptance_requirements,
    submit_acceptance,
)
from app.services.consent_access_service import issue_access, request_otp, verify_otp
from app.services.consent_instance_service import create_batch, confirm_professionally
from app.services.consent_paper_service import (
    document_bytes as paper_document_bytes,
    finalize as finalize_paper,
    prepare_packet,
    record_signed,
    upload_pages,
)
from app.services.consent_template_service import (
    confirm_content_review,
    create_template,
    publish_version,
)
from app.services.email_service import DemoEmailSink, use_company_email_provider
from app.services.odontogram_service import create_event, create_odontogram
from app.services.organization_service import save_dentist_professional_signature
from app.services.patient_service import create_patient, normalize_document
from app.services.platform_service import create_platform_company
from app.services.treatment_service import (
    change_budget_status,
    change_treatment_status,
    create_budget,
    create_payment,
    create_procedure,
    create_procedure_catalog_item,
    create_treatment,
)
from app.services.user_service import (
    assign_roles,
    assign_sites,
    change_status as change_user_status,
    create_user,
)


DATASET_VERSION = "aurora-v1"
DEMO_COMPANY_NAME = "Clínica Dental Aurora"
DEMO_COMPANY_SLUG = "clinica-dental-aurora-demo"
DEMO_SITE_NAME = "Sede Centro"
DEMO_DOCUMENT_PREFIX = "DEMO-AUR-"
DEMO_TEMPLATE_CODE = "AURORA-DEMO-CONSENT"
DEMO_MARKER = "[DEMO:AURORA-V1]"
BOGOTA = ZoneInfo("America/Bogota")


class DemoTenantError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoPlan:
    operation: str
    dataset: str
    company_id: UUID | None
    app_env: str
    database_target: str
    apply: bool
    counts: dict[str, int]
    checks: tuple[str, ...]


@dataclass(frozen=True)
class DemoStatus:
    found: bool
    company_id: UUID | None
    name: str | None
    slug: str | None
    allowlisted: bool
    identity_valid: bool
    counts: dict[str, int]
    consistency: tuple[str, ...]
    file_count: int


@dataclass
class DemoStorageTransaction:
    """Compensates filesystem changes made alongside the outer DB transaction."""

    company_id: UUID
    _quarantined: list[tuple[Path, Path]] = field(default_factory=list)
    _initial_paths: set[Path] = field(default_factory=set)
    _initial_files: set[Path] = field(default_factory=set)

    def roots(self) -> tuple[Path, ...]:
        branding = Path(settings.branding_storage_dir).resolve()
        consent = Path(settings.consent_final_storage_dir).resolve()
        shared = branding.parent
        candidates = (
            branding / str(self.company_id),
            consent / str(self.company_id),
            consent / "paper" / str(self.company_id),
            shared / "clinical_documents" / str(self.company_id),
            shared / "prescriptions" / str(self.company_id),
        )
        return tuple(dict.fromkeys(path.resolve() for path in candidates))

    def snapshot(self) -> None:
        self._initial_paths = {path for path in self.roots() if path.exists()}
        self._initial_files = {
            item.resolve()
            for root in self._initial_paths
            for item in root.rglob("*")
            if item.is_file()
        }

    def quarantine(self) -> None:
        for path in self.roots():
            if not path.exists():
                continue
            _assert_exact_tenant_path(path, self.company_id)
            target = path.parent / f".{path.name}.demo-quarantine-{uuid4().hex}"
            path.rename(target)
            self._quarantined.append((path, target))

    def rollback(self) -> None:
        for original, quarantine in reversed(self._quarantined):
            if original.exists():
                shutil.rmtree(original)
            if quarantine.exists():
                quarantine.rename(original)
        for path in self.roots():
            if path not in self._initial_paths and path.exists():
                _assert_exact_tenant_path(path, self.company_id)
                shutil.rmtree(path)
            elif path in self._initial_paths and path.exists():
                for item in sorted(path.rglob("*"), reverse=True):
                    resolved = item.resolve()
                    if item.is_file() and resolved not in self._initial_files:
                        item.unlink()
                    elif item.is_dir() and not any(item.iterdir()):
                        item.rmdir()

    def commit(self) -> None:
        for _, quarantine in self._quarantined:
            if quarantine.exists():
                shutil.rmtree(quarantine)
        self._quarantined.clear()


PATIENTS: tuple[tuple[str, str, str, date], ...] = (
    ("mariana-lopez", "Mariana", "López", date(1991, 4, 18)),
    ("andres-martinez", "Andrés", "Martínez", date(1985, 9, 7)),
    ("sofia-herrera", "Sofía", "Herrera", date(1997, 2, 13)),
    ("nicolas-castro", "Nicolás", "Castro", date(1979, 11, 21)),
    ("daniela-ramirez", "Daniela", "Ramírez", date(1993, 6, 5)),
    ("mateo-gomez", "Mateo", "Gómez", date(1988, 8, 29)),
    ("valeria-torres", "Valeria", "Torres", date(2000, 1, 16)),
    ("samuel-ortega", "Samuel", "Ortega", date(1972, 3, 11)),
    ("catalina-ruiz", "Catalina", "Ruiz", date(1995, 12, 2)),
    ("felipe-vargas", "Felipe", "Vargas", date(1983, 5, 23)),
    ("laura-mendez", "Laura", "Méndez", date(1990, 10, 30)),
    ("santiago-pena", "Santiago", "Peña", date(2002, 7, 14)),
    ("juliana-cardenas", "Juliana", "Cárdenas", date(1987, 1, 9)),
    ("tomas-salazar", "Tomás", "Salazar", date(1976, 6, 26)),
)

CATALOG: tuple[tuple[str, str, Decimal], ...] = (
    ("Profilaxis", "Prevención", Decimal("120000")),
    ("Restauración en resina", "Operatoria", Decimal("180000")),
    ("Endodoncia", "Endodoncia", Decimal("850000")),
    ("Reconstrucción", "Operatoria", Decimal("280000")),
    ("Corona", "Rehabilitación", Decimal("1200000")),
    ("Extracción", "Cirugía", Decimal("250000")),
    ("Blanqueamiento", "Estética", Decimal("650000")),
)


def demo_allowlist() -> set[UUID]:
    values: set[UUID] = set()
    for raw in os.getenv("DENTIA_DEMO_TENANT_IDS", "").split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            values.add(UUID(raw))
        except ValueError as exc:
            raise DemoTenantError("DENTIA_DEMO_TENANT_IDS contiene un UUID inválido.") from exc
    return values


def database_target() -> str:
    match = re.match(r"^[^:]+://(?:[^@]+@)?([^/:]+)(?::(\d+))?/([^?]+)", settings.database_url)
    if not match:
        return "configured-database"
    host, port, database = match.groups()
    return f"{host}:{port or 'default'}/{database}"


def is_production_target() -> bool:
    if settings.app_env.casefold() == "production":
        return True
    match = re.match(r"^[^:]+://(?:[^@]+@)?([^/:]+)", settings.database_url)
    host = match.group(1).casefold() if match else "unknown"
    return host not in {"localhost", "127.0.0.1", "::1", "postgres", "db"}


def deterministic_id(company_id: UUID, module: str, logical_key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"dentia:{company_id}:{DATASET_VERSION}:{module}:{logical_key}")


def _assert_exact_tenant_path(path: Path, company_id: UUID) -> None:
    if path.name != str(company_id) or path == path.parent:
        raise DemoTenantError("La ruta de storage no corresponde exactamente al tenant demo.")


def _metadata() -> RequestMetadata:
    return RequestMetadata(ip_address=None, user_agent="Dentia Demo CLI/WEB-2B")


def _context(session: Session, user: User, active_site_id: UUID | None = None) -> AuthContext:
    roles = list(
        session.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                UserRole.company_id == user.company_id,
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
        )
    )
    permissions = list(
        session.scalars(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == user.id,
                UserRole.company_id == user.company_id,
                UserRole.is_active.is_(True),
                RolePermission.is_active.is_(True),
                Permission.is_active.is_(True),
            )
            .distinct()
        )
    )
    auth_session = SimpleNamespace(id=None, active_site_id=active_site_id or user.default_site_id)
    return AuthContext(user=user, auth_session=auth_session, roles=roles, permissions=permissions)


def require_platform_actor(session: Session, actor_user_id: UUID) -> AuthContext:
    actor = session.scalar(
        select(User).where(User.id == actor_user_id, User.is_active.is_(True), User.status == "Activo")
    )
    if actor is None:
        raise DemoTenantError("El actor administrativo no existe o no está activo.")
    context = _context(session, actor)
    if "PLATFORM_ADMIN" not in context.roles:
        raise DemoTenantError("La operación requiere un Administrador de plataforma real.")
    return context


def require_demo_identity(session: Session, company_id: UUID, *, allowlist: bool = True) -> Company:
    company = session.scalar(select(Company).where(Company.id == company_id).with_for_update())
    if company is None:
        raise DemoTenantError("La empresa demo no existe.")
    failures: list[str] = []
    if company.slug != DEMO_COMPANY_SLUG:
        failures.append("slug")
    if company.name != DEMO_COMPANY_NAME:
        failures.append("nombre")
    if allowlist and company.id not in demo_allowlist():
        failures.append("allowlist UUID")
    if failures:
        raise DemoTenantError("Identidad demo inválida: " + ", ".join(failures) + ". ABORT.")
    return company


def _audit(session: Session, actor: User, company: Company, action: str, counts: dict[str, int]) -> None:
    session.add(
        AuditEvent(
            company_id=company.id,
            user_id=actor.id,
            session_id=None,
            entity="demo_tenant",
            entity_id=company.id,
            action=action,
            result="SUCCESS",
            detail={"dataset": DATASET_VERSION, "counts": counts},
            ip_address=None,
            user_agent="Dentia Demo CLI/WEB-2B",
        )
    )


def _one(session: Session, model, **filters):
    return session.scalar(select(model).filter_by(**filters))


def _reconcile_base(
    session: Session,
    company: Company,
    actor_context: AuthContext,
    *,
    admin_password: str | None,
) -> tuple[Site, User, User, User, Dentist, Dentist]:
    company.slug = DEMO_COMPANY_SLUG
    company.name = DEMO_COMPANY_NAME
    company.legal_name = "Clínica Dental Aurora — Datos sintéticos"
    company.tax_id = "DEMO-NO-TRIBUTARIO"
    company.normalized_tax_id = "DEMONOTRIBUTARIO"
    company.phone = "+00000000000"
    company.email = "contacto@aurora.demo.invalid"
    company.address = "Dirección sintética para demostración"
    company.city = "Bogotá"
    company.department = "Bogotá D.C."
    company.country = "Colombia"
    company.timezone = "America/Bogota"
    company.max_active_dentists = 3
    company.primary_dentist_name = "Dra. Valentina Ríos"
    company.professional_specialty = "Odontología general — DEMO"
    company.professional_license = "REGISTRO-DEMO-NO-VALIDO"
    company.header_text = "Clínica Dental Aurora — Entorno de demostración"
    company.footer_text = "Información completamente sintética."

    site = session.scalar(select(Site).where(Site.company_id == company.id).order_by(Site.created_at))
    if site is None:
        raise DemoTenantError("El aprovisionamiento no creó la sede base.")
    site.name = DEMO_SITE_NAME
    site.normalized_name = "sede centro"
    site.address = company.address
    site.city = company.city
    site.phone = company.phone
    site.timezone = "America/Bogota"
    site.status = "Activa"

    valentina = session.scalar(select(User).where(User.company_id == company.id).order_by(User.created_at))
    if valentina is None:
        raise DemoTenantError("El aprovisionamiento no creó la administradora demo.")
    valentina.name = "Dra. Valentina Ríos"
    valentina.must_change_password = False
    valentina.status = "Activo"
    valentina.is_active = True
    if admin_password:
        from app.core.security import hash_password

        valentina.password_hash = hash_password(admin_password)
    session.flush()
    tenant_context = _context(session, valentina, site.id)

    roles = {
        role.code: role
        for role in session.scalars(select(Role).where(Role.company_id == company.id, Role.is_active.is_(True)))
    }
    required = {"ADMINISTRATOR", "DENTIST_ADMIN", "DENTIST", "SECRETARY"}
    if not required.issubset(roles):
        raise DemoTenantError("Faltan roles empresariales requeridos para la demo.")
    # The standard catalog may contain a dormant PLATFORM_ADMIN role row, but
    # no Aurora user may ever be assigned to it (verified by audit_invariants).

    def ensure_user(name: str, email: str, role_codes: list[str]) -> User:
        normalized = email.casefold()
        user = session.scalar(select(User).where(User.normalized_email == normalized))
        if user is not None and user.company_id != company.id:
            raise DemoTenantError("Un correo demo ya pertenece a otra empresa.")
        if user is None:
            response = create_user(
                session,
                tenant_context,
                UserCreateRequest(
                    name=name,
                    email=email,
                    role_ids=[roles[code].id for code in role_codes],
                    site_ids=[site.id],
                    default_site_id=site.id,
                ),
                _metadata(),
            )
            user = session.get(User, response.user.id)
            change_user_status(session, tenant_context, user.id, "Activo", _metadata())
            user = session.get(User, user.id)
        else:
            user.name = name
            if user.status != "Activo" or not user.is_active:
                change_user_status(session, tenant_context, user.id, "Activo", _metadata())
                user = session.get(User, user.id)
        return user

    sebastian = ensure_user("Dr. Sebastián Torres", "sebastian@aurora.demo.invalid", ["DENTIST"])
    laura = ensure_user("Laura Gómez", "laura@aurora.demo.invalid", ["SECRETARY"])

    for user, role_codes in (
        (valentina, ["ADMINISTRATOR", "DENTIST_ADMIN"]),
        (sebastian, ["DENTIST"]),
        (laura, ["SECRETARY"]),
    ):
        assign_roles(
            session,
            tenant_context,
            user.id,
            UserRolesRequest(role_ids=[roles[code].id for code in role_codes]),
            _metadata(),
        )
        assign_sites(
            session,
            tenant_context,
            user.id,
            UserSitesRequest(site_ids=[site.id], default_site_id=site.id),
            _metadata(),
        )

    valentina_dentist = _one(session, Dentist, company_id=company.id, user_id=valentina.id)
    sebastian_dentist = _one(session, Dentist, company_id=company.id, user_id=sebastian.id)
    if valentina_dentist is None or sebastian_dentist is None:
        raise DemoTenantError("No se pudieron reconciliar los perfiles odontológicos demo.")
    for dentist, document in (
        (valentina_dentist, "DOC-DEMO-VALENTINA"),
        (sebastian_dentist, "DOC-DEMO-SEBASTIAN"),
    ):
        dentist.status = "Activo"
        dentist.is_active = True
        dentist.document_type = "Otro"
        dentist.document_number = document
        dentist.specialty = "Odontología general — DEMO"
        dentist.professional_license = "REGISTRO-DEMO-NO-VALIDO"
        if not _one(session, DentistSite, dentist_id=dentist.id, site_id=site.id):
            session.add(
                DentistSite(
                    company_id=company.id,
                    dentist_id=dentist.id,
                    site_id=site.id,
                    created_by=actor_context.user.id,
                )
            )
    session.flush()
    for dentist in (valentina_dentist, sebastian_dentist):
        if not dentist.signature_path:
            save_dentist_professional_signature(
                session,
                tenant_context,
                dentist.id,
                filename="firma-demo-no-valida.png",
                content_type="image/png",
                content=_signature_png_bytes(),
                metadata=_metadata(),
            )
    return site, valentina, sebastian, laura, valentina_dentist, sebastian_dentist


def _reconcile_patients(
    session: Session,
    context: AuthContext,
    *,
    sink_recipient: str,
) -> dict[str, Patient]:
    result: dict[str, Patient] = {}
    for index, (key, first, last, birth_date) in enumerate(PATIENTS, 1):
        document = f"{DEMO_DOCUMENT_PREFIX}{index:04d}"
        patient = session.scalar(
            select(Patient).where(
                Patient.company_id == context.user.company_id,
                Patient.normalized_document == normalize_document(document),
            )
        )
        if patient is None:
            email = sink_recipient if key == "sofia-herrera" else f"{key}@patients.aurora.demo.invalid"
            created = create_patient(
                session,
                context,
                PatientCreateRequest(
                    first_names=first,
                    last_names=last,
                    document_type="Otro",
                    document=document,
                    mobile=f"+0000000{index:04d}",
                    birth_date=birth_date,
                    sex="femenino" if index % 2 else "masculino",
                    email=email,
                    address="Dirección sintética de demostración",
                    city="Bogotá",
                    department="Bogotá D.C.",
                    administrative_notes=f"{DEMO_MARKER} Paciente completamente sintético.",
                ),
                _metadata(),
            )
            patient = session.get(Patient, created.id)
        if patient.company_id != context.user.company_id:
            raise DemoTenantError("Colisión cross-tenant en paciente demo.")
        result[key] = patient
    return result


def _reconcile_agenda(
    session: Session,
    context: AuthContext,
    patients: dict[str, Patient],
    site: Site,
    dentists: tuple[Dentist, Dentist],
    anchor: date,
) -> None:
    week_start = anchor - timedelta(days=anchor.weekday())
    now_local = datetime.now(BOGOTA)
    appointment_types = list(
        session.scalars(select(AppointmentType).where(AppointmentType.company_id == context.user.company_id))
    )
    if not appointment_types:
        raise DemoTenantError("No existen tipos de cita para construir la agenda demo.")
    by_name = {item.name: item for item in appointment_types}
    type_names = [name for name in ("Valoración", "Control", "Limpieza", "Tratamiento", "Urgencia") if name in by_name]
    if not type_names:
        type_names = [appointment_types[0].name]
    patient_values = list(patients.values())
    scheduled: list[Appointment] = []
    slots = (time(8, 0), time(10, 0), time(14, 0), time(16, 0))
    for day_offset in range(5):
        for slot_index, start_time in enumerate(slots):
            logical = f"week:{week_start.isoformat()}:{day_offset}:{slot_index}"
            item_id = deterministic_id(context.user.company_id, "appointment", logical)
            item = session.get(Appointment, item_id)
            if item is None:
                local_start = datetime.combine(week_start + timedelta(days=day_offset), start_time, BOGOTA)
                local_end = local_start + timedelta(minutes=45)
                past = local_end < now_local
                status = "Atendida" if past else ("Confirmada" if slot_index % 2 else "Programada")
                if past and day_offset == 0 and slot_index == 0:
                    status = "Cancelada"
                elif past and day_offset == 0 and slot_index == 1:
                    status = "No Asistió"
                elif past and day_offset == 0 and slot_index == 2:
                    status = "Reprogramada"
                item = Appointment(
                    id=item_id,
                    company_id=context.user.company_id,
                    patient_id=patient_values[(day_offset * 4 + slot_index) % len(patient_values)].id,
                    dentist_id=dentists[(day_offset + slot_index) % 2].id,
                    site_id=site.id,
                    appointment_type_id=by_name[type_names[(day_offset + slot_index) % len(type_names)]].id,
                    starts_at=local_start.astimezone(timezone.utc),
                    ends_at=local_end.astimezone(timezone.utc),
                    reason=f"{DEMO_MARKER} Atención sintética",
                    notes="Agenda relativa de demostración.",
                    status=status,
                    is_overbook=day_offset == 2 and slot_index == 3,
                    overbook_reason="Urgencia sintética" if day_offset == 2 and slot_index == 3 else None,
                    created_by=context.user.id,
                    updated_by=context.user.id,
                )
                session.add(item)
                session.flush()
                session.add(
                    AppointmentHistory(
                        company_id=context.user.company_id,
                        appointment_id=item.id,
                        previous_status=None,
                        new_status=status,
                        reason="Dataset Aurora v1",
                        user_id=context.user.id,
                    )
                )
            scheduled.append(item)

    categories = (
        [("overdue", anchor - timedelta(days=2), anchor - timedelta(days=9), "Pendiente", None)] * 2
        + [("upcoming", anchor + timedelta(days=index), anchor, "Pendiente", None) for index in range(1, 7)]
        + [("pending", anchor + timedelta(days=14 + index), anchor - timedelta(days=1), "Pendiente", None) for index in range(4)]
        + [("scheduled", anchor + timedelta(days=10 + index), anchor, "Cita programada", scheduled[index].id) for index in range(5)]
    )
    for index, (category, followup_date, contact_from, status, scheduled_id) in enumerate(categories):
        origin_id = deterministic_id(context.user.company_id, "followup-origin", str(index))
        origin = session.get(Appointment, origin_id)
        patient = patient_values[index % len(patient_values)]
        dentist = dentists[index % 2]
        if origin is None:
            start = datetime.combine(anchor - timedelta(days=30 + index), time(9, 0), BOGOTA)
            origin = Appointment(
                id=origin_id,
                company_id=context.user.company_id,
                patient_id=patient.id,
                dentist_id=dentist.id,
                site_id=site.id,
                appointment_type_id=appointment_types[index % len(appointment_types)].id,
                starts_at=start.astimezone(timezone.utc),
                ends_at=(start + timedelta(minutes=45)).astimezone(timezone.utc),
                reason=f"{DEMO_MARKER} Origen de seguimiento",
                status="Atendida",
                created_by=context.user.id,
                updated_by=context.user.id,
            )
            session.add(origin)
            session.flush()
        care_id = deterministic_id(context.user.company_id, "appointment-care", str(index))
        care = session.get(AppointmentCare, care_id)
        if care is None:
            care = AppointmentCare(
                id=care_id,
                company_id=context.user.company_id,
                appointment_id=origin.id,
                patient_id=patient.id,
                dentist_id=dentist.id,
                attention_description=f"{DEMO_MARKER} Atención clínica ficticia finalizada.",
                requires_followup=True,
                recommended_followup_date=followup_date,
                followup_reason="Control clínico sintético",
                registered_by=context.user.id,
                registered_at=origin.ends_at,
            )
            session.add(care)
            session.flush()
        followup_id = deterministic_id(context.user.company_id, "followup", str(index))
        if session.get(PatientFollowup, followup_id) is None:
            session.add(
                PatientFollowup(
                    id=followup_id,
                    company_id=context.user.company_id,
                    patient_id=patient.id,
                    origin_appointment_id=origin.id,
                    care_id=care.id,
                    dentist_id=dentist.id,
                    site_id=site.id,
                    followup_date=followup_date,
                    contact_from=contact_from,
                    reason=f"{DEMO_MARKER} Seguimiento {category}",
                    status=status,
                    scheduled_appointment_id=scheduled_id,
                    created_by=context.user.id,
                    updated_by=context.user.id,
                )
            )
    session.flush()


def _reconcile_commercial(
    session: Session,
    context: AuthContext,
    patients: dict[str, Patient],
    site: Site,
    dentists: tuple[Dentist, Dentist],
    anchor: date,
) -> dict[str, Treatment]:
    catalog: dict[str, ProcedureCatalogItem] = {}
    for name, category, value in CATALOG:
        item = session.scalar(
            select(ProcedureCatalogItem).where(
                ProcedureCatalogItem.company_id == context.user.company_id,
                func.lower(ProcedureCatalogItem.name) == name.casefold(),
            )
        )
        if item is None:
            response = create_procedure_catalog_item(
                session,
                context,
                ProcedureCatalogCreateRequest(
                    name=name,
                    category=category,
                    description=f"{DEMO_MARKER} Ítem sintético del catálogo Aurora.",
                    suggested_value=value,
                    suggested_scope_type="GENERAL",
                    odontogram_behavior="UNCONFIGURED",
                ),
                _metadata(),
            )
            item = session.get(ProcedureCatalogItem, response.id)
        catalog[name] = item

    specifications = {
        "mariana-lopez": ("Plan restaurador demo", ["Restauración en resina", "Profilaxis"]),
        "andres-martinez": ("Rehabilitación pieza 46 demo", ["Endodoncia", "Reconstrucción", "Corona"]),
        "nicolas-castro": ("Control preventivo demo", ["Profilaxis"]),
        "daniela-ramirez": ("Valoración y propuesta demo", ["Restauración en resina"]),
        "catalina-ruiz": ("Estética dental demo", ["Blanqueamiento"]),
        "laura-mendez": ("Tratamiento pausado demo", ["Corona"]),
    }
    treatments: dict[str, Treatment] = {}
    for index, (patient_key, (name, procedure_names)) in enumerate(specifications.items()):
        patient = patients[patient_key]
        treatment = session.scalar(
            select(Treatment).where(
                Treatment.company_id == context.user.company_id,
                Treatment.patient_id == patient.id,
                Treatment.name == name,
            )
        )
        if treatment is None:
            response = create_treatment(
                session,
                context,
                TreatmentCreateRequest(
                    patient_id=patient.id,
                    name=name,
                    description=f"{DEMO_MARKER} Caso comercial sintético.",
                    responsible_dentist_id=dentists[index % 2].id,
                    main_site_id=site.id,
                    start_date=anchor - timedelta(days=20 - index),
                ),
                _metadata(),
            )
            treatment = session.get(Treatment, response.id)
        procedure_ids: list[UUID] = []
        for procedure_index, procedure_name in enumerate(procedure_names):
            procedure = session.scalar(
                select(TreatmentProcedure).where(
                    TreatmentProcedure.treatment_id == treatment.id,
                    TreatmentProcedure.name == procedure_name,
                )
            )
            if procedure is None:
                item = catalog[procedure_name]
                response = create_procedure(
                    session,
                    context,
                    treatment.id,
                    ProcedureCreateRequest(
                        catalog_procedure_id=item.id,
                        name=item.name,
                        category=item.category,
                        dentist_id=dentists[index % 2].id,
                        site_id=site.id,
                        unit_value=item.suggested_value or Decimal("0"),
                        quantity=Decimal("1"),
                        status="Realizado" if patient_key == "andres-martinez" and procedure_index < 2 else "Pendiente",
                        estimated_date=anchor + timedelta(days=7 + procedure_index),
                        observations=f"{DEMO_MARKER} Procedimiento sintético.",
                    ),
                    _metadata(),
                )
                procedure = session.get(TreatmentProcedure, response.id)
            procedure_ids.append(procedure.id)

        budget = create_budget(
            session,
            context,
            treatment.id,
            BudgetCreateRequest(
                idempotency_key=f"aurora-{patient_key}-budget-v1",
                procedure_ids=procedure_ids,
                observations=f"{DEMO_MARKER} Valores ficticios, no constituyen tarifa sugerida.",
                expires_on=anchor + timedelta(days=30),
            ),
            _metadata(),
        )
        if patient_key in {"andres-martinez", "nicolas-castro", "mariana-lopez"} and budget.status != "Aprobado":
            budget = change_budget_status(
                session,
                context,
                budget.id,
                "Aprobado",
                "BUDGET_APPROVED",
                _metadata(),
            )
        if patient_key == "andres-martinez":
            if not session.scalar(
                select(func.count())
                .select_from(TreatmentPayment)
                .where(TreatmentPayment.treatment_id == treatment.id)
            ):
                create_payment(
                    session,
                    context,
                    treatment.id,
                    PaymentCreateRequest(
                        site_id=site.id,
                        dentist_id=dentists[index % 2].id,
                        procedure_ids=procedure_ids,
                        paid_at=datetime.combine(anchor - timedelta(days=1), time(15, 0), BOGOTA),
                        value=Decimal("500000"),
                        payment_method="Transferencia",
                        reference="DEMO-PAGO-PARCIAL",
                        observation=f"{DEMO_MARKER} Pago sintético.",
                        show_remaining_balance=True,
                    ),
                    _metadata(),
                )
        elif patient_key == "nicolas-castro":
            if not session.scalar(select(func.count()).select_from(TreatmentPayment).where(TreatmentPayment.treatment_id == treatment.id)):
                balance = Decimal(str(budget.final_value))
                create_payment(
                    session,
                    context,
                    treatment.id,
                    PaymentCreateRequest(
                        site_id=site.id,
                        dentist_id=dentists[index % 2].id,
                        procedure_ids=procedure_ids,
                        paid_at=datetime.combine(anchor - timedelta(days=2), time(11, 0), BOGOTA),
                        value=balance,
                        payment_method="Tarjeta",
                        reference="DEMO-PAGO-COMPLETO",
                        observation=f"{DEMO_MARKER} Pago sintético completo.",
                        show_remaining_balance=True,
                    ),
                    _metadata(),
                )
        if patient_key == "laura-mendez" and treatment.status != "Pausado":
            change_treatment_status(
                session,
                context,
                treatment.id,
                "Pausado",
                "TREATMENT_PAUSED",
                _metadata(),
                reason="Pausa sintética para demostración",
            )
        treatments[patient_key] = treatment
    return treatments


def _reconcile_clinical(
    session: Session,
    context: AuthContext,
    patients: dict[str, Patient],
    site: Site,
    dentist: Dentist,
    treatments: dict[str, Treatment],
    anchor: date,
) -> None:
    records: dict[str, UUID] = {}
    for key in ("mariana-lopez", "andres-martinez", "sofia-herrera", "nicolas-castro", "tomas-salazar"):
        response = create_clinical_record(
            session,
            context,
            patients[key].id,
            ClinicalRecordCreateRequest(
                opening_site_id=site.id,
                opening_dentist_id=dentist.id,
                chief_complaint=f"{DEMO_MARKER} Consulta odontológica ficticia.",
                current_situation="Caso sintético sin señales de alarma.",
                observations="Información creada exclusivamente para demostración.",
                allergies_state="NIEGA_ALERGIAS",
                medical_history_state="NIEGA_ANTECEDENTES",
            ),
            _metadata(),
        )
        records[key] = response.id

    for key, text_value in (
        ("mariana-lopez", "Se realizó valoración restauradora ficticia y control de higiene."),
        ("tomas-salazar", "Atención ficticia de urgencia, evolución estable y control indicado."),
    ):
        existing = session.scalar(
            text(
                "SELECT id FROM evoluciones_clinicas WHERE empresa_id=:company AND paciente_id=:patient AND texto_evolucion=:value"
            ),
            {"company": context.user.company_id, "patient": patients[key].id, "value": f"{DEMO_MARKER} {text_value}"},
        )
        if existing is None:
            response = create_clinical_evolution(
                session,
                context,
                patients[key].id,
                ClinicalEvolutionCreateRequest(
                    treatment_id=treatments.get(key).id if key in treatments else None,
                    site_id=site.id,
                    dentist_id=dentist.id,
                    attended_at=datetime.combine(anchor - timedelta(days=7), time(10, 0), BOGOTA),
                    evolution_text=f"{DEMO_MARKER} {text_value}",
                    assessment="Hallazgos ficticios coherentes con el caso demo.",
                    recommendations="Control periódico; texto no prescriptivo de demostración.",
                ),
                _metadata(),
            )
            sign_clinical_evolution(
                session,
                context,
                response.id,
                ClinicalEvolutionSignRequest(version=response.version, confirm_complete=True),
                _metadata(),
            )

    mariana = patients["mariana-lopez"]
    create_odontogram(session, context, mariana.id, OdontogramCreateRequest(), _metadata())
    existing_events = session.scalar(
        text("SELECT count(*) FROM odontograma_eventos WHERE empresa_id=:company AND paciente_id=:patient"),
        {"company": context.user.company_id, "patient": mariana.id},
    )
    if not existing_events:
        for code, name, color, symbol in (
            ("FIND_CARIES", "Caries", "#dc2626", "C"),
            ("FIND_RESTORATION", "Restauración existente", "#2563eb", "R"),
        ):
            item = session.scalar(
                select(OdontogramCatalogItem).where(
                    OdontogramCatalogItem.company_id == context.user.company_id,
                    OdontogramCatalogItem.code == code,
                )
            )
            if item is None:
                session.add(
                    OdontogramCatalogItem(
                        company_id=context.user.company_id,
                        code=code,
                        name=name,
                        type="FINDING",
                        category="Demo",
                        description=f"{DEMO_MARKER} Catálogo odontográfico sintético.",
                        color=color,
                        pattern="solid",
                        symbol=symbol,
                        allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
                        allowed_surfaces=[
                            "VESTIBULAR",
                            "LINGUAL",
                            "PALATAL",
                            "MESIAL",
                            "DISTAL",
                            "OCCLUSAL",
                            "INCISAL",
                        ],
                        is_active=True,
                    )
                )
        session.flush()
        catalog = {
            row.code: row
            for row in session.scalars(
                select(OdontogramCatalogItem).where(
                    OdontogramCatalogItem.code.in_(["FIND_CARIES", "FIND_RESTORATION", "OBS_NOTE"])
                )
            )
        }
        examples = (
            ("FIND_CARIES", "FINDING_ADDED", "FINDING", "36", ["OCCLUSAL"]),
            ("FIND_RESTORATION", "FINDING_ADDED", "FINDING", "15", ["MESIAL", "OCCLUSAL"]),
        )
        for code, event_type, layer, tooth_code, surfaces in examples:
            if code not in catalog:
                continue
            create_event(
                session,
                context,
                mariana.id,
                OdontogramEventCreateRequest(
                    event_type=event_type,
                    status="CONFIRMED",
                    clinical_date=datetime.combine(anchor - timedelta(days=6), time(11, 0), BOGOTA),
                    site_id=site.id,
                    dentist_id=dentist.id,
                    observation=f"{DEMO_MARKER} Hallazgo odontográfico sintético.",
                    details=[
                        OdontogramEventDetailInput(
                            catalog_item_id=catalog[code].id,
                            scope_type="TOOTH_SURFACE",
                            tooth_code=tooth_code,
                            dentition="PERMANENT",
                            surfaces=surfaces,
                            layer=layer,
                        )
                    ],
                ),
                _metadata(),
            )


def _signature_png_bytes() -> bytes:
    image = Image.new("RGB", (420, 140), "white")
    drawing = ImageDraw.Draw(image)
    drawing.line([(30, 95), (105, 35), (185, 100), (270, 45), (385, 90)], fill="#0f172a", width=6)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _signature_data_url() -> str:
    return "data:image/png;base64," + base64.b64encode(_signature_png_bytes()).decode("ascii")


def _create_consent_instance(
    session: Session,
    context: AuthContext,
    patient: Patient,
    site: Site,
    dentist: Dentist,
    version_id: UUID,
) -> ConsentInstance:
    response = create_batch(
        session,
        context,
        ConsentInstanceBatchCreateRequest(
            context=ConsentContextInput(
                patient_id=patient.id,
                site_id=site.id,
                dentist_profile_id=dentist.id,
                clinical_date=datetime.now(BOGOTA).date(),
            ),
            template_version_ids=[version_id],
        ),
        _metadata(),
    )[0]
    return session.get(ConsentInstance, response.id)


def _reconcile_consents(
    session: Session,
    context: AuthContext,
    patient: Patient,
    site: Site,
    dentist: Dentist,
    sink: DemoEmailSink,
) -> None:
    template = _one(session, ConsentTemplate, company_id=context.user.company_id, code=DEMO_TEMPLATE_CODE)
    if template is None:
        response = create_template(
            session,
            context,
            ConsentTemplateCreateRequest(
                code=DEMO_TEMPLATE_CODE,
                name="Consentimiento general Aurora — DEMO",
                description=f"{DEMO_MARKER} Documento sintético.",
                document_kind="GENERAL_CLINICAL_CONSENT",
                country_code="CO",
                language_code="es-CO",
                initial_version={
                    "title": "Consentimiento general de demostración",
                    "content": (
                        "# Consentimiento general de demostración\n\n"
                        "Paciente: {{ patient.full_name }}\n\n"
                        "Profesional: {{ professional.full_name }}\n\n"
                        "Fecha: {{ document.clinical_date }}\n\n"
                        "Documento sintético destinado exclusivamente a demostrar el flujo Dentia."
                    ),
                    "scope_type": "GENERAL",
                },
            ),
            _metadata(),
        )
        template = session.get(ConsentTemplate, response.id)
        version = session.scalar(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template.id))
        confirm_content_review(
            session,
            context,
            template.id,
            version.id,
            ConsentContentReviewRequest(confirmed=True),
            _metadata(),
        )
        publish_version(session, context, template.id, version.id, _metadata())
    version = session.scalar(
        select(ConsentTemplateVersion).where(
            ConsentTemplateVersion.template_id == template.id,
            ConsentTemplateVersion.status == "PUBLISHED",
        )
    )
    if version is None:
        raise DemoTenantError("La plantilla demo no tiene versión publicada.")

    instances = list(
        session.scalars(
            select(ConsentInstance).where(
                ConsentInstance.company_id == context.user.company_id,
                ConsentInstance.patient_id == patient.id,
                ConsentInstance.template_id == template.id,
            )
        )
    )
    by_status = {item.status for item in instances}
    if "DRAFT" not in by_status:
        _create_consent_instance(session, context, patient, site, dentist, version.id)
    if "READY_FOR_REVIEW" not in by_status:
        ready = _create_consent_instance(session, context, patient, site, dentist, version.id)
        confirm_professionally(
            session,
            context,
            ready.id,
            ConsentInstanceConfirmRequest(confirmed=True, row_version=ready.row_version),
            _metadata(),
        )
    if not any(item.status == "SIGNED" and item.completion_channel == "ELECTRONIC" for item in instances):
        electronic = _create_consent_instance(session, context, patient, site, dentist, version.id)
        confirm_professionally(
            session,
            context,
            electronic.id,
            ConsentInstanceConfirmRequest(confirmed=True, row_version=electronic.row_version),
            _metadata(),
        )
        issued = issue_access(session, context, electronic.id, _metadata())
        token = issued.public_path.rsplit("/", 1)[-1]
        with use_company_email_provider(context.user.company_id, sink):
            request_otp(session, token, _metadata())
            otp = sink.consume_latest_otp()
            cookie, _ = verify_otp(session, token, otp, _metadata())
            requirements = acceptance_requirements(session, token, cookie, _metadata())
            submit_acceptance(
                session,
                token,
                cookie,
                AcceptanceSubmitRequest(
                    idempotency_key=f"aurora-electronic-{electronic.id}",
                    acting_on_own_behalf=True,
                    declarations_version=requirements.declarations_version,
                    declaration_set_code=requirements.declaration_set_code,
                    declarations_set_sha256=requirements.declarations_set_sha256,
                    declarations=[{"code": item.code, "accepted": True} for item in requirements.declarations],
                    typed_full_name=requirements.signer_name or requirements.patient_name,
                    signature_data_url=_signature_data_url(),
                ),
                _metadata(),
            )
    instances = list(
        session.scalars(
            select(ConsentInstance).where(
                ConsentInstance.company_id == context.user.company_id,
                ConsentInstance.patient_id == patient.id,
                ConsentInstance.template_id == template.id,
            )
        )
    )
    if not any(item.status == "SIGNED" and item.completion_channel == "PAPER" for item in instances):
        paper = _create_consent_instance(session, context, patient, site, dentist, version.id)
        confirm_professionally(
            session,
            context,
            paper.id,
            ConsentInstanceConfirmRequest(confirmed=True, row_version=paper.row_version),
            _metadata(),
        )
        prepare_packet(session, context, paper.id, _metadata())
        printable, _ = paper_document_bytes(
            session,
            context,
            paper.id,
            final=False,
            metadata=_metadata(),
        )
        record_signed(session, context, paper.id, _metadata(), confirmed=True)
        upload_pages(session, context, paper.id, _metadata(), printable)
        finalize_paper(
            session,
            context,
            paper.id,
            ConsentPaperVerificationRequest(
                all_pages_present=True,
                correct_order=True,
                legible=True,
                signature_page_included=True,
                matches_printed_packet=True,
                physical_original_retained=True,
            ),
            _metadata(),
        )


def _reconcile_document(
    session: Session,
    context: AuthContext,
    patient: Patient,
    site: Site,
    dentist: Dentist,
    anchor: date,
) -> None:
    from app.models.clinical_document import ClinicalDocument

    existing = session.scalar(
        select(ClinicalDocument).where(
            ClinicalDocument.company_id == context.user.company_id,
            ClinicalDocument.patient_id == patient.id,
            ClinicalDocument.title == "Informe clínico sintético Aurora",
        )
    )
    if existing is not None:
        return
    response = create_document(
        session,
        context,
        patient.id,
        ClinicalDocumentCreateRequest(
            site_id=site.id,
            dentist_profile_id=dentist.id,
            document_type="CLINICAL_REPORT",
            title="Informe clínico sintético Aurora",
            subject="Resumen de caso demostrativo",
            body=(
                f"{DEMO_MARKER} Este informe contiene exclusivamente información ficticia "
                "para demostrar el flujo documental de Dentia."
            ),
            clinical_date=anchor,
        ),
        _metadata(),
    )
    finalize_document(session, context, response.id, _metadata())


def _counts(session: Session, company_id: UUID) -> dict[str, int]:
    from app.models.clinical_document import ClinicalDocument
    from app.models.treatment import Budget, TreatmentPayment

    models = {
        "users": User,
        "patients": Patient,
        "appointments": Appointment,
        "followups": PatientFollowup,
        "treatments": Treatment,
        "procedures": TreatmentProcedure,
        "budgets": Budget,
        "payments": TreatmentPayment,
        "consents": ConsentInstance,
        "documents": ClinicalDocument,
    }
    return {
        name: int(
            session.scalar(select(func.count()).select_from(model).where(model.company_id == company_id)) or 0
        )
        for name, model in models.items()
    }


def _file_count(company_id: UUID) -> int:
    transaction = DemoStorageTransaction(company_id)
    total = 0
    for root in transaction.roots():
        if root.exists():
            _assert_exact_tenant_path(root, company_id)
            total += sum(1 for path in root.rglob("*") if path.is_file())
    return total


def audit_invariants(
    session: Session,
    company: Company,
    *,
    sink: DemoEmailSink | None = None,
    require_allowlist: bool = True,
) -> tuple[str, ...]:
    checks: list[str] = []
    require_demo_identity(session, company.id, allowlist=require_allowlist)
    checks.append("identity:ok")
    forbidden = session.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.company_id == company.id, Role.code == "PLATFORM_ADMIN")
    )
    if forbidden:
        raise DemoTenantError("Un usuario demo tiene PLATFORM_ADMIN.")
    checks.append("global-role:absent")
    active_dentists = session.scalar(
        select(func.count()).select_from(Dentist).where(
            Dentist.company_id == company.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    ) or 0
    if active_dentists != 2 or active_dentists > company.max_active_dentists:
        raise DemoTenantError("La cuota/perfiles odontológicos demo es inconsistente.")
    checks.append("dentists:2-of-3")
    cross_queries = (
        "SELECT count(*) FROM citas c JOIN pacientes p ON p.id=c.paciente_id WHERE c.empresa_id=:id AND p.empresa_id<>:id",
        "SELECT count(*) FROM citas c JOIN sedes s ON s.id=c.sede_id WHERE c.empresa_id=:id AND s.empresa_id<>:id",
        "SELECT count(*) FROM citas c JOIN odontologos o ON o.id=c.odontologo_id WHERE c.empresa_id=:id AND o.empresa_id<>:id",
        "SELECT count(*) FROM tratamientos t JOIN pacientes p ON p.id=t.paciente_id WHERE t.empresa_id=:id AND p.empresa_id<>:id",
        "SELECT count(*) FROM consentimiento_instancias i JOIN pacientes p ON p.id=i.paciente_id WHERE i.empresa_id=:id AND p.empresa_id<>:id",
    )
    for query in cross_queries:
        if session.scalar(text(query), {"id": company.id}):
            raise DemoTenantError("Se detectó una referencia cross-tenant en el dataset demo.")
    checks.append("cross-tenant:absent")
    if sink is not None and any("[CODIGO REDACTADO]" not in record.body_redacted for record in sink.records if "Código" in record.subject):
        raise DemoTenantError("El sink conservó un OTP sin redacción.")
    checks.append("email-sink:scoped")
    for root in DemoStorageTransaction(company.id).roots():
        if root.exists():
            _assert_exact_tenant_path(root, company.id)
    checks.append("storage:tenant-scoped")
    return tuple(checks)


def _assert_reset_owned(session: Session, company_id: UUID) -> None:
    bad_patients = session.scalar(
        select(func.count()).select_from(Patient).where(
            Patient.company_id == company_id,
            ~Patient.normalized_document.startswith(normalize_document(DEMO_DOCUMENT_PREFIX)),
        )
    ) or 0
    allowed_names = {name for name, _, _ in CATALOG}
    bad_catalog = session.scalar(
        select(func.count()).select_from(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == company_id,
            ProcedureCatalogItem.name.notin_(allowed_names),
        )
    ) or 0
    bad_templates = session.scalar(
        select(func.count()).select_from(ConsentTemplate).where(
            ConsentTemplate.company_id == company_id,
            ~ConsentTemplate.code.startswith("AURORA-DEMO-"),
        )
    ) or 0
    if bad_patients or bad_catalog or bad_templates:
        raise DemoTenantError(
            "Reset abortado: existen datos operativos no reconocidos por Aurora v1."
        )


RIPS_TABLES: tuple[tuple[str, str], ...] = (
    ("colombia_rips_configurations", "empresa_id"),
    ("colombia_rips_providers", "empresa_id"),
    ("colombia_rips_provider_sites", "empresa_id"),
    ("colombia_rips_patient_profiles", "empresa_id"),
    ("colombia_rips_professional_profiles", "empresa_id"),
    ("colombia_rips_professional_assignments", "empresa_id"),
    ("colombia_rips_enabled_services", "empresa_id"),
    ("colombia_rips_procedure_cups_mappings", "company_id"),
    ("clinical_diagnosis_codings", "company_id"),
    ("rips_reportable_encounters", "company_id"),
    ("rips_reportable_service_lines", "company_id"),
    ("rips_reportable_line_diagnoses", "company_id"),
)


RESET_TABLES: tuple[tuple[str, str], ...] = (
    ("consentimiento_entregas_copia", "empresa_id"),
    ("consentimiento_documentos_finales", "empresa_id"),
    ("consentimiento_firmas_artefactos", "empresa_id"),
    ("consentimiento_evidencia_manifiestos", "empresa_id"),
    ("consentimiento_aceptacion_declaraciones", "empresa_id"),
    ("consentimiento_aceptaciones", "empresa_id"),
    ("consentimiento_solicitudes_aclaracion", "empresa_id"),
    ("consentimiento_sesiones_publicas", "empresa_id"),
    ("consentimiento_otp_desafios", "empresa_id"),
    ("consentimiento_paginas_papel", "empresa_id"),
    ("consentimiento_paquetes_papel", "empresa_id"),
    ("consentimiento_sesiones_acceso", "empresa_id"),
    ("consentimiento_instancia_procedimientos", "empresa_id"),
    ("consentimiento_adultos_responsables", "empresa_id"),
    ("consentimiento_instancias", "empresa_id"),
    ("consentimiento_plantilla_revisiones_contenido", "empresa_id"),
    ("consentimiento_plantilla_version_sedes", "empresa_id"),
    ("consentimiento_plantilla_version_procedimientos", "empresa_id"),
    ("consentimiento_plantilla_version_especialidades", "empresa_id"),
    ("consentimiento_biblioteca_instalaciones", "empresa_id"),
    ("consentimiento_plantilla_versiones", "empresa_id"),
    ("consentimiento_plantillas", "empresa_id"),
    ("consentimiento_instancia_consecutivos", "empresa_id"),
    ("receta_items", "empresa_id"),
    ("recetas", "empresa_id"),
    ("documentos_clinicos", "empresa_id"),
    ("odontograma_evento_detalles", "empresa_id"),
    ("odontograma_eventos", "empresa_id"),
    ("odontogramas", "empresa_id"),
    ("evoluciones_adendas", "empresa_id"),
    ("evoluciones_procedimientos", "empresa_id"),
    ("evoluciones_clinicas", "empresa_id"),
    ("historia_clinica_eventos", "empresa_id"),
    ("historias_clinicas_alergias", "empresa_id"),
    ("historias_clinicas_antecedentes", "empresa_id"),
    ("historias_clinicas_medicamentos", "empresa_id"),
    ("historias_clinicas", "empresa_id"),
    ("seguimiento_gestiones", "empresa_id"),
    ("seguimientos_paciente", "empresa_id"),
    ("atenciones_cita", "empresa_id"),
    ("cita_historial", "empresa_id"),
    ("pagos_tratamiento_procedimientos", "empresa_id"),
    ("pagos_tratamiento", "empresa_id"),
    ("presupuesto_detalle", "empresa_id"),
    ("presupuestos", "empresa_id"),
    ("tratamiento_eventos", "empresa_id"),
    ("tratamiento_procedimientos", "empresa_id"),
    ("citas", "empresa_id"),
    ("tratamientos", "empresa_id"),
    ("catalogo_procedimientos_diagnosticos", "empresa_id"),
    ("catalogo_procedimientos", "empresa_id"),
    ("responsables_paciente", "empresa_id"),
    ("pacientes", "empresa_id"),
    ("odontograma_catalogo", "empresa_id"),
)


def reset_operational_data(session: Session, company: Company) -> dict[str, int]:
    _assert_reset_owned(session, company.id)
    inspector = inspect(session.get_bind())
    for table_name, column_name in RIPS_TABLES:
        if inspector.has_table(table_name):
            count = session.scalar(
                text(f'SELECT count(*) FROM "{table_name}" WHERE "{column_name}"=:company_id'),
                {"company_id": company.id},
            )
            if count:
                raise DemoTenantError("Reset abortado: Aurora contiene datos RIPS fuera de WEB-2B.")
    session.execute(
        text(
            "UPDATE auth_sessions SET is_active=false, revoked_at=now(), revoke_reason='DEMO_RESET' "
            "WHERE empresa_id=:company_id AND is_active=true"
        ),
        {"company_id": company.id},
    )
    deleted: dict[str, int] = {}
    for table_name, column_name in RESET_TABLES:
        if not inspector.has_table(table_name):
            continue
        result = session.execute(
            text(f'DELETE FROM "{table_name}" WHERE "{column_name}"=:company_id'),
            {"company_id": company.id},
        )
        deleted[table_name] = int(result.rowcount or 0)
    session.flush()
    # Raw child-first DELETE statements bypass the ORM identity map. Expiring
    # it prevents reconciliation from mistaking deleted demo rows for live
    # records and is required for reset to rebuild every dependency.
    session.expire_all()
    return deleted


class DemoTenantOrchestrator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.storage_transaction: DemoStorageTransaction | None = None

    def plan(self, operation: str, company_id: UUID | None, *, apply: bool) -> DemoPlan:
        company = self.session.get(Company, company_id) if company_id else None
        identity_valid = bool(
            company
            and company.name == DEMO_COMPANY_NAME
            and company.slug == DEMO_COMPANY_SLUG
        )
        counts = _counts(self.session, company.id) if identity_valid else ({
            "users": 3,
            "patients": 14,
            "appointments": 37,
            "followups": 17,
            "treatments": 6,
            "procedures": 10,
            "budgets": 6,
            "payments": 2,
            "consents": 4,
            "documents": 1,
        } if company is None and operation == "create" else {})
        checks = ["dry-run" if not apply else "apply-requested", "no-startup-hook", "email-sink-required"]
        if company:
            checks.append("identity-match" if identity_valid else "identity-mismatch")
            checks.append("allowlisted" if company.id in demo_allowlist() else "not-allowlisted")
        return DemoPlan(
            operation=operation,
            dataset=DATASET_VERSION,
            company_id=company.id if company else company_id,
            app_env=settings.app_env,
            database_target=database_target(),
            apply=apply,
            counts=counts,
            checks=tuple(checks),
        )

    def status(self, company_id: UUID) -> DemoStatus:
        company = self.session.get(Company, company_id)
        if company is None:
            return DemoStatus(False, None, None, None, False, False, {}, (), 0)
        identity_valid = company.name == DEMO_COMPANY_NAME and company.slug == DEMO_COMPANY_SLUG
        consistency: tuple[str, ...] = ()
        if identity_valid and company.id in demo_allowlist():
            consistency = audit_invariants(self.session, company)
        return DemoStatus(
            found=True,
            company_id=company.id,
            name=company.name,
            slug=company.slug,
            allowlisted=company.id in demo_allowlist(),
            identity_valid=identity_valid,
            counts=_counts(self.session, company.id) if identity_valid else {},
            consistency=consistency,
            file_count=_file_count(company.id),
        )

    def create(
        self,
        actor_context: AuthContext,
        *,
        admin_email: str,
        admin_password: str,
        sink_recipient: str,
        anchor: date | None = None,
    ) -> DemoStatus:
        existing = self.session.scalar(select(Company).where(Company.slug == DEMO_COMPANY_SLUG))
        if existing is not None:
            if existing.name != DEMO_COMPANY_NAME:
                raise DemoTenantError("El slug demo está ocupado por otra empresa.")
            if existing.id not in demo_allowlist():
                raise DemoTenantError("La demo existente debe allowlistarse antes de update.")
            return self.update(
                actor_context,
                existing.id,
                admin_password=admin_password,
                sink_recipient=sink_recipient,
                anchor=anchor,
            )
        response = create_platform_company(
            self.session,
            actor_context,
            PlatformCompanyCreateRequest(
                company_name=DEMO_COMPANY_NAME,
                company_type="Clínica",
                tax_id="DEMO-NO-TRIBUTARIO",
                phone="+00000000000",
                email="contacto@aurora.demo.invalid",
                address="Dirección sintética para demostración",
                city="Bogotá",
                country="Colombia",
                timezone="America/Bogota",
                admin_name="Dra. Valentina Ríos",
                admin_email=admin_email,
                admin_password=admin_password,
            ),
            _metadata(),
        )
        company = self.session.get(Company, response.company.id)
        company.slug = DEMO_COMPANY_SLUG
        self.session.flush()
        self.storage_transaction = DemoStorageTransaction(company.id)
        self.storage_transaction.snapshot()
        # Creation is non-destructive; it may complete before the operator adds
        # the resulting UUID to the external allowlist.
        return self._populate(
            actor_context,
            company,
            admin_password=admin_password,
            sink_recipient=sink_recipient,
            anchor=anchor,
            require_allowlist=False,
            action="DEMO_TENANT_CREATED",
        )

    def update(
        self,
        actor_context: AuthContext,
        company_id: UUID,
        *,
        admin_password: str | None,
        sink_recipient: str,
        anchor: date | None = None,
    ) -> DemoStatus:
        company = require_demo_identity(self.session, company_id)
        return self._populate(
            actor_context,
            company,
            admin_password=admin_password,
            sink_recipient=sink_recipient,
            anchor=anchor,
            require_allowlist=True,
            action="DEMO_TENANT_UPDATED",
        )

    def reset(
        self,
        actor_context: AuthContext,
        company_id: UUID,
        *,
        sink_recipient: str,
        anchor: date | None = None,
    ) -> tuple[DemoStatus, dict[str, int]]:
        company = require_demo_identity(self.session, company_id)
        deleted = reset_operational_data(self.session, company)
        status = self._populate(
            actor_context,
            company,
            admin_password=None,
            sink_recipient=sink_recipient,
            anchor=anchor,
            require_allowlist=True,
            action="DEMO_TENANT_RESET",
        )
        return status, deleted

    def _populate(
        self,
        actor_context: AuthContext,
        company: Company,
        *,
        admin_password: str | None,
        sink_recipient: str,
        anchor: date | None,
        require_allowlist: bool,
        action: str,
    ) -> DemoStatus:
        if require_allowlist:
            require_demo_identity(self.session, company.id)
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": f"dentia-demo:{company.id}"},
        )
        site, valentina, _, _, dentist_a, dentist_b = _reconcile_base(
            self.session,
            company,
            actor_context,
            admin_password=admin_password,
        )
        context = _context(self.session, valentina, site.id)
        sink = DemoEmailSink(sink_recipient)
        patients = _reconcile_patients(self.session, context, sink_recipient=sink_recipient)
        anchor_date = anchor or datetime.now(BOGOTA).date()
        _reconcile_agenda(self.session, context, patients, site, (dentist_a, dentist_b), anchor_date)
        treatments = _reconcile_commercial(
            self.session,
            context,
            patients,
            site,
            (dentist_a, dentist_b),
            anchor_date,
        )
        _reconcile_clinical(
            self.session,
            context,
            patients,
            site,
            dentist_a,
            treatments,
            anchor_date,
        )
        _reconcile_consents(
            self.session,
            context,
            patients["sofia-herrera"],
            site,
            dentist_a,
            sink,
        )
        _reconcile_document(
            self.session,
            context,
            patients["mariana-lopez"],
            site,
            dentist_a,
            anchor_date,
        )
        checks = audit_invariants(
            self.session,
            company,
            sink=sink,
            require_allowlist=require_allowlist,
        )
        counts = _counts(self.session, company.id)
        _audit(self.session, actor_context.user, company, action, counts)
        self.session.flush()
        return DemoStatus(
            found=True,
            company_id=company.id,
            name=company.name,
            slug=company.slug,
            allowlisted=company.id in demo_allowlist(),
            identity_valid=True,
            counts=counts,
            consistency=checks,
            file_count=_file_count(company.id),
        )
