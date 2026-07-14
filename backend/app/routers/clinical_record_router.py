from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import (
    get_current_auth_context,
    get_request_metadata,
    require_permission,
)
from app.database.session import get_db
from app.schemas.clinical_record_schema import (
    AllergyInput,
    AllergyListResponse,
    AllergyResponse,
    AllergyUpdateRequest,
    ClinicalEvolutionAddendumCreateRequest,
    ClinicalEvolutionAddendumResponse,
    ClinicalEvolutionCreateRequest,
    ClinicalEvolutionDraftUpdateRequest,
    ClinicalEvolutionListResponse,
    ClinicalEvolutionResponse,
    ClinicalEvolutionSignRequest,
    ClinicalRecordCreateRequest,
    ClinicalRecordDraftUpdateRequest,
    ClinicalRecordEnvelope,
    ClinicalRecordResponse,
    ClinicalSummaryResponse,
    ClinicalTimelineResponse,
    MedicalHistoryResponse,
    MedicalHistoryUpsertRequest,
    MedicationInput,
    MedicationListResponse,
    MedicationResponse,
    MedicationUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.clinical_record_service import (
    ClinicalRecordError,
    create_clinical_evolution,
    create_evolution_addendum,
    create_allergy,
    create_clinical_record,
    create_medication,
    get_clinical_evolution,
    get_clinical_record,
    get_clinical_summary,
    list_clinical_evolutions,
    list_clinical_timeline,
    list_evolution_addenda,
    list_allergies,
    list_medical_history,
    list_medications,
    replace_medical_history,
    sign_clinical_evolution,
    update_allergy,
    update_clinical_evolution_draft,
    update_clinical_record_draft,
    update_medication,
)


router = APIRouter(prefix="/api/patients", tags=["Clinical Records"])
evolution_router = APIRouter(prefix="/api/clinical-evolutions", tags=["Clinical Evolutions"])


def handle_clinical_error(exc: ClinicalRecordError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{patient_id}/clinical-record", response_model=ClinicalRecordEnvelope)
def get_clinical_record_endpoint(
    patient_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.view_sensitive"))
    ],
) -> ClinicalRecordEnvelope:
    try:
        return get_clinical_record(
            session,
            context,
            patient_id,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.post(
    "/{patient_id}/clinical-record",
    response_model=ClinicalRecordResponse,
    status_code=201,
)
def create_clinical_record_endpoint(
    patient_id: UUID,
    payload: ClinicalRecordCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.create"))
    ],
) -> ClinicalRecordResponse:
    try:
        return create_clinical_record(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.patch(
    "/{patient_id}/clinical-record/draft",
    response_model=ClinicalRecordResponse,
)
def update_clinical_record_draft_endpoint(
    patient_id: UUID,
    payload: ClinicalRecordDraftUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> ClinicalRecordResponse:
    try:
        return update_clinical_record_draft(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get(
    "/{patient_id}/clinical-evolutions",
    response_model=ClinicalEvolutionListResponse,
)
def list_clinical_evolutions_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.view"))
    ],
    status: str | None = None,
    treatment_id: UUID | None = None,
    dentist_id: UUID | None = None,
    site_id: UUID | None = None,
) -> ClinicalEvolutionListResponse:
    try:
        return list_clinical_evolutions(
            session,
            context,
            patient_id,
            status=status,
            treatment_id=treatment_id,
            dentist_id=dentist_id,
            site_id=site_id,
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.post(
    "/{patient_id}/clinical-evolutions",
    response_model=ClinicalEvolutionResponse,
    status_code=201,
)
def create_clinical_evolution_endpoint(
    patient_id: UUID,
    payload: ClinicalEvolutionCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.create"))
    ],
) -> ClinicalEvolutionResponse:
    try:
        return create_clinical_evolution(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get("/{patient_id}/clinical-timeline", response_model=ClinicalTimelineResponse)
def clinical_timeline_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_timeline.view"))
    ],
) -> ClinicalTimelineResponse:
    try:
        return list_clinical_timeline(session, context, patient_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get("/{patient_id}/clinical-summary", response_model=ClinicalSummaryResponse)
def clinical_summary_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> ClinicalSummaryResponse:
    try:
        if (
            "patients.view" not in context.permissions
            and "clinical_records.view" not in context.permissions
        ):
            raise ClinicalRecordError("No tienes permisos para consultar el resumen clínico.", 403)
        return get_clinical_summary(session, context, patient_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get("/{patient_id}/medical-history", response_model=MedicalHistoryResponse)
def medical_history_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.view_sensitive"))
    ],
) -> MedicalHistoryResponse:
    try:
        return list_medical_history(session, context, patient_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.put("/{patient_id}/medical-history", response_model=MedicalHistoryResponse)
def update_medical_history_endpoint(
    patient_id: UUID,
    payload: MedicalHistoryUpsertRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> MedicalHistoryResponse:
    try:
        return replace_medical_history(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get("/{patient_id}/allergies", response_model=AllergyListResponse)
def allergies_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.view_sensitive"))
    ],
) -> AllergyListResponse:
    try:
        return list_allergies(session, context, patient_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.post("/{patient_id}/allergies", response_model=AllergyResponse, status_code=201)
def create_allergy_endpoint(
    patient_id: UUID,
    payload: AllergyInput,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> AllergyResponse:
    try:
        return create_allergy(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.patch("/{patient_id}/allergies/{allergy_id}", response_model=AllergyResponse)
def update_allergy_endpoint(
    patient_id: UUID,
    allergy_id: UUID,
    payload: AllergyUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> AllergyResponse:
    try:
        return update_allergy(
            session,
            context,
            patient_id,
            allergy_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.get("/{patient_id}/medications", response_model=MedicationListResponse)
def medications_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.view_sensitive"))
    ],
) -> MedicationListResponse:
    try:
        return list_medications(session, context, patient_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.post(
    "/{patient_id}/medications",
    response_model=MedicationResponse,
    status_code=201,
)
def create_medication_endpoint(
    patient_id: UUID,
    payload: MedicationInput,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> MedicationResponse:
    try:
        return create_medication(
            session,
            context,
            patient_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@router.patch(
    "/{patient_id}/medications/{medication_id}",
    response_model=MedicationResponse,
)
def update_medication_endpoint(
    patient_id: UUID,
    medication_id: UUID,
    payload: MedicationUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_records.update_draft"))
    ],
) -> MedicationResponse:
    try:
        return update_medication(
            session,
            context,
            patient_id,
            medication_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@evolution_router.get("/{evolution_id}", response_model=ClinicalEvolutionResponse)
def get_clinical_evolution_endpoint(
    evolution_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.view"))
    ],
) -> ClinicalEvolutionResponse:
    try:
        return get_clinical_evolution(
            session,
            context,
            evolution_id,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@evolution_router.patch("/{evolution_id}/draft", response_model=ClinicalEvolutionResponse)
def update_clinical_evolution_draft_endpoint(
    evolution_id: UUID,
    payload: ClinicalEvolutionDraftUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.update_draft"))
    ],
) -> ClinicalEvolutionResponse:
    try:
        return update_clinical_evolution_draft(
            session,
            context,
            evolution_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@evolution_router.post("/{evolution_id}/sign", response_model=ClinicalEvolutionResponse)
def sign_clinical_evolution_endpoint(
    evolution_id: UUID,
    payload: ClinicalEvolutionSignRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.sign"))
    ],
) -> ClinicalEvolutionResponse:
    try:
        return sign_clinical_evolution(
            session,
            context,
            evolution_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@evolution_router.get(
    "/{evolution_id}/addenda",
    response_model=list[ClinicalEvolutionAddendumResponse],
)
def list_evolution_addenda_endpoint(
    evolution_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.view"))
    ],
) -> list[ClinicalEvolutionAddendumResponse]:
    try:
        return list_evolution_addenda(session, context, evolution_id)
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)


@evolution_router.post(
    "/{evolution_id}/addendum",
    response_model=ClinicalEvolutionAddendumResponse,
    status_code=201,
)
def create_evolution_addendum_endpoint(
    evolution_id: UUID,
    payload: ClinicalEvolutionAddendumCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.add_addendum"))
    ],
) -> ClinicalEvolutionAddendumResponse:
    try:
        return create_evolution_addendum(
            session,
            context,
            evolution_id,
            payload,
            get_request_metadata(request),
        )
    except ClinicalRecordError as exc:
        raise handle_clinical_error(exc)
