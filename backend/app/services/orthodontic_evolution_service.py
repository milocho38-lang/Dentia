from __future__ import annotations

import calendar
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import Dentist
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution, ClinicalTimelineEvent
from app.models.company import Company
from app.models.orthodontics import (
    OrthodonticCase,
    OrthodonticCatalogOption,
    OrthodonticEvolution,
    OrthodonticEvolutionMiniScrew,
)
from app.models.site import Site
from app.schemas.clinical_record_schema import (
    ClinicalEvolutionCreateRequest,
    ClinicalEvolutionDraftUpdateRequest,
    ClinicalEvolutionSignRequest,
)
from app.schemas.orthodontic_evolution_schema import (
    CATALOG_TYPES,
    OrthodonticCatalogOptionCreateRequest,
    OrthodonticCatalogOptionResponse,
    OrthodonticCatalogResponse,
    OrthodonticEvolutionCreateRequest,
    OrthodonticEvolutionListResponse,
    OrthodonticEvolutionResponse,
    OrthodonticEvolutionSignRequest,
    OrthodonticEvolutionUpdateRequest,
    OrthodonticMiniScrewResponse,
    OrthodonticOptionSnapshot,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.clinical_record_service import (
    ClinicalRecordError,
    create_clinical_evolution,
    sign_clinical_evolution,
    update_clinical_evolution_draft,
)
from app.services.orthodontics_entitlement_service import (
    OrthodonticsError,
    require_assigned_orthodontist,
    require_orthodontics_clinical_access,
)


class OrthodonticEvolutionError(OrthodonticsError):
    pass


STRUCTURED_ONLY_NOTE = "Evolución ortodóncica estructurada."


def _clean(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    action: str,
    entity: str,
    entity_id: UUID,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result="SUCCESS",
            detail=detail or {},
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _case(session: Session, context: AuthContext, case_id: UUID, *, lock: bool = False) -> OrthodonticCase:
    statement = select(OrthodonticCase).where(
        OrthodonticCase.id == case_id,
        OrthodonticCase.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    case = session.scalar(statement)
    if case is None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_EVOLUTION_NOT_FOUND", "Caso de Ortodoncia no encontrado.", 404
        )
    return case


def _ensure_case_active(case: OrthodonticCase) -> None:
    if case.status != "ACTIVE":
        code = "ORTHODONTIC_EVOLUTION_CASE_SUSPENDED" if case.status == "SUSPENDED" else "ORTHODONTIC_EVOLUTION_CASE_CLOSED"
        message = (
            "Reactiva el caso antes de registrar o firmar evoluciones."
            if case.status == "SUSPENDED"
            else "Solo un caso activo admite evoluciones de Ortodoncia."
        )
        raise OrthodonticEvolutionError(code, message, 409)


def _clinical_access(session: Session, context: AuthContext, case: OrthodonticCase, *, write: bool) -> UUID:
    access = require_orthodontics_clinical_access(session, context, write=write)
    if access.dentist_id is None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_EVOLUTION_ACCESS_DENIED", "No existe identidad odontológica activa.", 403
        )
    require_assigned_orthodontist(
        session,
        company_id=case.company_id,
        dentist_id=access.dentist_id,
        site_id=case.primary_site_id,
    )
    return access.dentist_id


def _catalog_type(value: str) -> str:
    normalized = value.upper()
    if normalized not in CATALOG_TYPES:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_INVALID_CATALOG_OPTION", "Catálogo de Ortodoncia no válido.", 404
        )
    return normalized


def _catalog_response(item: OrthodonticCatalogOption) -> OrthodonticCatalogOptionResponse:
    return OrthodonticCatalogOptionResponse(
        id=item.id,
        catalog_type=item.catalog_type,
        scope=item.scope,
        code=item.code,
        label=item.label,
        status=item.status,
        sort_order=item.sort_order,
        interval_value=item.interval_value,
        interval_unit=item.interval_unit,
    )


def list_catalog(
    session: Session, context: AuthContext, catalog_type: str
) -> OrthodonticCatalogResponse:
    catalog_type = _catalog_type(catalog_type)
    items = list(
        session.scalars(
            select(OrthodonticCatalogOption)
            .where(
                OrthodonticCatalogOption.catalog_type == catalog_type,
                OrthodonticCatalogOption.status == "ACTIVE",
                or_(
                    OrthodonticCatalogOption.scope == "DENTIA_BASE",
                    OrthodonticCatalogOption.company_id == context.user.company_id,
                ),
            )
            .order_by(OrthodonticCatalogOption.sort_order, OrthodonticCatalogOption.label)
        )
    )
    return OrthodonticCatalogResponse(
        catalog_type=catalog_type,
        can_manage="orthodontics.catalog.manage" in context.permissions,
        items=[_catalog_response(item) for item in items],
    )


def _custom_code(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_") or "OPTION"
    return f"TENANT_{slug[:55]}_{uuid4().hex[:8].upper()}"


def create_catalog_option(
    session: Session,
    context: AuthContext,
    catalog_type: str,
    payload: OrthodonticCatalogOptionCreateRequest,
    metadata: RequestMetadata,
) -> OrthodonticCatalogOptionResponse:
    catalog_type = _catalog_type(catalog_type)
    if catalog_type == "CONTROL_INTERVAL" and payload.interval_value is None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_INVALID_CONTROL_INTERVAL",
            "El próximo control requiere valor y unidad.",
            422,
        )
    if catalog_type != "CONTROL_INTERVAL" and payload.interval_value is not None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_INVALID_CATALOG_OPTION",
            "Solo el catálogo de próximo control admite intervalos.",
            422,
        )
    item = OrthodonticCatalogOption(
        company_id=context.user.company_id,
        catalog_type=catalog_type,
        scope="TENANT",
        code=_custom_code(payload.label),
        label=payload.label,
        status="ACTIVE",
        sort_order=1000,
        interval_value=payload.interval_value,
        interval_unit=payload.interval_unit,
        created_by_user_id=context.user.id,
    )
    session.add(item)
    session.flush()
    _audit(
        session,
        context,
        metadata,
        action="ORTHODONTIC_CATALOG_OPTION_CREATED",
        entity="orthodontic_catalog_option",
        entity_id=item.id,
        detail={"catalog_type": catalog_type, "code": item.code},
    )
    session.commit()
    return _catalog_response(item)


def retire_catalog_option(
    session: Session,
    context: AuthContext,
    option_id: UUID,
    metadata: RequestMetadata,
) -> OrthodonticCatalogOptionResponse:
    item = session.scalar(
        select(OrthodonticCatalogOption)
        .where(
            OrthodonticCatalogOption.id == option_id,
            OrthodonticCatalogOption.company_id == context.user.company_id,
            OrthodonticCatalogOption.scope == "TENANT",
        )
        .with_for_update()
    )
    if item is None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_INVALID_CATALOG_OPTION",
            "La opción no existe o es una opción base inmutable.",
            404,
        )
    if item.status == "ACTIVE":
        item.status = "RETIRED"
        item.retired_at = datetime.now(timezone.utc)
        item.retired_by_user_id = context.user.id
        _audit(
            session,
            context,
            metadata,
            action="ORTHODONTIC_CATALOG_OPTION_RETIRED",
            entity="orthodontic_catalog_option",
            entity_id=item.id,
            detail={"catalog_type": item.catalog_type, "code": item.code},
        )
    session.commit()
    return _catalog_response(item)


def _visible_option(
    session: Session,
    context: AuthContext,
    option_id: UUID | None,
    expected_type: str,
) -> OrthodonticCatalogOption | None:
    if option_id is None:
        return None
    item = session.get(OrthodonticCatalogOption, option_id)
    if (
        item is None
        or item.catalog_type != expected_type
        or (item.scope == "TENANT" and item.company_id != context.user.company_id)
        or item.scope not in {"DENTIA_BASE", "TENANT"}
    ):
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_INVALID_CATALOG_OPTION", "Opción de catálogo no disponible.", 422
        )
    if item.status != "ACTIVE":
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_CATALOG_OPTION_INACTIVE", "La opción seleccionada está retirada.", 409
        )
    return item


def _snapshot(item: OrthodonticCatalogOption | None) -> tuple[UUID | None, str | None, str | None]:
    return (item.id, item.code, item.label) if item else (None, None, None)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def _suggested_date(parent: ClinicalEvolution, option: OrthodonticCatalogOption | None) -> date | None:
    if option is None or option.interval_value is None:
        return None
    local_date = parent.attended_at.astimezone(ZoneInfo(parent.timezone_name)).date()
    if option.interval_unit == "WEEK":
        return local_date + timedelta(weeks=option.interval_value)
    return _add_months(local_date, option.interval_value)


def _parent_payload(payload: OrthodonticEvolutionCreateRequest, dentist_id: UUID) -> ClinicalEvolutionCreateRequest:
    structured = _has_structured_content(payload)
    return ClinicalEvolutionCreateRequest(
        site_id=payload.site_id,
        dentist_id=dentist_id,
        attended_at=payload.attended_at,
        evolution_text=payload.notes or (STRUCTURED_ONLY_NOTE if structured else None),
        performed_procedure=payload.performed_summary,
        indications=payload.next_session_instructions,
    )


def _parent_update_payload(
    payload: OrthodonticEvolutionUpdateRequest, dentist_id: UUID
) -> ClinicalEvolutionDraftUpdateRequest:
    structured = _has_structured_content(payload)
    return ClinicalEvolutionDraftUpdateRequest(
        version=payload.clinical_evolution_version,
        site_id=payload.site_id,
        dentist_id=dentist_id,
        attended_at=payload.attended_at,
        evolution_text=payload.notes or (STRUCTURED_ONLY_NOTE if structured else None),
        performed_procedure=payload.performed_summary,
        indications=payload.next_session_instructions,
    )


def _has_structured_content(
    payload: OrthodonticEvolutionCreateRequest | OrthodonticEvolutionUpdateRequest,
) -> bool:
    return bool(
        payload.upper_material_option_id
        or payload.upper_size_option_id
        or payload.lower_material_option_id
        or payload.lower_size_option_id
        or payload.upper_aligner_note
        or payload.lower_aligner_note
        or payload.elastic_type
        or payload.elastic_configuration
        or payload.mini_screws
        or payload.next_session_instructions
        or payload.next_control_option_id
        or payload.alert_text
    )


def _apply_payload(
    session: Session,
    context: AuthContext,
    item: OrthodonticEvolution,
    parent: ClinicalEvolution,
    payload: OrthodonticEvolutionCreateRequest | OrthodonticEvolutionUpdateRequest,
) -> None:
    upper_material = _visible_option(session, context, payload.upper_material_option_id, "ARCH_MATERIAL")
    upper_size = _visible_option(session, context, payload.upper_size_option_id, "ARCH_SIZE")
    lower_material = _visible_option(session, context, payload.lower_material_option_id, "ARCH_MATERIAL")
    lower_size = _visible_option(session, context, payload.lower_size_option_id, "ARCH_SIZE")
    control = _visible_option(session, context, payload.next_control_option_id, "CONTROL_INTERVAL")
    (
        item.upper_material_option_id,
        item.upper_material_code,
        item.upper_material_label,
    ) = _snapshot(upper_material)
    item.upper_size_option_id, item.upper_size_code, item.upper_size_label = _snapshot(upper_size)
    (
        item.lower_material_option_id,
        item.lower_material_code,
        item.lower_material_label,
    ) = _snapshot(lower_material)
    item.lower_size_option_id, item.lower_size_code, item.lower_size_label = _snapshot(lower_size)
    item.upper_aligner_note = _clean(payload.upper_aligner_note)
    item.lower_aligner_note = _clean(payload.lower_aligner_note)
    item.elastic_type = _clean(payload.elastic_type)
    item.elastic_configuration = _clean(payload.elastic_configuration)
    item.next_session_instructions = _clean(payload.next_session_instructions)
    item.next_control_option_id, item.next_control_code, item.next_control_label = _snapshot(control)
    item.next_control_value = control.interval_value if control else None
    item.next_control_unit = control.interval_unit if control else None
    item.suggested_next_control_date = _suggested_date(parent, control)
    if item.suggested_next_control_date:
        local = datetime.combine(
            item.suggested_next_control_date,
            datetime.min.time(),
            tzinfo=ZoneInfo(parent.timezone_name),
        )
        parent.next_control_at = local.astimezone(timezone.utc)
        parent.next_control_reason = item.next_control_label
    else:
        parent.next_control_at = None
        parent.next_control_reason = None
    item.alert_text = _clean(payload.alert_text)
    item.alert_active = bool(payload.alert_active and item.alert_text)
    session.query(OrthodonticEvolutionMiniScrew).filter(
        OrthodonticEvolutionMiniScrew.orthodontic_evolution_id == item.id
    ).delete(synchronize_session=False)
    for position, screw in enumerate(payload.mini_screws):
        session.add(
            OrthodonticEvolutionMiniScrew(
                company_id=item.company_id,
                orthodontic_evolution_id=item.id,
                screw_type=screw.screw_type,
                location=screw.location,
                material=screw.material,
                measurement=screw.measurement,
                notes=screw.notes,
                sort_order=position,
            )
        )


def _extension(
    session: Session, context: AuthContext, evolution_id: UUID, *, lock: bool = False
) -> tuple[OrthodonticEvolution, ClinicalEvolution, OrthodonticCase]:
    statement = select(OrthodonticEvolution).where(
        OrthodonticEvolution.id == evolution_id,
        OrthodonticEvolution.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    item = session.scalar(statement)
    if item is None:
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_EVOLUTION_NOT_FOUND", "Evolución de Ortodoncia no encontrada.", 404
        )
    parent = session.get(ClinicalEvolution, item.clinical_evolution_id)
    case = _case(session, context, item.orthodontic_case_id, lock=lock)
    if (
        parent is None
        or parent.company_id != case.company_id
        or parent.patient_id != case.patient_id
        or parent.clinical_record_id != case.clinical_record_id
    ):
        raise OrthodonticEvolutionError(
            "ORTHODONTIC_EVOLUTION_ACCESS_DENIED", "La evolución clínica vinculada no es válida.", 409
        )
    return item, parent, case


def _mini_screws(session: Session, item_id: UUID) -> list[OrthodonticEvolutionMiniScrew]:
    return list(
        session.scalars(
            select(OrthodonticEvolutionMiniScrew)
            .where(OrthodonticEvolutionMiniScrew.orthodontic_evolution_id == item_id)
            .order_by(OrthodonticEvolutionMiniScrew.sort_order, OrthodonticEvolutionMiniScrew.id)
        )
    )


def _response(session: Session, item: OrthodonticEvolution, parent: ClinicalEvolution) -> OrthodonticEvolutionResponse:
    professional_name = session.scalar(select(Dentist.name).where(Dentist.id == parent.dentist_id)) or "Profesional no disponible"
    return OrthodonticEvolutionResponse(
        id=item.id,
        orthodontic_case_id=item.orthodontic_case_id,
        clinical_evolution_id=parent.id,
        professional_name=professional_name,
        site_id=parent.site_id,
        attended_at=parent.attended_at,
        timezone_name=parent.timezone_name,
        status=parent.status,
        row_version=item.row_version,
        clinical_evolution_version=parent.version,
        signed_at=parent.signed_at,
        schema_version=item.schema_version,
        performed_summary=parent.performed_procedure,
        notes=None if parent.evolution_text == STRUCTURED_ONLY_NOTE else parent.evolution_text,
        upper_material=OrthodonticOptionSnapshot(option_id=item.upper_material_option_id, code=item.upper_material_code, label=item.upper_material_label),
        upper_size=OrthodonticOptionSnapshot(option_id=item.upper_size_option_id, code=item.upper_size_code, label=item.upper_size_label),
        lower_material=OrthodonticOptionSnapshot(option_id=item.lower_material_option_id, code=item.lower_material_code, label=item.lower_material_label),
        lower_size=OrthodonticOptionSnapshot(option_id=item.lower_size_option_id, code=item.lower_size_code, label=item.lower_size_label),
        upper_aligner_note=item.upper_aligner_note,
        lower_aligner_note=item.lower_aligner_note,
        elastic_type=item.elastic_type,
        elastic_configuration=item.elastic_configuration,
        mini_screws=[OrthodonticMiniScrewResponse(id=s.id, screw_type=s.screw_type, location=s.location, material=s.material, measurement=s.measurement, notes=s.notes, sort_order=s.sort_order) for s in _mini_screws(session, item.id)],
        next_session_instructions=item.next_session_instructions,
        next_control=OrthodonticOptionSnapshot(option_id=item.next_control_option_id, code=item.next_control_code, label=item.next_control_label),
        next_control_value=item.next_control_value,
        next_control_unit=item.next_control_unit,
        suggested_next_control_date=item.suggested_next_control_date,
        alert_text=item.alert_text,
        alert_active=item.alert_active,
        orthodontic_payload_hash=item.orthodontic_payload_hash,
    )


def create_orthodontic_evolution(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticEvolutionCreateRequest,
    metadata: RequestMetadata,
) -> OrthodonticEvolutionResponse:
    case = _case(session, context, case_id, lock=True)
    _ensure_case_active(case)
    dentist_id = _clinical_access(session, context, case, write=True)
    try:
        parent_response = create_clinical_evolution(
            session,
            context,
            case.patient_id,
            _parent_payload(payload, dentist_id),
            metadata,
            commit=False,
        )
        parent = session.get(ClinicalEvolution, parent_response.id)
        assert parent is not None
        item = OrthodonticEvolution(
            company_id=case.company_id,
            orthodontic_case_id=case.id,
            clinical_evolution_id=parent.id,
        )
        session.add(item)
        session.flush()
        _apply_payload(session, context, item, parent, payload)
        timeline = session.scalar(
            select(ClinicalTimelineEvent).where(
                ClinicalTimelineEvent.entity_type == "clinical_evolution",
                ClinicalTimelineEvent.entity_id == parent.id,
                ClinicalTimelineEvent.event_type == "CLINICAL_EVOLUTION_CREATED",
            )
        )
        if timeline is not None:
            timeline.title = "Evolución de Ortodoncia creada"
            timeline.event_metadata = {
                **(timeline.event_metadata or {}),
                "clinical_module": "ORTHODONTICS",
                "orthodontic_case_id": str(case.id),
            }
        _audit(
            session,
            context,
            metadata,
            action="ORTHODONTIC_EVOLUTION_CREATED",
            entity="orthodontic_evolution",
            entity_id=item.id,
            detail={"case_id": str(case.id), "clinical_evolution_id": str(parent.id)},
        )
        session.commit()
        return _response(session, item, parent)
    except (ClinicalRecordError, IntegrityError) as exc:
        session.rollback()
        if isinstance(exc, ClinicalRecordError):
            raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_ACCESS_DENIED", str(exc), exc.status_code) from exc
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_CONFLICT", "No fue posible crear la evolución.", 409) from exc


def list_orthodontic_evolutions(
    session: Session, context: AuthContext, case_id: UUID
) -> OrthodonticEvolutionListResponse:
    case = _case(session, context, case_id)
    _clinical_access(session, context, case, write=False)
    rows = session.execute(
        select(OrthodonticEvolution, ClinicalEvolution)
        .join(ClinicalEvolution, ClinicalEvolution.id == OrthodonticEvolution.clinical_evolution_id)
        .where(
            OrthodonticEvolution.company_id == case.company_id,
            OrthodonticEvolution.orthodontic_case_id == case.id,
        )
        .order_by(ClinicalEvolution.attended_at.desc(), OrthodonticEvolution.id.desc())
    ).all()
    return OrthodonticEvolutionListResponse(items=[_response(session, item, parent) for item, parent in rows])


def get_orthodontic_evolution(
    session: Session, context: AuthContext, evolution_id: UUID
) -> OrthodonticEvolutionResponse:
    item, parent, case = _extension(session, context, evolution_id)
    _clinical_access(session, context, case, write=False)
    return _response(session, item, parent)


def update_orthodontic_evolution(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    payload: OrthodonticEvolutionUpdateRequest,
    metadata: RequestMetadata,
) -> OrthodonticEvolutionResponse:
    item, parent, case = _extension(session, context, evolution_id, lock=True)
    _ensure_case_active(case)
    dentist_id = _clinical_access(session, context, case, write=True)
    if parent.status != "DRAFT":
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_ALREADY_SIGNED", "Una evolución firmada no puede editarse.", 409)
    if item.row_version != payload.row_version:
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_VERSION_CONFLICT", "La evolución cambió; actualiza antes de guardar.", 409)
    try:
        update_clinical_evolution_draft(
            session,
            context,
            parent.id,
            _parent_update_payload(payload, dentist_id),
            metadata,
            commit=False,
            allow_orthodontic_extension=True,
        )
        _apply_payload(session, context, item, parent, payload)
        item.row_version += 1
        _audit(
            session,
            context,
            metadata,
            action="ORTHODONTIC_EVOLUTION_UPDATED",
            entity="orthodontic_evolution",
            entity_id=item.id,
            detail={"case_id": str(case.id), "row_version": item.row_version},
        )
        session.commit()
        return _response(session, item, parent)
    except ClinicalRecordError as exc:
        session.rollback()
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_ACCESS_DENIED", str(exc), exc.status_code) from exc


def _canonical_extension(session: Session, item: OrthodonticEvolution) -> dict:
    return {
        "schema_version": item.schema_version,
        "orthodontic_case_id": str(item.orthodontic_case_id),
        "upper_material": {"option_id": str(item.upper_material_option_id) if item.upper_material_option_id else None, "code": item.upper_material_code, "label": item.upper_material_label},
        "upper_size": {"option_id": str(item.upper_size_option_id) if item.upper_size_option_id else None, "code": item.upper_size_code, "label": item.upper_size_label},
        "lower_material": {"option_id": str(item.lower_material_option_id) if item.lower_material_option_id else None, "code": item.lower_material_code, "label": item.lower_material_label},
        "lower_size": {"option_id": str(item.lower_size_option_id) if item.lower_size_option_id else None, "code": item.lower_size_code, "label": item.lower_size_label},
        "upper_aligner_note": item.upper_aligner_note,
        "lower_aligner_note": item.lower_aligner_note,
        "elastic_type": item.elastic_type,
        "elastic_configuration": item.elastic_configuration,
        "mini_screws": [
            {"type": screw.screw_type, "location": screw.location, "material": screw.material, "measurement": screw.measurement, "notes": screw.notes, "sort_order": screw.sort_order}
            for screw in _mini_screws(session, item.id)
        ],
        "next_session_instructions": item.next_session_instructions,
        "next_control": {"option_id": str(item.next_control_option_id) if item.next_control_option_id else None, "code": item.next_control_code, "label": item.next_control_label, "value": item.next_control_value, "unit": item.next_control_unit},
        "suggested_next_control_date": item.suggested_next_control_date.isoformat() if item.suggested_next_control_date else None,
        "alert": {"text": item.alert_text, "active": item.alert_active},
    }


def orthodontic_signature_fragment(session: Session, clinical_evolution_id: UUID) -> dict | None:
    item = session.scalar(
        select(OrthodonticEvolution).where(OrthodonticEvolution.clinical_evolution_id == clinical_evolution_id)
    )
    if item is None:
        return None
    return {
        **_canonical_extension(session, item),
        "payload_hash": item.orthodontic_payload_hash,
    }


def require_orthodontic_addendum_access(
    session: Session,
    context: AuthContext,
    clinical_evolution_id: UUID,
) -> None:
    """Apply the ORT access gates when a generic addendum targets ORT history."""
    item = session.scalar(
        select(OrthodonticEvolution).where(
            OrthodonticEvolution.clinical_evolution_id == clinical_evolution_id,
            OrthodonticEvolution.company_id == context.user.company_id,
        )
    )
    if item is None:
        return
    case = _case(session, context, item.orthodontic_case_id)
    _clinical_access(session, context, case, write=True)


def prepare_orthodontic_extension_for_sign(
    session: Session, context: AuthContext, parent: ClinicalEvolution
) -> None:
    item = session.scalar(
        select(OrthodonticEvolution)
        .where(OrthodonticEvolution.clinical_evolution_id == parent.id)
        .with_for_update()
    )
    if item is None:
        return
    case = _case(session, context, item.orthodontic_case_id, lock=True)
    _ensure_case_active(case)
    _clinical_access(session, context, case, write=True)
    if parent.patient_id != case.patient_id or parent.clinical_record_id != case.clinical_record_id:
        raise ClinicalRecordError("La evolución ortodóncica no coincide con el caso.", 409)
    canonical = _canonical_extension(session, item)
    item.orthodontic_payload_hash = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sign_orthodontic_evolution(
    session: Session,
    context: AuthContext,
    evolution_id: UUID,
    payload: OrthodonticEvolutionSignRequest,
    metadata: RequestMetadata,
) -> OrthodonticEvolutionResponse:
    item, parent, case = _extension(session, context, evolution_id, lock=True)
    _ensure_case_active(case)
    _clinical_access(session, context, case, write=True)
    if item.row_version != payload.row_version:
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_VERSION_CONFLICT", "La evolución cambió; actualiza antes de firmar.", 409)
    try:
        sign_clinical_evolution(
            session,
            context,
            parent.id,
            ClinicalEvolutionSignRequest(version=payload.clinical_evolution_version, confirm_complete=payload.confirm_complete),
            metadata,
            commit=False,
            allow_orthodontic_extension=True,
        )
        item.row_version += 1
        _audit(
            session,
            context,
            metadata,
            action="ORTHODONTIC_EVOLUTION_SIGNED",
            entity="orthodontic_evolution",
            entity_id=item.id,
            detail={"case_id": str(case.id), "clinical_evolution_id": str(parent.id), "orthodontic_payload_hash": item.orthodontic_payload_hash},
        )
        session.commit()
        return _response(session, item, parent)
    except ClinicalRecordError as exc:
        session.rollback()
        raise OrthodonticEvolutionError("ORTHODONTIC_EVOLUTION_ALREADY_SIGNED" if exc.status_code == 409 else "ORTHODONTIC_EVOLUTION_ACCESS_DENIED", str(exc), exc.status_code) from exc
