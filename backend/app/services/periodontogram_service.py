from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution
from app.models.company import Company
from app.models.periodontogram import (
    PeriodontalExam,
    PeriodontalExamVersion,
    PeriodontalSite,
    PeriodontalTooth,
)
from app.models.site import Site
from app.schemas.periodontogram_schema import (
    PeriodontalDraftBatchUpdateRequest,
    PeriodontalExamActionResponse,
    PeriodontalExamCorrectionRequest,
    PeriodontalExamCreateRequest,
    PeriodontalExamFinalizeRequest,
    PeriodontalExamHistoryItem,
    PeriodontalExamListResponse,
    PeriodontalExamResponse,
    PeriodontalExamVersionResponse,
    PeriodontalEvolutionCandidateListResponse,
    PeriodontalEvolutionLinkRequest,
    PeriodontalEvolutionSummaryResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.periodontal_clinical import (
    MOLAR_FDI,
    PERMANENT_FDI,
    PERMANENT_FDI_ORDER,
    SITE_CODES,
    calculate_cal,
    calculate_periodontal_aggregates,
    is_periodontal_pocket,
)
from app.services.site_access_service import authorized_site_ids, is_authorized_site
from app.services.periodontogram_pilot_service import (
    PeriodontogramPilotError,
    require_periodontogram_pilot_access,
)


PERIODONTAL_SCHEMA_VERSION = "PERIODONTAL_EXAM_V2"
PERIODONTAL_CLINICAL_CONTRACT = {
    "calculation": "PD_MINUS_GM",
    "dentition": "PERMANENT",
    "gm_sign": "APICAL_NEGATIVE_CORONAL_POSITIVE",
    "pocket_visual_threshold_mm": 4,
    "sites_per_tooth": 6,
}
SITE_VALUE_FIELDS = (
    "probing_depth_mm",
    "gingival_margin_mm",
    "bleeding_on_probing",
    "plaque",
    "suppuration",
)


class PeriodontogramError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_hash(payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
            Patient.is_active.is_(True),
            Patient.status == "Activo",
        )
    )
    if patient is None:
        raise PeriodontogramError("PERIODONTAL_PATIENT_NOT_FOUND", "Paciente activo no encontrado.", 404)
    return patient


def _active_dentist(session: Session, context: AuthContext, site_id: UUID) -> Dentist:
    try:
        access = require_periodontogram_pilot_access(
            session,
            context,
            site_id=site_id,
        )
    except PeriodontogramPilotError as exc:
        raise PeriodontogramError(exc.code, str(exc), exc.status_code) from exc
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.id == access.dentist_id,
            Dentist.company_id == context.user.company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )
    if dentist is None:
        raise PeriodontogramError(
            "PERIODONTAL_DENTIST_IDENTITY_REQUIRED",
            "Se requiere un perfil odontológico activo para esta acción.",
            403,
        )
    dentist_site = session.scalar(
        select(DentistSite).where(
            DentistSite.company_id == context.user.company_id,
            DentistSite.dentist_id == dentist.id,
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if dentist_site is None:
        raise PeriodontogramError(
            "PERIODONTAL_DENTIST_SITE_DENIED",
            "El odontólogo no está activo en la sede seleccionada.",
            403,
        )
    return dentist


def _selected_site(session: Session, context: AuthContext, requested_site_id: UUID | None) -> UUID:
    site_id = requested_site_id or context.auth_session.active_site_id
    if site_id is None or not is_authorized_site(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=site_id,
    ):
        raise PeriodontogramError("PERIODONTAL_SITE_DENIED", "No tienes acceso a la sede seleccionada.", 403)
    return site_id


def _exam(session: Session, context: AuthContext, exam_id: UUID, *, lock: bool = False) -> PeriodontalExam:
    statement = select(PeriodontalExam).where(
        PeriodontalExam.id == exam_id,
        PeriodontalExam.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    exam = session.scalar(statement)
    if exam is None:
        raise PeriodontogramError("PERIODONTAL_EXAM_NOT_FOUND", "Periodontograma no encontrado.", 404)
    if not is_authorized_site(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=exam.site_id,
    ):
        raise PeriodontogramError("PERIODONTAL_EXAM_NOT_FOUND", "Periodontograma no encontrado.", 404)
    _active_dentist(session, context, exam.site_id)
    return exam


def _current_version(
    session: Session,
    exam: PeriodontalExam,
    *,
    lock: bool = False,
) -> PeriodontalExamVersion:
    statement = select(PeriodontalExamVersion).where(
        PeriodontalExamVersion.id == exam.current_version_id,
        PeriodontalExamVersion.exam_id == exam.id,
        PeriodontalExamVersion.company_id == exam.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    version = session.scalar(statement)
    if version is None:
        raise PeriodontogramError(
            "PERIODONTAL_CURRENT_VERSION_NOT_FOUND",
            "La versión vigente del periodontograma no está disponible.",
            409,
        )
    return version


def _blank_site(site_code: str) -> dict[str, Any]:
    return {
        "site_code": site_code,
        "probing_depth_mm": None,
        "gingival_margin_mm": None,
        "clinical_attachment_level_mm": None,
        "is_periodontal_pocket": False,
        "bleeding_on_probing": None,
        "plaque": None,
        "suppuration": None,
    }


def _blank_teeth_payload() -> list[dict[str, Any]]:
    return [
        {
            "fdi_number": fdi,
            "state": "PRESENT",
            "mobility_grade": None,
            "furcation_mesial": None,
            "furcation_distal": None,
            "clinical_note": None,
            "sites": [_blank_site(site_code) for site_code in SITE_CODES],
        }
        for fdi in PERMANENT_FDI_ORDER
    ]


def _clinical_rows(
    session: Session,
    version: PeriodontalExamVersion,
) -> tuple[list[PeriodontalTooth], dict[UUID, list[PeriodontalSite]]]:
    teeth = list(
        session.scalars(
            select(PeriodontalTooth).where(
                PeriodontalTooth.company_id == version.company_id,
                PeriodontalTooth.exam_id == version.exam_id,
                PeriodontalTooth.version_id == version.id,
            )
        )
    )
    sites = list(
        session.scalars(
            select(PeriodontalSite).where(
                PeriodontalSite.company_id == version.company_id,
                PeriodontalSite.exam_id == version.exam_id,
                PeriodontalSite.version_id == version.id,
            )
        )
    )
    sites_by_tooth: dict[UUID, list[PeriodontalSite]] = {}
    for site in sites:
        sites_by_tooth.setdefault(site.tooth_id, []).append(site)
    return teeth, sites_by_tooth


def _clinical_payload(session: Session, version: PeriodontalExamVersion) -> list[dict[str, Any]]:
    teeth, sites_by_tooth = _clinical_rows(session, version)
    if not teeth:
        snapshot_teeth = (version.snapshot or {}).get("teeth")
        return snapshot_teeth if isinstance(snapshot_teeth, list) else _blank_teeth_payload()
    tooth_by_fdi = {tooth.fdi_number: tooth for tooth in teeth}
    result: list[dict[str, Any]] = []
    for fdi in PERMANENT_FDI_ORDER:
        tooth = tooth_by_fdi.get(fdi)
        if tooth is None:
            continue
        site_by_code = {site.site_code: site for site in sites_by_tooth.get(tooth.id, [])}
        site_payload = []
        for site_code in SITE_CODES:
            site = site_by_code.get(site_code)
            if site is None:
                site_payload.append(_blank_site(site_code))
                continue
            site_payload.append(
                {
                    "site_code": site.site_code,
                    "probing_depth_mm": site.probing_depth_mm,
                    "gingival_margin_mm": site.gingival_margin_mm,
                    "clinical_attachment_level_mm": calculate_cal(
                        site.probing_depth_mm, site.gingival_margin_mm
                    ),
                    "is_periodontal_pocket": is_periodontal_pocket(site.probing_depth_mm),
                    "bleeding_on_probing": site.bleeding_on_probing,
                    "plaque": site.plaque,
                    "suppuration": site.suppuration,
                }
            )
        result.append(
            {
                "fdi_number": tooth.fdi_number,
                "state": tooth.state,
                "mobility_grade": tooth.mobility_grade,
                "furcation_mesial": tooth.furcation_mesial,
                "furcation_distal": tooth.furcation_distal,
                "clinical_note": tooth.clinical_note,
                "sites": site_payload,
            }
        )
    return result


def _validate_clinical_payload(teeth: list[dict[str, Any]]) -> None:
    if [tooth["fdi_number"] for tooth in teeth] != list(PERMANENT_FDI_ORDER):
        raise PeriodontogramError(
            "PERIODONTAL_INVALID_DENTITION",
            "La versión no contiene la dentición permanente completa y ordenada.",
            409,
        )
    for tooth in teeth:
        fdi = tooth["fdi_number"]
        state = tooth["state"]
        sites = tooth["sites"]
        if [site["site_code"] for site in sites] != list(SITE_CODES):
            raise PeriodontogramError(
                "PERIODONTAL_INVALID_SITES",
                f"La pieza {fdi} no contiene los seis sitios clínicos válidos.",
                409,
            )
        has_site_data = any(
            site[field] is not None for site in sites for field in SITE_VALUE_FIELDS
        )
        if state == "ABSENT" and has_site_data:
            raise PeriodontogramError(
                "PERIODONTAL_ABSENT_TOOTH_HAS_DATA",
                f"La pieza ausente {fdi} conserva mediciones activas.",
                409,
            )
        if state != "PRESENT" and tooth["mobility_grade"] is not None:
            raise PeriodontogramError(
                "PERIODONTAL_MOBILITY_NATURAL_ONLY",
                f"La pieza {fdi} no admite movilidad en su estado actual.",
                409,
            )
        has_furcation = tooth["furcation_mesial"] is not None or tooth["furcation_distal"] is not None
        if has_furcation and (state != "PRESENT" or fdi not in MOLAR_FDI):
            raise PeriodontogramError(
                "PERIODONTAL_INVALID_FURCATION",
                f"La furcación no es válida para la pieza {fdi}.",
                409,
            )
        if state != "IMPLANT" and any(site["suppuration"] is not None for site in sites):
            raise PeriodontogramError(
                "PERIODONTAL_SUPPURATION_IMPLANT_ONLY",
                f"La supuración solo aplica a implantes; revisa la pieza {fdi}.",
                409,
            )


def _seed_blank_clinical_rows(
    session: Session,
    exam: PeriodontalExam,
    version: PeriodontalExamVersion,
    actor_id: UUID,
) -> None:
    existing = session.scalar(
        select(PeriodontalTooth.id).where(PeriodontalTooth.version_id == version.id).limit(1)
    )
    if existing is not None:
        return
    teeth = [
        PeriodontalTooth(
            company_id=exam.company_id,
            exam_id=exam.id,
            version_id=version.id,
            fdi_number=fdi,
            state="PRESENT",
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        for fdi in PERMANENT_FDI_ORDER
    ]
    session.add_all(teeth)
    session.flush()
    session.add_all(
        [
            PeriodontalSite(
                company_id=exam.company_id,
                exam_id=exam.id,
                version_id=version.id,
                tooth_id=tooth.id,
                site_code=site_code,
                created_by_user_id=actor_id,
                updated_by_user_id=actor_id,
            )
            for tooth in teeth
            for site_code in SITE_CODES
        ]
    )


def _snapshot(exam: PeriodontalExam, version: PeriodontalExamVersion, teeth: list[dict[str, Any]]) -> dict:
    aggregates = calculate_periodontal_aggregates(teeth)
    return {
        "clinical_contract": PERIODONTAL_CLINICAL_CONTRACT,
        "clinical_data": version.content,
        "coverage": aggregates["coverage"],
        "exam": {
            "clinical_date": exam.clinical_date.isoformat(),
            "company_id": str(exam.company_id),
            "exam_id": str(exam.id),
            "patient_id": str(exam.patient_id),
            "responsible_dentist_id": str(exam.responsible_dentist_id),
            "site_id": str(exam.site_id),
        },
        "indices": aggregates["indices"],
        "schema_version": PERIODONTAL_SCHEMA_VERSION,
        "teeth": teeth,
    }


def _integrity(version: PeriodontalExamVersion) -> str:
    if version.status != "FINALIZED":
        return "NOT_APPLICABLE"
    if version.snapshot is None or not version.snapshot_hash:
        return "FAIL"
    return "PASS" if hmac.compare_digest(_canonical_hash(version.snapshot), version.snapshot_hash) else "FAIL"


def _require_permission(context: AuthContext, permission: str) -> None:
    if permission not in context.permissions:
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_PERMISSION_DENIED",
            "No tienes permiso para consultar evoluciones clínicas.",
            403,
        )


def _evolution_summary(
    evolution: ClinicalEvolution,
    dentist: Dentist | None,
    site: Site | None,
) -> PeriodontalEvolutionSummaryResponse:
    return PeriodontalEvolutionSummaryResponse(
        id=evolution.id,
        attended_at=evolution.attended_at,
        timezone_name=evolution.timezone_name,
        status=evolution.status,
        site_id=evolution.site_id,
        site_name=site.name if site else "Sede no disponible",
        dentist_id=evolution.dentist_id,
        dentist_name=dentist.name if dentist else "Profesional no disponible",
    )


def _linked_evolution(
    session: Session,
    exam: PeriodontalExam,
) -> PeriodontalEvolutionSummaryResponse | None:
    if exam.evolution_id is None:
        return None
    row = session.execute(
        select(ClinicalEvolution, Dentist, Site)
        .join(Dentist, Dentist.id == ClinicalEvolution.dentist_id)
        .join(Site, Site.id == ClinicalEvolution.site_id)
        .where(
            ClinicalEvolution.id == exam.evolution_id,
            ClinicalEvolution.company_id == exam.company_id,
            ClinicalEvolution.patient_id == exam.patient_id,
            ClinicalEvolution.site_id == exam.site_id,
        )
    ).one_or_none()
    if row is None:
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_LINK_INVALID",
            "El vínculo con la evolución clínica no es válido.",
            409,
        )
    return _evolution_summary(*row)


def _version_response(version: PeriodontalExamVersion) -> PeriodontalExamVersionResponse:
    return PeriodontalExamVersionResponse(
        id=version.id,
        exam_id=version.exam_id,
        version_number=version.version_number,
        status=version.status,
        schema_version=version.schema_version,
        row_version=version.row_version,
        content=version.content,
        snapshot=version.snapshot,
        snapshot_hash=version.snapshot_hash,
        integrity_status=_integrity(version),
        supersedes_version_id=version.supersedes_version_id,
        correction_reason=version.correction_reason,
        created_by_user_id=version.created_by_user_id,
        finalized_by_user_id=version.finalized_by_user_id,
        finalized_at=version.finalized_at,
        created_at=version.created_at,
    )


def _exam_response(session: Session, exam: PeriodontalExam) -> PeriodontalExamResponse:
    versions = list(
        session.scalars(
            select(PeriodontalExamVersion)
            .where(
                PeriodontalExamVersion.company_id == exam.company_id,
                PeriodontalExamVersion.exam_id == exam.id,
            )
            .order_by(PeriodontalExamVersion.version_number.desc())
        )
    )
    current = next((item for item in versions if item.id == exam.current_version_id), None)
    if current is None:
        raise PeriodontogramError(
            "PERIODONTAL_CURRENT_VERSION_NOT_FOUND",
            "La versión vigente del periodontograma no está disponible.",
            409,
        )
    dentist = session.get(Dentist, exam.responsible_dentist_id)
    site = session.get(Site, exam.site_id)
    company = session.get(Company, exam.company_id)
    teeth = _clinical_payload(session, current)
    aggregates = calculate_periodontal_aggregates(teeth)
    return PeriodontalExamResponse(
        id=exam.id,
        company_id=exam.company_id,
        patient_id=exam.patient_id,
        site_id=exam.site_id,
        site_name=site.name if site else "Sede no disponible",
        timezone_name=(site.timezone if site and site.timezone else company.timezone if company else "America/Bogota"),
        responsible_dentist_id=exam.responsible_dentist_id,
        professional_name=dentist.name if dentist else "Profesional no disponible",
        evolution_id=exam.evolution_id,
        linked_evolution=_linked_evolution(session, exam),
        status=exam.status,
        clinical_date=exam.clinical_date,
        finalized_at=exam.finalized_at,
        row_version=exam.row_version,
        current_version=_version_response(current),
        versions=[_version_response(item) for item in versions],
        teeth=teeth,
        coverage=aggregates["coverage"],
        indices=aggregates["indices"],
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    exam: PeriodontalExam,
    action: str,
    *,
    version: PeriodontalExamVersion,
    extra_detail: dict[str, Any] | None = None,
) -> None:
    detail: dict[str, Any] = {
        "patient_id": str(exam.patient_id),
        "site_id": str(exam.site_id),
        "version_id": str(version.id),
        "version_number": version.version_number,
    }
    detail.update(extra_detail or {})
    session.add(
        AuditEvent(
            company_id=exam.company_id,
            user_id=context.user.id,
            entity="periodontal_exam",
            entity_id=exam.id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def list_periodontal_exams(session: Session, context: AuthContext, patient_id: UUID) -> PeriodontalExamListResponse:
    _patient(session, context, patient_id)
    active_site_id = _selected_site(session, context, None)
    _active_dentist(session, context, active_site_id)
    site_ids = authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
    )
    if not site_ids:
        return PeriodontalExamListResponse(items=[], total=0)
    rows = session.execute(
        select(PeriodontalExam, PeriodontalExamVersion, Dentist, Site)
        .join(PeriodontalExamVersion, PeriodontalExamVersion.id == PeriodontalExam.current_version_id)
        .join(Dentist, Dentist.id == PeriodontalExam.responsible_dentist_id)
        .join(Site, Site.id == PeriodontalExam.site_id)
        .where(
            PeriodontalExam.company_id == context.user.company_id,
            PeriodontalExam.patient_id == patient_id,
            PeriodontalExam.site_id.in_(site_ids),
        )
        .order_by(PeriodontalExam.clinical_date.desc(), PeriodontalExam.created_at.desc())
    ).all()
    items = [
        PeriodontalExamHistoryItem(
            id=exam.id,
            clinical_date=exam.clinical_date,
            professional_name=dentist.name,
            site_name=site.name,
            status=exam.status,
            current_version_number=version.version_number,
            allowed_actions=[
                "VIEW",
                *(["FINALIZE"] if exam.status == "DRAFT" and "periodontogram.finalize" in context.permissions else []),
                *(["CORRECT"] if exam.status == "FINALIZED" and "periodontogram.correct" in context.permissions else []),
            ],
            created_at=exam.created_at,
        )
        for exam, version, dentist, site in rows
    ]
    return PeriodontalExamListResponse(items=items, total=len(items))


def get_periodontal_exam(session: Session, context: AuthContext, exam_id: UUID) -> PeriodontalExamResponse:
    return _exam_response(session, _exam(session, context, exam_id))


def list_periodontal_evolution_candidates(
    session: Session,
    context: AuthContext,
    exam_id: UUID,
) -> PeriodontalEvolutionCandidateListResponse:
    exam = _exam(session, context, exam_id)
    _require_permission(context, "clinical_evolutions.view")
    _require_permission(context, "clinical_records.view_sensitive")
    _active_dentist(session, context, exam.site_id)
    if exam.status != "FINALIZED":
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_LINK_REQUIRES_FINALIZED",
            "Finaliza el periodontograma antes de vincularlo a una evolución.",
            409,
        )
    statement = (
        select(ClinicalEvolution, Dentist, Site)
        .join(Dentist, Dentist.id == ClinicalEvolution.dentist_id)
        .join(Site, Site.id == ClinicalEvolution.site_id)
        .where(
            ClinicalEvolution.company_id == exam.company_id,
            ClinicalEvolution.patient_id == exam.patient_id,
            ClinicalEvolution.site_id == exam.site_id,
            ClinicalEvolution.status.in_(("DRAFT", "SIGNED")),
        )
        .order_by(ClinicalEvolution.attended_at.desc())
    )
    if "DENTIST_ADMIN" not in context.roles:
        statement = statement.where(ClinicalEvolution.created_by == context.user.id)
    rows = session.execute(statement).all()
    return PeriodontalEvolutionCandidateListResponse(
        items=[_evolution_summary(*row) for row in rows]
    )


def link_periodontal_exam_to_evolution(
    session: Session,
    context: AuthContext,
    exam_id: UUID,
    payload: PeriodontalEvolutionLinkRequest,
) -> PeriodontalExamActionResponse:
    exam = _exam(session, context, exam_id, lock=True)
    if exam.evolution_id == payload.evolution_id:
        return PeriodontalExamActionResponse(
            message="El periodontograma ya está vinculado a esta evolución.",
            exam=_exam_response(session, exam),
        )
    if exam.evolution_id is not None:
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_LINK_CONFLICT",
            "El periodontograma ya está vinculado a otra evolución y el vínculo no puede reemplazarse.",
            409,
        )
    if exam.row_version != payload.row_version:
        raise PeriodontogramError(
            "PERIODONTAL_STALE_VERSION",
            "El periodontograma cambió en otra sesión. Actualiza antes de vincular la evolución.",
            409,
        )
    if exam.status != "FINALIZED":
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_LINK_REQUIRES_FINALIZED",
            "Finaliza el periodontograma antes de vincularlo a una evolución.",
            409,
        )
    current_version = _current_version(session, exam)
    if _integrity(current_version) != "PASS":
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_LINK_INTEGRITY_FAILED",
            "No se puede vincular un periodontograma cuya integridad no sea válida.",
            409,
        )
    _require_permission(context, "clinical_evolutions.view")
    _require_permission(context, "clinical_records.view_sensitive")
    _active_dentist(session, context, exam.site_id)
    evolution = session.scalar(
        select(ClinicalEvolution).where(
            ClinicalEvolution.id == payload.evolution_id,
            ClinicalEvolution.company_id == exam.company_id,
            ClinicalEvolution.patient_id == exam.patient_id,
            ClinicalEvolution.site_id == exam.site_id,
            ClinicalEvolution.status.in_(("DRAFT", "SIGNED")),
        )
    )
    if evolution is None:
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_NOT_AVAILABLE",
            "La evolución no está disponible para este periodontograma.",
            404,
        )
    if "DENTIST_ADMIN" not in context.roles and evolution.created_by != context.user.id:
        raise PeriodontogramError(
            "PERIODONTAL_EVOLUTION_ACCESS_DENIED",
            "No tienes acceso clínico a la evolución seleccionada.",
            403,
        )
    exam.evolution_id = evolution.id
    exam.updated_by_user_id = context.user.id
    exam.row_version += 1
    session.add(
        AuditEvent(
            company_id=exam.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="periodontal_exam",
            entity_id=exam.id,
            action="PERIODONTAL_EXAM_EVOLUTION_LINKED",
            result="SUCCESS",
            detail={
                "evolution_id": str(evolution.id),
                "site_id": str(exam.site_id),
            },
        )
    )
    session.commit()
    session.refresh(exam)
    return PeriodontalExamActionResponse(
        message="Periodontograma vinculado a la evolución clínica.",
        exam=_exam_response(session, exam),
    )


def create_periodontal_exam(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: PeriodontalExamCreateRequest,
    metadata: RequestMetadata,
) -> PeriodontalExamActionResponse:
    _patient(session, context, patient_id)
    site_id = _selected_site(session, context, payload.site_id)
    dentist = _active_dentist(session, context, site_id)
    exam = PeriodontalExam(
        company_id=context.user.company_id,
        patient_id=patient_id,
        site_id=site_id,
        responsible_dentist_id=dentist.id,
        status="DRAFT",
        clinical_date=payload.clinical_date,
        row_version=1,
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(exam)
    session.flush()
    version = PeriodontalExamVersion(
        company_id=exam.company_id,
        exam_id=exam.id,
        version_number=1,
        status="DRAFT",
        schema_version=PERIODONTAL_SCHEMA_VERSION,
        row_version=1,
        content={},
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(version)
    session.flush()
    exam.current_version_id = version.id
    _seed_blank_clinical_rows(session, exam, version, context.user.id)
    _audit(session, context, metadata, exam, "PERIODONTAL_EXAM_CREATED", version=version)
    session.commit()
    session.refresh(exam)
    return PeriodontalExamActionResponse(
        message="Periodontograma creado en borrador.",
        exam=_exam_response(session, exam),
    )


def update_periodontal_draft(
    session: Session,
    context: AuthContext,
    exam_id: UUID,
    payload: PeriodontalDraftBatchUpdateRequest,
    metadata: RequestMetadata,
) -> PeriodontalExamActionResponse:
    exam = _exam(session, context, exam_id, lock=True)
    _active_dentist(session, context, exam.site_id)
    version = _current_version(session, exam, lock=True)
    if exam.row_version != payload.row_version:
        raise PeriodontogramError(
            "PERIODONTAL_STALE_VERSION",
            "El periodontograma cambió. Recarga antes de guardar.",
            409,
        )
    if exam.status != "DRAFT" or version.status != "DRAFT":
        raise PeriodontogramError(
            "PERIODONTAL_DRAFT_REQUIRED",
            "Solo se puede modificar una versión en borrador.",
            409,
        )
    _seed_blank_clinical_rows(session, exam, version, context.user.id)
    session.flush()
    teeth, sites_by_tooth = _clinical_rows(session, version)
    tooth_by_fdi = {tooth.fdi_number: tooth for tooth in teeth}

    requested_fdi = {item.fdi_number for item in payload.teeth} | {item.fdi_number for item in payload.sites}
    invalid_fdi = sorted(requested_fdi - PERMANENT_FDI)
    if invalid_fdi:
        raise PeriodontogramError(
            "PERIODONTAL_INVALID_FDI",
            f"FDI permanente no válido: {', '.join(map(str, invalid_fdi))}.",
            422,
        )

    changed_teeth = 0
    changed_sites = 0
    for item in payload.teeth:
        tooth = tooth_by_fdi[item.fdi_number]
        fields = item.model_fields_set
        new_state = item.state if "state" in fields and item.state is not None else tooth.state
        state_changed = new_state != tooth.state
        site_rows = sites_by_tooth.get(tooth.id, [])
        has_data = any(
            value is not None
            for value in (tooth.mobility_grade, tooth.furcation_mesial, tooth.furcation_distal)
        ) or any(getattr(site, field) is not None for site in site_rows for field in SITE_VALUE_FIELDS)
        if state_changed and has_data and not item.clear_clinical_data:
            raise PeriodontogramError(
                "PERIODONTAL_STATE_CHANGE_REQUIRES_CLEAR",
                "Cambiar el estado de un diente con datos requiere confirmar su limpieza clínica.",
                409,
            )
        if item.clear_clinical_data:
            tooth.mobility_grade = None
            tooth.furcation_mesial = None
            tooth.furcation_distal = None
            for site in site_rows:
                for field in SITE_VALUE_FIELDS:
                    setattr(site, field, None)
                site.updated_by_user_id = context.user.id
        tooth.state = new_state
        if "mobility_grade" in fields:
            tooth.mobility_grade = item.mobility_grade
        if "furcation_mesial" in fields:
            tooth.furcation_mesial = item.furcation_mesial
        if "furcation_distal" in fields:
            tooth.furcation_distal = item.furcation_distal
        if "clinical_note" in fields:
            tooth.clinical_note = item.clinical_note.strip() if item.clinical_note else None
        if tooth.state != "PRESENT" and tooth.mobility_grade is not None:
            raise PeriodontogramError(
                "PERIODONTAL_MOBILITY_NATURAL_ONLY",
                "La movilidad solo aplica a dientes naturales presentes.",
                422,
            )
        if tooth.state != "PRESENT" and (
            tooth.furcation_mesial is not None or tooth.furcation_distal is not None
        ):
            raise PeriodontogramError(
                "PERIODONTAL_FURCATION_NATURAL_ONLY",
                "La furcación solo aplica a dientes naturales presentes.",
                422,
            )
        if tooth.fdi_number not in MOLAR_FDI and (
            tooth.furcation_mesial is not None or tooth.furcation_distal is not None
        ):
            raise PeriodontogramError(
                "PERIODONTAL_FURCATION_MOLAR_ONLY",
                "La furcación solo aplica a molares elegibles.",
                422,
            )
        if tooth.state == "ABSENT":
            tooth.mobility_grade = None
            tooth.furcation_mesial = None
            tooth.furcation_distal = None
        tooth.updated_by_user_id = context.user.id
        changed_teeth += 1

    for item in payload.sites:
        tooth = tooth_by_fdi[item.fdi_number]
        if tooth.state == "ABSENT":
            raise PeriodontogramError(
                "PERIODONTAL_ABSENT_TOOTH_HAS_NO_SITES",
                "No se pueden registrar sitios clínicos en un diente ausente.",
                422,
            )
        site = next(
            (candidate for candidate in sites_by_tooth.get(tooth.id, []) if candidate.site_code == item.site_code),
            None,
        )
        if site is None:
            raise PeriodontogramError(
                "PERIODONTAL_SITE_NOT_FOUND",
                "El sitio periodontal solicitado no está disponible.",
                409,
            )
        for field in item.model_fields_set - {"fdi_number", "site_code"}:
            setattr(site, field, getattr(item, field))
        if tooth.state != "IMPLANT" and site.suppuration is not None:
            raise PeriodontogramError(
                "PERIODONTAL_SUPPURATION_IMPLANT_ONLY",
                "La supuración se registra únicamente para implantes en este alcance.",
                422,
            )
        site.updated_by_user_id = context.user.id
        changed_sites += 1

    version.schema_version = PERIODONTAL_SCHEMA_VERSION
    version.updated_by_user_id = context.user.id
    version.row_version += 1
    exam.updated_by_user_id = context.user.id
    exam.row_version += 1
    _audit(
        session,
        context,
        metadata,
        exam,
        "PERIODONTAL_EXAM_DRAFT_UPDATED",
        version=version,
        extra_detail={"changed_sites": changed_sites, "changed_teeth": changed_teeth},
    )
    session.commit()
    session.refresh(exam)
    return PeriodontalExamActionResponse(
        message="Borrador periodontal actualizado.",
        exam=_exam_response(session, exam),
    )


def finalize_periodontal_exam(
    session: Session,
    context: AuthContext,
    exam_id: UUID,
    payload: PeriodontalExamFinalizeRequest,
    metadata: RequestMetadata,
) -> PeriodontalExamActionResponse:
    exam = _exam(session, context, exam_id, lock=True)
    _active_dentist(session, context, exam.site_id)
    version = _current_version(session, exam, lock=True)
    if exam.row_version != payload.row_version:
        raise PeriodontogramError(
            "PERIODONTAL_STALE_VERSION", "El periodontograma cambió. Recarga antes de finalizar.", 409
        )
    if exam.status != "DRAFT" or version.status != "DRAFT":
        raise PeriodontogramError(
            "PERIODONTAL_EXAM_ALREADY_FINALIZED", "El periodontograma ya está finalizado.", 409
        )
    _seed_blank_clinical_rows(session, exam, version, context.user.id)
    session.flush()
    version.schema_version = PERIODONTAL_SCHEMA_VERSION
    teeth = _clinical_payload(session, version)
    _validate_clinical_payload(teeth)
    frozen = _snapshot(exam, version, teeth)
    finalized_at = _now()
    version.snapshot = frozen
    version.snapshot_hash = _canonical_hash(frozen)
    version.status = "FINALIZED"
    version.finalized_by_user_id = context.user.id
    version.finalized_at = finalized_at
    version.updated_by_user_id = context.user.id
    version.row_version += 1
    exam.status = "FINALIZED"
    exam.finalized_at = finalized_at
    exam.updated_by_user_id = context.user.id
    exam.row_version += 1
    _audit(session, context, metadata, exam, "PERIODONTAL_EXAM_FINALIZED", version=version)
    _audit(session, context, metadata, exam, "PERIODONTAL_EXAM_VERSION_FINALIZED", version=version)
    session.commit()
    session.refresh(exam)
    return PeriodontalExamActionResponse(
        message="Periodontograma finalizado e inmutable.",
        exam=_exam_response(session, exam),
    )


def correct_periodontal_exam(
    session: Session,
    context: AuthContext,
    exam_id: UUID,
    payload: PeriodontalExamCorrectionRequest,
    metadata: RequestMetadata,
) -> PeriodontalExamActionResponse:
    exam = _exam(session, context, exam_id, lock=True)
    _active_dentist(session, context, exam.site_id)
    source = _current_version(session, exam, lock=True)
    if exam.row_version != payload.row_version:
        raise PeriodontogramError(
            "PERIODONTAL_STALE_VERSION", "El periodontograma cambió. Recarga antes de corregir.", 409
        )
    if exam.status != "FINALIZED" or source.status != "FINALIZED":
        raise PeriodontogramError(
            "PERIODONTAL_CORRECTION_REQUIRES_FINALIZED",
            "Solo un periodontograma finalizado puede corregirse.",
            409,
        )
    existing_draft = session.scalar(
        select(PeriodontalExamVersion.id).where(
            PeriodontalExamVersion.exam_id == exam.id,
            PeriodontalExamVersion.status == "DRAFT",
        )
    )
    if existing_draft is not None:
        raise PeriodontogramError(
            "PERIODONTAL_DRAFT_ALREADY_EXISTS",
            "Ya existe una corrección en borrador para este periodontograma.",
            409,
        )
    next_number = session.scalar(
        select(func.max(PeriodontalExamVersion.version_number)).where(
            PeriodontalExamVersion.exam_id == exam.id
        )
    ) or 1
    version = PeriodontalExamVersion(
        company_id=exam.company_id,
        exam_id=exam.id,
        version_number=next_number + 1,
        status="DRAFT",
        schema_version=PERIODONTAL_SCHEMA_VERSION,
        row_version=1,
        content={},
        supersedes_version_id=source.id,
        correction_reason=payload.reason.strip(),
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(version)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise PeriodontogramError(
            "PERIODONTAL_DRAFT_ALREADY_EXISTS",
            "Ya existe una corrección en borrador para este periodontograma.",
            409,
        ) from exc

    source_teeth, source_sites_by_tooth = _clinical_rows(session, source)
    if source_teeth:
        cloned_teeth: dict[UUID, PeriodontalTooth] = {}
        for source_tooth in source_teeth:
            clone = PeriodontalTooth(
                company_id=exam.company_id,
                exam_id=exam.id,
                version_id=version.id,
                fdi_number=source_tooth.fdi_number,
                state=source_tooth.state,
                mobility_grade=source_tooth.mobility_grade,
                furcation_mesial=source_tooth.furcation_mesial,
                furcation_distal=source_tooth.furcation_distal,
                clinical_note=source_tooth.clinical_note,
                created_by_user_id=context.user.id,
                updated_by_user_id=context.user.id,
            )
            session.add(clone)
            cloned_teeth[source_tooth.id] = clone
        session.flush()
        session.add_all(
            [
                PeriodontalSite(
                    company_id=exam.company_id,
                    exam_id=exam.id,
                    version_id=version.id,
                    tooth_id=cloned_teeth[source_tooth.id].id,
                    site_code=site.site_code,
                    probing_depth_mm=site.probing_depth_mm,
                    gingival_margin_mm=site.gingival_margin_mm,
                    bleeding_on_probing=site.bleeding_on_probing,
                    plaque=site.plaque,
                    suppuration=site.suppuration,
                    created_by_user_id=context.user.id,
                    updated_by_user_id=context.user.id,
                )
                for source_tooth in source_teeth
                for site in source_sites_by_tooth.get(source_tooth.id, [])
            ]
        )
    else:
        _seed_blank_clinical_rows(session, exam, version, context.user.id)

    exam.current_version_id = version.id
    exam.status = "DRAFT"
    exam.finalized_at = None
    exam.updated_by_user_id = context.user.id
    exam.row_version += 1
    _audit(session, context, metadata, exam, "PERIODONTAL_EXAM_CORRECTION_STARTED", version=version)
    session.commit()
    session.refresh(exam)
    return PeriodontalExamActionResponse(
        message="Nueva versión de corrección creada en borrador.",
        exam=_exam_response(session, exam),
    )
