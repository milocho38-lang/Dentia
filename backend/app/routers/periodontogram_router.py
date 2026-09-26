from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.periodontogram_schema import (
    PeriodontalExamActionResponse,
    PeriodontalExamCorrectionRequest,
    PeriodontalExamCreateRequest,
    PeriodontalDraftBatchUpdateRequest,
    PeriodontalExamFinalizeRequest,
    PeriodontalExamListResponse,
    PeriodontalExamResponse,
    PeriodontalEvolutionCandidateListResponse,
    PeriodontalEvolutionLinkRequest,
    PeriodontogramPilotAccessResponse,
)
from app.services.auth_service import AuthContext
from app.services.periodontogram_service import (
    PeriodontogramError,
    correct_periodontal_exam,
    create_periodontal_exam,
    finalize_periodontal_exam,
    get_periodontal_exam,
    link_periodontal_exam_to_evolution,
    list_periodontal_exams,
    list_periodontal_evolution_candidates,
    update_periodontal_draft,
)
from app.services.periodontogram_pilot_service import (
    resolve_periodontogram_pilot_access,
)


router = APIRouter(tags=["Periodontogram"])


def _handle(exc: PeriodontogramError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get(
    "/api/periodontograms/access",
    response_model=PeriodontogramPilotAccessResponse,
)
def periodontogram_access_endpoint(
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.view"))],
) -> PeriodontogramPilotAccessResponse:
    return resolve_periodontogram_pilot_access(session, context)


@router.get(
    "/api/patients/{patient_id}/periodontograms",
    response_model=PeriodontalExamListResponse,
)
def list_periodontograms_endpoint(
    patient_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.view"))],
) -> PeriodontalExamListResponse:
    try:
        return list_periodontal_exams(session, context, patient_id)
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.patch(
    "/api/periodontograms/{exam_id}/draft",
    response_model=PeriodontalExamActionResponse,
)
def update_periodontogram_draft_endpoint(
    exam_id: UUID,
    payload: PeriodontalDraftBatchUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.update_draft"))],
) -> PeriodontalExamActionResponse:
    try:
        return update_periodontal_draft(
            session, context, exam_id, payload, get_request_metadata(request)
        )
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.post(
    "/api/patients/{patient_id}/periodontograms",
    response_model=PeriodontalExamActionResponse,
    status_code=201,
)
def create_periodontogram_endpoint(
    patient_id: UUID,
    payload: PeriodontalExamCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.create"))],
) -> PeriodontalExamActionResponse:
    try:
        return create_periodontal_exam(
            session, context, patient_id, payload, get_request_metadata(request)
        )
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.get(
    "/api/periodontograms/{exam_id}",
    response_model=PeriodontalExamResponse,
)
def get_periodontogram_endpoint(
    exam_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.view"))],
) -> PeriodontalExamResponse:
    try:
        return get_periodontal_exam(session, context, exam_id)
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.get(
    "/api/periodontograms/{exam_id}/evolution-candidates",
    response_model=PeriodontalEvolutionCandidateListResponse,
)
def list_periodontogram_evolution_candidates_endpoint(
    exam_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.view"))],
) -> PeriodontalEvolutionCandidateListResponse:
    try:
        return list_periodontal_evolution_candidates(session, context, exam_id)
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.post(
    "/api/periodontograms/{exam_id}/evolution-link",
    response_model=PeriodontalExamActionResponse,
)
def link_periodontogram_evolution_endpoint(
    exam_id: UUID,
    payload: PeriodontalEvolutionLinkRequest,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.finalize"))],
) -> PeriodontalExamActionResponse:
    try:
        return link_periodontal_exam_to_evolution(session, context, exam_id, payload)
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.post(
    "/api/periodontograms/{exam_id}/finalize",
    response_model=PeriodontalExamActionResponse,
)
def finalize_periodontogram_endpoint(
    exam_id: UUID,
    payload: PeriodontalExamFinalizeRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.finalize"))],
) -> PeriodontalExamActionResponse:
    try:
        return finalize_periodontal_exam(
            session, context, exam_id, payload, get_request_metadata(request)
        )
    except PeriodontogramError as exc:
        raise _handle(exc)


@router.post(
    "/api/periodontograms/{exam_id}/correct",
    response_model=PeriodontalExamActionResponse,
    status_code=201,
)
def correct_periodontogram_endpoint(
    exam_id: UUID,
    payload: PeriodontalExamCorrectionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[AuthContext, Depends(require_permission("periodontogram.correct"))],
) -> PeriodontalExamActionResponse:
    try:
        return correct_periodontal_exam(
            session, context, exam_id, payload, get_request_metadata(request)
        )
    except PeriodontogramError as exc:
        raise _handle(exc)
