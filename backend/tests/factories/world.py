from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, normalize_email, utc_now
from app.core.security_catalog import PERMISSIONS, ROLES
from app.models.agenda import Appointment, AppointmentType, Dentist, DentistSite, Patient
from app.models.associations import RolePermission, UserRole, UserSite
from app.models.auth_session import AuthSession
from app.models.clinical_document import ClinicalDocument
from app.models.clinical_record import ClinicalEvolution, ClinicalRecord
from app.models.company import Company
from app.models.odontogram import Odontogram
from app.models.permission import Permission
from app.models.prescription import Prescription, PrescriptionItem
from app.models.role import Role
from app.models.site import Site
from app.models.treatment import Budget, BudgetDetail, Treatment, TreatmentPayment
from app.models.user import User


@dataclass(frozen=True)
class Actor:
    user: User
    token: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class TenantData:
    company: Company
    site_1: Site
    site_2: Site
    admin: Actor
    dentist_admin: Actor
    dentist: Actor
    secretary: Actor
    restricted_site_1: Actor
    inactive_user: Actor
    inactive_membership_user: Actor
    patient: Patient
    dentist_profile: Dentist
    appointment_type: AppointmentType
    appointment: Appointment
    treatment: Treatment
    budget: Budget
    payment: TreatmentPayment
    clinical_record: ClinicalRecord
    evolution: ClinicalEvolution
    odontogram: Odontogram
    prescription: Prescription
    clinical_document: ClinicalDocument
    prescription_content: bytes
    clinical_document_content: bytes


@dataclass(frozen=True)
class SecurityWorld:
    tenant_a: TenantData
    tenant_b: TenantData
    platform_admin: Actor
    no_company_user: User


def _seed_permissions(session: Session) -> dict[str, Permission]:
    permissions: dict[str, Permission] = {}
    for definition in PERMISSIONS:
        permission = Permission(
            code=definition.code,
            name=definition.name,
            module=definition.module,
            description=definition.description,
        )
        session.add(permission)
        permissions[definition.code] = permission
    session.flush()
    return permissions


def _seed_roles(
    session: Session,
    company: Company,
    permissions: dict[str, Permission],
    *,
    created_by: UUID | None = None,
) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for definition in ROLES:
        role = Role(
            company_id=company.id,
            code=definition.code,
            name=definition.name,
            description=definition.description,
            is_system=True,
            created_by=created_by,
        )
        session.add(role)
        roles[definition.code] = role
    session.flush()
    for definition in ROLES:
        role = roles[definition.code]
        for permission_code in definition.permission_codes:
            session.add(
                RolePermission(
                    company_id=company.id,
                    role_id=role.id,
                    permission_id=permissions[permission_code].id,
                    created_by=created_by,
                )
            )
    session.flush()
    return roles


def _company(session: Session, label: str) -> Company:
    company = Company(
        name=f"Clínica Ficticia {label}",
        legal_name=f"Clínica Ficticia {label} SAS",
        slug=f"dentia-test-{label.casefold()}-{uuid4().hex[:8]}",
        tax_id=f"TEST-{label}",
        phone="+570000000",
        email=f"contacto-{label.casefold()}@example.test",
        address=f"Calle Test {label}",
        city="Bogotá",
        country="Colombia",
        status="Activa",
    )
    session.add(company)
    session.flush()
    return company


def _site(session: Session, company: Company, label: str) -> Site:
    site = Site(
        company_id=company.id,
        name=f"Sede {label}",
        normalized_name=f"sede {label}".casefold(),
        address=f"Carrera Test {label}",
        city="Bogotá",
        timezone="America/Bogota",
        status="Activa",
    )
    session.add(site)
    session.flush()
    return site


def _user(session: Session, company: Company, default_site: Site, label: str, *, active: bool = True) -> User:
    user = User(
        company_id=company.id,
        default_site_id=default_site.id,
        name=f"Usuario {label}",
        email=f"{label.casefold().replace(' ', '-')}-{uuid4().hex[:6]}@example.test",
        normalized_email=normalize_email(f"{label.casefold().replace(' ', '-')}-{uuid4().hex[:6]}@example.test"),
        phone="+570000000",
        password_hash=hash_password("DentiaTestPassword123!"),
        status="Activo" if active else "Inactivo",
        is_active=active,
        failed_login_attempts=0,
        must_change_password=False,
        auth_version=1,
    )
    user.normalized_email = normalize_email(user.email)
    session.add(user)
    session.flush()
    return user


def _assign(
    session: Session,
    *,
    company: Company,
    user: User,
    roles: dict[str, Role],
    role_codes: tuple[str, ...],
    sites: tuple[Site, ...],
    active_membership: bool = True,
) -> None:
    for code in role_codes:
        session.add(
            UserRole(
                company_id=company.id,
                user_id=user.id,
                role_id=roles[code].id,
                is_active=active_membership,
                created_by=user.id,
            )
        )
    for index, site in enumerate(sites):
        session.add(
            UserSite(
                company_id=company.id,
                user_id=user.id,
                site_id=site.id,
                is_default=index == 0,
                is_active=active_membership,
                created_by=user.id,
            )
        )
    session.flush()


def _token(session: Session, user: User, site: Site | None, role_codes: tuple[str, ...]) -> str:
    session_id = uuid4()
    auth_session = AuthSession(
        id=session_id,
        company_id=user.company_id,
        user_id=user.id,
        active_site_id=site.id if site else None,
        refresh_token_hash=hashlib.sha256(f"{session_id}.refresh".encode()).hexdigest(),
        token_family_id=uuid4(),
        rotation_counter=0,
        ip_address="127.0.0.1",
        user_agent="dentia-security-tests",
        last_seen_at=utc_now(),
        expires_at=utc_now() + timedelta(hours=2),
    )
    session.add(auth_session)
    session.flush()
    token, _ = create_access_token(
        user_id=user.id,
        session_id=session_id,
        company_id=user.company_id,
        site_id=site.id if site else None,
        roles=list(role_codes),
        auth_version=user.auth_version,
    )
    return token


def _actor(
    session: Session,
    *,
    company: Company,
    roles: dict[str, Role],
    role_codes: tuple[str, ...],
    sites: tuple[Site, ...],
    label: str,
    active: bool = True,
    active_membership: bool = True,
) -> Actor:
    user = _user(session, company, sites[0], label, active=active)
    _assign(
        session,
        company=company,
        user=user,
        roles=roles,
        role_codes=role_codes,
        sites=sites,
        active_membership=active_membership,
    )
    token = _token(session, user, sites[0], role_codes)
    return Actor(user=user, token=token, roles=role_codes)


def _clinical_resources(
    session: Session,
    *,
    company: Company,
    site: Site,
    creator: User,
    label: str,
    storage_root: Path,
) -> tuple[
    Patient,
    Dentist,
    AppointmentType,
    Appointment,
    Treatment,
    Budget,
    TreatmentPayment,
    ClinicalRecord,
    ClinicalEvolution,
    Odontogram,
    Prescription,
    ClinicalDocument,
    bytes,
    bytes,
]:
    patient = Patient(
        company_id=company.id,
        first_names=f"Paciente {label}",
        last_names="Seguridad",
        document_type="CC",
        document=f"{label}0001",
        normalized_document=f"{label}0001",
        mobile="+573000000000",
        normalized_mobile="573000000000",
        birth_date=date(1990, 1, 1),
        sex="no informa",
        email=f"paciente-{label.casefold()}@example.test",
        normalized_email=f"paciente-{label.casefold()}@example.test",
        status="Activo",
        search_text=f"paciente {label.casefold()} seguridad {label}0001 573000000000",
        profile_complete=True,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(patient)
    session.flush()

    dentist = Dentist(company_id=company.id, user_id=creator.id, name=f"Dra. {label}", status="Activo", created_by=creator.id)
    session.add(dentist)
    session.flush()
    session.add(DentistSite(company_id=company.id, dentist_id=dentist.id, site_id=site.id, created_by=creator.id))

    appointment_type = AppointmentType(
        company_id=company.id,
        name=f"Valoración {label}",
        suggested_duration_minutes=30,
        allows_overbook=True,
        created_by=creator.id,
    )
    session.add(appointment_type)
    session.flush()

    starts = datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc)
    appointment = Appointment(
        company_id=company.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        site_id=site.id,
        appointment_type_id=appointment_type.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        reason=f"Consulta {label}",
        status="Programada",
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(appointment)
    session.flush()

    treatment = Treatment(
        company_id=company.id,
        patient_id=patient.id,
        name=f"Tratamiento {label}",
        status="Aprobado",
        responsible_dentist_id=dentist.id,
        main_site_id=site.id,
        start_date=date(2026, 8, 1),
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(treatment)
    session.flush()

    budget_id = uuid4()
    budget = Budget(
        id=budget_id,
        company_id=company.id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        series_id=budget_id,
        version=1,
        is_current=True,
        status="Aprobado",
        gross_value=Decimal("100000"),
        discount_value=Decimal("0"),
        discount_calculated_value=Decimal("0"),
        final_value=Decimal("100000"),
        issued_at=starts,
        approved_at=starts,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(budget)
    session.flush()
    session.add(
        BudgetDetail(
            company_id=company.id,
            budget_id=budget.id,
            name=f"Procedimiento {label}",
            quantity=Decimal("1"),
            unit_value=Decimal("100000"),
            total_value=Decimal("100000"),
            order=1,
            scope_type="GENERAL",
        )
    )
    session.flush()

    payment = TreatmentPayment(
        company_id=company.id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        budget_id=budget.id,
        site_id=site.id,
        dentist_id=dentist.id,
        paid_at=starts + timedelta(hours=1),
        value=Decimal("25000"),
        payment_method="Efectivo",
        reference=f"REF-{label}",
        observation=f"Pago ficticio {label}",
        receipt_sequence=1,
        receipt_number=f"CP-{label}-000001",
        status="valido",
        registered_by=creator.id,
    )
    session.add(payment)
    session.flush()

    clinical_record = ClinicalRecord(
        company_id=company.id,
        patient_id=patient.id,
        opening_site_id=site.id,
        opening_dentist_id=dentist.id,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(clinical_record)
    session.flush()

    evolution = ClinicalEvolution(
        company_id=company.id,
        patient_id=patient.id,
        clinical_record_id=clinical_record.id,
        appointment_id=appointment.id,
        treatment_id=treatment.id,
        site_id=site.id,
        dentist_id=dentist.id,
        attended_at=starts,
        timezone_name="America/Bogota",
        evolution_text=f"Evolución ficticia {label}",
        status="SIGNED",
        signed_at=starts,
        signed_by=creator.id,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(evolution)
    session.flush()

    odontogram = Odontogram(
        company_id=company.id,
        patient_id=patient.id,
        clinical_record_id=clinical_record.id,
        status="ACTIVE",
        preferred_dentition="PERMANENT",
        created_by=creator.id,
    )
    session.add(odontogram)

    prescription_bytes = f"%PDF-1.4 fake prescription {label}".encode()
    prescription_rel = f"{company.id}/prescription-{label}.pdf"
    prescription_path = storage_root / "prescriptions" / prescription_rel
    prescription_path.parent.mkdir(parents=True, exist_ok=True)
    prescription_path.write_bytes(prescription_bytes)
    prescription = Prescription(
        company_id=company.id,
        site_id=site.id,
        patient_id=patient.id,
        professional_user_id=creator.id,
        dentist_profile_id=dentist.id,
        related_treatment_id=treatment.id,
        related_evolution_id=evolution.id,
        related_appointment_id=appointment.id,
        status="FINALIZED",
        prescription_number=f"RX-{label}-1",
        sequence=1,
        clinical_date=date(2026, 8, 1),
        prescription_snapshot={"items": []},
        patient_snapshot={"name": f"Paciente {label} Seguridad"},
        professional_snapshot={"name": dentist.name},
        institution_snapshot={"company": {"name": company.name}},
        pdf_storage_path=prescription_rel,
        pdf_sha256=hashlib.sha256(prescription_bytes).hexdigest(),
        integrity_hash=hashlib.sha256(f"rx-{label}".encode()).hexdigest(),
        finalized_at=starts,
        finalized_by=creator.id,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(prescription)
    session.flush()
    session.add(
        PrescriptionItem(
            company_id=company.id,
            prescription_id=prescription.id,
            position=1,
            generic_name="Ibuprofeno test",
            pharmaceutical_form="Tableta",
            concentration="400 mg",
            dose="1 tableta",
            route="Oral",
            frequency="Cada 8 horas",
            duration="3 días",
            total_quantity="9",
        )
    )

    document_bytes = f"%PDF-1.4 fake clinical document {label}".encode()
    document_rel = f"{company.id}/document-{label}.pdf"
    document_path = storage_root / "clinical_documents" / document_rel
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_bytes(document_bytes)
    clinical_document = ClinicalDocument(
        company_id=company.id,
        site_id=site.id,
        patient_id=patient.id,
        professional_user_id=creator.id,
        dentist_profile_id=dentist.id,
        related_treatment_id=treatment.id,
        related_evolution_id=evolution.id,
        related_appointment_id=appointment.id,
        document_type="CLINICAL_REPORT",
        status="FINALIZED",
        document_number=f"DOC-{label}-1",
        sequence=1,
        title=f"Informe {label}",
        subject=f"Asunto {label}",
        body=f"Contenido clínico ficticio {label}",
        clinical_date=date(2026, 8, 1),
        document_snapshot={"body": f"Contenido clínico ficticio {label}"},
        patient_snapshot={"name": f"Paciente {label} Seguridad"},
        professional_snapshot={"name": dentist.name},
        institution_snapshot={"company": {"name": company.name}},
        pdf_storage_path=document_rel,
        pdf_sha256=hashlib.sha256(document_bytes).hexdigest(),
        integrity_hash=hashlib.sha256(f"doc-{label}".encode()).hexdigest(),
        finalized_at=starts,
        finalized_by=creator.id,
        created_by=creator.id,
        updated_by=creator.id,
    )
    session.add(clinical_document)
    session.flush()

    return (
        patient,
        dentist,
        appointment_type,
        appointment,
        treatment,
        budget,
        payment,
        clinical_record,
        evolution,
        odontogram,
        prescription,
        clinical_document,
        prescription_bytes,
        document_bytes,
    )


def _tenant(session: Session, permissions: dict[str, Permission], label: str, storage_root: Path) -> TenantData:
    company = _company(session, label)
    site_1 = _site(session, company, f"{label}1")
    site_2 = _site(session, company, f"{label}2")
    roles = _seed_roles(session, company, permissions)
    admin = _actor(session, company=company, roles=roles, role_codes=("ADMINISTRATOR",), sites=(site_1, site_2), label=f"{label} Admin")
    dentist_admin = _actor(session, company=company, roles=roles, role_codes=("DENTIST_ADMIN",), sites=(site_1, site_2), label=f"{label} Dentist Admin")
    dentist = _actor(session, company=company, roles=roles, role_codes=("DENTIST",), sites=(site_1,), label=f"{label} Dentist")
    secretary = _actor(session, company=company, roles=roles, role_codes=("SECRETARY",), sites=(site_1, site_2), label=f"{label} Secretary")
    restricted = _actor(session, company=company, roles=roles, role_codes=("SECRETARY",), sites=(site_1,), label=f"{label} Restricted")
    inactive = _actor(session, company=company, roles=roles, role_codes=("SECRETARY",), sites=(site_1,), label=f"{label} Inactive", active=False)
    inactive_membership = _actor(
        session,
        company=company,
        roles=roles,
        role_codes=("SECRETARY",),
        sites=(site_1,),
        label=f"{label} Inactive Membership",
        active_membership=False,
    )
    (
        patient,
        dentist_profile,
        appointment_type,
        appointment,
        treatment,
        budget,
        payment,
        clinical_record,
        evolution,
        odontogram,
        prescription,
        clinical_document,
        prescription_content,
        clinical_document_content,
    ) = _clinical_resources(session, company=company, site=site_1, creator=dentist_admin.user, label=label, storage_root=storage_root)
    session.commit()
    return TenantData(
        company=company,
        site_1=site_1,
        site_2=site_2,
        admin=admin,
        dentist_admin=dentist_admin,
        dentist=dentist,
        secretary=secretary,
        restricted_site_1=restricted,
        inactive_user=inactive,
        inactive_membership_user=inactive_membership,
        patient=patient,
        dentist_profile=dentist_profile,
        appointment_type=appointment_type,
        appointment=appointment,
        treatment=treatment,
        budget=budget,
        payment=payment,
        clinical_record=clinical_record,
        evolution=evolution,
        odontogram=odontogram,
        prescription=prescription,
        clinical_document=clinical_document,
        prescription_content=prescription_content,
        clinical_document_content=clinical_document_content,
    )


def build_security_world(session: Session, storage_root: Path) -> SecurityWorld:
    permissions = _seed_permissions(session)
    tenant_a = _tenant(session, permissions, "A", storage_root)
    tenant_b = _tenant(session, permissions, "B", storage_root)
    platform_company = _company(session, "Platform")
    platform_site = _site(session, platform_company, "Platform")
    platform_roles = _seed_roles(session, platform_company, permissions)
    platform_admin = _actor(
        session,
        company=platform_company,
        roles=platform_roles,
        role_codes=("PLATFORM_ADMIN",),
        sites=(platform_site,),
        label="Platform Admin",
    )
    no_company_user = User(
        company_id=platform_company.id,
        default_site_id=platform_site.id,
        name="Usuario Sin Empresa Activa",
        email=f"sin-empresa-{uuid4().hex[:6]}@example.test",
        normalized_email=f"sin-empresa-{uuid4().hex[:6]}@example.test",
        password_hash=hash_password("DentiaTestPassword123!"),
        status="Activo",
        is_active=True,
    )
    no_company_user.normalized_email = normalize_email(no_company_user.email)
    session.add(no_company_user)
    session.commit()
    return SecurityWorld(tenant_a=tenant_a, tenant_b=tenant_b, platform_admin=platform_admin, no_company_user=no_company_user)
