from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_request_metadata, require_permission
from app.database.session import get_db
from app.schemas.orthodontic_evolution_schema import (
    OrthodonticCatalogOptionCreateRequest,
    OrthodonticCatalogOptionResponse,
    OrthodonticCatalogResponse,
    OrthodonticEvolutionCreateRequest,
    OrthodonticEvolutionListResponse,
    OrthodonticEvolutionResponse,
    OrthodonticEvolutionSignRequest,
    OrthodonticEvolutionUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.orthodontic_evolution_service import (
    OrthodonticEvolutionError,
    create_catalog_option,
    create_orthodontic_evolution,
    get_orthodontic_evolution,
    list_catalog,
    list_orthodontic_evolutions,
    retire_catalog_option,
    sign_orthodontic_evolution,
    update_orthodontic_evolution,
)


router = APIRouter(tags=["Orthodontics"])


def _handle(exc: OrthodonticEvolutionError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get(
    "/api/orthodontics/catalogs/{catalog_type}",
    response_model=OrthodonticCatalogResponse,
)
def catalog_endpoint(
    catalog_type: str,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.catalog.view"))
    ],
) -> OrthodonticCatalogResponse:
    try:
        return list_catalog(session, context, catalog_type)
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/catalogs/{catalog_type}/options",
    response_model=OrthodonticCatalogOptionResponse,
    status_code=201,
)
def create_catalog_option_endpoint(
    catalog_type: str,
    payload: OrthodonticCatalogOptionCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.catalog.manage"))
    ],
) -> OrthodonticCatalogOptionResponse:
    try:
        return create_catalog_option(
            session, context, catalog_type, payload, get_request_metadata(request)
        )
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/catalog-options/{option_id}/retire",
    response_model=OrthodonticCatalogOptionResponse,
)
def retire_catalog_option_endpoint(
    option_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("orthodontics.catalog.manage"))
    ],
) -> OrthodonticCatalogOptionResponse:
    try:
        return retire_catalog_option(
            session, context, option_id, get_request_metadata(request)
        )
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.get(
    "/api/orthodontics/cases/{case_id}/evolutions",
    response_model=OrthodonticEvolutionListResponse,
)
def list_evolutions_endpoint(
    case_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.view"))
    ],
) -> OrthodonticEvolutionListResponse:
    try:
        return list_orthodontic_evolutions(session, context, case_id)
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/cases/{case_id}/evolutions",
    response_model=OrthodonticEvolutionResponse,
    status_code=201,
)
def create_evolution_endpoint(
    case_id: UUID,
    payload: OrthodonticEvolutionCreateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.create"))
    ],
) -> OrthodonticEvolutionResponse:
    try:
        return create_orthodontic_evolution(
            session, context, case_id, payload, get_request_metadata(request)
        )
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.get(
    "/api/orthodontics/evolutions/{evolution_id}",
    response_model=OrthodonticEvolutionResponse,
)
def get_evolution_endpoint(
    evolution_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.view"))
    ],
) -> OrthodonticEvolutionResponse:
    try:
        return get_orthodontic_evolution(session, context, evolution_id)
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.patch(
    "/api/orthodontics/evolutions/{evolution_id}/draft",
    response_model=OrthodonticEvolutionResponse,
)
def update_evolution_endpoint(
    evolution_id: UUID,
    payload: OrthodonticEvolutionUpdateRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.update_draft"))
    ],
) -> OrthodonticEvolutionResponse:
    try:
        return update_orthodontic_evolution(
            session, context, evolution_id, payload, get_request_metadata(request)
        )
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)


@router.post(
    "/api/orthodontics/evolutions/{evolution_id}/sign",
    response_model=OrthodonticEvolutionResponse,
)
def sign_evolution_endpoint(
    evolution_id: UUID,
    payload: OrthodonticEvolutionSignRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    context: Annotated[
        AuthContext, Depends(require_permission("clinical_evolutions.sign"))
    ],
) -> OrthodonticEvolutionResponse:
    try:
        return sign_orthodontic_evolution(
            session, context, evolution_id, payload, get_request_metadata(request)
        )
    except OrthodonticEvolutionError as exc:
        raise _handle(exc)
